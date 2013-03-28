# Built-in
import copy
import logging
from functools import partial
import collections

# Third-party
import numpy
import h5py

# Lazyflow
from lazyflow.request import Request, RequestPool, RequestLock
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import TinyVector, getIntersectingBlocks, getBlockBounds, roiToSlice, getIntersection

logger = logging.getLogger(__name__)

class OpCompressedCache(Operator):
    """
    A blockwise cache that stores each block as a separate in-memory hdf5 file with a compressed dataset.
    """
    Input = InputSlot() # Also used to asynchronously force data into the cache via __setitem__ (see setInSlot(), below()
    BlockShape = InputSlot(optional=True) # If not provided, the entire input is treated as one block
    
    Output = OutputSlot() # Output as numpy arrays

    InputHdf5 = InputSlot(optional=True)
    CleanBlocks = OutputSlot() # A list of rois (tuples) of the blocks that are currently stored in the cache
    OutputHdf5 = OutputSlot() # Provides data as hdf5 datasets.  Only allowed for rois that exactly match a block.
    
    def __init__(self, *args, **kwargs):
        super( OpCompressedCache, self ).__init__( *args, **kwargs )
        self._blockshape = None
        self._cacheFiles = {}
        self._dirtyBlocks = set()
        self._lock = RequestLock()
        self._blockLocks = {}


    def cleanUp(self):
        logger.debug( "Cleaning up" )
        self._closeAllCacheFiles()
        super( OpCompressedCache, self ).cleanUp()


    def setupOutputs(self):
        self._closeAllCacheFiles()
        self.Output.meta.assignFrom(self.Input.meta)
        self.OutputHdf5.meta.assignFrom(self.Input.meta)
        self.CleanBlocks.meta.shape = (1,)
        self.CleanBlocks.meta.dtype = object

        # Clip blockshape to image bounds
        if self.BlockShape.ready():
            self._blockshape = numpy.minimum( self.BlockShape.value, self.Input.meta.shape )
        else:
            self._blockshape = self.Input.meta.shape
        
        # Choose optimal chunkshape
        self._chunkshape = self._chooseChunkshape(self._blockshape)


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
        assert len(roi.stop) == len(self.Input.meta.shape), "roi: {} has the wrong number of dimensions for Input shape: {}".format( roi, self.Input.meta.shape )
        assert numpy.less_equal(roi.stop, self.Input.meta.shape).all(), "roi: {} is out-of-bounds for Input shape: {}".format( roi, self.Input.meta.shape )
        
        block_starts = getIntersectingBlocks( self._blockshape, (roi.start, roi.stop) )
        block_starts = map( tuple, block_starts )

        # Ensure all block cache files are up-to-date
        reqPool = RequestPool() # (Do the work in parallel.)
        for block_start in block_starts:
            entire_block_roi = getBlockBounds( self.Input.meta.shape, self._blockshape, block_start )
            f = partial( self._ensureCached, entire_block_roi)
            reqPool.add( Request(f) )
        logger.debug( "Waiting for {} blocks...".format( len(block_starts) ) )
        reqPool.wait()

        # Copy data from each block
        # (Parallelism not needed here: h5py will serialize these requests anyway)
        logger.debug( "Copying data from {} blocks...".format( len(block_starts) ) )
        for block_start in block_starts:
            entire_block_roi = getBlockBounds( self.Input.meta.shape, self._blockshape, block_start )

            # This block's portion of the roi
            intersecting_roi = getIntersection( (roi.start, roi.stop), entire_block_roi )
            
            # Compute slicing within destination array and slicing within this block
            destination_relative_intersection = numpy.subtract(intersecting_roi, roi.start)
            block_relative_intersection = numpy.subtract(intersecting_roi, block_start)
            
            # Copy from block to destination
            dataset = self._getBlockDataset( entire_block_roi )
            destination[ roiToSlice(*destination_relative_intersection) ] = dataset[ roiToSlice( *block_relative_intersection ) ]
        return destination


    def _executeCleanBlocks(self, destination):
        """
        Execute function for the CleanBlocks output slot, which produces 
        an *unsorted* list of block rois that the cache currently holds.
        """
        # Set difference: clean = existing - dirty
        clean_block_starts = set( self._cacheFiles.keys() ) - self._dirtyBlocks
        
        inputShape = self.Input.meta.shape
        clean_block_rois = map( partial( getBlockBounds, inputShape, self._blockshape ),
                                clean_block_starts )
        destination[0] = map( partial(map, TinyVector), clean_block_rois )
        return destination

    def _executeOutputHdf5(self, roi, destination):
        logger.debug("Servicing request for hdf5 block {}".format( roi ))

        assert isinstance( destination, h5py.Group ), "OutputHdf5 slot requires an hdf5 GROUP to copy into (not a numpy array)."
        assert ((roi.start % self._blockshape) == 0).all(), "OutputHdf5 slot requires roi to be exactly one block."
        block_roi = getBlockBounds( self.Input.meta.shape, self._blockshape, roi.start )
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
        """
        # Choose a chunkshape:
        # - same time dimension as blockshape
        # - same channel dimension as blockshape
        # - aim for roughly 100k (for decent compression/decompression times)
        # - aim for roughly the same ratio of xyz sizes as the blockshape

        # Start with a copy of blockshape
        axes = self.Input.meta.getTaggedShape().keys()
        taggedBlockshape = collections.OrderedDict( zip(axes, self._blockshape) )
        taggedChunkshape = copy.copy( taggedBlockshape )

        dtypeBytes = self._getDtypeBytes(self.Input.meta.dtype)

        # How much xyz space can a chunk occupy and still fit within 100k?
        desiredSpace = 100000.0 / dtypeBytes
        for key in 'tc':
            if key in taggedChunkshape:
                desiredSpace /= taggedChunkshape[key] 
        logger.debug("desired space: {}".format( desiredSpace ))

        # How big is the blockshape?
        blockshapeSpace = 1.0
        numSpaceAxes = 0.0
        for key in 'xyz':
            if key in taggedBlockshape:
                numSpaceAxes += 1.0
                blockshapeSpace *= taggedBlockshape[key]
        logger.debug("blockshape space: {}".format( blockshapeSpace ))
        
        # Determine factor to shrink each spatial dimension
        factor = blockshapeSpace / float(desiredSpace)
        factor = factor**(1/numSpaceAxes)
        logger.debug("factor: {}".format(factor))
        
        # Adjust by factor
        for key in 'xyz':
            if key in taggedChunkshape:
                taggedChunkshape[key] /= factor
                taggedChunkshape[key] = max(1, taggedChunkshape[key])
                taggedChunkshape[key] = int(taggedChunkshape[key])

        chunkshape = taggedChunkshape.values()
        
        # h5py will crash if the chunkshape is larger than the dataset shape.
        chunkshape = numpy.minimum(self._blockshape, chunkshape )

        chunkshape = tuple( chunkshape )
        logger.debug("Using chunk shape: {}".format( chunkshape ))
        return chunkshape

    def _getDtypeBytes(self, dtype):
        if type(dtype) is numpy.dtype:
            # Make sure we're dealing with a type (e.g. numpy.float64),
            #  not a numpy.dtype
            dtype = dtype.type
        return dtype().nbytes


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
                logger.debug("Creating a cache file for block: {}".format( list(block_start) ))
                # Create an in-memory hdf5 file with a unique name
                filename = str(id(self)) + str(id(self._cacheFiles)) + str(block_start) 
                mem_file = h5py.File(filename, driver='core', backing_store=False, mode='w')                
                
                # Make a compressed dataset
                datashape = tuple( entire_block_roi[1] - entire_block_roi[0] )
                mem_file.create_dataset('data',
                                        shape=datashape,
                                        dtype=self.Input.meta.dtype,
                                        chunks=self._chunkshape,
                                        compression='lzf' ) # lzf should be faster than gzip, 
                                                            # with a slightly worse compression ratio
                    
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
                    
                    if logger.isEnabledFor(logging.DEBUG):
                        uncompressed_size = numpy.prod(data.shape) * self._getDtypeBytes(data.dtype)
                        storage_size = block_file["data"].id.get_storage_size()
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

    def _setInSlotInput(self, slot, subindex, roi, value):
        assert len(roi.stop) == len(self.Input.meta.shape), "roi: {} has the wrong number of dimensions for Input shape: {}".format( roi, self.Input.meta.shape )
        assert numpy.less_equal(roi.stop, self.Input.meta.shape).all(), "roi: {} is out-of-bounds for Input shape: {}".format( roi, self.Input.meta.shape )
        
        block_starts = getIntersectingBlocks( self._blockshape, (roi.start, roi.stop) )
        block_starts = map( tuple, block_starts )

        # Copy data to each block
        logger.debug( "Copying data INTO {} blocks...".format( len(block_starts) ) )
        for block_start in block_starts:
            entire_block_roi = getBlockBounds( self.Input.meta.shape, self._blockshape, block_start )

            # This block's portion of the roi
            intersecting_roi = getIntersection( (roi.start, roi.stop), entire_block_roi )
            
            # Compute slicing within source array and slicing within this block
            source_relative_intersection = numpy.subtract(intersecting_roi, roi.start)
            block_relative_intersection = numpy.subtract(intersecting_roi, block_start)
            
            # Copy from source to block
            dataset = self._getBlockDataset( entire_block_roi )
            dataset[ roiToSlice( *block_relative_intersection ) ] = value[ roiToSlice(*source_relative_intersection) ]

            # Here, we assume that if this function is used to update ANY PART of a 
            #  block, he is responsible for updating the ENTIRE block.
            # Therefore, this block is no longer 'dirty'
            self._dirtyBlocks.discard( block_start )

#            self.Output._sig_value_changed()
#            self.OutputHdf5._sig_value_changed()
#            self.CleanBlocks._sig_value_changed()

    def _setInSlotInputHdf5(self, slot, subindex, roi, value):
        logger.debug("Setting block {} from hdf5".format( roi ))
        assert isinstance( value, h5py.Dataset ), "InputHdf5 slot requires an hdf5 Dataset to copy from (not a numpy array)."
        assert ((roi.start % self._blockshape) == 0).all(), "InputHdf5 slot requires roi to be exactly one block."
        block_roi = getBlockBounds( self.Input.meta.shape, self._blockshape, roi.start )
        assert (block_roi == numpy.array((roi.start, roi.stop))).all(), "InputHdf5 slot requires roi to be exactly one block."

        cachefile = self._getCacheFile( block_roi )
        logger.debug( "Copying HDF5 data directly into block {}".format( block_roi ) )
        assert cachefile['data'].dtype == value.dtype
        assert cachefile['data'].shape == value.shape
        del cachefile['data']
        cachefile.copy( value, 'data' )

        block_start = tuple(roi.start)
        self._dirtyBlocks.discard( block_start )

#        self.Output._sig_value_changed()
#        self.OutputHdf5._sig_value_changed()
#        self.CleanBlocks._sig_value_changed()

    def _getBlockDataset(self, entire_block_roi):
        """
        Get the correct cache file and return the *dataset* handle,
        not a numpy array of its contents.
        """
        block_file = self._getCacheFile(entire_block_roi)
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



















































