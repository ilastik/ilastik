import numpy
import vigra
import lazyflow
from lazyflow.operators import OpMetadataInjector, OpOutputProvider, OpMetadataSelector

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



if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})
