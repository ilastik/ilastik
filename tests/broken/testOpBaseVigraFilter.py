import unittest
import itertools
import vigra
from lazyflow.graph import Graph
from lazyflow.operators.imgFilterOperators import OpGaussianSmoothing,\
     OpLaplacianOfGaussian, OpStructureTensorEigenvalues,\
     OpHessianOfGaussianEigenvalues, OpGaussianGradientMagnitude,\
     OpDifferenceOfGaussians, OpHessianOfGaussian

class TestOpBaseVigraFilter(unittest.TestCase):

    def setUp(self):

        self.testDimensions = ['xyzc','xyc','txyc','txyzc']
        self.graph = Graph()

    def generalOperatorTest(self,operator,sigma1,sigma2=None):
        for dim in self.testDimensions:
            testArray = vigra.VigraArray((10,)*len(dim),axistags=vigra.VigraArray.defaultAxistags(dim))
            operator.inputs["Input"].setValue(testArray)
            operator.inputs["Sigma"].setValue(sigma1)
            if sigma2 is not None:
                operator.inputs["Sigma2"].setValue(sigma2)
            for i,j in [(i,j) for i,j in itertools.permutations(range(0,10),2) if i<j]:
                start = [i]*len(dim)
                stop = [j]*len(dim)
                operator.outputs["Output"](start,stop).wait()
    
    def test_GaussianSmoothing(self):
        opGaussianSmoothing = OpGaussianSmoothing(graph=self.graph)
        self.generalOperatorTest(opGaussianSmoothing, 2.0)
    
    def test_DifferenceOfGaussians(self):
        opDifferenceOfGaussians = OpDifferenceOfGaussians(graph=self.graph)
        self.generalOperatorTest(opDifferenceOfGaussians, 2.0, 3.0)
    
    def test_LaplacianOfGaussian(self):
        opLaplacianOfGaussian = OpLaplacianOfGaussian(graph=self.graph)
        self.generalOperatorTest(opLaplacianOfGaussian, 2.0)
        
    def test_StructureTensorEigenvalues(self):
        opStructureTensorEigenvalues = OpStructureTensorEigenvalues(graph=self.graph)
        self.generalOperatorTest(opStructureTensorEigenvalues, 1.5,2.0)
        
    def test_GaussianGradientMagnitude(self):
        opGaussianGradientMagnitude = OpGaussianGradientMagnitude(graph=self.graph)
        self.generalOperatorTest(opGaussianGradientMagnitude, 2.0)
        
    def test_HessianOfGaussian(self):
        opHessianOfGaussian = OpHessianOfGaussian(graph=self.graph)
        self.generalOperatorTest(opHessianOfGaussian, 2.0)

    def test_HessianOfGaussianEigenvalues(self):
        opHessianOfGaussianEigenvalues = OpHessianOfGaussianEigenvalues(graph=self.graph)
        self.generalOperatorTest(opHessianOfGaussianEigenvalues,2.0)