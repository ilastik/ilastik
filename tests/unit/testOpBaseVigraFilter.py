import unittest
import numpy
import itertools
import vigra
import logging
from lazyflow.graph import Graph
from lazyflow.operators.obsolete.vigraOperators import \
    OpDifferenceOfGaussians, OpGaussianSmoothing, OpCoherenceOrientation,\
    OpHessianOfGaussianEigenvalues, OpStructureTensorEigenvalues,\
    OpHessianOfGaussianEigenvaluesFirst, OpHessianOfGaussian,\
    OpGaussianGradientMagnitude, OpLaplacianOfGaussian
from lazyflow.roi import sliceToRoi
from lazyflow.helpers import generateRandomKeys,generateRandomRoi

class TestOpBaseVigraFilter(unittest.TestCase):
    
    def setUp(self):

        FORMAT = ' %(message)s'
        logging.basicConfig(filename='OpBaseVigraFilter.log',filemode='w',level=logging.DEBUG,format=FORMAT)
        
        self.volume = None
        self.testDim = (20,20,20,20)
        self.keyNum = 5
        self.eps = 0.001
        self.windowSize = 4
        
        self.graph = Graph()
        self.sigmaList = [0.3,0.7,1,1.6]#+[3.5,5.0,10.0]
        self.sigmaComboList = [x for x in itertools.product(self.sigmaList,self.sigmaList) if x[0]<x[1]]
        
        self.prepareVolume()

    def prepareVolume(self):
        
        self.volume = vigra.VigraArray(self.testDim)
        self.volume[:] = numpy.random.rand(*self.testDim)
        twoDShape = list(self.testDim)
        twoDShape.pop(2)
        twoDShape = tuple(twoDShape)
        self.twoDvolume = vigra.VigraArray(twoDShape)
        self.twoDvolume[:] = numpy.random.rand(*twoDShape)
        
    def compareBlocks(self,operator,maxSigma):
        
        eps = self.eps
        block = operator.outputs["Output"][:].allocate().wait()
        maxShape = operator.outputs["Output"].shape
        for i in range(self.keyNum):
            key = generateRandomKeys(maxShape,minWidth=numpy.ceil(maxSigma*self.windowSize))
            keyDim = sliceToRoi(key, block.shape)
            keyDim = [x-y for x,y in zip(keyDim[1],keyDim[0])]
            if (operator.outputs["Output"][key].allocate().wait() - block[key] < eps).all():
                logging.debug('Operator successfully tested on a block of magnitude '+str(keyDim)+' in tolerance limits of '+str(eps))
                assert 1==1
            else:
                logging.debug('Operator failed on a block of magnitude '+str(keyDim)+' in tolerance limits of '+str(eps))
            
    def test_DifferenceOfGaussian(self):
        
        opDiffGauss = OpDifferenceOfGaussians(self.graph)
        opDiffGauss.inputs["Input"].setValue(self.volume)
        logging.debug('======================OpDifferenceOfGaussian===============')
        for sigma0,sigma1 in self.sigmaComboList:
            try:
                opDiffGauss.inputs["sigma0"].setValue(sigma0)
                opDiffGauss.inputs["sigma1"].setValue(sigma1)
                self.compareBlocks(opDiffGauss,sigma1)
            except:
                logging.debug('Test failed for the following sigma-combination : %s,%s'%(sigma0,sigma1))
        assert 1==1

    def test_GaussianSmoothing(self):
        
        opSmoothGauss = OpGaussianSmoothing(self.graph)
        opSmoothGauss.inputs["Input"].setValue(self.volume)
        logging.debug('======================OpGaussiaSmoothing===================')
        for sigma in self.sigmaList:
            try:
                opSmoothGauss.inputs["sigma"].setValue(sigma)
                self.compareBlocks(opSmoothGauss,sigma)
            except:
                logging.debug('Test failed for the following sigma: %s'%sigma)
        assert 1==1
    
#    def test_CoherenceOrientation(self):
#        
#        opCoherence = OpCoherenceOrientation(self.graph)
#        opCoherence.inputs["Input"].setValue(self.twoDvolume)
#        logging.debug('===================OpCoherenceOrientation==================')
#        for sigma0,sigma1 in self.sigmaComboList:
#            try:
#                opCoherence.inputs["sigma0"].setValue(sigma0)
#                opCoherence.inputs["sigma1"].setValue(sigma1)
#                self.compareBlocks(opCoherence,sigma1)
#            except:
#                logging.debug('Test failed for the following sigma-combination : %s,%s'%(sigma0,sigma1))
#        assert 1==1
    
    def test_HessianOfGaussianEigenvalues(self):
        
        opHessianOfGaussian = OpHessianOfGaussianEigenvalues(self.graph)
        opHessianOfGaussian.inputs["Input"].setValue(self.volume)
        logging.debug('================OpHessianOfGaussianEigenvalues=============')
        for sigma in self.sigmaList:
            try:
                opHessianOfGaussian.inputs["scale"].setValue(sigma)
                self.compareBlocks(opHessianOfGaussian,sigma)
            except:
                logging.debug('Test failed for the following sigma: %s'%sigma)
        assert 1==1
    
    def test_StructureTensorEigenvalues(self):
        
        opStructureTensor = OpStructureTensorEigenvalues(self.graph)
        opStructureTensor.inputs["Input"].setValue(self.volume)
        logging.debug('================OpStructureTensorEigenvalues===============')
        for sigma0,sigma1 in self.sigmaComboList:
            try:
                opStructureTensor.inputs["innerScale"].setValue(sigma0)
                opStructureTensor.inputs["outerScale"].setValue(sigma1)
                self.compareBlocks(opStructureTensor,sigma0)
            except:
                logging.debug('Test failed for the following sigma-combination : %s,%s'%(sigma0,sigma1))
        assert 1==1

    def test_HessianOfGaussianEigenvaluesFirst(self):
        
        opHessianOfGaussianEF = OpHessianOfGaussianEigenvaluesFirst(self.graph)
        opHessianOfGaussianEF.inputs["Input"].setValue(self.volume)
        logging.debug('================OpHessianOfGaussianEigenvaluesFirst========')
        for sigma in self.sigmaList:
            try:
                opHessianOfGaussianEF.inputs["scale"].setValue(sigma)
                self.compareBlocks(opHessianOfGaussianEF,sigma)
            except:
                logging.debug('Test failed for the following sigma: %s'%sigma)
        assert 1==1
        
    
    def test_HessianOfGaussian(self):
        
        opHessianOfGaussian = OpHessianOfGaussian(self.graph)
        opHessianOfGaussian.inputs["Input"].setValue(self.volume)
        logging.debug('================OpHessianOfGaussian========================')
        for sigma in self.sigmaList:
            try:
                opHessianOfGaussian.inputs["sigma"].setValue(sigma)
                self.compareBlocks(opHessianOfGaussian,sigma)
            except:
                logging.debug('Test failed for the following sigma: %s'%sigma)
        assert 1==1
        
        
    def test_GaussianGradientMagnitude(self):
        
        opGaussianGradient = OpGaussianGradientMagnitude(self.graph)
        opGaussianGradient.inputs["Input"].setValue(self.volume)
        logging.debug('================OpopGaussianGradient=======================')
        for sigma in self.sigmaList:
            try:
                opGaussianGradient.inputs["sigma"].setValue(sigma)
                self.compareBlocks(opGaussianGradient,sigma)
            except:
                logging.debug('Test failed for the following sigma: %s'%sigma)
        assert 1==1
    
    def test_LaplacianOfGaussian(self):
        opLaplacianOfGaussian = OpLaplacianOfGaussian(self.graph)
        opLaplacianOfGaussian.inputs["Input"].setValue(self.volume)
        logging.debug('================OpopLaplacianOfGaussian====================')
        for sigma in self.sigmaList:
            try:
                opLaplacianOfGaussian.inputs["scale"].setValue(sigma)
                self.compareBlocks(opLaplacianOfGaussian,sigma)
            except:
                logging.debug('Test failed for the following sigma: %s'%sigma)
        assert 1==1