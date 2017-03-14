###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#		   http://ilastik.org/license/
###############################################################################

import time
import collections
from itertools import starmap
import numpy
import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.opCache import ManagedBlockedCache
from lazyflow.request import RequestLock
from lazyflow.roi import getIntersection, roiFromShape, roiToSlice, containing_rois, sliceToRoi

import logging
logger = logging.getLogger(__name__)

class OpUnblockedArrayCache(Operator, ManagedBlockedCache):
    """
    This cache operator stores the results of all requests that pass through 
    it, in exactly the same blocks that were requested.

    - If there are any overlapping requests, then the data for the overlapping portion will 
        be stored multiple times, except for the special case where the new request happens 
        to fall ENTIRELY within an existing block of data.
    - If any portion of a stored block is marked dirty, the entire block is discarded.

    Unlike other caches, this cache does not impose its own blocking on the data.
    Instead, it is assumed that the downstream operators have chosen some reasonable blocking.
    Hopefully the downstream operators are reasonably consistent in the blocks they request data with,
    since every unique result is cached separately.
    """
    Input = InputSlot(allow_mask=True)
    CompressionEnabled = InputSlot(value=False) # If True, compression will be enabled for certain dtypes
    Output = OutputSlot(allow_mask=True)
    BypassModeEnabled = InputSlot(value=False)

    CleanBlocks = OutputSlot() # A list of slicings indicating which blocks are stored in the cache and clean.
    
    def __init__(self, *args, **kwargs):
        super( OpUnblockedArrayCache, self ).__init__(*args, **kwargs)
        self._lock = RequestLock()
        self._resetBlocks()

        self.Input.notifyUnready(self._resetBlocks)

        # Now that we're initialized, it's safe to register with the memory manager
        self.registerWithMemoryManager()
    
    def _standardize_roi(self, start, stop):
        # We use rois as dict keys.
        # For comparison purposes, all rois in the dict keys are assumed to be tuple-of-tuples-of-int
        start = tuple(map(int, start))
        stop = tuple(map(int, stop))        
        return (start, stop)

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        self.CleanBlocks.meta.shape = (1,)
        self.CleanBlocks.meta.dtype = object # it's a list
    
    def execute(self, slot, subindex, roi, result):
        if slot is self.Output:
            self._execute_Output(slot, subindex, roi, result)
        elif slot is self.CleanBlocks:
            self._execute_CleanBlocks(slot, subindex, roi, result)
        else:
            assert False, "Unknown output slot: {}".format( slot.name )
        
    def _execute_Output(self, slot, subindex, roi, result):
        self._execute_Output_impl((roi.start, roi.stop), result)
        
    def _execute_Output_impl(self, request_roi, result):
        request_roi = self._standardize_roi(*request_roi)
        with self._lock:
            block_roi = self._get_containing_block_roi( request_roi )
            if block_roi is not None:
                # Data is already in the cache. Just extract it.
                block_relative_roi = numpy.array( request_roi ) - block_roi[0]
                self.Output.stype.copy_data(result, self._block_data[block_roi][ roiToSlice(*block_relative_roi) ])
                return

        if self.Input.meta.dontcache:
            # Data isn't in the cache, but we don't want to cache it anyway.
            self.Input(*request_roi).writeInto(result).block()
            return
        
        # Data isn't in the cache, so request it and cache it
        self._fetch_and_store_block(request_roi, out=result)

    def _get_containing_block_roi(self, request_roi):
        # Does this roi happen to fit ENTIRELY within an existing stored block?
        request_roi = self._standardize_roi(*request_roi)
        outer_rois = containing_rois( self._block_data.keys(), request_roi )
        if len(outer_rois) > 0:
            # Standardize roi for usage as dict key
            block_roi = self._standardize_roi( *outer_rois[0] )
            return block_roi
        return None

    def _fetch_and_store_block(self, block_roi, out):
        if out is not None:
            roi_shape = numpy.array(block_roi[1]) - block_roi[0]
            assert (out.shape == roi_shape).all()
        
        # Get lock for this block (create first if necessary)
        with self._lock:
            if block_roi not in self._block_locks:
                self._block_locks[block_roi] = RequestLock()
            block_lock = self._block_locks[block_roi]

        # Handle identical simultaneous requests for the same block
        # without preventing parallel requests for different blocks.
        with block_lock:
            if block_roi in self._block_data:
                if out is None:
                    # Extra [:] here is in case we are decompressing from a chunkedarray
                    return self._block_data[block_roi][:]
                else:
                    # Extra [:] here is in case we are decompressing from a chunkedarray
                    self.Output.stype.copy_data(out, self._block_data[block_roi][:])
                    return out

            req = self.Input(*block_roi)
            if out is not None:
                req.writeInto(out)
            block_data = req.wait()
            self._store_block_data(block_roi, block_data)
        return block_data

    
    def _store_block_data(self, block_roi, block_data):
        """
        Copy block_data and store it into the cache.
        The block_lock is not obtained here, so lock it before you call this.
        """
        with self._lock:
            if self.CompressionEnabled.value and numpy.dtype(block_data.dtype) in [numpy.dtype(numpy.uint8),
                                                                                   numpy.dtype(numpy.uint32),
                                                                                   numpy.dtype(numpy.float32)]:
                compressed_block = vigra.ChunkedArrayCompressed( block_data.shape, vigra.Compression.LZ4, block_data.dtype )
                compressed_block[:] = block_data
                block_storage_data = compressed_block
            else:
                block_storage_data = block_data.copy()

            # Store the data.
            # First double-check that the block wasn't removed from the 
            #   cache while we were requesting it. 
            # (Could have happened via propagateDirty() or eventually the arrayCacheMemoryMgr)
            if block_roi in self._block_locks:
                self._block_data[block_roi] = block_storage_data

        self._last_access_times[block_roi] = time.time()

    def _execute_CleanBlocks(self, slot, subindex, roi, result):
        with self._lock:
            block_rois = sorted(self._block_data.keys())            
            block_slicings = list(starmap( roiToSlice, block_rois ))
            result[0] = block_slicings

    def setInSlot(self, slot, subindex, roi, block_data):
        assert slot == self.Input
        block_roi = (tuple(roi.start), tuple(roi.stop))
        
        with self._lock:
            if block_roi not in self._block_locks:
                self._block_locks[block_roi] = RequestLock()
            block_lock = self._block_locks[block_roi]

        with block_lock:
            self._store_block_data(block_roi, block_data)

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.BypassModeEnabled or slot == self.CompressionEnabled:
          pass 
        else:
            dirty_roi = self._standardize_roi( roi.start, roi.stop )
            maximum_roi = roiFromShape(self.Input.meta.shape)
            maximum_roi = self._standardize_roi( *maximum_roi )
            
            if dirty_roi == maximum_roi:
                # Optimize the common case:
                # Everything is dirty, so no need to loop
                self._resetBlocks()
            else:
                # FIXME: This is O(N) for now.
                #        We should speed this up by maintaining a bookkeeping data structure in execute().
                for block_roi in self._block_data.keys():
                    if getIntersection(block_roi, dirty_roi, assertIntersect=False):
                        self.freeBlock(block_roi)
    
            self.Output.setDirty( roi.start, roi.stop )

    ##
    ## OpManagedCache interface implementation
    ##
    def usedMemory(self):
        total = 0.0
        for k in self._block_data.keys():
            try:
                block = self._block_data[k]
                bytes_per_pixel = numpy.dtype(block.dtype).itemsize
                portion = block.size * bytes_per_pixel
            except (KeyError, AttributeError):
                # what could have happened and why it's fine
                #  * block was deleted (then it does not occupy memory)
                #  * block is not array data (then we don't know how
                #    much memory it ouccupies)
                portion = 0.0
            total += portion
        return total
    
    def fractionOfUsedMemoryDirty(self):
        # dirty memory is discarded immediately
        return 0.0

    def lastAccessTime(self):
        return super(OpUnblockedArrayCache, self).lastAccessTime()

    def getBlockAccessTimes(self):
        with self._lock:
            # needs to be locked because dicts must not change size
            # during iteration
            l = [(k, self._last_access_times[k])
                 for k in self._last_access_times]
        return l

    def freeMemory(self):
        used = self.usedMemory()
        self._resetBlocks()
        return used

    def freeBlock(self, key):
        with self._lock:
            if key not in self._block_locks:
                return 0
            block = self._block_data[key]
            bytes_per_pixel = numpy.dtype(block.dtype).itemsize
            mem = block.size * bytes_per_pixel
            del self._block_data[key]
            del self._block_locks[key]
            del self._last_access_times[key]
            return mem

    def freeDirtyMemory(self):
        return 0.0

    def _resetBlocks(self, *_):
        with self._lock:
            self._block_data = {}
            self._block_locks = {}
            self._last_access_times = collections.defaultdict(float)
