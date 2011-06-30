

from lazyflow.graph import *


class OpSingleChannelSelector(Operator):
    name = "SingleChannelSelector"
    description = "Select One channel from a Multichannel Image"
    
    inputSlots = [InputSlot("Input"),InputSlot("Index",stype='integer')]
    outputSlots = [OutputSlot("Output")]
    
    def notifyConnectAll(self):
        self.outputs["Output"]._dtype =self.inputs["Input"].dtype 
        self.outputs["Output"]._shape = self.inputs["Input"].shape[:-1]+(1,)
        self.outputs["Output"]._axistags = self.inputs["Input"].axistags
        
        
        
    def getOutSlot(self, slot, key, result):
        
        index=self.inputs["Index"].value
        #FIXME: check the axistags for a multichannel image
        assert self.inputs["Input"].shape[:-1]>index, "Requested channel out of Range"       
        newKey = key[:-1]
        newKey += (slice(0,self.inputs["Input"].shape[-1],None),)        
        
        
        im=self.inputs["Input"][newKey].allocate().wait()
        
        
        result=im[...,index]