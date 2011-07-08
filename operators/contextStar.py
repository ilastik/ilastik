import numpy

from lazyflow.graph import Operators, Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot
from lazyflow.roi import sliceToRoi, roiToSlice, block_view
from Queue import Empty
from collections import deque
import greenlet, threading
import copy
import context

class OpStarContext2D(Operator):
    name = "StarContext2D"
    description = ""
       
    inputSlots = [InputSlot("PMaps"),InputSlot("Radii"),InputSlot("ClassesCount")]
    outputSlots = [OutputSlot("Output")]    
    
    def notifyConnectAll(self):
        nclasses=self.inputs["ClassesCount"].value
        radii=self.inputs["Radii"].value
        
        self.outputs["Output"]._dtype = self.inputs["PMaps"].dtype
        
        assert len(self.inputs["PMaps"].shape) == 3 , "not implemented for 3D"
        
        h,w,c=self.inputs["PMaps"].shape
        
        self.outputs["Output"]._shape = (h,w,8*2*nclasses*len(radii))
        
        
        self.outputs["Output"]._axistags = copy.copy(self.inputs["PMaps"].axistags)

    def getOutSlot(self, slot, key, result):
        pmaps = self.inputs["PMaps"][:].allocate().wait()
        
        radii=self.inputs["Radii"].value
        
        radii=numpy.array(radii,dtype=numpy.uint32)
        print "We are in the business"
        print radii, radii.dtype
        context.starContext2Dmulti(radii,pmaps,result)
        
        
