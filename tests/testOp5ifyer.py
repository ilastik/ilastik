import unittest
import random
import vigra
import numpy
from lazyflow.graph import Graph
from volumina.adaptors import Op5ifyer
from lazyflow.roi import TinyVector

class TestOp5ifyer(unittest.TestCase):
    
    def setUp(self):
        self.array = None
        self.axis = list('txyzc')
        self.tests = 20
        graph = Graph()
        self.operator = Op5ifyer(graph)
        
    def prepareVolnOp(self):
        tags = random.sample(self.axis,random.randint(2,len(self.axis)))
        tagStr = ''
        for s in tags:
            tagStr += s
        axisTags = vigra.defaultAxistags(tagStr)
        
        self.shape = []
        for tag in axisTags:
            self.shape.append(random.randint(20,30))
        
        self.array = (numpy.random.rand(*tuple(self.shape))*255)
        self.array =  (float(250)/255*self.array + 5).astype(int)
        self.inArray = vigra.VigraArray(self.array,axistags = axisTags)
        self.operator.inputs["input"].setValue(self.inArray)
    
    def test_Full(self):
        for i in range(self.tests):
            self.prepareVolnOp()
            result = self.operator.outputs["output"]().wait()
            if len(result.shape) == 5 and numpy.all(result == self.array):
                assert 1==1
            
    def test_Roi(self):
        for i in range(self.tests):
            self.prepareVolnOp()
            shape = self.operator.outputs["output"].shape
            roi = [None,None]
            roi[1]=[numpy.random.randint(2,s) if s != 1 else 1 for s in shape]
            roi[0]=[numpy.random.randint(0,roi[1][i]) if s != 1 else 0 for i,s in enumerate(shape)]
            roi[0]=TinyVector(roi[0])
            roi[1]=TinyVector(roi[1])
            result = self.operator.outputs["output"](roi[0],roi[1]).wait()
            if len(result.shape) == 5 and numpy.all(result == self.array):
                assert 1==1