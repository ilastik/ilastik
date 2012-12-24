import os
import numpy
import h5py
import logging
logger = logging.getLogger(__name__)
from lazyflow.jsonConfig import AutoEval, FormattedField, JsonConfigSchema
from lazyflow.roi import getIntersection, roiToSlice
from lazyflow.pathHelpers import PathComponents

class BlockwiseFileset(object):
    
    DescriptionFields = \
    {
        "name" : str,
        "format" : str,
        "axes" : str,
        "shape" : tuple,
        "dtype" : AutoEval(),
        "block_shape" : list,
        "block_file_name_format" : FormattedField( requiredFields=["roiString"] )
    }
    
    DescriptionSchema = JsonConfigSchema( DescriptionFields )

    def __init__( self, descriptionFilePath, mode='r' ):
        self.mode = mode
        self.descriptionFilePath = descriptionFilePath
        self.description = BlockwiseFileset.DescriptionSchema.parseConfigFile( descriptionFilePath )
        
        assert self.description.format == "hdf5", "Only hdf5 blockwise filesets are supported so far."

    def readData(self, roi, out_array):
        if out_array is None:
            out_array = numpy.ndarray( shape=numpy.subtract(roi[1], roi[0]), dtype=self.description.dtype )
        self._transferData(roi, out_array, read=True)

    def writeData(self, roi, data):
        assert self.mode != 'r'        
        self._transferData(roi, data, read=False)

    def _transferData( self, roi, array_data, read ):
        block_shape = numpy.array( self.description.block_shape )
        block_starts = BlockwiseFileset.getIntersectingBlocks(self.description.block_shape, roi)
        
        entire_dataset_roi = ([0] *len(self.description.shape), self.description.shape)
        
        # TODO: Parallelize this loop
        for block_start in block_starts:
            entire_block_roi = ( block_start, block_start + block_shape )
            entire_block_roi = getIntersection( entire_block_roi, entire_dataset_roi )
            transfer_block_roi = getIntersection( entire_block_roi, roi )
            block_relative_roi = ( transfer_block_roi[0] - block_start, transfer_block_roi[1] - block_start )

            self._transferBlockData( entire_block_roi, block_relative_roi, array_data[ roiToSlice( *transfer_block_roi ) ], read )

    def _transferBlockData( self, entire_block_roi, block_relative_roi, array_data, read ):
        datasetFilename = self.description.block_file_name_format.format( roiString=str(entire_block_roi) )
        datasetDir = self.getDatasetDirectory( entire_block_roi[0] )
        datasetPath = os.path.join( datasetDir, datasetFilename )

        if self.description.format == "hdf5":
            # For the hdf5 format, the full path format INCLUDES the dataset name, e.g. /path/to/myfile.h5/volume/data
            path_parts = PathComponents( datasetPath )
            hdf5FilePath = path_parts.externalPath
            if read:
                with h5py.File(hdf5FilePath, 'r') as hdf5File:
                    array_data[...] = hdf5File[ path_parts.internalPath ][ roiToSlice( *block_relative_roi ) ]
            else:
                if not os.path.exists( datasetDir ):
                    os.makedirs( datasetDir )
                with h5py.File(hdf5FilePath) as hdf5File:
                    if path_parts.internalPath not in hdf5File:
                        hdf5File.create_dataset( path_parts.internalPath, shape=( entire_block_roi[1] - entire_block_roi[0] ), dtype=self.description.dtype )
                    hdf5File[ path_parts.internalPath ][ roiToSlice( *block_relative_roi ) ] = array_data[...]
        else:
            assert False, "Unknown format"        

    @staticmethod
    def getIntersectingBlocks( blockshape, roi ):
        """
        Returns the start coordinate of each block that the given roi intersects.
        For example:
    
        >>> getIntersectingBlocks( (10, 20), [(15, 25),(23, 40)] )
        array([[10, 20],
               [20, 20]])
    
        >>> getIntersectingBlocks( (10, 20), [(15, 25),(23, 41)] )
        array([[10, 20],
               [10, 40],
               [20, 20],
               [20, 40]]) 
    
        """
        assert len(blockshape) == len(roi[0]) == len(roi[1]), "blockshape and roi are mismatched."
        roistart = numpy.array( roi[0] )
        roistop = numpy.array( roi[1] )
        blockshape = numpy.array( blockshape )
        
        block_index_map_start = roistart / blockshape
        block_index_map_stop = ( roistop + (blockshape - 1) ) / blockshape # Add (blockshape-1) first as a faster alternative to ceil() 
        block_index_map_shape = block_index_map_stop - block_index_map_start
        
        num_axes = len(blockshape)
        block_indices = numpy.indices( block_index_map_shape )
        block_indices = numpy.rollaxis( block_indices, 0, num_axes+1 )
        block_indices += block_index_map_start
    
        indices_shape = block_indices.shape
        indices_list = numpy.reshape( block_indices, (numpy.prod(indices_shape[0:-1]), indices_shape[-1]) )
    
        # Multiply by blockshape to get the list of start coordinates
        return (indices_list * blockshape)

    def getDatasetDirectory( self, blockstart ):
        blockFilePath = os.path.split(self.descriptionFilePath)[0]
        for axis, start in zip(self.description.axes, blockstart):
            blockFilePath = os.path.join( blockFilePath, "{}_{:08d}".format( axis, start ) )
        return blockFilePath
