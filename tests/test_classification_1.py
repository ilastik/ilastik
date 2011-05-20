import numpy, vigra
import time
from graph import *
import gc
import roi
import copy

from operators.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper, OpMultiMultiArrayPiper
from mockOperators import ArrayProvider, SingleValueProvider
from graph import MultiInputSlot

import sys, vigra
import copy

        
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
    
    def resultingChannels(self):
        return 1
    
    
class OpHessianOfGaussianEigenvalues(OpBaseVigraFilter):
    name = "HessianOfGaussianEigenvalues"
    vigraFilter = staticmethod(vigra.filters.hessianOfGaussianEigenvalues)
    
    def resultingChannels(self):
        temp = self.outputs["Output"].axistags.axisTypeCount(vigra.AxisType.Space)
        return temp

class OpMultiArrayStacker(Operator):
    inputSlots = [MultiInputSlot("MultiInput")]
    outputSlots = [OutputSlot("SingleOutput")]
    
    def notifyPartialMultiConnect(self, slots, indexes):
        #print "  OpMultiArrayStacker.notifyConnect() with", slots, indexes
        self.outputs["SingleOutput"]._dtype = self.inputs["MultiInput"][-1].dtype
        self.outputs["SingleOutput"]._axistags = copy.copy(self.inputs["MultiInput"][-1].axistags)
        if self.outputs["SingleOutput"]._axistags.axisTypeCount(vigra.AxisType.Channels) == 0:
            self.outputs["SingleOutput"]._axistags.insertChannelAxis()
        
        c = 0
        for inSlot in self.inputs["MultiInput"]:
            c += inSlot.shape[-1]
        self.outputs["SingleOutput"]._shape = (200,200,200,4)     

    
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
                v = inSlot[key_].writeInto(result[...,cnt:cnt+channels+1])
                cnt += channels
            v()
                 
if __name__ == "__main__":

    shape = (200,200,200)
    numThreads = 1
    axistags = vigra.VigraArray.defaultAxistags(len(shape)+1)
    axistags.dropChannelAxis()
    
    key = [[50,50,50,0],[100,100,100,4]]
    
    g = Graph(numThreads = numThreads)
    
    multislot = OpMultiArrayPiper(g)
    
    
    for i in range(3):
        provider = ArrayProvider("Random input", shape=shape, dtype=numpy.float32, axistags=axistags)
        provider.setData(numpy.random.rand(*provider.shape).astype(provider.dtype).view(vigra.VigraArray))
        multislot.inputs["MultiInput"].connectAdd(provider)
    
    featuresInput = OpArrayPiper(g)
    featuresInput.inputs["Input"].connect(multislot.outputs["MultiOutput"])
    sigmaProvider1 = SingleValueProvider("Sigma", float)
    sigmaProvider2 = SingleValueProvider("Sigma", float)
    sigmaProvider1.setValue(1.2)
    sigmaProvider2.setValue(2.2)

    
    opa = OpGaussianSmooting(g)
    opb = OpHessianOfGaussianEigenvalues(g)
        
    print "LLLLLLLLLEVEL",featuresInput.outputs["Output"].level, len(featuresInput.outputs["Output"])
        
        
        
    opa.inputs["Input"].connect(featuresInput.outputs["Output"])
    opb.inputs["Input"].connect(featuresInput.outputs["Output"])
    
    opa.inputs["Sigma"].connect(sigmaProvider1)
    opb.inputs["Sigma"].connect(sigmaProvider2)
    
    
    print "zzzzzzzzzzzasidjhaksjdhkajsdhkjasdhk", opa.outputs["Output"].level, len( opa.outputs["Output"])
    
    featuresOutput = OpMultiMultiArrayPiper(g)
    featuresOutput.inputs["MultiInput"].connectAdd(opa.outputs["Output"])
    featuresOutput.inputs["MultiInput"].connectAdd(opb.outputs["Output"])
    
    
    cacher = OpArrayCache(g)
    cacher.inputs["Input"].connect(featuresOutput.outputs["MultiOutput"])

    print "LLLLLLLLLEVEL",cacher.outputs["Output"].level, len(cacher.outputs["Output"])


    opc = OpMultiArrayStacker(g)
    opc.inputs['MultiInput'].connect(cacher.outputs["Output"])

    print "LLLLLLLLLEVEL",cacher.outputs["Output"].level, len(cacher.outputs["Output"])

    key = roi.roiToSlice(numpy.array(key[0]), numpy.array(key[1]))

    for i in range(3):
        res1 = opc.outputs["SingleOutput"][i][key].allocate()
        
    g.finalize()




