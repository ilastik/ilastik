import numpy, vigra
import time
from lazyflow.graph import *
import gc
from lazyflow import roi
import copy
import sys

from lazyflow.operators.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper, OpMultiMultiArrayPiper
from tests.mockOperators import ArrayProvider, SingleValueProvider
        
class OpBaseVigraFilter(OpArrayPiper):
    inputSlots = [InputSlot("Input"), InputSlot("Sigma")]
    outputSlots = [OutputSlot("Output")]    
    
    name = "OpBaseVigraFilter"
    vigraFilter = None
    
    def __init__(self, graph):
        OpArrayPiper.__init__(self, graph)
        
    def getOutSlot(self, slot, key, result):
        if self.resultingChannels() > 1:
            key = key[0:-1]
        v = self.inputs["Input"][key].allocate()
        t = v()
        #print self.name, "for shape", t.shape, "and key", key
        req = self.inputs["Sigma"][:].allocate()
        sigma = req()
        #print "tttttttttttttt", sigma, sigma.shape, sigma.dtype
        sigma = float(sigma[0])
        temp = self.vigraFilter(numpy.require(t[:], dtype=numpy.float32), sigma)
        #print "xxxxxxxxxxxxxxxxxxxxxxxxxxx", self.name, key, result.shape
        #print " XXXXXXXXXXXXXXXXXXX ", self.name, temp.axistags
        result[:] = temp
        
    def notifyConnect(self, inputSlot):
        if inputSlot == self.inputs["Input"]:
            self.outputs["Output"]._dtype = inputSlot.dtype
            p = self.inputs["Input"].partner
            self.outputs["Output"]._axistags = copy.copy(inputSlot.axistags)
            
            channels = self.resultingChannels()
            if channels > 1:
                self.outputs["Output"]._shape = inputSlot.shape + (channels,)
                if self.outputs["Output"]._axistags.axisTypeCount(vigra.AxisType.Channels) == 0:
                    self.outputs["Output"]._axistags.insertChannelAxis()
            else:
                self.outputs["Output"]._shape = inputSlot.shape
            
            
                
        elif inputSlot == self.inputs["Sigma"]:
            self.outputs["Output"].setDirty()
            
    def resultingChannels(self):
        raise RuntimeError('resultingChannels() not implemented')
        

class OpGaussianSmooting(OpBaseVigraFilter):
    name = "GaussianSmooting"
    vigraFilter = staticmethod(vigra.filters.gaussianSmoothing)
    
    def notifyConnect(self, inputSlot):
        if inputSlot == self.inputs["Input"]:
            self.numChannels  = inputSlot.axistags.axisTypeCount(vigra.AxisType.Channels)
            self.channelIndex = self.inputs["Input"].axistags.channelIndex
        
        OpBaseVigraFilter.notifyConnect(self, inputSlot)
    
    def getOutSlot(self, slot, key, result):
        numChannels = self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Channels)
        assert numChannels in [0,1]
        
        keys = []
        if numChannels == 0:
            keys.append(key)
        else:
            for i in range(self.inputs["Input"].shape[self.channelIndex]):
                k = list(copy.copy(key))
                k[-1] = slice(i,i+1,None)
                keys.append(tuple(k))
       
        req = self.inputs["Sigma"][:].allocate()
        sigma = req()
        sigma = float(sigma[0])
        
        for i,k in enumerate(keys):
            v = self.inputs["Input"][k].allocate()
            t = v()
            t = numpy.require(t, dtype=numpy.float32)
            t = t.view(vigra.VigraArray)
            t.axistags = self.inputs["Input"].axistags
            
            temp = self.vigraFilter(t, sigma)
            if numChannels == 0:
                result[:] = temp
            else:
                s = [slice(None,None,None) if j != self.channelIndex else slice(i,i+1,None) for j in range(result.ndim)]
                result[s] = temp

    def resultingChannels(self):
        return self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Channels)
    
    
class OpHessianOfGaussianEigenvalues(OpBaseVigraFilter):
    name = "HessianOfGaussianEigenvalues"
    vigraFilter = staticmethod(vigra.filters.hessianOfGaussianEigenvalues)
    
    def resultingChannels(self):
        temp = self.outputs["Output"].axistags.axisTypeCount(vigra.AxisType.Space)
        return temp

class OpMultiArrayStacker(Operator):
    inputSlots = [MultiInputSlot("MultiInput")]
    outputSlots = [OutputSlot("SingleOutput")]
    
    def notifySubConnect(self, slots, indexes):
        #print "  OpMultiArrayStacker.notifyConnect() with", slots, indexes
        self.outputs["SingleOutput"]._dtype = self.inputs["MultiInput"][-1].dtype
        self.outputs["SingleOutput"]._axistags = copy.copy(self.inputs["MultiInput"][-1].axistags)
        if self.outputs["SingleOutput"]._axistags.axisTypeCount(vigra.AxisType.Channels) == 0:
            self.outputs["SingleOutput"]._axistags.insertChannelAxis()
        
        c = 0
        for inSlot in self.inputs["MultiInput"]:
            if inSlot.axistags.axisTypeCount(vigra.AxisType.Channels) == 0:
                c += 1
            else:
                c += inSlot.shape[inSlot.axistags.channelIndex]
        self.outputs["SingleOutput"]._shape = inSlot.shape[:-1] + (c,)    

    
    def getOutSlot(self, slot, key, result):
        cnt = 0
        key = key[:-1]
        for i, inSlot in enumerate(self.inputs['MultiInput']):
            #print "a sadf sadf sadf asdf ", key
            if inSlot.axistags.axisTypeCount(vigra.AxisType.Channels) == 0:
                 
                v = inSlot[key].writeInto(result[..., cnt])
                cnt += 1
            else:
                channels = inSlot.shape[inSlot.axistags.channelIndex]
                #print " 555555555 55555555555555 adding end slicer", result.shape
                key_ = key + (slice(None,None,None),)
                v = inSlot[key_].writeInto(result[...,cnt:cnt+channels])
                cnt += channels
            v()
                 
if __name__ == "__main__":
    shape = (200,200,200)
    numThreads = 1
    axistags = vigra.VigraArray.defaultAxistags(len(shape)+1)
    axistags.dropChannelAxis()
    
    key = [[50,50,50,0],[100,100,100,5]]
    
    g = Graph(numThreads = numThreads)
    
    multislot = OpMultiArrayPiper(g)
    
    numImages = 2
    
    for i in range(numImages):
        shape = list(shape)
        shape[1] += i
        shape = tuple(shape)
        provider = ArrayProvider("Random input", shape=shape, dtype=numpy.float32, axistags=axistags)
        #data = numpy.random.rand(*provider.shape)
        data = numpy.zeros(provider.shape)
        data[:] = i
        data = data.astype(provider.dtype).view(vigra.VigraArray)
        provider.setData(data)
        multislot.inputs["MultiInput"].connectAdd(provider)
    
    featuresInput = OpArrayPiper(g)
    featuresInput.inputs["Input"].connect(multislot.outputs["MultiOutput"])
    sigmaProvider1 = SingleValueProvider("Sigma", float)
    sigmaProvider2 = SingleValueProvider("Sigma", float)
    sigmaProvider1.setValue(1.2)
    sigmaProvider2.setValue(2.2)

    for i in range(numImages):
        print multislot.outputs["MultiOutput"][i][7,7,:].allocate()
    
    islot = featuresInput.inputs["Input"]
    oslot = featuresInput.outputs["Output"]
    for i in range(numImages):
        print "--------"
        print i
        print "--------"
        #p = islot[i].partner
        #print p.name, p.operator, p.shape, p.dtype, p
        #print islot, islot[i]
        #print islot.operator, islot[i].operator
        print featuresInput.outputs["Output"][i][7,7,30:40].allocate()
        #print p[7,7,:].allocate()
        print oslot, oslot.operator, oslot[i], oslot[i].operator


    opa = OpGaussianSmooting(g)
    opb = OpHessianOfGaussianEigenvalues(g)
    opc = OpArrayPiper(g)
    
    print "LLLLLLLLLEVEL",featuresInput.outputs["Output"].level, len(featuresInput.outputs["Output"])
        
        
        
    opa.inputs["Input"].connect(featuresInput.outputs["Output"])
    opb.inputs["Input"].connect(featuresInput.outputs["Output"])
    opc.inputs["Input"].connect(featuresInput.outputs["Output"])
    
    opa.inputs["Sigma"].connect(sigmaProvider1)
    opb.inputs["Sigma"].connect(sigmaProvider2)
    
    
    print "zzzzzzzzzzzasidjhaksjdhkajsdhkjasdhk", opa.outputs["Output"].level, len( opa.outputs["Output"])
    
    featuresOutput = OpMultiArrayPiper(g)
    featuresOutput.inputs["MultiInput"].connectAdd(opa.outputs["Output"])
    featuresOutput.inputs["MultiInput"].connectAdd(opb.outputs["Output"])
    featuresOutput.inputs["MultiInput"].connectAdd(opc.outputs["Output"])
    
    print "llllllllllll", len(featuresOutput.outputs["MultiOutput"])
    
    cacher = OpArrayCache(g)
    cacher.inputs["Input"].connect(featuresOutput.outputs["MultiOutput"])

    print "LLLLLLLLLEVEL",cacher.outputs["Output"].level, len(cacher.outputs["Output"])


    opc = OpMultiArrayStacker(g)
    opc.inputs['MultiInput'].connect(cacher.outputs["Output"])

    print "LLLLLLLLLEVEL",cacher.outputs["Output"].level, len(cacher.outputs["Output"])


    for i in range(numImages):
        print "##########################################"
        print " image ", i
        print "##########################################"

        iinput = featuresInput.inputs["Input"][i]
        print "featuresInput", iinput.__class__
        print "Input", iinput.shape
        oo = featuresInput.outputs["Output"][i]
        print "Output",oo.shape
        print "---"

        iinput = opa.inputs["Input"][i]
        print "opa", iinput.__class__
        print "Input", iinput.shape
        oo = opa.outputs["Output"][i]
        print "Output",oo.shape
        print "---"
        
        iinput = featuresOutput.inputs["MultiInput"][i]
        print "featuresOutput", iinput.__class__, len(featuresOutput.inputs["MultiInput"][i]),len(featuresOutput.outputs["MultiOutput"][i])
        for ii, iiinput in enumerate(iinput):
            print "Input", iiinput.shape
            oo = featuresOutput.outputs["MultiOutput"][i][ii]
            print "Output",oo.shape
            print "--"
        print "---"
        

        iinput = cacher.inputs["Input"][i]
        print "cacher", iinput.__class__
        for ii, iiinput in enumerate(iinput):
            print "Input", iiinput.shape
            oo = cacher.outputs["Output"][i][ii]
            print "Output",oo.shape
            print "--"
        print "---"

        key_ = roi.roiToSlice(numpy.array(key[0]), numpy.array(key[1]))
        res1 = opc.outputs["SingleOutput"][i][key_].allocate()
        
        print res1.shape
        
        print res1[7,7,:,4]
        #assert (res1[...,0] == i).all()
    
    g.finalize()




