import os
import sys
import shutil
import tempfile
import numpy
from lazyflow.blockwiseFileset import BlockwiseFileset
from lazyflow.roi import sliceToRoi

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)

class TestBlockwiseFileset(object):
    
    @classmethod
    def setupClass(cls):
        testConfig = \
        """
        {
            "name" : "synapse_small",
            "format" : "hdf5",
            "axes" : "txyzc",
            "shape" : [1,400,400,200,1],
            "dtype" : "numpy.uint8",
            "block_shape" : [1, 50, 50, 50, 100],
            "block_file_name_format" : "cube{roiString}.h5/volume/data"
        }
        """
        cls.tempDir = tempfile.mkdtemp()
        cls.configpath = os.path.join(cls.tempDir, "config.json")
        with open(cls.configpath, 'w') as f:
            f.write(testConfig)
    
        logger.debug( "Loading config file..." )
        cls.bfs = BlockwiseFileset( cls.configpath, 'w' )
        cls.dataShape = tuple(cls.bfs.description.shape)
    
        logger.debug( "Creating random test data..." )
        cls.data = numpy.random.randint(255, size=cls.dataShape ).astype(numpy.uint8)
        
    @classmethod
    def teardownClass(cls):
        shutil.rmtree(cls.tempDir)

    def test_1_BasicWrite(self):
        logger.debug( "Writing test data..." )
        self.bfs.writeData( ([0,0,0,0,0], self.dataShape), self.data )
    
    def test_2_ReadAll(self):
        logger.debug( "Reading data..." )
        read_data = numpy.zeros( tuple(self.dataShape), dtype=numpy.uint8 )
        self.bfs.readData( ([0,0,0,0,0], self.dataShape), read_data )
        
        logger.debug( "Checking data..." )
        assert (self.data == read_data).all(), "Data didn't match."
    
    def test_3_ReadSome(self):
        logger.debug( "Reading data..." )
        slicing = numpy.s_[:, 50:150, 50:150, 50:150, :]
        roi = sliceToRoi( slicing, self.dataShape )
        roiShape = roi[1] - roi[0]
        read_data = numpy.zeros( tuple(roiShape), dtype=numpy.uint8 )
        
        self.bfs.readData( roi, read_data )
        
        logger.debug( "Checking data..." )
        assert self.data[slicing].shape == read_data.shape
        assert (self.data[slicing] == read_data).all(), "Data didn't match."

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
