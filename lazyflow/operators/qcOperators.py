from lazyflow.graph import *
from lazyflow import roi 


class OpLabelToImage(Operator):
    name = "OpLabelToImage"
    description = "Transforms a label array to an Image "
 
    inputSlots = [InputSlot("Input"), InputSlot("PatchWidth")]
    outputSlots = [OutputSlot("Output")]    

    def notifyConnectAll(self):

        inputSlot = self.inputs["Input"]
        self.patchWidth = self.inputs["PatchWidth"].value        
        shape =  self.inputs["Input"].shape      
        
        self.outputs["Output"]._dtype = inputSlot.dtype
        self.outputs["Output"]._shape = tuple(numpy.array(shape) * self.patchWidth) 
        self.outputs["Output"]._axistags = inputSlot.axistags

        assert self.patchWidth > 0, "OpLabelToImage: input'PatchWidth' must be positive number !"
 
    def getOutSlot(self, slot, key, result):
        
        inputShape = self.inputs["Input"].shape
        outShape=numpy.array(inputShape) * self.patchWidth         
        
        wstart, wstop = sliceToRoi(key, outShape)      
        
        rstart = wstart/self.patchWidth
        
        rstop = (wstop+self.patchWidth-1)/self.patchWidth

        rkey = roiToSlice(rstart, rstop)
        
        
        labels = self.inputs["Input"][rkey].allocate().wait()
        
        shape=numpy.array(result.shape)
        wsubstart = [0,0]
        wsubstop =  numpy.minimum(self.patchWidth - wstart + self.patchWidth*(wstart/self.patchWidth),wstop-wstart)   
        
        for row in labels:
            for e in row:
                wsubkey = roiToSlice(wsubstart, wsubstop)

                result[wsubkey] = numpy.zeros(tuple(wsubstop-wsubstart)) + e
                wsubstart[1] = wsubstop[1]
                wsubstop[1] = numpy.minimum(wsubstop[1] + self.patchWidth, wstop[1]-wstart[1])

            wsubstart[1] = 0
            wsubstop[1] = numpy.minimum(self.patchWidth - wstart[1] + self.patchWidth*(wstart[1]/self.patchWidth), wstop[1]-wstart[1])
            
            wsubstart[0] = wsubstop[0]
            wsubstop[0] = numpy.minimum(self.patchWidth + wsubstop[0], wstop[0]-wstart[0])

    def notifyDirty(self,slot,key):
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"]._shape
    
    @property
    def dtype(self):
        return self.outputs["Output"]._dtype
        