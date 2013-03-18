import os
import time
import errno
import functools
import threading
import numpy
import Queue
from lazyflow.utility.io.blockwiseFileset import BlockwiseFileset, BlockwiseFilesetFactory
from lazyflow.utility.io.RESTfulVolume import RESTfulVolume
from lazyflow.roi import getIntersectingBlocks
from lazyflow.utility import FileLock
from lazyflow.utility.jsonConfig import JsonConfigParser

import logging
logger = logging.getLogger(__name__)

class RESTfulBlockwiseFileset(BlockwiseFileset):
    """
    This class combines the functionality of :py:class:`RESTfulVolume` and :py:class:`BlockwiseFileset`
    to provide access to a remote dataset (e.g. from http://openconnecto.me), with all downloaded data 
    cached locally as blocks stored in a directory tree of hdf5 files.

    This class must be constructed with a description of both the remote dataset and the local 
    storage format, provided in a JSON file with a composite schema specified by 
    :py:data:`RESTfulBlockwiseFileset.DescriptionFields`.

    .. note:: See the unit tests in ``tests/testRESTfulBlockwiseFileset.py`` for example usage.

    Here's an example description file.
    
    .. code-block:: json

        {
            "_schema_name" : "RESTful-blockwise-fileset-description",
            "_schema_version" : 1.0,
        
            "remote_description" : 
            {
                "_schema_name" : "RESTful-volume-description",
                "_schema_version" : 1.0,
            
                "name" : "Bock11-level0",
                "format" : "hdf5",
                "axes" : "zyx",
        
                "## NOTE": "The origin offset determines how coordinates are translated when converted to a url.",
                "## NOTE": "The origin_offset for the bock11 dataset must be at least 2917, because for some reason that's where it starts.",
                "origin_offset" : [2917, 0, 0],
        
                "## NOTE": "The website says that the data goes up to plane 4156, but it actually errors out past 4150",
                "bounds" : [4150, 135424, 119808],
                "dtype" : "numpy.uint8",
                "url_format" : "http://openconnecto.me/emca/bock11/hdf5/0/{x_start},{x_stop}/{y_start},{y_stop}/{z_start},{z_stop}/",
                "hdf5_dataset" : "cube"
            },
        
            "local_description" :
            {
                "_schema_name" : "blockwise-fileset-description",
                "_schema_version" : 1.0,
        
                "name" : "bock11-blocks",
                "format" : "hdf5",
                "axes" : "zyx",
                "shape" : "[ 4150-2917, 135424, 119808 ]",
                "dtype" : "numpy.uint8",
                "block_shape" : [32, 256, 256],
                "block_file_name_format" : "block-{roiString}.h5/cube",
                "dataset_root_dir" : "blocks-256x256x32",
        
                "## NOTE":"These optional parameters tell ilastik to view only a portion of the on-disk dataset.",
                "## NOTE":"view_origin MUST be aligned to a block start corner.",
                "## NOTE":"view_shape is optional, but recommended because volumina slows down when there are 1000s of tiles.",
                "view_origin" : "[0, 50*1024, 50*1024]",
                "view_shape" : "[4150-2917, 10*256, 10*256]"
            }
        }
    """

    #: This member specifies the schema of the description file.
    #: It is merely a composite of two nested schemas: one that describes the remote volume,
    #: and another that describes the local storage format.  See the source code to see the field names.
    DescriptionFields = \
    {
        "_schema_name" : "RESTful-blockwise-fileset-description",
        "_schema_version" : 1.0,

        # Description of the RESTful Volume
        "remote_description" : JsonConfigParser( RESTfulVolume.DescriptionFields ),
        
        # Description of the local block layout
        "local_description" : JsonConfigParser( BlockwiseFileset.DescriptionFields )
    }
    DescriptionSchema = JsonConfigParser( DescriptionFields )
    
    @classmethod
    def readDescription(cls, descriptionFilePath):
        """
        Parse the description file at the given path and return a 
        :py:class:`jsonConfig.Namespace` object with the description parameters.
        The file will be parsed according to the schema given by :py:data:`RESTfulBlockwiseFileset.DescriptionFields`.
        Any optional parameters not provided by the user are filled in automatically.
        
        :param descriptionFilePath: The path to the description file to parse.
        """
        description = RESTfulBlockwiseFileset.DescriptionSchema.parseConfigFile( descriptionFilePath )
        RESTfulVolume.updateDescription(description.remote_description)
        return description

    @classmethod
    def writeDescription(cls, descriptionFilePath, descriptionFields):
        """
        Write a :py:class:`jsonConfig.Namespace` object to the given path.
        
        :param descriptionFilePath: The path to overwrite with the description fields.
        :param descriptionFields: The fields to write.
        """
        RESTfulBlockwiseFileset.DescriptionSchema.writeConfigFile( descriptionFilePath, descriptionFields )

    @classmethod
    def _createAndReturnBlockwiseFileset(self, descriptionFilePath, mode):
        try:
            rbfs = RESTfulBlockwiseFileset( descriptionFilePath )
            assert mode == 'r', "RESTfulBlockwiseFilesets may only be opened in read-only mode."
        except JsonConfigParser.SchemaError:
            rbfs = None
        return rbfs
    
    def __init__(self, compositeDescriptionPath ):
        """
        Constructor.  Uses `readDescription` interally.
        
        :param compositeDescriptionPath: The path to a JSON file that describes both the remote 
                                         volume and local storage structure.  The JSON file schema is specified by 
                                         :py:data:`RESTfulBlockwiseFileset.DescriptionFields`.
        """
        # Parse the description file, which contains sub-configs for the blockwise description and RESTful description
        self.compositeDescription = RESTfulBlockwiseFileset.readDescription( compositeDescriptionPath )

        self.localDescription = self.compositeDescription.local_description
        self.remoteDescription = self.compositeDescription.remote_description

        super( RESTfulBlockwiseFileset, self ).__init__( compositeDescriptionPath, 'r', preparsedDescription=self.localDescription )
        self._remoteVolume = RESTfulVolume( preparsedDescription=self.remoteDescription )
        
        try:
            if not self.localDescription.block_file_name_format.endswith( self.remoteDescription.hdf5_dataset ):
                msg = "Your RESTful volume description file must specify an hdf5 internal dataset name that matches the one in your Blockwise Fileset description file!"
                msg += "RESTful volume dataset name is '{}', but blockwise fileset format is '{}'".format( self.remoteDescription.hdf5_dataset, self.localDescription.block_file_name_format )
                raise RuntimeError(msg)
            if self.localDescription.axes != self.remoteDescription.axes:
                raise RuntimeError( "Your RESTful volume's axes must match the blockwise dataset axes. ('{}' does not match '{}')".format( self.remoteDescription.axes, self.localDescription.axes ) )
            if ( numpy.array(self.localDescription.shape) > numpy.array(self.remoteDescription.shape) ).any():
                raise RuntimeError( "Your local blockwise volume shape must be smaller in all dimensions than the remote volume shape.")
        except:
            logger.error("Error loading dataset from {}".format( compositeDescriptionPath ))
            raise

    def readData(self, roi, out_array=None):
        """
        Read data from the fileset.  If any of the requested data is not yet available locally, download it first.
        
        :param roi: The region of interest to read from the dataset.  Must be a tuple of iterables: (start, stop).
        :param out_array: The location to store the read data.  Must be the correct size for the given roi.  If not provided, an array is created for you.
        :returns: The requested data.  If out_array was provided, returns out_array.
        """
        assert (numpy.array(roi[1]) <= numpy.array(self.localDescription.view_shape)).all(), "Requested roi '{}' is out of dataset bounds '{}'".format(roi, self.localDescription.view_shape) 

        # Before reading the data, make sure all the blocks we'll need to access are available on disk.
        block_starts = getIntersectingBlocks(self.localDescription.block_shape, roi)
        self._waitForBlocks( block_starts )
        
        return super( RESTfulBlockwiseFileset, self ).readData( roi, out_array )

    def _waitForBlocks(self, block_starts):
        """
        Initiate downloads for those blocks that need it.
        (Some blocks in the list may already be downloading.)
        Then wait for all necessary downloads to complete (including the ones that we didn't initiate).
        """
        # Only wait for those that are missing.
        missing_blocks = []
        for block_start in block_starts:
            if self.getBlockStatus(block_start) == BlockwiseFileset.BLOCK_NOT_AVAILABLE:
                missing_blocks.append( block_start )

        # Start by creating all necessary directories.
        self._ensureDirectoriesExist( missing_blocks )

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
        :param blockFilePathComponents: A lazyflow.utility.PathComponents object describing the location of the block dataset file. 
        """
        try:
            # The blockFilePath has already been offset to accomodate any view offset, but the roi has not.
            # Offset the roi coordinates before requesting them from the remote volume.
            translated_roi = []
            translated_roi.append( numpy.add( entire_block_roi[0], self.description.view_origin ) )
            translated_roi.append( numpy.add( entire_block_roi[1], self.description.view_origin ) )

            logger.debug( "Downloading block: {}".format( entire_block_roi[0] ) )
            self._remoteVolume.downloadSubVolume( translated_roi, blockFilePathComponents.totalPath() )
            self.setBlockStatus(entire_block_roi[0], BlockwiseFileset.BLOCK_AVAILABLE)
        finally:
            fileLock.release()

    def downloadAllBlocks(self, max_parallel, skip_preparation=False):
        """
        Download all blocks in the local view.
        This is used in utility scripts for downloading an entire volume at once.
        This function is NOT intended to be used by multiple threads in parallel
        (i.e. it doesn't protect against downloading the same block twice.)
        """
        view_shape = self.localDescription.view_shape
        view_roi = ([0]*len(view_shape), view_shape)
        block_starts = list( getIntersectingBlocks(self.localDescription.block_shape, view_roi) )
        
        if not skip_preparation:
            self._ensureDirectoriesExist( block_starts )

        # Only wait for those that are missing.
        blockQueue = Queue.Queue()
        for block_start in block_starts:
            if self.getBlockStatus(block_start) == BlockwiseFileset.BLOCK_NOT_AVAILABLE:
                blockQueue.put( block_start )

        num_blocks = blockQueue.qsize()
        logger.debug( "Preparing to download {} blocks".format( num_blocks ) )

        failedBlockQueue = Queue.Queue()

        threads = []
        for _ in range(max_parallel):
            th = threading.Thread( target=functools.partial( self._downloadFromQueue, num_blocks, blockQueue, failedBlockQueue ) )
            threads.append(th)
            th.start()

        for th in threads:
            th.join()

        errors = not failedBlockQueue.empty()
        while not failedBlockQueue.empty():
            logger.error( "Failed to download block {}.  Does it have a leftover lockfile?".format( failedBlockQueue.get() ) )
        
        logger.debug("FINISHED DOWNLOADING.")
        if errors:
            logger.error("There were errors during the download process.  Check error log output!")

    def _downloadFromQueue(self, num_blocks, blockQueue, failedBlockQueue):
        """
        Helper function for downloadAllBlocks(), above.
        """
        try:
            while not blockQueue.empty():
                block_start = blockQueue.get(block=False)
                entire_block_roi = self.getEntireBlockRoi(block_start) # Roi of this whole block within the whole dataset
                blockFilePathComponents = self.getDatasetPathComponents( block_start )
                
                # Obtain lock
                fileLock = FileLock( blockFilePathComponents.externalPath )
                if not fileLock.acquire(False):
                    failedBlockQueue.put( block_start )
                else:
                    try:
                        # Download the block
                        # (This function releases the lock for us.)
                        self._downloadBlock(fileLock, entire_block_roi, blockFilePathComponents)
                        logger.debug( "Finished downloading {}/{}".format( num_blocks-blockQueue.qsize(), num_blocks ) )
                    except:
                        if fileLock.locked():
                            fileLock.release()
                            self.setBlockStatus(entire_block_roi[0], BlockwiseFileset.BLOCK_NOT_AVAILABLE)
                        failedBlockQueue.put( block_start )
                        raise
        except Queue.Empty:
            return

    def _ensureDirectoriesExist(self, block_starts):
        """
        Create all directories that the provided blocks will be stored in.
        """
        # If the directory already exists, ignore the resulting error.
        for block_start in block_starts:
            blockDir = self.getDatasetDirectory( block_start )
            try:
                os.makedirs( blockDir )
            except OSError, e:
                if e.errno != errno.EEXIST:
                    raise

BlockwiseFilesetFactory.register( RESTfulBlockwiseFileset._createAndReturnBlockwiseFileset )


if __name__ == "__main__":
    import sys
    logger.addHandler( logging.StreamHandler( sys.stdout ) )
    logger.setLevel( logging.DEBUG )

    vol = RESTfulBlockwiseFileset('/home/bergs/bock/bock11/description-256.json')
    vol.purgeAllLocks()
    vol.downloadAllBlocks(2)











