import os
import sys
import shutil
import tempfile
import numpy
from lazyflow.blockwiseFileset import BlockwiseFileset

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)

class TestBlockwiseFileset(object):
    
    def setUp(self):
        testConfig = \
        """
        {
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
        with open(self.configpath, 'w') as f:
            f.write(testConfig)

    def tearDown(self):
        shutil.rmtree(self.tempDir)

    def testBasicWriteAndRead(self):
        logger.debug( "Loading config file..." )
        bfs = BlockwiseFileset( self.configpath, 'w' )
        dataShape = tuple(bfs.description.shape)
    
        logger.debug( "Creating random test data..." )
        data = numpy.random.randint(255, size=dataShape ).astype(numpy.uint8)
        
        logger.debug( "Writing test data..." )
        bfs.writeData( ([0,0,0,0,0], dataShape), data )
    
        logger.debug( "Reading data..." )
        read_data = numpy.zeros( tuple(dataShape), dtype=numpy.uint8 )
        bfs.readData( ([0,0,0,0,0], dataShape), read_data )
        
        logger.debug( "Checking data..." )
        assert (data == read_data).all(), "Data didn't match."

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
