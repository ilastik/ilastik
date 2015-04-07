import numpy

from lazyflow.graph import InputSlot, OutputSlot
from lazyflow.operators.opCache import OpCache
from lazyflow.request import RequestLock
from lazyflow.roi import getIntersection, roiFromShape, roiToSlice, containing_rois

import logging
logger = logging.getLogger(__name__)

class OpUnblockedArrayCache(OpCache):
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
    Output = OutputSlot(allow_mask=True)
    
    def __init__(self, *args, **kwargs):
        super( OpUnblockedArrayCache, self ).__init__(*args, **kwargs)
        self._lock = RequestLock()
        self._block_data = {}
        self._block_locks = {}
    
    def _standardize_roi(self, start, stop):
        # We use rois as dict keys.
        # For comparison purposes, all rois in the dict keys are assumed to be tuple-of-tuples-of-int
        start = tuple(map(int, start))
        stop = tuple(map(int, stop))        
        return (start, stop)

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
    
    def execute(self, slot, subindex, roi, result):
        with self._lock:
            # Does this roi happen to fit ENTIRELY within an existing stored block?
            outer_rois = containing_rois( self._block_data.keys(), (roi.start, roi.stop) )
            if len(outer_rois) > 0:
                # Use the first one we found
                block_roi = self._standardize_roi( *outer_rois[0] )
                block_relative_roi = numpy.array( (roi.start, roi.stop) ) - block_roi[0]
                self.Output.stype.copy_data(result, self._block_data[block_roi][ roiToSlice(*block_relative_roi) ])
                return
                
        # Standardize roi for usage as dict key
        block_roi = self._standardize_roi( roi.start, roi.stop )
        
        # Get lock for this block (create first if necessary)
        with self._lock:
            if block_roi not in self._block_locks:
                self._block_locks[block_roi] = RequestLock()
            block_lock = self._block_locks[block_roi]

        # Handle identical simultaneous requests
        with block_lock:
            try:
                self.Output.stype.copy_data(result, self._block_data[block_roi])
                return
            except KeyError:
                # Not yet stored: Request it now.
                self.Input(roi.start, roi.stop).writeInto(result).block()
                block = result.copy()
                with self._lock:
                    # Store the data.
                    # First double-check that the block wasn't removed from the 
                    #   cache while we were requesting it. 
                    # (Could have happened via propagateDirty() or eventually the arrayCacheMemoryMgr)
                    if block_roi in self._block_locks:
                        self._block_data[block_roi] = block

    def propagateDirty(self, slot, subindex, roi):
        dirty_roi = self._standardize_roi( roi.start, roi.stop )
        maximum_roi = roiFromShape(self.Input.meta.shape)
        maximum_roi = self._standardize_roi( *maximum_roi )
        
        with self._lock:
            if dirty_roi == maximum_roi:
                # Optimize the common case:
                # Everything is dirty, so no need to loop
                self._block_data = {}
                self._block_locks = {}
            else:
                # FIXME: This is O(N) for now.
                #        We should speed this up by maintaining a bookkeeping data structure in execute().
                for block_roi in self._block_data.keys():
                    if getIntersection(block_roi, dirty_roi, assertIntersect=False):
                        del self._block_data[block_roi]
                        del self._block_locks[block_roi]

        self.Output.setDirty( roi.start, roi.stop )

    ##
    ## OpCache interface implementation
    ##
    def generateReport(self, report):
        raise NotImplementedError()
        
    def usedMemory(self):
        """used memory in bytes"""
        return 0 #overwrite me
    
    def fractionOfUsedMemoryDirty(self):
        """fraction of the currently used memory that is marked as dirty"""
        return 0 #overwrite me

    def lastAccessTime(self):
        """timestamp of last access (time.time())"""
        return 0 #overwrite me
