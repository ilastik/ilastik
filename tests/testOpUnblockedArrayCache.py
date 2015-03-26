import numpy as np
import vigra

from lazyflow.request import RequestPool
from lazyflow.graph import Graph
from lazyflow.roi import roiToSlice
from lazyflow.operators.opUnblockedArrayCache import OpUnblockedArrayCache
from lazyflow.utility.testing import OpArrayPiperWithAccessCount

import logging
logger = logging.getLogger( __name__ )
cacheLogger = logging.getLogger( "lazyflow.operators.opUnblockedArrayCache" )

class TestOpUnblockedArrayCacheCache(object):
    def testBasic(self):
        graph = Graph()
        opDataProvider = OpArrayPiperWithAccessCount( graph=graph )
        opCache = OpUnblockedArrayCache( graph=graph )
        
        data = np.random.random( (100,100,100) ).astype(np.float32)
        opDataProvider.Input.setValue( vigra.taggedView( data, 'zyx' ) )
        opCache.Input.connect( opDataProvider.Output )
        
        roi = ((30, 30, 30), (50, 50, 50))
        cache_data = opCache.Output( *roi ).wait()
        assert (cache_data == data[roiToSlice(*roi)]).all()
        assert opDataProvider.accessCount == 1

        # Request the same data a second time.
        # Access count should not change.
        cache_data = opCache.Output( *roi ).wait()
        assert (cache_data == data[roiToSlice(*roi)]).all()
        assert opDataProvider.accessCount == 1
        
        # Now invalidate a part of the data
        # The cache will discard it, so the access count should increase.
        opDataProvider.Input.setDirty( (30, 30, 30), (31, 31, 31) )
        cache_data = opCache.Output( *roi ).wait()
        assert (cache_data == data[roiToSlice(*roi)]).all()
        assert opDataProvider.accessCount == 2
                
        # Repeat this next part just for safety
        for _ in range(10):
            # Make sure the cache is empty
            opDataProvider.Input.setDirty( (30, 30, 30), (31, 31, 31) )
            opDataProvider.accessCount = 0

            # Create many requests for the same data.
            # Upstream data should only be accessed ONCE.
            pool = RequestPool()
            for _ in range(10):
                pool.add( opCache.Output( *roi ) )
            pool.wait()
            assert opDataProvider.accessCount == 1

        # Also, make sure requests for INNER rois of stored blocks are also serviced from memory
        opDataProvider.accessCount = 0
        inner_roi = ((35, 35, 35), (45, 45, 45))
        cache_data = opCache.Output( *inner_roi ).wait()
        assert (cache_data == data[roiToSlice(*inner_roi)]).all()
        assert opDataProvider.accessCount == 0

    def testCacheApi(self):
        graph = Graph()
        opDataProvider = OpArrayPiperWithAccessCount( graph=graph )
        opCache = OpUnblockedArrayCache( graph=graph )
        
        data = np.random.random( (100,100,100) ).astype(np.float32)
        opDataProvider.Input.setValue( vigra.taggedView( data, 'zyx' ) )
        opCache.Input.connect( opDataProvider.Output )

        opCache.Output[10:20, 20:40, 50:100].wait()
        opCache.Output[11:21, 22:43, 53:90].wait()

        l = opCache.getBlockAccessTimes()
        assert len(l) == 2
        for k, t in l:
            assert t > 0.0


if __name__ == "__main__":
    # Set up logging for debug
    import sys
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
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
    
        