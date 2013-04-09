import numpy
import vigra
from lazyflow.graph import Graph
from lazyflow.operators import OpVigraLabelVolume
from lazyflow.utility.slicingtools import sl, slicing2shape

class TestOpVigraLabelVolume(object):

    def setUp(self):
        graph = Graph()
        
        inputData = numpy.random.random( (1,10,100,100,1) )
        inputData = ( inputData < 0.1 ).astype(numpy.uint8)
        inputData = inputData.view(vigra.VigraArray)
        inputData.axistags = vigra.defaultAxistags('txyzc')
        self.inputData = inputData

        self.op = OpVigraLabelVolume(graph=graph)
        self.op.Input.setValue( inputData )

    def testBasic(self):
        labeled = self.op.Output[...].wait()
        assert labeled.shape == self.inputData.shape

    def testBasicWithBackground(self):
        self.op.BackgroundValue.setValue(0)
        labeled = self.op.Output[...].wait()
        assert labeled.shape == self.inputData.shape


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
