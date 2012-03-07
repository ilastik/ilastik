from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.obsolete.vigraOperators import *
import vigra


class OpStackWriter(Operator):
    name = "Stack File Writer"
    category = "Output"
    
    inputSlots = [InputSlot("filepath", stype = "string"), \
                  InputSlot("dummy", stype = "list"), \
                  InputSlot("input")]
    outputSlots = [OutputSlot("WritePNGStack")]
    
    def setupOutputs(self):
        assert self.inputs['input'].shape is not None
        self.outputs["WritePNGStack"]._shape = self.inputs['input'].shape
        self.outputs["WritePNGStack"]._dtype = object
    
    def execute(self,slot,roi,result):
        image = self.inputs["input"][roi.toSlice()].allocate().wait()

        filepath = self.inputs["filepath"].value
        filepath = filepath.split(".")
        filetype = filepath[-1]
        filepath = filepath[0:-1]
        filepath = "/".join(filepath)
        dummy = self.inputs["dummy"].value
        
        if "xy" in dummy:
            pass
        if "xz" in dummy:
            pass
        if "xt" in dummy:
            for i in range(image.shape[2]):
                for j in range(image.shape[3]):
                    for k in range(image.shape[4]):
                        vigra.impex.writeImage(image[:,:,i,j,k],filepath+"-xt-y_%04d_z_%04d_c_%04d." % (i,j,k)+filetype)
        if "yz" in dummy:
            for i in range(image.shape[0]):
                for j in range(image.shape[1]):
                    for k in range(image.shape[4]):
                        vigra.impex.writeImage(image[i,j,:,:,k],filepath+"-yz-t_%04d_x_%04d_c_%04d." % (i,j,k)+filetype)
        if "yt" in dummy:
            for i in range(image.shape[1]):
                for j in range(image.shape[3]):
                    for k in range(image.shape[4]):
                        vigra.impex.writeImage(image[:,i,:,j,k],filepath+"-yt-x_%04d_z_%04d_c_%04d." % (i,j,k)+filetype)
        if "zt" in dummy:
            for i in range(image.shape[1]):
                for j in range(image.shape[2]):
                    for k in range(image.shape[4]):
                        vigra.impex.writeImage(image[:,i,j,:,k],filepath+"-zt-x_%04d_y_%04d_c_%04d." % (i,j,k)+filetype)
        
