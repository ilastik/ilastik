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
# Built-in
import logging
from functools import partial
import collections
import itertools
import time

# Third-party
import numpy
import h5py

# Lazyflow
from lazyflow.request import Request, RequestPool, RequestLock
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import TinyVector, getIntersectingBlocks, getBlockBounds, roiToSlice, getIntersection
from lazyflow.operators.opCache import ManagedBlockedCache
from lazyflow.utility.chunkHelpers import chooseChunkShape

logger = logging.getLogger(__name__)


def get_storage_size(h5dataset):
    '''
    get the storage size allocated for this hdf5 dataset in bytes

    (shorthand for the hidden h5py functionality)
    '''
    return h5py.h5d.DatasetID.get_storage_size(h5dataset.id)

class OpUnmanagedCompressedCache(Operator):
    """
    A blockwise cache that stores each block as a separate in-memory hdf5 file with a compressed dataset.

    The files for each block have an internal chunk-shape, which corresponds to
    the amount of data that has to be decompressed for a single pixel lookup.
    The chunk shape is prioritized as follows:
        1. Input.meta.ideal_blockshape
           (make sure to set BlockShape to a multiple of ideal_blockshape!)
        2. BlockShape, if available and smaller than 1MiB (raw)
        3. Automatically determined shape with t=1, c=1 and xyz such that the
           blocks are smaller than 1MiB (raw)

    Note: This class is not managed by the memory manager, so there can be non-managed subclasses.
          The "managed" version is OpCompressedCache, defined below.
    
    Note: 
      * It is not safe to call execute() and change the blockshape
        simultaneously.
      * it is not safe to reuse this cache #FIXME
    """
    # Also used to asynchronously force data into the cache via __setitem__ (see setInSlot(), below()
    Input = InputSlot(allow_mask=True) 

    # shape of internal in-memory hdf5 files (defaults to the whole volume)
    BlockShape = InputSlot(optional=True)

    # Output as numpy arrays
    Output = OutputSlot(allow_mask=True)

    InputHdf5 = InputSlot(optional=True, allow_mask=True)
    # A list of rois (tuples) of the blocks that are currently stored in the cache
    CleanBlocks = OutputSlot()
    # Provides data as hdf5 datasets.  Only allowed for rois that exactly match a block.
    OutputHdf5 = OutputSlot(allow_mask=True)

    def __init__(self, *args, **kwargs):
        super( OpUnmanagedCompressedCache, self ).__init__( *args, **kwargs )
        self._lock = RequestLock()
        self._init_cache(None)
        self._block_id_counter = itertools.count() # Used to ensure unique in-memory file names
        self._ignore_ideal_blockshape = False

    def _init_cache(self, new_blockshape):
        with self._lock:
            self._blockshape = new_blockshape
            self._cacheFiles = {}
            self._dirtyBlocks = set()
            self._blockLocks = {}
            self._chunkshape = self._chooseChunkshape(self._blockshape)
            self._last_access_times = collections.defaultdict(float)

    def cleanUp(self):
        logger.debug( "Cleaning up" )
        self._closeAllCacheFiles()
        super( OpUnmanagedCompressedCache, self ).cleanUp()


    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        self.OutputHdf5.meta.assignFrom(self.Input.meta)
        self.CleanBlocks.meta.shape = (1,)
        self.CleanBlocks.meta.dtype = object

        # no block shape given -> use the whole volume as one block
        new_blockshape = self.Input.meta.shape
        if self.BlockShape.ready():
            new_blockshape = self.BlockShape.value

        if len(new_blockshape) != len(self.Input.meta.shape):
            self.Output.meta.NOTREADY = True
            self.CleanBlocks.meta.NOTREADY = True
            self.OutputHdf5.meta.NOTREADY = True
            self._init_cache(None)
            return

        # Clip blockshape to image bounds
        new_blockshape = tuple(numpy.minimum( new_blockshape, self.Input.meta.shape ))

        if new_blockshape != self._blockshape:
            # If the blockshape changes, we have to reset the entire cache.
            self._init_cache(new_blockshape)

        self.Output.meta.ideal_blockshape = self._chunkshape
        

    def execute(self, slot, subindex, roi, destination):
        if slot == self.Output:
            return self._executeOutput(roi, destination)
        elif slot == self.CleanBlocks:
            return self._executeCleanBlocks(destination)
        elif slot == self.OutputHdf5:
            return self._executeOutputHdf5( roi, destination )
        else:
            assert False, "Unknown output slot: {}".format( slot.name )
        

    def _executeOutput(self, roi, destination):
        assert len(roi.stop) == len(self.Input.meta.shape), \
            "roi: {} has the wrong number of dimensions for Input shape: {}"\
            "".format( roi, self.Input.meta.shape )
        assert numpy.less_equal(roi.stop, self.Input.meta.shape).all(), \
            "roi: {} is out-of-bounds for Input shape: {}"\
            "".format( roi, self.Input.meta.shape )
        
        block_starts = getIntersectingBlocks( self._blockshape, (roi.start, roi.stop) )
        block_starts = map( tuple, block_starts )

        # Ensure all block cache files are up-to-date
        self._waitForBlocks(block_starts)
        self._copyData(roi, destination, block_starts)
        return destination

    def _waitForBlocks(self, block_starts):
        """
        Make sure that all blocks in the given list of blocks are present in the cache before returning.
        (Blocks that are not yet present will be requested from our Input slot.)
        """
        reqPool = RequestPool() # (Do the work in parallel.)
        for block_start in block_starts:
            entire_block_roi = getBlockBounds( self.Output.meta.shape, self._blockshape, block_start )
            f = partial( self._ensureCached, entire_block_roi)
            reqPool.add( Request(f) )
        logger.debug( "Waiting for {} blocks...".format( len(block_starts) ) )
        reqPool.wait()

    def _copyData(self, roi, destination, block_starts):
        # Copy data from each block
        # (Parallelism not needed here: h5py will serialize these requests anyway)
        logger.debug( "Copying data from {} blocks...".format( len(block_starts) ) )
        for block_start in block_starts:
            entire_block_roi = getBlockBounds( self.Output.meta.shape, self._blockshape, block_start )

            # This block's portion of the roi
            intersecting_roi = getIntersection( (roi.start, roi.stop), entire_block_roi )
            
            # Compute slicing within destination array and slicing within this block
            destination_relative_intersection = numpy.subtract(intersecting_roi, roi.start)
            block_relative_intersection = numpy.subtract(intersecting_roi, block_start)
            destination_relative_intersection_slicing = roiToSlice(*destination_relative_intersection)
            block_relative_intersection_slicing = roiToSlice( *block_relative_intersection )
            
            # Copy from block to destination
            dataset = self._getBlockDataset( entire_block_roi )
            if self.Output.meta.has_mask:
                destination.data[ destination_relative_intersection_slicing ] = dataset["data"][ block_relative_intersection_slicing ]
                destination.mask[ destination_relative_intersection_slicing ] = dataset["mask"][ block_relative_intersection_slicing ]
                destination.fill_value = dataset["fill_value"][()]
            else:
                destination[ destination_relative_intersection_slicing ] = dataset[ block_relative_intersection_slicing ]
            self._last_access_times[block_start] = time.time()

    def _executeCleanBlocks(self, destination):
        """
        Execute function for the CleanBlocks output slot, which produces 
        an *unsorted* list of block rois that the cache currently holds.
        """
        # Set difference: clean = existing - dirty
        clean_block_starts = set( self._cacheFiles.keys() ) - self._dirtyBlocks
        
        output_shape = self.Output.meta.shape
        clean_block_rois = map( partial( getBlockBounds, output_shape, self._blockshape ),
                                clean_block_starts )
        destination[0] = map( partial(map, TinyVector), clean_block_rois )
        return destination

    def _executeOutputHdf5(self, roi, destination):
        logger.debug("Servicing request for hdf5 block {}".format( roi ))

        assert isinstance( destination, h5py.Group ), "OutputHdf5 slot requires an hdf5 GROUP to copy into (not a numpy array)."
        assert ((roi.start % self._blockshape) == 0).all(), "OutputHdf5 slot requires roi to be exactly one block."
        block_roi = getBlockBounds( self.Output.meta.shape, self._blockshape, roi.start )
        assert (block_roi == numpy.array((roi.start, roi.stop))).all(), "OutputHdf5 slot requires roi to be exactly one block."

        block_roi = [roi.start, roi.stop]
        self._ensureCached( block_roi )
        dataset = self._getBlockDataset( block_roi )
        assert str(block_roi) not in destination, "destination hdf5 group already has a dataset with this block's name"
        destination.copy( dataset, str(block_roi) )
        return destination        

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Input:
            # Keep track of dirty blocks
            if self._blockshape is not None:
                with self._lock:
                    block_starts = getIntersectingBlocks( self._blockshape, (roi.start, roi.stop) )
                    block_starts = map( tuple, block_starts )
                    
                    for block_start in block_starts:
                        self._dirtyBlocks.add( block_start )
            # Forward to downstream connections
            self.Output.setDirty( roi )
        elif slot == self.BlockShape:
            # Everything is dirty
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown output slot"

    def _chooseChunkshape(self, blockshape):
        """
        Choose an optimal chunkshape for our blockshape and Input shape.
        We assume access patterns to vary more in space than in time or channel
        and choose the inner chunk shape to be about 1MiB slices of t and c.
        Furthermore, we use the function
          lazyflow.utility.chunkHelpers.chooseChunkShape()
        to preserve the aspect ratio of the input (at least approximately).
        """
        if blockshape is None:
            return None

        def isConsistent(idealshape):
            """
            check if ideal block shape and given block shape are consistent

            shapes are consistent if, for each dimension,
                * input is unready, or
                * blockshape equals fullshape, or
                * idealshape divides blockshape evenly
            """
            if not self.Input.ready():
                return True

            fullshape = self.Input.meta.shape
            z = zip(idealshape, blockshape, fullshape)
            m = map(lambda (i, b, f): b == f or b % i == 0, z)
            return all(m)

        if not self._ignore_ideal_blockshape and self.Input.ready():
            # take the ideal chunk shape, but check if sane
            ideal = self.Input.meta.ideal_blockshape
            if ideal is not None:
                if len(ideal) == len(blockshape):
                    ideal = numpy.asarray(ideal, dtype=numpy.int)
                    for i, d in enumerate(ideal):
                        if d == 0:
                            ideal[i] = blockshape[i]
                    if not isConsistent(ideal):
                        logger.warn("{}: BlockShape and ideal_blockshape are "
                                    "inconsistent {} vs {}".format(self.name, blockshape, ideal))
                    else:
                        return tuple(ideal)
                else:
                    logger.warn("{}: Encountered meta.ideal_blockshape that does "
                                "not fit the data".format(self.name))

        # we need to figure out an ideal chunk shape on our own

        # Start with a copy of blockshape
        axes = self.Output.meta.getTaggedShape().keys()
        taggedBlockShape = collections.OrderedDict(zip(axes, self._blockshape))

        dtypeBytes = self._getDtypeBytes(self.Output.meta.dtype)

        desiredSpace = 1024**2 / float(dtypeBytes)

        if numpy.prod(blockshape) <= desiredSpace:
            return blockshape

        # set t and c to 1
        for key in 'tc':
            if key in taggedBlockShape:
                taggedBlockShape[key] = 1
        logger.debug("desired space: {}".format(desiredSpace))

        # extract only the spatial shape
        spatialKeys = [k for k in taggedBlockShape.keys() if k in 'xyz']
        spatialShape = [taggedBlockShape[k] for k in spatialKeys]
        newSpatialShape = chooseChunkShape(spatialShape, desiredSpace)
        for k, v in zip(spatialKeys, newSpatialShape):
            taggedBlockShape[k] = v
        chunkShape = tuple(taggedBlockShape.values())
        logger.debug("Using chunk shape: {}".format(chunkShape))
        return chunkShape

    def _getDtypeBytes(self, dtype):
        if type(dtype) is numpy.dtype:
            # Make sure we're dealing with a type (e.g. numpy.float64),
            #  not a numpy.dtype
            dtype = dtype.type
        return dtype().nbytes

    def usedMemory(self):
        tot, unc = self._usedMemory()
        self._compression_factor = 1.0
        if tot > 0:
            self._compression_factor = unc/float(tot)
        return tot

    def _usedMemory(self):
        tot = 0.0
        unc = 0.0
        for key in self._cacheFiles.keys():
            real, virt = self._memoryForBlock(key)
            tot += real
            unc += virt
        return tot, unc

    def _memoryForBlock(self, key):
        try:
            group = self._cacheFiles[key]
        except KeyError:
            # entry was removed, ignore it
            return 0
        tot = 0
        unc = 0
        if "data" in group:
            ds = group["data"]
            # actual size
            tot += get_storage_size(ds)
            # uncompressed size
            unc += ds.size * self._getDtypeBytes(ds.dtype)
        if "mask" in group:
            tot += group["mask"].size *\
                self._getDtypeBytes(group["mask"].dtype)
        if "fill_value" in group:
            tot += group["fill_value"].size *\
                self._getDtypeBytes(group["fill_value"].dtype)
        return tot, unc

    def _getCacheFile(self, entire_block_roi):
        """
        Get the cache file for the block that starts at block_start.
        If it doesn't exist yet, create it first.
        """
        block_start = tuple(entire_block_roi[0])
        if block_start in self._cacheFiles:
            return self._cacheFiles[block_start]
        with self._lock:
            if block_start not in self._cacheFiles:
                # Create an in-memory hdf5 file with a unique name 
                # (the counter ensures that even blocks that have been deleted previously get a unique name when they are re-created).
                logger.debug("Creating a cache file for block: {}".format( list(block_start) ))
                filename = str(id(self)) + str(id(self._cacheFiles)) + str(block_start) + str(self._block_id_counter.next())
                mem_file = h5py.File(filename, driver='core', backing_store=False, mode='w')

                # h5py will crash if the chunkshape is larger than the dataset shape.
                datashape = tuple( entire_block_roi[1] - entire_block_roi[0] )
                chunkshape = numpy.minimum(numpy.array(datashape), self._chunkshape )
                chunkshape = tuple(chunkshape)

                # Make a compressed dataset
                mem_file.create_dataset('data',
                                        shape=datashape,
                                        dtype=self.Output.meta.dtype,
                                        chunks=chunkshape,
                                        compression='lzf' ) # lzf should be faster than gzip,
                                                            # with a slightly worse compression ratio
                # Add mask information if needed.
                if self.Output.meta.has_mask:
                    mem_file.create_dataset('mask',
                                            shape=datashape,
                                            dtype=bool,
                                            chunks=chunkshape,
                                            compression='lzf' ) # lzf should be faster than gzip,
                                                                # with a slightly worse compression ratio
                    mem_file.create_dataset('fill_value',
                                            shape=tuple(),
                                            dtype=self.Output.meta.dtype )

                self._blockLocks[block_start] = RequestLock()
                self._cacheFiles[block_start] = mem_file
                self._dirtyBlocks.add( block_start )
            return self._cacheFiles[block_start]


    def _ensureCached(self, entire_block_roi):
        """
        Ensure that the cache file for the given block is up-to-date.
        (Refresh it if it's dirty.)
        """
        block_start = tuple(entire_block_roi[0])
        block_file = self._getCacheFile(entire_block_roi)
        if block_start in self._dirtyBlocks:
            updated_cache = False
            with self._blockLocks[block_start]:
                # Check AGAIN now that we have the lock.
                # (Avoid doing this twice in parallel requests.)
                if block_start in self._dirtyBlocks:
                    # Can't write directly into the hdf5 dataset because 
                    #  h5py.dataset.__getitem__ creates a copy, not a view.
                    # We must use a temporary numpy array to hold the data.
                    data = self.Input(*entire_block_roi).wait()
                    block_file['data'][...] = data
                    if self.Output.meta.has_mask:
                        block_file['mask'][...] = data.mask
                        block_file['fill_value'][...] = data.fill_value
                    
                    if logger.isEnabledFor(logging.DEBUG):
                        uncompressed_size = numpy.prod(data.shape) * self._getDtypeBytes(data.dtype)
                        storage_size = block_file["data"].id.get_storage_size()
                        if 'mask' in block_file:
                            storage_size += block_file["mask"].id.get_storage_size()
                        if 'fill_value' in block_file:
                            storage_size += block_file["fill_value"].id.get_storage_size()
                        logger.debug("Storage for block: {} is {}. ({}% of original)".format( block_start, storage_size, 100*storage_size/uncompressed_size ))
                    with self._lock:
                        self._dirtyBlocks.remove( block_start )
                    updated_cache = True

            if updated_cache:
                # Now that the lock is released, signal that the cache was updated. 
                self.Output._sig_value_changed()
                self.OutputHdf5._sig_value_changed()
                self.CleanBlocks._sig_value_changed()

    def setInSlot(self, slot, subindex, roi, value):
        """
        Overridden from Operator
        """
        if slot == self.Input:
            self._setInSlotInput(slot, subindex, roi, value)
        elif slot == self.InputHdf5:
            self._setInSlotInputHdf5(slot, subindex, roi, value)
        else:
            assert False, "Invalid input slot for setInSlot(): {}".format( slot.name )

    def _setInSlotInput(self, slot, subindex, roi, value, store_zero_blocks=True):
        """
        Write the data in the array 'value' into the cache.
        If the optional store_zero_blocks param is False, then don't bother 
        creating cache blocks for blocks that are totally zero.
        """
        assert len(roi.stop) == len(self.Input.meta.shape), \
            "roi: {} has the wrong number of dimensions for Input shape: {}"\
            "".format( roi, self.Input.meta.shape )
        assert numpy.less_equal(roi.stop, self.Input.meta.shape).all(), \
            "roi: {} is out-of-bounds for Input shape: {}"\
            "".format( roi, self.Input.meta.shape )
        
        block_starts = getIntersectingBlocks( self._blockshape, (roi.start, roi.stop) )
        block_starts = map( tuple, block_starts )

        # Copy data to each block
        logger.debug( "Copying data INTO {} blocks...".format( len(block_starts) ) )
        for block_start in block_starts:
            entire_block_roi = getBlockBounds( self.Output.meta.shape, self._blockshape, block_start )

            # This block's portion of the roi
            intersecting_roi = getIntersection( (roi.start, roi.stop), entire_block_roi )
            
            # Compute slicing within source array and slicing within this block
            source_relative_intersection = numpy.subtract(intersecting_roi, roi.start)
            block_relative_intersection = numpy.subtract(intersecting_roi, block_start)
            source_relative_intersection_slicing = roiToSlice( *source_relative_intersection )
            block_relative_intersection_slicing = roiToSlice( *block_relative_intersection )
            
            new_block_data = value[ source_relative_intersection_slicing ]
            new_block_sum = new_block_data.sum()
            if not store_zero_blocks and new_block_sum == 0 and block_start not in self._cacheFiles:
                # Special fast-path: If this block doesn't exist yet, 
                #  don't bother creating if we're just going to fill it with zeros.
                # (This feature is used by the OpCompressedUserLabelArray)
                pass
            else:
                # Copy from source to block
                dataset = self._getBlockDataset( entire_block_roi )
                if self.Output.meta.has_mask:
                    dataset["data"][ block_relative_intersection_slicing ] = new_block_data.data
                    dataset["mask"][ block_relative_intersection_slicing ] = new_block_data.mask
                    dataset["fill_value"][()] = new_block_data.fill_value

                    # Untested. Write a test to use this.
                    # # If we can, remove this block entirely.
                    # if not store_zero_blocks and new_block_sum == 0 and (dataset["data"][:] == 0).all() and (dataset["mask"]).any() and (dataset["fill_value"] == 0).all():
                    #     with self._lock:
                    #         with self._blockLocks[block_start]:
                    #            self._cacheFiles[block_start].close()
                    #            del self._cacheFiles[block_start]
                    #         del self._blockLocks[block_start]
                else:
                    dataset[ block_relative_intersection_slicing ] = new_block_data

                    # If we can, remove this block entirely.
                    if not store_zero_blocks and new_block_sum == 0 and (dataset[:] == 0).all():
                        with self._lock:
                            with self._blockLocks[block_start]:
                               self._cacheFiles[block_start].close()
                               del self._cacheFiles[block_start]
                            del self._blockLocks[block_start]
    
            # Here, we assume that if this function is used to update ANY PART of a 
            #  block, he is responsible for updating the ENTIRE block.
            # Therefore, this block is no longer 'dirty'
            self._dirtyBlocks.discard( block_start )
    
    #            self.Output._sig_value_changed()
    #            self.OutputHdf5._sig_value_changed()
    #            self.CleanBlocks._sig_value_changed()

    def _setInSlotInputHdf5(self, slot, subindex, roi, value):
        logger.debug("Setting block {} from hdf5".format( roi ))
        if self.Output.meta.has_mask:
            assert isinstance( value, h5py.Group ), "InputHdf5 slot requires an hdf5 Group to copy from (not a numpy masked array)."
        else:
            assert isinstance( value, h5py.Dataset ), "InputHdf5 slot requires an hdf5 Dataset to copy from (not a numpy array)."

        block_roi = getBlockBounds( self.Output.meta.shape, self._blockshape, roi.start )

        roi_is_exactly_one_block = True
        roi_is_exactly_one_block &= ((roi.start % self._blockshape) == 0).all()
        roi_is_exactly_one_block &= (block_roi == numpy.array((roi.start, roi.stop))).all()
        if roi_is_exactly_one_block:
            cachefile = self._getCacheFile( block_roi )
            logger.debug( "Copying HDF5 data directly into block {}".format( block_roi ) )

            if self.Output.meta.has_mask:
                assert len(value) == 3

                for each in ["data", "mask", "fill_value"]:
                    assert each in value
                    assert cachefile[each].dtype == value[each].dtype
                    assert cachefile[each].shape == value[each].shape

                for each in ["data", "mask", "fill_value"]:
                    del cachefile[each]
                    cachefile.copy( value[each], each )
            else:
                assert cachefile['data'].dtype == value.dtype
                assert cachefile['data'].shape == value.shape
                del cachefile['data']
                cachefile.copy( value, 'data' )

            block_start = tuple(roi.start)
            self._dirtyBlocks.discard( block_start )
        else:
            # This hdf5 data does not correspond to exactly one block.
            # We must uncompress it and write it the "normal" way (the slow way)
            # FIXME: This would use less memory if we uncompressed the data block-by-block
            data = None

            if self.Output.meta.has_mask:
                data = numpy.ma.masked_array(
                    value["data"][()],
                    mask=value["mask"][()],
                    fill_value=value["fill_value"][()],
                    shrink=False
                )
            else:
                data = value[()]

            self.Input[roiToSlice(roi.start, roi.stop)] = data

#        self.Output._sig_value_changed()
#        self.OutputHdf5._sig_value_changed()
#        self.CleanBlocks._sig_value_changed()

    def _getBlockDataset(self, entire_block_roi):
        """
        Get the correct cache file and return the *dataset* handle,
        not a numpy array of its contents.
        """
        block_file = self._getCacheFile(entire_block_roi)
        if self.Output.meta.has_mask:
            return block_file['/']
        else:
            return block_file['data']


    def _closeAllCacheFiles(self):
        logger.debug( "Closing all caches" )
        cacheFiles = self._cacheFiles
        for k,v in cacheFiles.items():
            with self._blockLocks[k]:
                v.close()
        with self._lock:
            self._blockLocks = {}
            self._cacheFiles = {}

class OpCompressedCache(OpUnmanagedCompressedCache, ManagedBlockedCache):

    def __init__(self, *args, **kwargs):
        super(OpCompressedCache, self).__init__(*args, **kwargs)
        # Now that we're initialized, it's safe to register with the memory manager
        self.registerWithMemoryManager()

    def fractionOfUsedMemoryDirty(self):
        tot = 0.0
        dirty = 0.0
        for key in self._cacheFiles.keys():
            real, virt = self._memoryForBlock(key)
            tot += real
            if key in self._dirtyBlocks:
                dirty += real
        if tot > 0:
            return dirty / tot
        else:
            return 0.0
    
    def generateReport(self, report):
        super(OpCompressedCache, self).generateReport(report)
        report.dtype = self.Output.meta.dtype
        f = self._compression_factor
        report.info = "Compression factor: {:.2f}".format(f)

    def freeMemory(self):
        mem = self.usedMemory()
        self._closeAllCacheFiles()
        with self._lock:
            self._cacheFiles = {}
            self._dirtyBlocks = set()
        return mem

    def freeDirtyMemory(self):
        dirty = 0.0
        for key in self._cacheFiles.keys():
            if key in self._dirtyBlocks:
                dirty += self.freeBlock(key)
                with self._lock:
                    self._dirtyBlocks.discard(key)
        return dirty

    def freeBlock(self, block_id):
        if block_id not in self._blockLocks:
            return 0
        with self._blockLocks[block_id]:
            try:
                f = self._cacheFiles[block_id]
            except KeyError:
                # this file was deleted
                return 0
            if "data" not in f:
                return 0
            ds = f["data"]
            # use actual size, not number of bytes in
            # *uncompressed* array
            mem = get_storage_size(ds)
            f.close()
            del self._cacheFiles[block_id]
            del self._last_access_times[block_id]
            return mem

    def getBlockAccessTimes(self):
        with self._lock:
            # needs to be locked because dicts must not change size
            # during iteration
            return [(key, self._last_access_times[key])
                    for key in self._last_access_times]
