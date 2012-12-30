import sys
import numpy
import threading
from lazyflow.graph import Graph
from lazyflow.roi import getIntersectingBlocks, getBlockBounds, roiToSlice
from lazyflow.operators import OpArrayPiper

from lazyflow.roiRequestBatch import RoiRequestBatch

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)

class TestRoiRequestBatch(object):
    
    def testBasic(self):
        op = OpArrayPiper( graph=Graph() )
        inputData = numpy.indices( (100,100) ).sum(0)
        op.Input.setValue( inputData )
        roiList = []
        block_starts = getIntersectingBlocks( [10,10], ([0,0], [100, 100]) )
        for block_start in block_starts:
            roiList.append( getBlockBounds( [100,100], [10,10], block_start ) )    
    
        results = numpy.zeros( (100,100), dtype=numpy.int32 )
        resultslock = threading.Lock()

        resultsCount = [0]
        
        def handleResult(roi, result):
            assert resultslock.acquire(False), "resultslock is contested! Access to callback is supposed to be automatically serialized."
            results[ roiToSlice( *roi ) ] = result
            logger.debug( "Got result for {}".format(roi) )
            resultslock.release()
            resultsCount[0] += 1

        progressList = []
        def handleProgress( progress ):
            progressList.append( progress )
            logger.debug( "Progress update: {}".format(progress) )
        
        batch = RoiRequestBatch(op.Output, roiList, handleResult, batchSize=10)
        batch.progressSignal.subscribe( handleProgress )
        
        batch.start()
        logger.debug( "Got {} results".format( resultsCount[0] ) )
        assert (results == inputData).all()

        # Progress reporting MUST start with 0 and end with 100        
        assert progressList[0] == 0, "Invalid progress reporting."
        assert progressList[-1] == 100, "Invalid progress reporting."
        
        # There should be some intermediate progress reporting, but exactly how much is unspecified.
        assert len(progressList) >= 10
        
        logger.debug( "FINISHED" )

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)


