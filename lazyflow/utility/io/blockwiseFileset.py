import os
import threading
import numpy
import h5py
import logging
logger = logging.getLogger(__name__)

from lazyflow.utility.jsonConfig import AutoEval, FormattedField, JsonConfigParser
from lazyflow.roi import getIntersection, roiToSlice
from lazyflow.utility import PathComponents, getPathVariants, FileLock
from lazyflow.roi import getIntersectingBlocks, getBlockBounds

try:
    import vigra
    _use_vigra = True
except:
    _use_vigra = False

class BlockwiseFileset(object):
    """
    This class handles writing and reading a 'blockwise file set'.
    A 'blockwise file set' is a directory with a particular structure, which contains the entire dataset broken up into blocks.
    Important parameters (e.g. shape, dtype, blockshape) are specified in a JSON file, which must match the schema given by :py:data:`BlockwiseFileset.DescriptionFields`.
    The parent directory of the description file is considered to be the top-most directory in the blockwise dataset hierarchy.
    
    - Simultaneous reads are threadsafe.
    - NOT threadsafe for reading and writing simultaneously (or writing and writing).
    - NOT threadsafe for closing.  Do not call close() while reading or writing.

    .. note:: See the unit tests in ``tests/testBlockwiseFileset.py`` for example usage.
    """

    #: These fields describe the schema of the description file.
    #: See the source code comments for a description of each field.    
    DescriptionFields = \
    {
        "_schema_name" : "blockwise-fileset-description",
        "_schema_version" : 1.0,

        "name" : str,
        "format" : str,
        "axes" : str,
        "shape" : AutoEval(numpy.array), # This is the shape of the VIEW
        "dtype" : AutoEval(),
        "chunks" : AutoEval(numpy.array), # Optional.  If null, no chunking. Only used when writing data.
        "block_shape" : AutoEval(numpy.array),
        "view_origin" : AutoEval(numpy.array), # Optional.  Defaults to zeros.  All requests will be translated before the data is accessed.
                                # For example, if the offset is [100, 200, 300], then a request for roi([0,0,0],[2,2,2]) 
                                #  will pull from the dataset on disk as though the request was ([100,200,300],[102,202,302]).
                                # It is an error to specify an view_origin that is not a multiple of the block_shape.
        "view_shape" : AutoEval(numpy.array), # Optional.  Defaults to (shape - view_origin) Limits the shape of the provided data.
        "block_file_name_format" : FormattedField( requiredFields=["roiString"] ), # For hdf5, include dataset name, e.g. myfile_block{roiString}.h5/volume/data
        "dataset_root_dir" : str, # Abs path or relative to the description file itself. Defaults to "." if left blank.
        "hash_id" : str # Not user-defined (clients may use this)
    }
    DescriptionSchema = JsonConfigParser( DescriptionFields )

    @classmethod
    def readDescription(cls, descriptionFilePath):
        """
        Parse the description file at the given path and return a 
        :py:class:`jsonConfig.Namespace` object with the description parameters.
        The file will be parsed according to the schema given by :py:data:`BlockwiseFileset.DescriptionFields`.
        
        :param descriptionFilePath: The path to the description file to parse.
        """
        return BlockwiseFileset.DescriptionSchema.parseConfigFile( descriptionFilePath )

    @classmethod
    def writeDescription(cls, descriptionFilePath, descriptionFields):
        """
        Write a :py:class:`jsonConfig.Namespace` object to the given path.
        
        :param descriptionFilePath: The path to overwrite with the description fields.
        :param descriptionFields: The fields to write.
        """
        BlockwiseFileset.DescriptionSchema.writeConfigFile( descriptionFilePath, descriptionFields )

    class BlockNotReadyError(Exception):
        """
        This exception is raised if `readData()` is called for data that isn't available on disk.
        """
        def __init__(self, block_start):
            self.block_start = block_start

    @property
    def description(self):
        """
        The :py:class:`jsonConfig.Namespace` object that describes this dataset.
        """
        return self._description

    def __init__( self, descriptionFilePath, mode='r', preparsedDescription=None ):
        """
        Constructor.  Uses `readDescription` interally.
        
        :param descriptionFilePath: The path to the .json file that describes the dataset.
        :param mode: Set to ``'r'`` if the fileset should be read-only.
        :param preparsedDescription: (Optional) Provide pre-parsed description fields, in which case the provided description file will not be parsed.
        """
        assert mode == 'r' or mode == 'a', "Valid modes are 'r' or 'a', not '{}'".format(mode)
        self.mode = mode
        
        assert descriptionFilePath is not None, "Must provide a path to the description file, even if you are providing pre-parsed fields. (Path is used to find block directory)."
        self._descriptionFilePath = descriptionFilePath
        
        if preparsedDescription is not None:
            self._description = preparsedDescription
        else:
            self._description = BlockwiseFileset.readDescription( descriptionFilePath )

        assert self._description.format == "hdf5", "Only hdf5 blockwise filesets are supported so far."
        
        if self._description.view_origin is None:
            self._description.view_origin = (0,) * len(self._description.shape)
        assert (numpy.mod( self._description.view_origin, self._description.block_shape ) == 0).all(), "view_origin is not compatible with block_shape.  Must be a multiple!"

        if self._description.view_shape is None:
            self._description.view_shape = numpy.subtract( self._description.shape, self._description.view_origin )
        view_roi = (self._description.view_origin, numpy.add(self._description.view_origin, self._description.view_shape))
        assert (numpy.subtract( self._description.shape, view_roi[1] ) >= 0).all(), "View ROI must not exceed on-disk shape."

        if self._description.dataset_root_dir is None:
            # Default to same directory as the description file
            self._description.dataset_root_dir = "."
        
        self._lock = threading.Lock()
        self._openBlockFiles = {}
        self._fileLocks = {}
        self._closed = False

    def __del__(self):
        if not self._closed:
            self.close()

    def close(self):
        """
        Close all open block files.
        """
        with self._lock:
            assert not self._closed
            paths = self._openBlockFiles.keys()
            for path in paths:
                blockFile = self._openBlockFiles[path]
                blockFile.close()
                if self.mode == 'a':
                    fileLock = self._fileLocks[path]
                    fileLock.release()
            self._closed = True
            

    def readData(self, roi, out_array=None):
        """
        Read data from the fileset.
        
        :param roi: The region of interest to read from the dataset.  Must be a tuple of iterables: (start, stop).
        :param out_array: The location to store the read data.  Must be the correct size for the given roi.  If not provided, an array is created for you.
        :returns: The requested data.  If out_array was provided, returns out_array.
        """
        if out_array is None:
            out_array = numpy.ndarray( shape=numpy.subtract(roi[1], roi[0]), dtype=self._description.dtype )
        assert ( numpy.subtract(roi[1], roi[0]) == out_array.shape ).all(), "out_array must match roi shape"
        self._transferData(roi, out_array, read=True)
        return out_array

    def writeData(self, roi, data):
        """
        Write data to the fileset.
        
        :param roi: The region of interest to write the data to.  Must be a tuple of iterables: (start, stop).
        :param data: The data to write.  Must be the correct size for the given roi.
        """
        assert self.mode != 'r'
        self._transferData(roi, data, read=False)

    def getDatasetDirectory( self, blockstart ):
        """
        Return the directory that contains the block that starts at the given coordinates.
        """
        # Add the view origin to find the on-disk block coordinates
        blockstart = numpy.add( blockstart, self._description.view_origin )
        descriptionFileDir = os.path.split(self._descriptionFilePath)[0]
        absPath, relPath = getPathVariants( self._description.dataset_root_dir, descriptionFileDir )
        blockFilePath = absPath

        for axis, start in zip(self._description.axes, blockstart):
            blockFilePath = os.path.join( blockFilePath, "{}_{:08d}".format( axis, start ) )
        return blockFilePath

    def _getBlockFileName(self, block_start):
        """
        Get the path to the block file that starts at the given coordinate.
        """
        # Translate to find disk block start
        block_start = numpy.add( self._description.view_origin, block_start )
        # Get true (disk) block bounds (i.e. use on-disk shape, not view_shape)
        entire_block_roi = getBlockBounds( self._description.shape, self._description.block_shape, block_start )
        roiString = "{}".format( (list(entire_block_roi[0]), list(entire_block_roi[1]) ) )
        datasetFilename = self._description.block_file_name_format.format( roiString=roiString )
        return datasetFilename

    def getDatasetPathComponents(self, block_start):
        """
        Return a PathComponents object for the block file that corresponds to the given block start coordinate.
        """
        datasetFilename = self._getBlockFileName(block_start)
        datasetDir = self.getDatasetDirectory( block_start )
        datasetPath = os.path.join( datasetDir, datasetFilename )

        return PathComponents( datasetPath )

    BLOCK_NOT_AVAILABLE = 0
    BLOCK_AVAILABLE = 1
    def getBlockStatus(self, blockstart):
        """
        Check a block's status.
        (Just because a block file exists doesn't mean that it has valid data.)
        Returns a status code of either ``BlockwiseFileset.BLOCK_AVAILABLE`` or ``BlockwiseFileset.BLOCK_NOT_AVAILABLE``.
        """
        blockDir = self.getDatasetDirectory(blockstart)
        statusFilePath = os.path.join(blockDir, "STATUS.txt")

        if not os.path.exists( statusFilePath ):
            return BlockwiseFileset.BLOCK_NOT_AVAILABLE
        else:
            return BlockwiseFileset.BLOCK_AVAILABLE

    def setBlockStatus(self, blockstart, status):
        """
        Set a block status on disk.
        We use a simple convention: If the status file exists, the block is available.  Otherwise, it ain't.
        
        :param status: Must be either ``BlockwiseFileset.BLOCK_AVAILABLE`` or ``BlockwiseFileset.BLOCK_NOT_AVAILABLE``.
        """
        blockDir = self.getDatasetDirectory( blockstart )
        statusFilePath = os.path.join(blockDir, "STATUS.txt")
        
        if status == BlockwiseFileset.BLOCK_AVAILABLE:
            # touch the status file.
            open( statusFilePath, 'w' ).close()
        elif os.path.exists( statusFilePath ):
            # Remove the status file
            os.remove( statusFilePath )

    def getEntireBlockRoi(self, block_start):
        """
        Return the roi for the entire block that starts at the given coordinate.
        """
        return getBlockBounds( self._description.view_shape, self._description.block_shape, block_start )

    def getAllBlockRois(self):
        """
        Return the list of rois for all VIEWED blocks in the dataset.
        """
        entire_dataset_roi = ([0]*len(self._description.view_shape), self._description.view_shape)
        block_starts = getIntersectingBlocks(self._description.block_shape, entire_dataset_roi)
        rois = []
        for block_start in block_starts:
            rois.append(self.getEntireBlockRoi(block_start))
        return rois

    def _transferData( self, roi, array_data, read ):
        """
        Read or write data from/to the fileset.
        
        :param roi: The region of interest.
        :param array_data: If ``read`` is True, ``array_data`` is the destination array for the read data.  If ``read`` is False, array_data contains the data to write to disk.
        :param read: If True, read data from the fileset into ``array_data``.  Otherwise, write data from ``array_data`` into the fileset on disk.
        :type read: bool
        """
        entire_dataset_roi = ([0] *len(self._description.view_shape), self._description.view_shape)
        clipped_roi = getIntersection( roi, entire_dataset_roi )
        assert (numpy.array(clipped_roi) == numpy.array(roi)).all(), "Roi {} does not fit within dataset bounds: {}".format(roi, self._description.view_shape)
        
        block_starts = getIntersectingBlocks(self._description.block_shape, roi)
        
        # TODO: Parallelize this loop?
        for block_start in block_starts:
            entire_block_roi = self.getEntireBlockRoi(block_start) # Roi of this whole block within the whole dataset
            transfer_block_roi = getIntersection( entire_block_roi, roi ) # Roi of data needed from this block within the whole dataset
            block_relative_roi = ( transfer_block_roi[0] - block_start, transfer_block_roi[1] - block_start ) # Roi of needed data from this block, relative to the block itself
            array_data_roi = (transfer_block_roi[0] - roi[0], transfer_block_roi[1] - roi[0]) # Roi of data needed from this block within array_data

            self._transferBlockData( entire_block_roi, block_relative_roi, array_data[ roiToSlice( *array_data_roi ) ], read )

    def _transferBlockData( self, entire_block_roi, block_relative_roi, array_data, read ):
        """
        Read or write data to a single block in the fileset.
        
        :param entire_block_roi: The roi of the entire block, relative to the whole dataset.
        :param block_relative_roi: The roi of the data being read/written, relative to the block itself (not the whole dataset).
        :param array_data: Either the source or the destination of the data being transferred to/from the fileset on disk.
        :param read: If True, read data from the block into ``array_data``.  Otherwise, write data from ``array_data`` into the block on disk.
        :type read: bool
        """
        datasetPathComponents = self.getDatasetPathComponents(entire_block_roi[0])

        if self._description.format == "hdf5":
            self._transferBlockDataHdf5( entire_block_roi, block_relative_roi, array_data, read, datasetPathComponents )
        else:
            assert False, "Unknown format"        

    def _transferBlockDataHdf5(self, entire_block_roi, block_relative_roi, array_data, read, datasetPathComponents ):
        """
        Transfer a block of data to/from an hdf5 dataset.
        See _transferBlockData() for details.
        """
        # For the hdf5 format, the full path format INCLUDES the dataset name, e.g. /path/to/myfile.h5/volume/data
        path_parts = datasetPathComponents
        datasetDir = path_parts.externalDirectory
        hdf5FilePath = path_parts.externalPath
        if len(path_parts.internalPath) == 0:
            raise RuntimeError("Your hdf5 block filename format MUST specify an internal path, e.g. block{roiString}.h5/volume/blockdata")

        block_start = entire_block_roi[0]
        if read:
            # Check for problems before reading.
            if self.getBlockStatus( block_start ) is not BlockwiseFileset.BLOCK_AVAILABLE:
                raise BlockwiseFileset.BlockNotReadyError( block_start )

            hdf5File = self._getOpenHdf5Blockfile( hdf5FilePath )
            array_data[...] = hdf5File[ path_parts.internalPath ][ roiToSlice( *block_relative_roi ) ]
        else:
            # Create the directory
            if not os.path.exists( datasetDir ):
                os.makedirs( datasetDir )

            # Clear the block status.
            # The CALLER is responsible for setting it again.
            self.setBlockStatus( block_start, BlockwiseFileset.BLOCK_NOT_AVAILABLE )

            # Write the block data file
            hdf5File = self._getOpenHdf5Blockfile( hdf5FilePath )
            if path_parts.internalPath not in hdf5File:
                chunks = self._description.chunks
                if chunks is not None:
                    chunks = tuple(chunks)
                dataset = hdf5File.create_dataset( path_parts.internalPath,
                                         shape=( entire_block_roi[1] - entire_block_roi[0] ),
                                         dtype=self._description.dtype,
                                         chunks=chunks )
                if _use_vigra:
                    dataset.attrs['axistags'] = vigra.defaultAxistags( self._description.axes ).toJSON()
            hdf5File[ path_parts.internalPath ][ roiToSlice( *block_relative_roi ) ] = array_data[...]

    def _getOpenHdf5Blockfile(self, blockFilePath):
        """
        Return a handle to the open hdf5File at the given path.
        If we haven't opened the file yet, open it first.
        """
        # Try once without locking
        if blockFilePath in self._openBlockFiles.keys():
            return self._openBlockFiles[ blockFilePath ]

        # Obtain the lock and try again
        with self._lock:
            if blockFilePath not in self._openBlockFiles.keys():
                try:
                    writeLock = FileLock( blockFilePath )
                    if self.mode == 'a':
                        writeLock.acquire( blocking=False )
                        self._fileLocks[blockFilePath] = writeLock
                    elif self.mode == 'r':
                        assert writeLock.available(), "Can't read from a file that is being written to elsewhere."
                    else: 
                        assert False, "Unsupported mode"
                    self._openBlockFiles[ blockFilePath ] = h5py.File( blockFilePath, self.mode )
                except:
                    logger.error( "Couldn't open {}".format(blockFilePath) )
                    raise
            return self._openBlockFiles[ blockFilePath ]

    def purgeAllLocks(self):
        """
        Clears all .lock files from the local blockwise fileset.
        This may be necessary if previous processes crashed or were killed while some blocks were downloading.
        You must ensure that this is NOT called while more than one process (or thread) has access to the fileset.
        For example, in a master/worker situation, call this only from the master, before the workers have been started.
        """
        found_lock = False
        
        view_shape = self.description.view_shape
        view_roi = ([0]*len(view_shape), view_shape)
        block_starts = list( getIntersectingBlocks(self.description.block_shape, view_roi) )
        for block_start in block_starts:
            blockFilePathComponents = self.getDatasetPathComponents( block_start )
            fileLock = FileLock( blockFilePathComponents.externalPath )
            found_lock |= fileLock.purge()
        
        return found_lock











