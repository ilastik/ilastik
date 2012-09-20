import numpy
from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators import OpArrayPiper, OpMultiInputConcatenater

class TestMultiInputConcatenater(object):
    def test(self):
        g = Graph()
        
        array1 = numpy.zeros((1,1), dtype=float)
        array2 = numpy.ones((2,2), dtype=float)
        array3 = numpy.zeros((3,3), dtype=float)
        
        array4 = numpy.zeros((4,4), dtype=float)
        array5 = numpy.zeros((5,5), dtype=float)
        array6 = numpy.zeros((6,6), dtype=float)
        
        array2[0,0] = 0.123
        array6[0,0] = 0.456
        
        opIn0Provider = OperatorWrapper( OpArrayPiper, graph=g )
        
        # We will provide 2 lists to concatenate
        # The first is provided by a separate operator which we set up in advance
        opIn0Provider.Input.resize(3)
        opIn0Provider.Input[0].setValue( array1 )
        opIn0Provider.Input[1].setValue( array2 )
        opIn0Provider.Input[2].setValue( array3 )
        
        op = OpMultiInputConcatenater(graph=g)
        op.Inputs.resize(2) # Two lists to concatenate
        
        # Connect the first list
        op.Inputs[0].connect( opIn0Provider.Output )
        
        # Set up the second list directly via setValue() (no external operator)
        op.Inputs[1].resize(3)
        op.Inputs[1][0].setValue( array4 )
        op.Inputs[1][1].setValue( array5 )
        op.Inputs[1][2].setValue( array6 )
        
        print op.Inputs[0][0].meta
        print op.Inputs[0][1].meta
        print op.Inputs[0][2].meta
        print op.Output[0].meta
        print op.Output[1].meta
        print op.Output[2].meta
        
        assert len(op.Output) == 6
        assert op.Output[0].meta.shape == array1.shape
        assert op.Output[5].meta.shape == array6.shape
        
        assert numpy.all(op.Output[1][...].wait() == array2[...])
        assert numpy.all(op.Output[5][...].wait() == array6[...])
        
        op.Inputs[0].removeSlot(1, 2)
        
        print len(op.Output)
        assert len(op.Output) == 5
        assert op.Output[0].meta.shape == array1.shape
        assert op.Output[4].meta.shape == array6.shape
        
        assert numpy.all(op.Output[1][...].wait() == array3[...])
        assert numpy.all(op.Output[4][...].wait() == array6[...])

if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})
