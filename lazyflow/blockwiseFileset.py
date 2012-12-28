import os
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
        "chunks" : list, # Optional.  If null, no chunking.
        "block_shape" : list,
        "block_file_name_format" : FormattedField( requiredFields=["roiString"] ),
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

    def __init__( self, descriptionFilePath, mode='r' ):
        """
        Constructor.
        :param descriptionFilePath: The path to the .json file that describes the dataset.
        :param mode: Set to 'r' if the fileset should be read-only.
        """
        self.mode = mode
        self.descriptionFilePath = descriptionFilePath
        self.description = BlockwiseFileset.readDescription( descriptionFilePath )
        
        assert self.description.format == "hdf5", "Only hdf5 blockwise filesets are supported so far."

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
        datasetFilename = self.description.block_file_name_format.format( roiString=str(entire_block_roi) )
        datasetDir = self.getDatasetDirectory( entire_block_roi[0] )
        datasetPath = os.path.join( datasetDir, datasetFilename )

        if self.description.format == "hdf5":
            self._transferBlockDataHdf5( entire_block_roi, block_relative_roi, array_data, read, datasetPath )
        else:
            assert False, "Unknown format"        

    def _transferBlockDataHdf5(self, entire_block_roi, block_relative_roi, array_data, read, datasetPath ):
        """
        Transfer a block of data to/from an hdf5 dataset.
        See _transferBlockData() for details.
        """
        # For the hdf5 format, the full path format INCLUDES the dataset name, e.g. /path/to/myfile.h5/volume/data
        path_parts = PathComponents( datasetPath )
        datasetDir = path_parts.externalDirectory
        hdf5FilePath = path_parts.externalPath
        statusFilePath = os.path.join(datasetDir, "STATUS.txt")
        if read:
            # Check for problems before reading.
            if self.getBlockStatus( entire_block_roi[0] ) is not BlockwiseFileset.BLOCK_AVAILABLE:
                raise RuntimeError( "Can't read block: Data isn't available or isn't ready.".format( hdf5FilePath ) )
            with h5py.File(hdf5FilePath, 'r') as hdf5File:
                try:
                    array_data[...] = hdf5File[ path_parts.internalPath ][ roiToSlice( *block_relative_roi ) ]
                except:
                    assert False
        else:
            # Create the directory
            if not os.path.exists( datasetDir ):
                os.makedirs( datasetDir )

            # Delete previous status file (if present)
            if os.path.exists( statusFilePath ):
                os.remove( statusFilePath )

            # Write the block data file
            with h5py.File(hdf5FilePath) as hdf5File:
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

            # Create the statusfile
            with file( os.path.join(datasetDir, "STATUS.txt"), 'w' ) as statusFile:
                statusFile.write("READY")

