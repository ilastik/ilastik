import os
import sys
import shutil
import tempfile
import numpy
from lazyflow.graph import Graph
from lazyflow.roi import getIntersectingBlocks
from lazyflow.utility.io.blockwiseFileset import BlockwiseFileset
from lazyflow.operators.ioOperators import OpBlockwiseFilesetReader

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)

class TestOpBlockwiseFilesetReader(object):
    
    def setUp(self):
        """
        Create a blockwise fileset to test with.
        """
        testConfig = \
        """
        {
            "_schema_name" : "blockwise-fileset-description",
            "_schema_version" : 1.0,

            "name" : "synapse_small",
            "format" : "hdf5",
            "axes" : "txyzc",
            "shape" : [1,400,400,100,1],
            "dtype" : "numpy.uint8",
            "block_shape" : [1, 50, 50, 50, 100],
            "block_file_name_format" : "cube{roiString}.h5/volume/data"
        }
        """
        self.tempDir = tempfile.mkdtemp()
        self.configpath = os.path.join(self.tempDir, "config.json")

        logger.debug( "Loading config file..." )
        with open(self.configpath, 'w') as f:
            f.write(testConfig)
        
        logger.debug( "Creating random test data..." )
        bfs = BlockwiseFileset( self.configpath, 'a' )
        dataShape = tuple(bfs.description.shape)
        self.data = numpy.random.randint( 255, size=dataShape ).astype(numpy.uint8)
        
        logger.debug( "Writing test data..." )
        datasetRoi = ([0,0,0,0,0], dataShape)
        bfs.writeData( datasetRoi, self.data )
        block_starts = getIntersectingBlocks(bfs.description.block_shape, datasetRoi)
        for block_start in block_starts:
            bfs.setBlockStatus(block_start, BlockwiseFileset.BLOCK_AVAILABLE)        

    def tearDown(self):
        shutil.rmtree(self.tempDir)

    def testRead(self):
        graph = Graph()
        op = OpBlockwiseFilesetReader(graph=graph)
        op.DescriptionFilePath.setValue( self.configpath )
        
        slice1 = numpy.s_[ :, 20:150, 20:150, 20:100, : ]
        readData = op.Output[ slice1 ].wait()
        assert (readData == self.data[slice1]).all()

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)


