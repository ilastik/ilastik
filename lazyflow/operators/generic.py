from lazyflow.graph import *
from lazyflow import roi 


def axisTagObjectFromFlag(flag):
    
    if flag in ['x','y','z']:
        type=vigra.AxisType.Space
    elif flag=='c':
        type=vigra.AxisType.Space
    else:
        raise
    
    return vigra.AxisTags(vigra.AxisInfo(flag,type)) 


class OpMultiArraySlicer(Operator):
    inputSlots = [InputSlot("Input"),InputSlot('AxisFlag')]
    outputSlots = [MultiOutputSlot("Slices",level=1)]

    name = "Multi Array Slicer"
    category = "Misc"
    
    def notifyConnectAll(self):
        
        dtype=self.inputs["Input"].dtype
        flag=self.inputs["AxisFlag"].value
        
        indexAxis=self.inputs["Input"].axistags.index(flag)
        outshape=list(self.inputs["Input"].shape)
        n=outshape.pop(indexAxis)
        outshape=tuple(outshape)
        
        outaxistags=copy.copy(self.inputs["Input"].axistags) 
        
        del outaxistags[flag]
    
        self.outputs["Slices"].resize(n)
        
        for o in self.outputs["Slices"]:
            o._dtype=dtype
            o._axistags=copy.copy(outaxistags)
            o._shape=outshape 
        
            
    def getSubOutSlot(self, slots, indexes, key, result):
        start,stop=roi.sliceToRoi(key,self.outputs["Slices"][indexes[0]].shape)
        
        
        oldstart,oldstop=start,stop
        
        start=list(start)
        stop=list(stop)
        
        flag=self.inputs["AxisFlag"].value
        indexAxis=self.inputs["Input"].axistags.index(flag)
        
        start.insert(indexAxis,indexes[0])
        stop.insert(indexAxis,indexes[0])
        
        #print "WHAT ATTATATTATATTATA ", start,stop,oldstart,oldstop
        
        newKey=roi.roiToSlice(numpy.array(start),numpy.array(stop))
        
        
        
        writeKey=roi.roiToSlice(oldstart,oldstop)
        writeKey=list(writeKey)
        writeKey.insert(indexAxis,0)
        writeKey=tuple(writeKey)
        
        ttt = self.inputs["Input"][newKey].allocate().wait()
        
        
        result[:]=ttt[writeKey ]#+ (0,)]







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
                
        self.outputs["Output"]._shape = outShape
        self.outputs["Output"]._axistags = self.inputs["Input"].axistags
        self.outputs["Output"]._dtype = self.inputs["Input"].dtype

    def getOutSlot(self, slot, key, resultArea):
        start = self.inputs["Start"].value
        stop = self.inputs["Stop"].value
        temp = tuple(numpy.array(stop) - numpy.array(start))
        
        readStart, readStop = sliceToRoi(key)
        
        newKey = ()
        i = 0
        i2 = 0
        for e in temp:
            if e > 0:
                newKey += (slice(start[i2] + readStart[i], start[i2] + readStop[i],None),)
                i +=1
            else:
                newKey += (slice(start[i2], start[i2], None),)
            i2 += 1
            
        res = self.inputs["Input"][newKey].allocate().wait()
        
        resultArea[:] = res.squeeze()[:]
        
        