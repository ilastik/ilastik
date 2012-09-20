from lazyflow.operators.imgFilterOperators import OpPixelFeaturesPresmoothed
from lazyflow.graph import Graph
from unittest import TestCase
import numpy,random

class testOpPixelFeaturesPreesmoothed(TestCase):
    
    def setUp(self):
        self.shape = (10,)*5
        self.testVol = numpy.random.rand(*self.shape)
        self.graph = Graph()
        self.operator = OpPixelFeaturesPresmoothed(graph=self.graph)
        self.matrix = None
        self.scales = None
        
    def calcChannelDimFeatureArray(self,matrix):
        operatorList = self.operator.operatorList
        print matrix
    
    def setupMatrixAndScales(self):
        self.scales = [1.5,2.0,2.5]
        self.matrix = [[bool(random.getrandbits(1)) for i in range(len(self.scales))] for j in range(6)]
        self.operator.inputs["Matrix"].setValue(self.matrix)
        self.operator.inputs["Scales"].setValue(self.scales)
        
    def test2Dimensions(self):
        for i in range(self.shape[1]/2):
            twoDimVol = self.testVol[0,i,:,:,:]
            self.setupMatrixAndScales()
            self.operator.inputs["Input"].setValue(twoDimVol)
            self.operator.outputs["Output"]().wait()
            
    def test3Dimensions(self):
        for i in range(self.shape[0]/2):
            threeDimVol = self.testVol[i,:,:,:,:]
            self.setupMatrixAndScales()
            self.operator.inputs["Input"].setValue(threeDimVol)
            self.operator.outputs["Output"]().wait()
                
    def test4Dimension(self):
        fourDimVol = self.testVol
        for i in range(0,6):
            self.setupMatrixAndScales()
            self.operator.inputs["Input"].setValue(fourDimVol)
            self.operator.outputs["Output"]().wait()