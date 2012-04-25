from unittest import TestCase
import vigra,numpy
from lazyflow.graph import Graph
from lazyflow.operators import OpArrayPiper
from lazyflow.helpers import generateRandomRoi
from lazyflow.roi import roiToSlice

class TestRoiInterdaxe(TestCase):
    
    def setUp(self):
        self.testVol = vigra.VigraArray((200,200,200))
        self.testVol[:] = numpy.random.rand(200,200,200)
        self.graph = Graph()
        self.op = OpArrayPiper(self.graph)
        self.op.inputs["Input"].setValue(self.testVol)
        
        
    def test_roi(self):
        
        for i in range(20):
            roi = generateRandomRoi((200,200,200))
            print roi 
            self.op.outputs["Output"](start=roi[0], stop=roi[1]).wait()