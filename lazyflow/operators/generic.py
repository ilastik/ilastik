

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
        assert self.inputs["Input"].shape[-1]>index, "Requested channel out of Range"       
        newKey = key[:-1]
        newKey += (slice(0,self.inputs["Input"].shape[-1],None),)        
        
        
        im=self.inputs["Input"][newKey].allocate().wait()
        
        
        result=im[...,index]
        
        
        
class OpSubRegion(Operator):
    name = "OpSubRegion"
    description = "Select a region of interest from an numpy array"
    
    inputSlots = [InputSlot("Input"), InputSlot("Start"), InputSlot("Stop")]
    outputSlots = [OutputSlot("Output")]
    
    def notifyConnectAll(self):
        start = self.inputs["Start"].value
        stop = self.inputs["Stop"].value
        assert isinstance(start, tuple)
        assert isinstance(stop, tuple)
        assert len(start) == len(self.inputs["Input"].shape)
        assert len(start) == len(stop)
        assert (numpy.array(stop)>= numpy.array(start)).all()
        
        temp = tuple(numpy.array(stop) - numpy.array(start))        
        #drop singleton dimensions
        outShape = ()        
        for e in temp:
            if e > 0:
                outShape = outShape + (e,)
                
        self.outputs["Output"].shape = outShape

    def getOutSlot(self, slot, key, resultArea):
        start = self.inputs["Start"].value
        stop = self.inputs["Stop"].value
        temp = tuple(numpy.array(stop) - numpy.array(start))
        
        newKey = ()
        i = 0
        i2 = 0
        for e in temp:
            if e > 0:
                newKey += (key[i],)
                i +=1
            else:
                newKey += (slice(start[i2],start[i2],None))
            i2 += 1
            
        req = self.inputs["Input"][newKey].writeInto(resultArea).wait()
        
        