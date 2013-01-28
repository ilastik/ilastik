import time
import threading
import numpy
import vigra
import lazyflow
import lazyflow.graph
from lazyflow.operators import OpMetadataInjector, OpOutputProvider, OpMetadataSelector, OpValueCache, OpMetadataMerge

class TestOpMetadataInjector(object):
    
    def test(self):
        g = lazyflow.graph.Graph()
        op = OpMetadataInjector(graph=g)
    
        additionalMetadata = {'layertype' : 7}
        op.Metadata.setValue( additionalMetadata )
        op.Input.setValue('Hello')
    
        # Output value should match input value
        assert op.Output.value == op.Input.value
    
        # Make sure all input metadata was copied to the output
        assert all( ((k,v) in op.Output.meta.items()) for k,v in op.Input.meta.items())
    
        # Check that the additional metadata was added to the output
        assert op.Output.meta.layertype == 7
    
        # Make sure dirtyness gets propagated to the output.
        dirtyList = []
        def handleDirty(*args):
            dirtyList.append(True)
    
        op.Output.notifyDirty( handleDirty )
        op.Input.setValue( 8 )
        assert len(dirtyList) == 1


class TestOpOutputProvider(object):
    
    def test(self):
        from lazyflow.graph import Graph, MetaDict
        g = Graph()
        
        # Create some data to give    
        shape = (1,2,3,4,5)
        data = numpy.indices(shape, dtype=int).sum(0)
        meta = MetaDict()
        meta.axistags = vigra.defaultAxistags( 'xtycz' )
        meta.shape = shape
        meta.dtype = int
    
        opProvider = OpOutputProvider( data, meta, graph=g )
        assert (opProvider.Output[0:1, 1:2, 0:3, 2:4, 3:5].wait() == data[0:1, 1:2, 0:3, 2:4, 3:5]).all()
        for k,v in meta.items():
            if k != '_ready' and k != '_dirty':
                assert opProvider.Output.meta[k] == v

class TestOpMetadataSelector(object):
    
    def test(self):
        from lazyflow.graph import Graph, MetaDict
        g = Graph()
        
        # Create some data to give    
        shape = (1,2,3,4,5)
        data = numpy.indices(shape, dtype=int).sum(0)
        meta = MetaDict()
        meta.axistags = vigra.defaultAxistags( 'xtycz' )
        meta.shape = shape
        meta.dtype = int
    
        opProvider = OpOutputProvider( data, meta, graph=g )
        
        op = OpMetadataSelector(graph=g)
        op.Input.connect( opProvider.Output )
        
        op.MetadataKey.setValue('shape')    
        assert op.Output.value == shape
        
        op.MetadataKey.setValue('axistags')
        assert op.Output.value == meta.axistags

class TestOpMetadataMerge(object):
    
    def test(self):
        from lazyflow.graph import Graph, MetaDict
        from lazyflow.operators import OpArrayPiper
        graph = Graph()
        opDataSource = OpArrayPiper(graph=graph)
        opDataSource.Input.setValue( numpy.ndarray((9,10), dtype=numpy.uint8) )
        
        # Create some metadata    
        shape = (1,2,3,4,5)
        data = numpy.indices(shape, dtype=int).sum(0)
        meta = MetaDict()
        meta.specialdata = "Salutations"
        meta.notsospecial = "Hey"
    
        opProvider = OpOutputProvider( data, meta, graph=graph )
        
        op = OpMetadataMerge(graph=graph)
        op.Input.connect( opDataSource.Output )
        op.MetadataSource.connect( opProvider.Output )
        op.FieldsToClone.setValue( ['specialdata'] )
        
        assert op.Output.ready()
        assert op.Output.meta.shape == opDataSource.Output.meta.shape
        assert op.Output.meta.dtype == opDataSource.Output.meta.dtype
        assert op.Output.meta.specialdata == meta.specialdata
        assert op.Output.meta.notsospecial is None

class TestOpValueCache(object):
    
    class OpSlowComputation(lazyflow.graph.Operator):
        Input = lazyflow.graph.InputSlot()
        Output = lazyflow.graph.OutputSlot()

        def __init__(self, *args, **kwargs):
            super(TestOpValueCache.OpSlowComputation, self).__init__(*args, **kwargs)
            self.executionCount = 0
        
        def setupOutputs(self):
            self.Output.meta.assignFrom(self.Input.meta)
        
        def execute(self, slot, subindex, roi, result):
            self.executionCount += 1
            time.sleep(2)
            result[...] = self.Input.value
        
        def propagateDirty(self, inputSlot, subindex, roi):
            self.Output.setDirty(roi)
    
    def test_basic(self):
        graph = lazyflow.graph.Graph()
        op = OpValueCache(graph=graph)
        assert not op._dirty
        op.Input.setValue('Hello')
        assert op._dirty
        assert op.Output.value == 'Hello'

        outputDirtyCount = [0]
        def handleOutputDirty(slot, roi):
            outputDirtyCount[0] += 1
        op.Output.notifyDirty(handleOutputDirty)
        
        op.forceValue('Goodbye')
        # The cache itself isn't dirty (won't ask input for value)
        assert not op._dirty
        assert op.Output.value == 'Goodbye'
        
        # But the cache notified downstream slots that his value changed
        assert outputDirtyCount[0] == 1

    def test_multithread(self):
        graph = lazyflow.graph.Graph()
        opCompute = TestOpValueCache.OpSlowComputation(graph=graph)
        opCache = OpValueCache(graph=graph)

        opCompute.Input.setValue(100)
        opCache.Input.connect(opCompute.Output)

        def checkOutput():
            assert opCache.Output.value == 100

        threads = []
        for i in range(100):
            threads.append( threading.Thread(target=checkOutput) )
        
        for t in threads:
            t.start()
            
        for t in threads:
            t.join()

        assert opCompute.executionCount == 1
        assert opCache._dirty == False
        assert opCache._request is None
        assert opCache.Output.value == 100

#if __name__ == "__main__":
#    import logging
#    traceLogger = logging.getLogger("TRACE.lazyflow.operators.valueProviders.OpValueCache")
#    traceLogger.setLevel(logging.DEBUG)
#    handler = logging.StreamHandler()
#    handler.setLevel(logging.DEBUG)
#    traceLogger.addHandler(handler)

#    import nose
#    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})

if __name__ == "__main__":
    import sys
    import nose
    #sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
