from lazyflow.graph import *
import context


class OpVarianceContext2D(Operator):
    name = "VarianceContext2D"
    description = "Compute averages and variances in the neighborhoods of different sizes"
       
    inputSlots = [InputSlot("PMaps"),InputSlot("Radii"),InputSlot("ClassesCount")]
    outputSlots = [OutputSlot("Output")]    
    
    def notifyConnectAll(self):
        #print
        #print "********************************************************************* calling notifyConnectAll",self.inputs["PMaps"].shape
        #print
        nclasses=self.inputs["ClassesCount"].value
        radii=self.inputs["Radii"].value
        
        self.outputs["Output"]._dtype = self.inputs["PMaps"].dtype
        
        assert len(self.inputs["PMaps"].shape) == 3 , "not implemented for 3D"
        
        h,w,c=self.inputs["PMaps"].shape
        
        self.outputs["Output"]._shape = (h,w,2*nclasses*len(radii))
        
        self.outputs["Output"]._axistags = copy.copy(self.inputs["PMaps"].axistags)

    def getOutSlot(self, slot, key, result):
        pmaps = self.inputs["PMaps"][:].allocate().wait()
        
        radii=self.inputs["Radii"].value
        
        radii=numpy.array(radii,dtype=numpy.uint32)
        print "We are in the business"
        print radii, radii.dtype
        context.varContext2Dmulti(radii,pmaps,result)