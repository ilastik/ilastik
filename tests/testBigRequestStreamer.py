import gc
import sys
import numpy
import psutil
import threading
from lazyflow.graph import Graph, Operator, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.operators import OpArrayPiper
from lazyflow.request import Request

from lazyflow.utility import BigRequestStreamer

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)

class TestBigRequestStreamer(object):

    def testBasic(self):
        op = OpArrayPiper( graph=Graph() )
        inputData = numpy.indices( (100,100) ).sum(0)
        op.Input.setValue( inputData )
    
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
        
        totalVolume = numpy.prod( inputData.shape )
        batch = BigRequestStreamer(op.Output, [(0,0), (100,100)], (10,10) )
        batch.resultSignal.subscribe( handleResult )
        batch.progressSignal.subscribe( handleProgress )
        
        batch.execute()
        logger.debug( "Got {} results".format( resultsCount[0] ) )
        assert (results == inputData).all()

        # Progress reporting MUST start with 0 and end with 100        
        assert progressList[0] == 0, "Invalid progress reporting."
        assert progressList[-1] == 100, "Invalid progress reporting."
        
        # There should be some intermediate progress reporting, but exactly how much is unspecified.
        assert len(progressList) >= 10
        
        logger.debug( "FINISHED" )

    def testForMemoryLeaks(self):
        """
        If the BigRequestStreamer doesn't clean requests as they complete, they'll take up too much memory.
        """
        
        class OpNonsense( Operator ):
            """
            Provide nonsense data of the correct shape for each request.
            """
            Output = OutputSlot()

            def setupOutputs(self):
                self.Output.meta.dtype = numpy.float32
                self.Output.shape = (2000, 2000, 2000)
    
            def execute(self, slot, subindex, roi, result):
                """
                Simulate a cascade of requests, to make sure that the entire cascade is properly freed.
                """
                roiShape = roi.stop - roi.start
                def getResults1():
                    return numpy.indices(roiShape, self.Output.meta.dtype).sum()
                def getResults2():
                    req = Request( getResults1 )
                    req.submit()
                    result[:] = req.wait()
                    return result

                req = Request( getResults2 )
                req.submit()
                result[:] = req.wait()
                return result
        
            def propagateDirty(self, slot, subindex, roi):
                pass

        gc.collect()

        vmem = psutil.virtual_memory()
        start_mem_usage_mb = (vmem.total - vmem.available) / (1000*1000)
        logger.debug( "Starting test with memory usage at: {} MB".format( start_mem_usage_mb ) )

        op = OpNonsense( graph=Graph() )
        def handleResult( roi, result ):
            pass

        def handleProgress( progress ):
            #gc.collect()
            logger.debug( "Progress update: {}".format( progress ) )
            #vmem = psutil.virtual_memory()
            #finished_mem_usage_mb = (vmem.total - vmem.available) / (1000*1000)
            #difference_mb = finished_mem_usage_mb - start_mem_usage_mb
            #logger.debug( "Progress update: {} with memory usage at: {} MB ({} MB increase)".format( progress, finished_mem_usage_mb, difference_mb ) )

        batch = BigRequestStreamer(op.Output, [(0,0,0), (100,1000,1000)], (100,100,100) )
        batch.resultSignal.subscribe( handleResult )
        batch.progressSignal.subscribe( handleProgress )
        batch.execute()

        vmem = psutil.virtual_memory()
        finished_mem_usage_mb = (vmem.total - vmem.available) / (1000*1000)
        difference_mb = finished_mem_usage_mb - start_mem_usage_mb
        logger.debug( "Finished execution with memory usage at: {} MB ({} MB increase)".format( finished_mem_usage_mb, difference_mb ) )

        # Collect
        gc.collect()

        vmem = psutil.virtual_memory()
        finished_mem_usage_mb = (vmem.total - vmem.available) / (1000*1000)
        difference_mb = finished_mem_usage_mb - start_mem_usage_mb
        logger.debug( "Finished test with memory usage at: {} MB ({} MB increase)".format( finished_mem_usage_mb, difference_mb ) )
        assert difference_mb < 200, "BigRequestStreamer seems to have memory leaks.  After executing, RAM usage increased by {}".format( difference_mb )

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)

