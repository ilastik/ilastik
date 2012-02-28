from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.obsolete.vigraOperators import *
import vigra


class OpStackWriter(Operator):
    name = "Stack File Writer"
    category = "Output"
    
    inputSlots = [InputSlot("filepath", stype = "string"), \
                  InputSlot("input")]
    outputSlots = [OutputSlot("WritePNGStack")]
    
    def setupOutputs(self):
        self.outputs["WritePNGStack"]._shape = self.inputs['input'].shape
        self.outputs["WritePNGStack"]._dtype = object
    
    def execute(self,slot,roi,result):
        image = self.inputs["input"][roi.toSlice()].allocate().wait()

        filepath = self.inputs["filepath"].value
        filepath = filepath.split(".")
        filetype = filepath[-1]
        filepath = filepath[0:-1]
        filepath = "/".join(filepath)
        
        for i in range(image.shape[3]):
            vigra.impex.writeImage(image[0,:,:,i,0],filepath+"_%04d." % (i)+filetype)
