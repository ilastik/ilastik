from unittest import TestCase
import vigra,numpy
from lazyflow.graph import Graph,Operator,InputSlot,OutputSlot
from lazyflow.operators import OpArrayPiper
from lazyflow.helpers import generateRandomRoi

class OpRoiTest(Operator):
    
    inputSlots = [InputSlot("input")]
    outputSlots = [OutputSlot("output")]
    
    def setupOutputs(self):
        
        self.outputs["output"]._dtype = self.inputs["input"]._dtype
        self.outputs["output"]._shape = self.inputs["input"]._shape
        self.outputs["output"]._axistags = self.inputs["input"]._axistags
        
    def execute(self,slot,roi,result):
        
        tmpRes = self.inputs["input"](start=roi.start,stop=roi.stop).wait()
        result[:] = tmpRes
        return result

class TestRoiInterdace(TestCase):
    
    def setUp(self):
        self.testVol = vigra.VigraArray((200,200,200))
        self.testVol[:] = numpy.random.rand(200,200,200)
        self.graph = Graph()
        self.op = OpArrayPiper(self.graph)
        self.op.inputs["Input"].setValue(self.testVol)
        self.roiOp = OpRoiTest(self.graph)
        self.roiOp.inputs["input"].setValue(self.testVol)
        
    def test_roi(self):
        
        for i in range(20):
            roi = generateRandomRoi((200,200,200))
            result=self.op.outputs["Output"](start=roi[0], stop=roi[1]).wait()
    
    def test_RoiOp(self):
        
        for i in range(20):
            roi = generateRandomRoi((200,200,200))
            result=self.roiOp.outputs["output"](start=roi[0], stop=roi[1]).wait()
