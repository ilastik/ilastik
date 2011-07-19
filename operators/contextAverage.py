import numpy
from lazyflow.graph import Operators, Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot
from lazyflow.roi import sliceToRoi, roiToSlice, block_view
from Queue import Empty
from collections import deque
import greenlet, threading
import copy
import context

class OpAverageContext2D(Operator):
    name = "AverageContext2D"
    description = ""
       
    inputSlots = [InputSlot("PMaps"),InputSlot("Radii"),InputSlot("ClassesCount")]
    outputSlots = [OutputSlot("Output")]    
    
    def notifyConnectAll(self):
        nclasses=self.inputs["ClassesCount"].value
        radii=self.inputs["Radii"].value
        
        self.outputs["Output"]._dtype = self.inputs["PMaps"].dtype
        
        assert len(self.inputs["PMaps"].shape) == 3 , "not implemented for 3D"
        
        h,w,c=self.inputs["PMaps"].shape
        
        self.outputs["Output"]._shape = (h,w,nclasses*len(radii))
        print "JJJJJJJJJJJJJJJJJJJJJJJJJJJ-------------#################", self.inputs["PMaps"].axistags
        self.outputs["Output"]._axistags = copy.copy(self.inputs["PMaps"].axistags)

    def getOutSlot(self, slot, key, result):
        pmaps = self.inputs["PMaps"][:].allocate().wait()
        
        radii=self.inputs["Radii"].value
        
        radii=numpy.array(radii,dtype=numpy.uint32)
        print "We are in the business"
        print radii, radii.dtype
        context.avContext2Dmulti(radii,pmaps,result)
        