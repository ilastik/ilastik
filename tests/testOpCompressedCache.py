import sys
import logging

import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators import OpCompressedCache, OpArrayPiper

logger = logging.getLogger("tests.testOpCompressedCache")
cacheLogger = logging.getLogger("lazyflow.operators.opCompressedCache")

class TestOpCompressedCache( object ):
    
    def testBasic5d(self):
        logger.info("Generating sample data...")
        sampleData = numpy.indices((3, 100, 200, 150, 2), dtype=numpy.float32).sum(0)
        sampleData = sampleData.view( vigra.VigraArray )
        sampleData.axistags = vigra.defaultAxistags('txyzc')
        
        graph = Graph()
        opData = OpArrayPiper( graph=graph )
        opData.Input.setValue( sampleData )
        
        op = OpCompressedCache( parent=None, graph=graph )
        logger.debug("Setting block shape...")
        op.BlockShape.setValue( [1, 100, 75, 50, 2] )
        op.Input.connect( opData.Output )
        
        assert op.Output.ready()
        
        slicing = numpy.s_[ 0:2, 0:100, 50:150, 75:150, 0:1 ]
        expectedData = sampleData[slicing].view(numpy.ndarray)
        
        logger.debug("Requesting data...")
        readData = op.Output[slicing].wait()
        
        logger.debug("Checking data...")    
        assert (readData == expectedData).all(), "Incorrect output!"

    def testBasic3d(self):
        logger.info("Generating sample data...")
        sampleData = numpy.indices((100, 200, 150), dtype=numpy.float32).sum(0)
        sampleData = sampleData.view( vigra.VigraArray )
        sampleData.axistags = vigra.defaultAxistags('xyz')
        
        graph = Graph()
        opData = OpArrayPiper( graph=graph )
        opData.Input.setValue( sampleData )
        
        op = OpCompressedCache( parent=None, graph=graph )
        logger.debug("Setting block shape...")
        op.BlockShape.setValue( [100, 75, 50] )
        op.Input.connect( opData.Output )
        
        assert op.Output.ready()
        
        slicing = numpy.s_[ 0:100, 50:150, 75:150 ]
        expectedData = sampleData[slicing].view(numpy.ndarray)
        
        logger.debug("Requesting data...")
        readData = op.Output[slicing].wait()
        
        logger.debug("Checking data...")    
        assert (readData == expectedData).all(), "Incorrect output!"

    def testBasic4d_txyc(self):
        logger.info("Generating sample data...")
        sampleData = numpy.indices((3, 200, 150, 2), dtype=numpy.float32).sum(0)
        sampleData = sampleData.view( vigra.VigraArray )
        sampleData.axistags = vigra.defaultAxistags('txyc')
        
        graph = Graph()
        opData = OpArrayPiper( graph=graph )
        opData.Input.setValue( sampleData )
        
        op = OpCompressedCache( parent=None, graph=graph )
        logger.debug("Setting block shape...")
        op.BlockShape.setValue( [1, 75, 50, 2] )
        op.Input.connect( opData.Output )
        
        assert op.Output.ready()
        
        slicing = numpy.s_[ 1:3, 50:150, 75:150, 0:1 ]
        expectedData = sampleData[slicing].view(numpy.ndarray)
        
        logger.debug("Requesting data...")
        readData = op.Output[slicing].wait()
        
        logger.debug("Checking data...")    
        assert (readData == expectedData).all(), "Incorrect output!"

    def testBasic2d(self):
        logger.info("Generating sample data...")
        sampleData = numpy.indices((200, 150), dtype=numpy.float32).sum(0)
        sampleData = sampleData.view( vigra.VigraArray )
        sampleData.axistags = vigra.defaultAxistags('txyc')
        
        graph = Graph()
        opData = OpArrayPiper( graph=graph )
        opData.Input.setValue( sampleData )
        
        op = OpCompressedCache( parent=None, graph=graph )
        logger.debug("Setting block shape...")
        op.BlockShape.setValue( [75, 50] )
        op.Input.connect( opData.Output )
        
        assert op.Output.ready()
        
        slicing = numpy.s_[ 50:150, 75:150 ]
        expectedData = sampleData[slicing].view(numpy.ndarray)
        
        logger.debug("Requesting data...")
        readData = op.Output[slicing].wait()
        
        logger.debug("Checking data...")    
        assert (readData == expectedData).all(), "Incorrect output!"

    def testBasicOneBlock(self):
        logger.info("Generating sample data...")
        sampleData = numpy.indices((3, 100, 200, 150, 2), dtype=numpy.float32).sum(0)
        sampleData = sampleData.view( vigra.VigraArray )
        sampleData.axistags = vigra.defaultAxistags('txyzc')
        
        graph = Graph()
        opData = OpArrayPiper( graph=graph )
        opData.Input.setValue( sampleData )
        
        op = OpCompressedCache( parent=None, graph=graph )
        # NO Block shape for this test.
        #op.BlockShape.setValue( [1, 100, 75, 50, 2] )
        op.Input.connect( opData.Output )
        
        assert op.Output.ready()
        
        slicing = numpy.s_[ 0:2, 0:100, 50:150, 75:150, 0:1 ]
        expectedData = sampleData[slicing].view(numpy.ndarray)
        
        logger.debug("Requesting data...")
        readData = op.Output[slicing].wait()
        
        logger.debug("Checking data...")    
        assert (readData == expectedData).all(), "Incorrect output!"

if __name__ == "__main__":
    # Set up logging for debug
    logHandler = logging.StreamHandler( sys.stdout )
    logger.addHandler( logHandler )
    cacheLogger.addHandler( logHandler )

    logger.setLevel( logging.DEBUG )
    cacheLogger.setLevel( logging.DEBUG )

    # Run nose
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
