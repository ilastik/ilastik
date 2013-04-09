from lazyflow.operators.imgFilterOperators import OpGaussianSmoothing
import vigra
import numpy
from lazyflow.graph import Graph
from numpy.testing import assert_array_almost_equal

class TestAnisotropicVigraFeatures():

    def setUp(self):
        self.delta = numpy.zeros((19, 19, 19, 1), dtype=numpy.float32)
        self.delta[9, 9, 9, 0]=1
        self.delta = self.delta.view(vigra.VigraArray)
        self.delta.axistags = vigra.defaultAxistags(4)
        
        self.dataShape = ((100, 100, 100, 1))
        self.randomData = (numpy.random.random(self.dataShape) * 100).astype(int)
        self.randomData = self.randomData.view(vigra.VigraArray)
        self.randomData.axistags = vigra.defaultAxistags(4)
        
        self.anisotropicSigmas = [(3, 3, 1), (1.6, 1.6, 1)]
        self.isotropicSigmasTuple = [(3, 3, 3), (1, 1, 1)]
        self.isotropicSigmas = [3, 1]
        
        
    def testGaussianSmoothing(self):
        graph = Graph()
        oper = OpGaussianSmoothing(graph=graph)
        oper.Input.setValue(self.delta)
        for sigma in self.anisotropicSigmas:
            oper.Sigma.setValue(sigma)
            desired = vigra.filters.gaussianSmoothing(self.delta, sigma)
            result = oper.Output[:].wait()
            assert_array_almost_equal(numpy.asarray(desired), numpy.asarray(result), 2)
            
        for isigma, sigma in enumerate(self.isotropicSigmasTuple):
            oper.Sigma.setValue(sigma)
            result = oper.Output[:].wait()
            oper.Sigma.setValue(self.isotropicSigmas[isigma])
            result2 = oper.Output[:].wait()
            assert_array_almost_equal(numpy.asarray(result), numpy.asarray(result2), 2)
            
            desired = vigra.filters.gaussianSmoothing(self.delta, sigma)
            assert_array_almost_equal(numpy.asarray(desired), numpy.asarray(result), 2)

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
