import numpy
import vigra
from lazyflow.graph import Graph
from lazyflow.operators.opColorizeLabels import OpColorizeLabels

class TestOpColorizeLabels(object):
    def test(self):
        # Create a label array that's symmetric about the x-y axes
        data = numpy.indices((10,10), dtype=int).sum(0)
    
        assert (data == data.transpose()).all()
    
        data = data.view(vigra.VigraArray)
        data.axistags = vigra.defaultAxistags('xy')
        data = data.withAxes(*'txyzc')
    
        assert data.shape == (1,10,10,1,1)
    
        graph = Graph()
        op = OpColorizeLabels(graph=graph)
        op.Input.setValue(data)
    
        colorizedData = op.Output[...].wait()
        
        # Output is colorized (3 channels)
        assert colorizedData.shape == (1,10,10,1,3)

        # If we transpose x-y, then the data should still be the same,
        # which implies that identical labels got identical colors
        # (i.e. we chose deterministic colors)
        assert (colorizedData == colorizedData.transpose(0,2,1,3,4)).all()

        # Different labels should get different colors
        assert ( colorizedData[0,1,1,0,0] != colorizedData[0,2,2,0,0]
              or colorizedData[0,1,1,0,1] != colorizedData[0,2,2,0,1]
              or colorizedData[0,1,1,0,2] != colorizedData[0,2,2,0,2] )
        
if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
