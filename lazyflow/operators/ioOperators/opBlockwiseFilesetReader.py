import os
import tempfile
import urllib2
import numpy
import h5py
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.jsonConfig import JsonConfigSchema, AutoEval, FormattedField

import logging
logger = logging.getLogger(__name__)

BlockwiseFilesetDescriptionFields = \
{
    "name" : str,
    "format" : str,
    "axes" : str,
    "shape" : list,
    "dtype" : AutoEval(),
    "block_dims" : dict,
    "block_file_name_format" : FormattedField( requiredFields=["roiString"] )
}

class OpBlockwiseFilesetReader(Operator):
    """
    """
    name = "OpBlockwiseFilesetReader"

    DescriptionFilePath = InputSlot(stype='filestring')
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpBlockwiseFilesetReader, self).__init__(*args, **kwargs)
        self._configSchema = JsonConfigSchema( OpBlockwiseFilesetReader )
        self._axes = None
        self._blockshape = None

    def setupOutputs(self):
        # Read the dataset description file
        descriptionFields = self._configSchema.parseConfigFile( self.DescriptionFilePath.value )

        # Check for errors in the description file
        axes = descriptionFields.axes 
        assert False not in map(lambda a: a in 'txyzc', axes), "Unknown axis type.  Known axes: txyzc  Your axes:".format(axes)
        assert descriptionFields.format == "hdf5", "Only hdf5 blockwise filesets are supported so far."

        # Save description file members
        self._axes = descriptionFields.axes
        self._urlFormat = descriptionFields.url_format
        self._origin_offset = numpy.array(descriptionFields.origin_offset)
        self._block_file_name_format = descriptionFields.block_file_name_format
        self._blockshape = map( lambda key: descriptionFields.block_dims[key], descriptionFields.axes )

        outputShape = tuple( descriptionFields.shape )

#        # If the dataset has no channel axis, add one to the output as a convenience.
#        if 'c' not in axes:
#            outputShape += (1,)
#            self._axes += 'c'
#            self._origin_offset = numpy.array( list(self._origin_offset) + [0] )

        self.Output.meta.shape = outputShape
        self.Output.meta.dtype = descriptionFields.dtype
        self.Output.meta.axistags = vigra.defaultAxistags(self._axes)

    def execute(self, slot, subindex, roi, result):
        # Get the list of blocks we need to access
        blockstarts = self.getIntersectingBlocks( (roi.start, roi.stop) )

        # TODO: Parallelize this loop
        for blockstart in blockstarts:
            blockroi = self.getBlockIntersection( blockstart, (roi.start, roi.stop) )
            resultSlice = roiToSlice(blockstart + blockroi[0], blockstart + blockroi[1])
            
            hdf5Dataset = self.getDatasetForBlock( blockstart )
            result[ resultSlice ] = hdf5Dataset[ roiToSlice(blockroi[0], blockroi[1]) ]

    
        expectedFilePath = self._block_file_name_format.format(  )

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.DescriptionFilePath, "Unknown input slot."
        self.Output.setDirty( slice(None) )
        
    def getBlockIntersection(self, blockstart, roi):
        return getBlockIntersection(self.Output.meta.shape, self._blockshape, blockstart, roi)
    
    def getIntersectingBlocks(self, roi):
        return getIntersectingBlocks(self._blockshape, roi)
    
    def getDatasetForBlock(self, blockstart):
        baseDir = os.path.split( self.DescriptionFilePath.value )[0]
        datasetDir = getDatasetDirectory(baseDir)
        datasetPath = os.path.join( self._block_file_name_format.format( roiString=str(blockstart) ) )
        

def getDatasetDirectory(baseDir, axes, blockstart ):
    datasetDir = baseDir
    for axis, start in zip(axes, blockstart):
        blockFilePath = os.path.join( datasetDir, "{}_{:08d}".format( axis, start ) )
    return blockFilePath

def getBlockIntersection(outershape, blockshape, blockstart, roi):
    """
    Clip the given roi until it fits within a particular block region.
    The block is specified via blockshape and blockstart.
    Also clip the result to outershape, which is a 
    """
    # Get all needed shapes, etc. as numpy arrays for easy manipulation 
    outershape = numpy.array( outershape )
    blockshape = numpy.array( blockshape )
    blockstart = numpy.array( blockstart )
    blockstop = blockstart + blockshape
    roistart = numpy.array( roi[0] )
    roistop = numpy.array( roi[1] )    
    outerstart = numpy.zeros( (len(outershape)), dtype=int )

    # Clip to outer bounds
    roistart = numpy.maximum( roistart, outerstart )
    roistop = numpy.minimum( roistop, outershape )

    # Clip to inner bounds
    roistart = numpy.maximum( roistart, blockstart )    
    roistop = numpy.minimum( roistop, blockstop )

    assert numpy.prod( roistop - roistart ) > 0, "Roi {} does not intersect this block.  Why are you asking for the intersection?".format(roi)    
    return (roistart, roistop)

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


if __name__ == "__main__":
    testConfig = \
"""
{
    "name" : "gigacube",
    "format" : "hdf5",
    "axes" : "txyzc",
    "shape" : [1, 1020, 1020, 1020, 1],
    "dtype" : "numpy.uint8"
    "block_dims" : { 't' : 1, 'x' : 500, 'y' : 500, 'z' : 500, 'c' : 1 }
    "block_file_name_format" : "cube{roiString}.h5/volume/data",
}
"""

inter = getIntersectingBlocks( (10,10,10), [(25, 15, 0), (45, 55, 10)] )
print inter.shape
print inter

















