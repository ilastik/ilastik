import os
import threading
import numpy
import h5py
import logging
logger = logging.getLogger(__name__)

from lazyflow.jsonConfig import AutoEval, FormattedField, JsonConfigSchema
from lazyflow.roi import getIntersection, roiToSlice
from lazyflow.pathHelpers import PathComponents, getPathVariants
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
    Important parameters (e.g. shape, dtype, blockshape) are specified in a json file, which must match the schema given by BlockwiseFileset.DescriptionFields.
    The parent directory of the description file is considered to be the top-most directory in the blockwise dataset hierarchy.
    
    Simultaneous reads are threadsafe.
    NOT threadsafe for reading and writing simultaneously (or writing and writing).
    NOT threadsafe for closing.  Do not call close() while reading or writing.
    """
    
    # Description config file schema:
    DescriptionFields = \
    {
        "_schema_name" : "blockwise-fileset-description",
        "_schema_version" : 1.0,

        "name" : str,
        "format" : str,
        "axes" : str,
        "shape" : list,
        "dtype" : AutoEval(),
        "chunks" : list, # Optional.  If null, no chunking. Only used when writing data.
        "block_shape" : list,
        "block_file_name_format" : FormattedField( requiredFields=["roiString"] ), # For hdf5, include dataset name, e.g. myfile_block{roiString}.h5/volume/data
        "dataset_root_dir" : str, # Abs path or relative to the description file itself. Defaults to "." if left blank.
        "hash_id" : str # Not user-defined (clients may use this)
    }
    DescriptionSchema = JsonConfigSchema( DescriptionFields )

    @classmethod
    def readDescription(cls, descriptionFilePath):
        return BlockwiseFileset.DescriptionSchema.parseConfigFile( descriptionFilePath )

    @classmethod
    def writeDescription(cls, descriptionFilePath, descriptionFields):
        BlockwiseFileset.DescriptionSchema.writeConfigFile( descriptionFilePath, descriptionFields )

    class BlockNotReadyError(Exception):
        def __init__(self, block_start):
            self.block_start = block_start

    def __init__( self, descriptionFilePath, mode='r', preparsedDescription=None ):
        """
        Constructor.
        :param descriptionFilePath: The path to the .json file that describes the dataset.
        :param mode: Set to 'r' if the fileset should be read-only.
        :param preparsedDescription: (Optional) Provide pre-parsed description fields, in which case the provided description file will not be parsed.
        """
        assert mode == 'r' or mode == 'a', "Valid modes are 'r' or 'a', not '{}'".format(mode)
        self.mode = mode
        
        assert descriptionFilePath is not None, "Must provide a path to the description file, even if you are providing pre-parsed fields. (Path is used to find block directory)."
        self.descriptionFilePath = descriptionFilePath
        
        if preparsedDescription is not None:
            self.description = preparsedDescription
        else:
            self.description = BlockwiseFileset.readDescription( descriptionFilePath )

        assert self.description.format == "hdf5", "Only hdf5 blockwise filesets are supported so far."
        
        self._lock = threading.Lock()
        self._openBlockFiles = {}
        self._closed = False

    def close(self):
        with self._lock:
            assert not self._closed
            paths = self._openBlockFiles.keys()
            for path in paths:
                blockFile = self._openBlockFiles[path].blockFile
                blockFile.close()
            self._closed = True
            

    def readData(self, roi, out_array=None):
        """
        Read data from the fileset.
        :param roi: The region of interest to read from the dataset.  Must be a tuple of iterables: (start, stop).
        :param out_array: The location to store the read data.  Must be the correct size for the given roi.  If not provided, an array is created for you.
        :returns: The requested data.  If out_array was provided, returns out_array.
        """
        if out_array is None:
            out_array = numpy.ndarray( shape=numpy.subtract(roi[1], roi[0]), dtype=self.description.dtype )
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
        blockFilePath = self.description.dataset_root_dir
        descriptionFileDir = os.path.split(self.descriptionFilePath)[0]
        if blockFilePath is None:
            blockFilePath = descriptionFileDir
        else:
            absPath, relPath = getPathVariants( blockFilePath, descriptionFileDir )
            blockFilePath = absPath

        for axis, start in zip(self.description.axes, blockstart):
            blockFilePath = os.path.join( blockFilePath, "{}_{:08d}".format( axis, start ) )
        return blockFilePath

    def getDatasetPathComponents(self, block_start):
        """
        Return a PathComponents object for the block file that corresponds to the given block start coordinate.
        """
        entire_block_roi = self.getEntireBlockRoi(block_start)
        roiString = "{}".format( (list(entire_block_roi[0]), list(entire_block_roi[1]) ) )
        datasetFilename = self.description.block_file_name_format.format( roiString=roiString )
        datasetDir = self.getDatasetDirectory( entire_block_roi[0] )
        datasetPath = os.path.join( datasetDir, datasetFilename )

        return PathComponents( datasetPath )

    BLOCK_NOT_AVAILABLE = 0
    BLOCK_AVAILABLE = 1
    def getBlockStatus(self, blockstart):
        """
        Check a block's status.
        (Just because a block file exists doesn't mean that it has valid data.)
        """
        blockDir = self.getDatasetDirectory(blockstart)
        statusFilePath = os.path.join(blockDir, "STATUS.txt")

        if not os.path.exists( statusFilePath ):
            return BlockwiseFileset.BLOCK_NOT_AVAILABLE
        else:
            return BlockwiseFileset.BLOCK_AVAILABLE

    def setBlockStatus(self, blockstart, status):
        """
        Set a block status on disk.  We use a simple convention: If the status file exists, the block is available.  Otherwise, it ain't.
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
        return getBlockBounds( self.description.shape, self.description.block_shape, block_start )

    def getAllBlockRois(self):
        entire_dataset_roi = ([0] *len(self.description.shape), self.description.shape)
        block_starts = getIntersectingBlocks(self.description.block_shape, entire_dataset_roi)
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
        entire_dataset_roi = ([0] *len(self.description.shape), self.description.shape)
        clipped_roi = getIntersection( roi, entire_dataset_roi )
        assert (numpy.array(clipped_roi) == numpy.array(roi)).all(), "Roi {} does not fit within dataset bounds: {}".format(roi, self.description.shape)
        
        block_starts = getIntersectingBlocks(self.description.block_shape, roi)
        
        # TODO: Parallelize this loop
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

        if self.description.format == "hdf5":
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

            hdf5File = self._getOpenBlockfile( hdf5FilePath )
            array_data[...] = hdf5File[ path_parts.internalPath ][ roiToSlice( *block_relative_roi ) ]
        else:
            # Create the directory
            if not os.path.exists( datasetDir ):
                os.makedirs( datasetDir )

            # Clear the block status.
            # The CALLER is responsible for setting it again.
            self.setBlockStatus( block_start, BlockwiseFileset.BLOCK_NOT_AVAILABLE )

            # Write the block data file
            hdf5File = self._getOpenBlockfile( hdf5FilePath )
            if path_parts.internalPath not in hdf5File:
                chunks = self.description.chunks
                if chunks is not None:
                    chunks = tuple(chunks)
                dataset = hdf5File.create_dataset( path_parts.internalPath,
                                         shape=( entire_block_roi[1] - entire_block_roi[0] ),
                                         dtype=self.description.dtype,
                                         chunks=chunks )
                if _use_vigra:
                    dataset.attrs['axistags'] = vigra.defaultAxistags( self.description.axes ).toJSON()
            hdf5File[ path_parts.internalPath ][ roiToSlice( *block_relative_roi ) ] = array_data[...]

    def _getOpenBlockfile(self, blockFilePath):
        # Try once without locking
        if blockFilePath in self._openBlockFiles:
            return self._openBlockFiles[ blockFilePath ]

        # Obtain the lock and try again
        with self._lock:
            if blockFilePath not in self._openBlockFiles.keys():
                self._openBlockFiles[ blockFilePath ] = h5py.File( blockFilePath, self.mode )
            return self._openBlockFiles[ blockFilePath ]












