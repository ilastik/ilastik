# Built-in
import copy
import logging
import functools
import collections

# Third-party
import numpy
import h5py

# Lazyflow
from lazyflow.request import Request, RequestPool, RequestLock
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import getIntersectingBlocks, getBlockBounds, roiToSlice, getIntersection

logger = logging.getLogger(__name__)

class OpCompressedCache(Operator):
    """
    A blockwise cache that stores each block as a separate in-memory hdf5 file with a compressed dataset.
    """
    Input = InputSlot()
    BlockShape = InputSlot(optional=True) # If not provided, the entire input is treated as one block
    Output = OutputSlot()
    
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

        # Clip blockshape to image bounds
        if self.BlockShape.ready():
            self._blockshape = numpy.minimum( self.BlockShape.value, self.Input.meta.shape )
        else:
            self._blockshape = self.Input.meta.shape
        
        # Choose optimal chunkshape
        self._chunkshape = self._chooseChunkshape(self._blockshape)


    def execute(self, slot, subindex, roi, destination):
        assert slot == self.Output, "Uknown output slot"
        assert len(roi.stop) == len(self.Input.meta.shape), "roi: {} has the wrong number of dimensions for Input shape: {}".format( roi, self.Input.meta.shape )
        assert numpy.less_equal(roi.stop, self.Input.meta.shape).all(), "roi: {} is out-of-bounds for Input shape: {}".format( roi, self.Input.meta.shape )
        
        block_starts = getIntersectingBlocks( self._blockshape, (roi.start, roi.stop) )
        block_starts = map( lambda x: tuple(x), block_starts )

        # Ensure all block cache files are up-to-date
        reqPool = RequestPool() # (Do the work in parallel.)
        for block_start in block_starts:
            entire_block_roi = getBlockBounds( self.Input.meta.shape, self._blockshape, block_start )
            f = functools.partial( self._ensureCached, entire_block_roi, block_start )
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
            dataset = self._getBlockDataset( entire_block_roi, block_start )
            destination[ roiToSlice(*destination_relative_intersection) ] = dataset[ roiToSlice( *block_relative_intersection ) ]
        return destination

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Input:
            # Keep track of dirty blocks
            with self._lock:
                block_starts = getIntersectingBlocks( self._blockshape, (roi.start, roi.stop) )
                block_starts = map( lambda x: tuple(x), block_starts )
                
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

        dtype = self.Input.meta.dtype
        if type(dtype) is numpy.dtype:
            # Make sure we're dealing with a type (e.g. numpy.float64),
            #  not a numpy.dtype
            dtype = dtype.type
        dtypeBytes = dtype().nbytes

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


    def _getCacheFile(self, entire_block_roi, block_start):
        """
        Get the cache file for the block that starts at block_start.
        If it doesn't exist yet, create it first.
        """
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


    def _ensureCached(self, entire_block_roi, block_start):
        """
        Ensure that the cache file for the given block is up-to-date.
        (Refresh it if it's dirty.)
        """
        block_file = self._getCacheFile(entire_block_roi, block_start)
        if block_start in self._dirtyBlocks:
            with self._blockLocks[block_start]:
                # Check AGAIN now that we have the lock.
                # (Avoid doing this twice in parallel requests.)
                if block_start in self._dirtyBlocks:                
                    # Can't write directly into the hdf5 dataset because 
                    #  h5py.dataset.__getitem__ creates a copy, not a view.
                    # We must use a temporary numpy array to hold the data.
                    data = self.Input(*entire_block_roi).wait()
                    block_file['data'][...] = data
            with self._lock:
                self._dirtyBlocks.remove( block_start )


    def _getBlockDataset(self, entire_block_roi, block_start):
        """
        Get the correct cache file and return the *dataset* handle,
        not a numpy array of its contents.
        """
        block_file = self._getCacheFile(entire_block_roi, block_start)
        return block_file['data']


    def _closeAllCacheFiles(self):
        logger.debug( "Closing all caches" )
        with self._lock:
            for k,v in self._cacheFiles:
                with self._blockLocks[k]:
                    v.close()
            self._blockLocks = {}
            self._cacheFiles = {}



















































