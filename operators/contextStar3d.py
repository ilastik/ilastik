import numpy
from lazyflow.graph import *

#from lazyflow import operators
from lazyflow.roi import sliceToRoi, roiToSlice, block_view
import copy
import context

class OpContextStar3D(Operator):
    name = "ContextStar3D"
    description = ""
       
    inputSlots = [InputSlot("PMaps"),InputSlot("Radii_triplets"),InputSlot("ClassesCount")]
    outputSlots = [OutputSlot("Output")]    
    
    def notifyConnectAll(self):
        
        nclasses=self.inputs["ClassesCount"].value
        radii_triplets = self.inputs["Radii_triplets"].value
        
        
        self.outputs["Output"]._dtype = self.inputs["PMaps"].dtype
        
        #assert len(self.inputs["PMaps"].shape) == 3 , "not implemented for 3D"
        
        print self.inputs["PMaps"].shape
        h,w,z,c=self.inputs["PMaps"].shape
        
        #self.outputs["Output"]._shape = (h,w,z,nclasses*len(radii_x)*len(radii_y)*len(radii_z)*26)
        self.outputs["Output"]._shape = (h,w,z,nclasses*radii_triplets.shape[0]*26)
        self.outputs["Output"]._axistags = copy.copy(self.inputs["PMaps"].axistags)

    def getOutSlot(self, slot, key, result):
        #FIXME: shouldn't we only request the roi+context here?
        pmaps = self.inputs["PMaps"][:].allocate().wait()
        
        radii_triplets = self.inputs["Radii_triplets"].value

        print "We are in the business"
        #print radii, radii.dtype
        context.starContext3Dnew(radii_triplets,pmaps,result)