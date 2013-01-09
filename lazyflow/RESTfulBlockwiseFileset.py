import os
import time
import errno
import functools
import threading
import numpy
from lazyflow.blockwiseFileset import BlockwiseFileset
from lazyflow.RESTfulVolume import RESTfulVolume
from lazyflow.roi import getIntersectingBlocks
from lazyflow.fileLock import FileLock
from lazyflow.jsonConfig import JsonConfigSchema

class RESTfulBlockwiseFileset(BlockwiseFileset):
    
    DescriptionFields = \
    {
        "_schema_name" : "RESTful-blockwise-fileset-description",
        "_schema_version" : 1.0,

        # Description of the RESTful Volume
        "remote_description" : JsonConfigSchema( RESTfulVolume.DescriptionFields ),
        
        # Description of the local block layout
        "local_description" : JsonConfigSchema( BlockwiseFileset.DescriptionFields )
    }
    DescriptionSchema = JsonConfigSchema( DescriptionFields )
    
    @classmethod
    def readDescription(cls, descriptionFilePath):
        description = RESTfulBlockwiseFileset.DescriptionSchema.parseConfigFile( descriptionFilePath )
        RESTfulVolume.updateDescription(description.remote_description)
        return description        

    @classmethod
    def writeDescription(cls, descriptionFilePath, descriptionFields):
        RESTfulBlockwiseFileset.DescriptionSchema.writeConfigFile( descriptionFilePath, descriptionFields )

    
    def __init__(self, compositeDescriptionPath ):
        # Parse the description file, which contains sub-configs for the blockwise description and RESTful description
        self.compositeDescription = RESTfulBlockwiseFileset.readDescription( compositeDescriptionPath )

        self.localDescription = self.compositeDescription.local_description
        self.remoteDescription = self.compositeDescription.remote_description

        super( RESTfulBlockwiseFileset, self ).__init__( compositeDescriptionPath, 'r', preparsedDescription=self.localDescription )
        self._remoteVolume = RESTfulVolume( preparsedDescription=self.remoteDescription )
        
        if not self.description.block_file_name_format.endswith( self._remoteVolume.description.hdf5_dataset ):
            msg = "Your RESTful volume description file must specify an hdf5 internal dataset name that matches the one in your Blockwise Fileset description file!"
            msg += "RESTful volume dataset name is '{}', but blockwise fileset format is '{}'".format( self._remoteVolume.description.hdf5_dataset, self.description.block_file_name_format )
            raise RuntimeError(msg)
        if self.description.axes != self._remoteVolume.description.axes:
            raise RuntimeError( "Your RESTful volume's axes must match the blockwise dataset axes. ('{}' does not match '{}')".format( self._remoteVolume.description.axes, self.description.axes ) )
        if ( numpy.array(self.description.shape) > numpy.array(self._remoteVolume.description.shape) ).any():
            raise RuntimeError( "Your local blockwise volume shape must be smaller in all dimensions than the remote volume shape.")

    def readData(self, roi, out_array=None):
        assert (numpy.array(roi[1]) <= numpy.array(self.description.view_shape)).all(), "Requested roi '{}' is out of dataset bounds '{}'".format(roi, self.description.view_shape) 
        # Before reading the data, check each of the needed blocks and download them first
        block_starts = getIntersectingBlocks(self.description.block_shape, roi)

        missing_blocks = []
        for block_start in block_starts:
            if self.getBlockStatus(block_start) == BlockwiseFileset.BLOCK_NOT_AVAILABLE:
                missing_blocks.append( block_start )

        self._waitForBlocks( missing_blocks )
        
        return super( RESTfulBlockwiseFileset, self ).readData( roi, out_array )

    def _waitForBlocks(self, missing_blocks):
        """
        Initiate downloads for those blocks that need it.
        (Some blocks in the list may already be downloading.)
        Then wait for all necessary downloads to complete (including the ones that we didn't initiate).
        """
        # Start by creating all necessary directories.
        # If the directory already exists, ignore the resulting error.
        for block_start in missing_blocks:
            blockDir = self.getDatasetDirectory( block_start )
            try:
                os.makedirs( blockDir )
            except OSError, e:
                if e.errno != errno.EEXIST:
                    raise

        # Attempt to lock each path we need to create.
        # Locks we fail to obtain are already being fetched by other processes, which is okay.
        acquired_locks = []
        unobtained_locks = []
        for block_start in missing_blocks:
            entire_block_roi = self.getEntireBlockRoi(block_start) # Roi of this whole block within the whole dataset
            blockFilePathComponents = self.getDatasetPathComponents( block_start )

            fileLock = FileLock( blockFilePathComponents.externalPath )
            if fileLock.acquire(False):
                acquired_locks.append( (entire_block_roi, fileLock) )
            else:
                unobtained_locks.append( (entire_block_roi, fileLock) )
        
        # We are now responsible for downloading the data for the file paths we were able to lock.
        # Start a separate thread for each.
        downloadThreads = []
        for block_roi, fileLock in acquired_locks:
            blockFilePathComponents = self.getDatasetPathComponents( block_roi[0] )
            th = threading.Thread( target=functools.partial( self._downloadBlock, fileLock, block_roi, blockFilePathComponents ) )
            downloadThreads.append(th)
        
        # Start all the threads
        for th in downloadThreads:
            th.start()
        
        # Wait for them all to complete
        for th in downloadThreads:
            th.join()
        
        # Finally, wait for the blocks that we COULDN'T lock (they must be downloading in other processes somewhere...)
        for block_roi, fileLock in unobtained_locks:
            while self.getBlockStatus(block_roi[0]) == BlockwiseFileset.BLOCK_NOT_AVAILABLE:
                time.sleep(5)
    
    def _downloadBlock(self, fileLock, entire_block_roi, blockFilePathComponents):
        """
        Download the data for the given block, then release its file lock.
        :param fileLock: The lock for the file we are about to create.  MUST BE LOCKED already.
        :param entire_block_roi: The roi for the block to download.
        :param blockFilePathComponents: A lazyflow.pathHelpers.PathComponents object describing the location of the block dataset file. 
        """
        try:
            self._remoteVolume.downloadSubVolume( entire_block_roi, blockFilePathComponents.totalPath() )
            self.setBlockStatus(entire_block_roi[0], BlockwiseFileset.BLOCK_AVAILABLE)
        finally:
            fileLock.release()

















