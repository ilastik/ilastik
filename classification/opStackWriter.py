from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.obsolete.vigraOperators import *
import vigra


class OpStackWriter(Operator):
    name = "PNG Stack Writer"
    
    inputSlots = [InputSlot("Filepath", stype = "string"), InputSlot("Filetype", stype = "string"), InputSlot("input")]
    outputSlots = [OutputSlot("WritePNGStack")]
    
    def setupOutputs(self):
        self.outputs["WritePNGStack"]._shape = self.inputs['input'].shape
        self.outputs["WritePNGStack"]._dtype = object
    
    def execute(self,slot,roi,result):
        print "OpStackWirter.roi", roi
        image = self.inputs["input"][roi.toSlice()].allocate().wait()
        print '  image has shape', image.shape
        filepath = self.inputs["Filepath"].value
        filetype = self.inputs["Filetype"].value

        for i in range(image.shape[3]):
            vigra.impex.writeImage(image[0,:,:,i,0],filepath+"_%04d." % (i)+filetype)