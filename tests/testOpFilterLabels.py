import numpy
import vigra
from lazyflow.graph import Graph
from lazyflow.operators import OpFilterLabels
from lazyflow.utility.slicingtools import sl, slicing2shape

class TestOpFilterLabels(object):

    def setUp(self):

        inputData = numpy.zeros((1,10,100,100,1), dtype=int)
        inputData = inputData.view(vigra.VigraArray)
        inputData.axistags = vigra.defaultAxistags('txyzc')
        
        inputData[0,0, 50:53, 50:53, 0] = 1 # 9 voxels
        inputData[0,1, 50:52, 50:52, 0] = 2 # 4 voxels
        inputData[0,2, 50:52, 50:53, 0] = 3 # 6 voxels
        
        self.inputData = inputData

    def testBasic(self):
        graph = Graph()
        op = OpFilterLabels(graph=graph)
        op.Input.setValue( self.inputData )
        op.MinLabelSize.setValue(6)

        filtered = op.Output[...].wait()
        assert filtered.shape == self.inputData.shape
        
        expectedData = numpy.array(self.inputData)
        expectedData[0,1, 50:52, 50:52, 0] = 0 # 4 voxels, should be gone
        
        assert (filtered == expectedData).all()
        
        op.MaxLabelSize.setValue(8)
        expectedData[0, 0, 50:53, 50:53, 0] = 0
        filtered2 = op.Output[:].wait()
        assert (filtered2 == expectedData).all()


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
