import sys
import logging

import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators import OpCachedLabelImage, OpDummyData

logger = logging.getLogger("tests.testOpCachedLabelImage")
labelerLogger = logging.getLogger("lazyflow.operators.opCachedLabelImage")

class TestOpCachedLabelImage(object):
    
    def testBasic(self):
        graph = Graph()
        # OpDummyData needs an input array to decide what shape/dtype/axes to make the output
        a = numpy.ndarray( shape=(2,100,100,100,3), dtype=numpy.uint32 )
        v = a.view( vigra.VigraArray )
        v.axistags = vigra.defaultAxistags('txyzc')

        # OpDummyData provides a simple binary image with a bunch of thick diagonal planes.
        opData = OpDummyData( graph=graph )
        opData.Input.setValue( v )
        assert opData.Output.ready()
        assert opData.Output.meta.axistags is not None
        
        # Each plane should get it's own label...        
        op = OpCachedLabelImage( graph=graph )
        op.Input.connect( opData.Output )
        assert op.Output.ready()
        
        labels = op.Output[:].wait()
        logger.warn( "labels:\n{}".format( str(labels[0,:20,:20,0,0])) )

        cached_labels = op.CachedOutput[:].wait()
        logger.warn( "cached_labels:\n{}".format( str(cached_labels[0,:20,:20,0,0])) )
        assert (labels == cached_labels).all()

if __name__ == "__main__":
    # Set up logging for debug
    logHandler = logging.StreamHandler( sys.stdout )
    logger.addHandler( logHandler )
    labelerLogger.addHandler( logHandler )

    logger.setLevel( logging.DEBUG )
    labelerLogger.setLevel( logging.DEBUG )

    # Run nose
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)

        