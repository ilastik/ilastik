import numpy, vigra

from lazyflow.graph import *
import gc
from lazyflow import roi

from operators import OpArrayPiper, OpMultiArrayPiper


class OpMultiArrayStacker(Operator):
    inputSlots = [MultiInputSlot("Images")]
    outputSlots = [OutputSlot("Output")]
    
    def notifySubConnect(self, slots, indexes):
        #print "  OpMultiArrayStacker.notifyConnect() with", slots, indexes
        self.outputs["Output"]._dtype = self.inputs["MultiInput"][-1].dtype
        self.outputs["Output"]._axistags = copy.copy(self.inputs["MultiInput"][-1].axistags)
        if self.outputs["Output"]._axistags.axisTypeCount(vigra.AxisType.Channels) == 0:
            self.outputs["Output"]._axistags.insertChannelAxis()
        
        c = 0
        for inSlot in self.inputs["MultiInput"]:
            if inSlot.axistags.axisTypeCount(vigra.AxisType.Channels) == 0:
                c += 1
            else:
                c += inSlot.shape[inSlot.axistags.channelIndex]
        self.outputs["Output"]._shape = inSlot.shape[:-1] + (c,)    

    
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


class OpBaseVigraFilter(OpArrayPiper):
    inputSlots = [InputSlot("Input"), InputSlot("Sigma")]
    outputSlots = [OutputSlot("Output")]    
    
    name = "OpBaseVigraFilter"
    vigraFilter = None
    outputDtype = numpy.float32 
    inputDtype = numpy.float32
    
    def __init__(self, graph):
        OpArrayPiper.__init__(self, graph)
        
    def getOutSlot(self, slot, key, result):
        
        start, stop = roi.sliceToRoi(key,self.inputs["Input"].shape)

        subkey = key[0:-1]
        channelsPerChannel = self.resultingChannels()
        
        print self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Channels), self.inputs["Input"].shape
        
        if self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Channels) > 0:
            for i in range(numpy.floor(start[-1]/channelsPerChannel),numpy.ceil(stop[-1]/channelsPerChannel)):
                print "jjjjjjjjj", i
                v = self.inputs["Input"][subkey + (i,)].allocate()
                t = v().squeeze()
                req = self.inputs["Sigma"][:].allocate()
                sigma = req()
                sigma = float(sigma[0])
                
                
                temp = self.vigraFilter(numpy.require(t[:], dtype=self.inputDtype), sigma)

                if channelsPerChannel>1:
                    result[subkey,i*channelsPerChannel:(i+1)*channelsPerChannel] = temp
                else:
                    result[subkey + (i,)] = temp
        else:
            v = self.inputs["Input"][subkey].allocate()
            t = v()
            req = self.inputs["Sigma"][:].allocate()
            sigma = req()
            sigma = float(sigma[0])
            
            temp = self.vigraFilter(numpy.require(t[:], dtype=self.inputDtype), sigma)
            result[subkey,0:channelsPerChannel] = temp
            
    def notifyConnect(self, inputSlot):
        if inputSlot == self.inputs["Input"]:
            numChannels  = 1
            if inputSlot.axistags.axisTypeCount(vigra.AxisType.Channels) > 0:
                channelIndex = self.inputs["Input"].axistags.channelIndex
                numChannels = self.inputs["Input"].shape[channelIndex]*self.resultingChannels()
                inShapeWithoutChannels = inputSlot.shape[:-1]
            else:
                inShapeWithoutChannels = inputSlot.shape
                        
            self.outputs["Output"]._dtype = self.outputDtype
            p = self.inputs["Input"].partner
            self.outputs["Output"]._axistags = copy.copy(inputSlot.axistags)
            
            channelsPerChannel = self.resultingChannels()
            
            self.outputs["Output"]._shape = inShapeWithoutChannels + (numChannels * channelsPerChannel,)
            if self.outputs["Output"]._axistags.axisTypeCount(vigra.AxisType.Channels) == 0:
                self.outputs["Output"]._axistags.insertChannelAxis()
                
        elif inputSlot == self.inputs["Sigma"]:
            self.outputs["Output"].setDirty()
            
    def resultingChannels(self):
        raise RuntimeError('resultingChannels() not implemented')
        

class OpGaussianSmoothing(OpBaseVigraFilter):
    name = "GaussianSmoothing"
    vigraFilter = staticmethod(vigra.filters.gaussianSmoothing)
    outputDtype = numpy.float32 
        

    def resultingChannels(self):
        return 1
    
    
class OpHessianOfGaussianEigenvalues(OpBaseVigraFilter):
    name = "HessianOfGaussianEigenvalues"
    vigraFilter = staticmethod(vigra.filters.hessianOfGaussianEigenvalues)
    outputDtype = numpy.float32 

    def resultingChannels(self):
        temp = self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space)
        return temp


class OpHessianOfGaussian(OpBaseVigraFilter):
    name = "HessianOfGaussian"
    vigraFilter = staticmethod(vigra.filters.hessianOfGaussian)
    outputDtype = numpy.float32 

    def resultingChannels(self):
        temp = self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space)**2
        return temp

class OpLaplacianOfGaussian(OpBaseVigraFilter):
    name = "LaplacianOfGaussian"
    vigraFilter = staticmethod(vigra.filters.laplacianOfGaussian)
    outputDtype = numpy.float32 

    def resultingChannels(self):
        return 1

class OpOpening(OpBaseVigraFilter):
    name = "Opening"
    vigraFilter = staticmethod(vigra.filters.multiGrayscaleOpening)
    outputDtype = numpy.uint8 
    inputDtype = numpy.uint8 

    def resultingChannels(self):
        return 1

class OpClosing(OpBaseVigraFilter):
    name = "Closing"
    vigraFilter = staticmethod(vigra.filters.multiGrayscaleClosing)
    outputDtype = numpy.uint8 
    inputDtype = numpy.uint8 

    def resultingChannels(self):
        return 1

class OpErosion(OpBaseVigraFilter):
    name = "Erosion"
    vigraFilter = staticmethod(vigra.filters.multiGrayscaleErosion)
    outputDtype = numpy.uint8 
    inputDtype = numpy.uint8 

    def resultingChannels(self):
        return 1

class OpDilation(OpBaseVigraFilter):
    name = "Dilation"
    vigraFilter = staticmethod(vigra.filters.multiGrayscaleDilation)
    outputDtype = numpy.uint8 
    inputDtype = numpy.uint8 

    def resultingChannels(self):
        return 1



class OpImageReader(Operator):
    name = "Image Reader"
    inputSlots = [InputSlot("Filename")]
    outputSlots = [OutputSlot("Image")]
    
    def notifyConnect(self, inputSlot):
        filename = self.inputs["Filename"][:].allocate().wait()[0]
        info = vigra.impex.ImageInfo(filename)
        
        oslot = self.outputs["Image"]
        oslot._shape = info.getShape()
        oslot._dtype = info.getDtype()
        oslot._axistags = info.getAxisTags()
    
    def getOutSlot(self, slot, key, result):
        filename = self.inputs["Filename"][:].allocate().wait()[0]
        temp = vigra.impex.readImage(filename)
        
        result[:] = temp[key]
    

class OpImageWriter(Operator):
    name = "Image Writer"
    inputSlots = [InputSlot("Filename"), InputSlot("Image")]
    
    def notifyConnect(self, inputSlot):
        
        if self.inputs["Filename"].partner is not None and self.inputs["Image"].partner is not None:
            filename = self.inputs["Filename"][:].allocate().wait()[0]
    
            image = self.inputs["Image"][:].allocate().wait()
            imSlot = self.inputs["Image"]
            vimage = vigra.VigraArray(image, dtype = imSlot.dtype, axistags = imSlot.axistags)
            vigra.impex.writeImage(vimage, filename)
        