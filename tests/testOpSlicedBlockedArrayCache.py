import threading
import numpy
import vigra
from lazyflow.graph import Graph
from lazyflow.roi import sliceToRoi, roiToSlice
from lazyflow.operators import OpArrayPiper, OpSlicedBlockedArrayCache

class KeyMaker():
    def __getitem__(self, *args):
        return list(*args)
make_key = KeyMaker()

class OpArrayPiperWithAccessCount(OpArrayPiper):
    """
    A simple array piper that counts how many times its execute function has been called.
    """
    def __init__(self, *args, **kwargs):
        super(OpArrayPiperWithAccessCount, self).__init__(*args, **kwargs)
        self.accessCount = 0
        self._lock = threading.Lock()
        self.printRoi = False
    
    def execute(self,slot,roi,result):
        with self._lock:
            self.accessCount += 1
        
        if self.printRoi:
            print "Access: ",roi
        
        super(OpArrayPiperWithAccessCount, self).execute(slot, roi, result)
        

class TestOpSlicedBlockedArrayCache(object):

    def setUp(self):
        self.dataShape = (1,100,100,10,1)
        self.data = (numpy.random.random(self.dataShape) * 100).astype(int)
        self.data = self.data.view(vigra.VigraArray)
        self.data.axistags = vigra.defaultAxistags('txyzc')

        graph = Graph()
        opProvider = OpArrayPiperWithAccessCount(graph=graph)
        opProvider.Input.setValue(self.data)
        self.opProvider = opProvider
        
        opCache = OpSlicedBlockedArrayCache(graph=graph)
        opCache.Input.connect(opProvider.Output)
        opCache.innerBlockShape.setValue( ( (10,1,10,10,10), (10,10,1,10,10), (10,10,10,1,10) ) )
        opCache.outerBlockShape.setValue( ( (20,2,20,20,20), (20,20,2,20,20), (20,20,20,2,20) ) )
        opCache.fixAtCurrent.setValue(False)
        self.opCache = opCache

    def testCacheAccess(self):
        opCache = self.opCache
        opProvider = self.opProvider        
        
        
        # Block-aligned request
        slicing = make_key[0:1, 0:10, 10:20, 0:10, 0:1]
        oldAccessCount = opProvider.accessCount
        data = opCache.Output( slicing ).wait()
        data = data.view(vigra.VigraArray)
        data.axistags = opCache.Output.meta.axistags
        assert (data == self.data[slicing]).all()

        # Our slice intersects 5 outer blocks and 10 inner blocks
        minAccess = oldAccessCount + 5
        maxAccess = oldAccessCount + 10
        assert opProvider.accessCount >= minAccess
        assert opProvider.accessCount <= maxAccess
        oldAccessCount = opProvider.accessCount

        # Same request should come from cache, so access count is unchanged
        data = opCache.Output( slicing ).wait()
        assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(opProvider.accessCount, oldAccessCount)

        # Not block-aligned request
        slicing = make_key[0:1, 45:65, 10:20, 0:10, 0:1]
        data = opCache.Output( slicing ).wait()
        data = data.view(vigra.VigraArray)
        data.axistags = opCache.Output.meta.axistags
        assert (data == self.data[slicing]).all()

        # Our slice intersects 5 outer block and 20 inner blocks
        minAccess = oldAccessCount + 10
        maxAccess = oldAccessCount + 20
        assert opProvider.accessCount >= minAccess
        assert opProvider.accessCount <= maxAccess
        oldAccessCount = opProvider.accessCount

        # Same request should come from cache, so access count is unchanged
        data = opCache.Output( slicing ).wait()
        assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(opProvider.accessCount, oldAccessCount)

    def testDirtySource(self):
        opCache = self.opCache
        opProvider = self.opProvider        
        
        oldAccessCount = 0
        assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(opProvider.accessCount, oldAccessCount)

        # Request
        slicing = make_key[:, 0:50, 15:45, 0:10, :]
        data = opCache.Output( slicing ).wait()
        data = data.view(vigra.VigraArray)
        data.axistags = opCache.Output.meta.axistags
        assert (data == self.data[slicing]).all()
        
        # Our slice intersects 3*3*5=9 outerBlocks
        minAccess = oldAccessCount + 45
        maxAccess = oldAccessCount + 90
        assert opProvider.accessCount >= minAccess
        assert opProvider.accessCount <= maxAccess
        oldAccessCount = opProvider.accessCount

        # Track dirty notifications
        gotDirtyKeys = []
        def handleDirty(slot, roi):
            gotDirtyKeys.append( list(roiToSlice(roi.start, roi.stop)) )
        opCache.Output.notifyDirty(handleDirty)
        
        # Change some of the input data and mark it dirty
        dirtykey = make_key[0:1, 10:20, 20:30, 0:3, 0:1]
        self.data[dirtykey] = 0.12345
        opProvider.Input.setDirty(dirtykey)        
        assert len(gotDirtyKeys) > 0
        
        # Same request, but should need to access the data again due to dirtiness
        data = opCache.Output( slicing ).wait()
        data = data.view(vigra.VigraArray)
        data.axistags = opCache.Output.meta.axistags
        assert (data == self.data[slicing]).all()

        # The dirty data intersected 2 outerBlocks and a total of 3 innerBlock.
        minAccess = oldAccessCount + 2
        maxAccess = oldAccessCount + 3
        assert opProvider.accessCount >= minAccess
        assert opProvider.accessCount <= maxAccess
        oldAccessCount = opProvider.accessCount

    def testFixAtCurrent(self):
        opCache = self.opCache
        opProvider = self.opProvider        

        # Track dirty notifications
        gotDirtyKeys = []
        def handleDirty(slot, roi):
            gotDirtyKeys.append( list(roiToSlice(roi.start, roi.stop)) )
        opCache.Output.notifyDirty(handleDirty)
        
        opCache.fixAtCurrent.setValue(True)

        oldAccessCount = 0
        assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(opProvider.accessCount, oldAccessCount)

        # Request (no access to provider because fixAtCurrent)
        slicing = make_key[:, 0:50, 15:45, 0:1, :]
        data = opCache.Output( slicing ).wait()
        assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(opProvider.accessCount, oldAccessCount)

        # We haven't accessed this data yet,
        #  but fixAtCurrent is True so the cache gives us zeros
        assert (data == 0).all()

        opCache.fixAtCurrent.setValue(False)

        # Request again.  Data should match this time.
        oldAccessCount = opProvider.accessCount
        data = opCache.Output( slicing ).wait()
        data = data.view(vigra.VigraArray)
        data.axistags = opCache.Output.meta.axistags
        assert (data == self.data[slicing]).all()

        # Our slice intersects 3*3=9 outerBlocks, and a total of 20 innerBlocks
        # Inner caches are allowed to split up the accesses, so there could be as many as 20
        minAccess = oldAccessCount + 9
        maxAccess = oldAccessCount + 20
        assert opProvider.accessCount >= minAccess
        assert opProvider.accessCount <= maxAccess
        oldAccessCount = opProvider.accessCount

        # Request again.  Data should match WITHOUT requesting from the source.
        data = opCache.Output( slicing ).wait()
        data = data.view(vigra.VigraArray)
        data.axistags = opCache.Output.meta.axistags
        assert (data == self.data[slicing]).all()
        assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(opProvider.accessCount, oldAccessCount)

        # Freeze it again
        opCache.fixAtCurrent.setValue(True)

        # Clear previous
        gotDirtyKeys = []

        # Change some of the input data that ISN'T cached yet and mark it dirty
        dirtykey = make_key[0:1, 90:100, 90:100, 0:1, 0:1]
        self.data[dirtykey] = 0.12345
        opProvider.Input.setDirty(dirtykey)

        # Dirtiness not propagated due to fixAtCurrent
        assert len(gotDirtyKeys) == 0
        
        # Same request.  Data should still match the previous data (not yet refreshed)
        data2 = opCache.Output( slicing ).wait()
        data2 = data2.view(vigra.VigraArray)
        data2.axistags = opCache.Output.meta.axistags
        assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(opProvider.accessCount, oldAccessCount)
        assert (data2 == data).all()

        # Unfreeze.
        opCache.fixAtCurrent.setValue(False)

        # Some data became dirty while we were fixed, 
        #  but no one had ever asked for it.
        # In such cases, the dirtiness is not propagated downstream.
        assert len(gotDirtyKeys) == 0

        # Same request.  Data should be updated now that we're unfrozen.
        data = opCache.Output( slicing ).wait()
        data = data.view(vigra.VigraArray)
        data.axistags = opCache.Output.meta.axistags
        assert (data == self.data[slicing]).all()

        # Dirty data did not intersect with this request.
        # Data should still be cached (no extra accesses)
        assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(opProvider.accessCount, oldAccessCount)

        ###########################3
        # Freeze it again
        opCache.fixAtCurrent.setValue(True)

        # Clear previous
        gotDirtyKeys = []
        
        # Change some of the input data that IS cached and mark it dirty
        dirtykey = make_key[:, 0:25, 20:40, 0:1, :]
        self.data[dirtykey] = 0.54321
        opProvider.Input.setDirty(dirtykey)

        # Dirtiness not propagated due to fixAtCurrent
        assert len(gotDirtyKeys) == 0
        
        # Same request.  Data should still match the previous data (not yet refreshed)
        data2 = opCache.Output( slicing ).wait()
        data2 = data2.view(vigra.VigraArray)
        data2.axistags = opCache.Output.meta.axistags
        assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(opProvider.accessCount, oldAccessCount)
        assert (data2 == data).all()

        # Unfreeze. Previous dirty notifications should now be seen.
        opCache.fixAtCurrent.setValue(False)
        assert len(gotDirtyKeys) > 0

        # Same request.  Data should be updated now that we're unfrozen.
        data = opCache.Output( slicing ).wait()
        data = data.view(vigra.VigraArray)
        data.axistags = opCache.Output.meta.axistags
        assert (data == self.data[slicing]).all()

        # The dirty data intersected 2 outerBlocks, and a total of 6 innerblocks
        # Inner caches are allowed to split up the accesses, so there could be as many as 6
        minAccess = oldAccessCount + 2
        maxAccess = oldAccessCount + 6
        assert opProvider.accessCount >= minAccess
        assert opProvider.accessCount <= maxAccess
        oldAccessCount = opProvider.accessCount

        #####################        

        #### Repeat plain dirty test to ensure fixAtCurrent didn't mess up the block states.

        gotDirtyKeys = []

        # Change some of the input data and mark it dirty
        dirtykey = make_key[0:1, 10:11, 20:21, 0:3, 0:1]
        self.data[dirtykey] = 0.54321
        opProvider.Input.setDirty(dirtykey)

        assert len(gotDirtyKeys) > 0
        
        # Should need access again.
        slicing = make_key[:, 0:50, 15:45, 0:10, :]
        data = opCache.Output( slicing ).wait()
        data = data.view(vigra.VigraArray)
        data.axistags = opCache.Output.meta.axistags
        assert (data == self.data[slicing]).all()

        # The dirty data intersected 3*3*5 outerBlocks 
        minAccess = oldAccessCount + 45
        maxAccess = oldAccessCount + 90
        assert opProvider.accessCount >= minAccess
        assert opProvider.accessCount <= maxAccess
        oldAccessCount = opProvider.accessCount

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)











