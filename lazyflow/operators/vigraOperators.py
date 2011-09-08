import numpy, vigra, h5py

from lazyflow.graph import *
import gc
from lazyflow import roi
import copy

from operators import OpArrayPiper, OpMultiArrayPiper

from generic import OpMultiArrayStacker, getSubKeyWithFlags, popFlagsFromTheKey

import math

from threading import Lock


class OpMultiArrayStackerOld(Operator):
    inputSlots = [MultiInputSlot("Images")]
    outputSlots = [OutputSlot("Output")]

    name = "Multi Array Stacker"
    category = "Misc"

    def notifySubConnect(self, slots, indexes):
        dtypeDone = False        
        c = 0
        for inSlot in self.inputs["Images"]:
            if inSlot.partner is not None:
                if dtypeDone is False:
                    self.outputs["Output"]._dtype = inSlot.dtype
                    self.outputs["Output"]._axistags = copy.copy(inSlot.axistags)
                    if self.outputs["Output"]._axistags.axisTypeCount(vigra.AxisType.Channels) == 0:
                        self.outputs["Output"]._axistags.insertChannelAxis()
                    
                if inSlot.axistags.axisTypeCount(vigra.AxisType.Channels) == 0:
                    c += 1
                else:
                    c += inSlot.shape[inSlot.axistags.channelIndex]
        self.outputs["Output"]._shape = inSlot.shape[:-1] + (c,)    

    
    def getOutSlot(self, slot, key, result):
        cnt = 0
        written = 0
        start, stop = roi.sliceToRoi(key, self.outputs["Output"].shape)
        key = key[:-1]
        requests = []
        for i, inSlot in enumerate(self.inputs['Images']):
            if inSlot.partner is not None:
                req = None
                if inSlot.axistags.axisTypeCount(vigra.AxisType.Channels) == 0:
                    if cnt >= start[-1] and start[-1] + written < stop[-1]:
                        req = inSlot[key].writeInto(result[..., cnt])
                        written += 1
                    cnt += 1
                    
                else:
                    channels = inSlot.shape[inSlot.axistags.channelIndex]
                    if cnt + channels >= start[-1] and start[-1] - cnt < channels and start[-1] + written < stop[-1]:
                        
                        begin = 0
                        if cnt < start[-1]:
                            begin = start[-1] - cnt
                        end = channels
                        if cnt + end > stop[-1]:
                            end -= cnt + end - stop[-1]
                        key_ = key + (slice(begin,end,None),)

                        assert (end <= numpy.array(inSlot.shape)).all()
                        assert (begin < numpy.array(inSlot.shape)).all(), "begin : %r, shape: %r" % (begin, inSlot.shape)
                        req = inSlot[key_].writeInto(result[...,written:written+end-begin])
                        written += end - begin
                    cnt += channels
               
                if req is not None:
                   requests.append(req)
        
        for r in requests:
            r.wait()


class Op5ToMulti(Operator):
    name = "5 Elements to Multislot"
    category = "Misc"

    
    inputSlots = [InputSlot("Input0"),InputSlot("Input1"),InputSlot("Input2"),InputSlot("Input3"),InputSlot("Input4")]
    outputSlots = [MultiOutputSlot("Outputs")]
        
    def notifyConnect(self, slot):
        length = 0
        for slot in self.inputs.values():
            if slot.connected():
                length += 1                

        self.outputs["Outputs"].resize(length)

        i = 0
        for sname in sorted(self.inputs.keys()):
            slot = self.inputs[sname]
            if slot.connected():
                self.outputs["Outputs"][i]._dtype = slot.dtype
                self.outputs["Outputs"][i]._axistags = copy.copy(slot.axistags)
                self.outputs["Outputs"][i]._shape = slot.shape
                i += 1       

    def notifyDisonnect(self, slot):
        self.notifyConnect(None)                        
        
    def getSubOutSlot(self, slots, indexes, key, result):
        i = 0
        for sname in sorted(self.inputs.keys()):
            slot = self.inputs[sname]
            if slot.connected():
                if i == indexes[0]:
                    result[:] = slot[key].allocate().wait()
                    break
                i += 1                

class Op10ToMulti(Op5ToMulti):
    name = "10 Elements to Multislot"
    category = "Misc"

    inputSlots = [InputSlot("Input0"), InputSlot("Input1"),InputSlot("Input2"),InputSlot("Input3"),InputSlot("Input4"),InputSlot("Input5"), InputSlot("Input6"),InputSlot("Input7"),InputSlot("Input8"),InputSlot("Input9")]
    outputSlots = [MultiOutputSlot("Outputs")]


class Op20ToMulti(Op5ToMulti):
    name = "20 Elements to Multislot"
    category = "Misc"

    inputSlots = [InputSlot("Input00"), InputSlot("Input01"),InputSlot("Input02"),InputSlot("Input03"),InputSlot("Input04"),InputSlot("Input05"), InputSlot("Input06"),InputSlot("Input07"),InputSlot("Input08"),InputSlot("Input09"),InputSlot("Input10"), InputSlot("Input11"),InputSlot("Input12"),InputSlot("Input13"),InputSlot("Input14"),InputSlot("Input15"), InputSlot("Input16"),InputSlot("Input17"),InputSlot("Input18"),InputSlot("Input19")]
    outputSlots = [MultiOutputSlot("Outputs")]



class Op50ToMulti(Op5ToMulti):
    
    name = "N Elements to Multislot"
    category = "Misc"

    inputSlots=[]
    for i in xrange(50):
        inputSlots.append(InputSlot("Input%.2d"%(i)))
    outputSlots = [MultiOutputSlot("Outputs")]

    





class OpPixelFeatures(OperatorGroup):
    name="OpPixelFeatures"
    category = "Vigra filter"
    
    inputSlots = [InputSlot("Input"), InputSlot("Matrix"), InputSlot("Scales")]
    outputSlots = [OutputSlot("Output"), OutputSlot("ArrayOfOperators")]
    
    def _createInnerOperators(self):
        # this method must setup the
        # inner operators and connect them (internally)
        
        self.source = OpArrayPiper(self.graph)
        
        self.stacker = OpMultiArrayStacker(self.graph)
        
        self.multi = Op50ToMulti(self.graph)
        
        
        self.stacker.inputs["Images"].connect(self.multi.outputs["Outputs"])
        
        
    def notifyConnectAll(self):
        if self.inputs["Scales"].connected() and self.inputs["Matrix"].connected():

            self.stacker.inputs["Images"].disconnect()
            self.scales = self.inputs["Scales"].value
            self.matrix = self.inputs["Matrix"].value 
            
            if type(self.matrix)!=numpy.ndarray:
                raise RuntimeError("OpPixelFeatures: Please input a numpy.ndarray as 'Matrix'")
            
            dimCol = len(self.scales)
            dimRow = self.matrix.shape[0]
            
            assert dimCol== self.matrix.shape[1], "Please check the matrix or the scales they are not the same"
            assert dimRow==6, "Right now the features are fixed"
    
            oparray = []
            for j in range(dimRow):
                oparray.append([])
    
            i = 0
            for j in range(dimCol):
                oparray[i].append(OpGaussianSmoothing(self.graph))
                oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                oparray[i][j].inputs["sigma"].setValue(self.scales[j])
            i = 1
            for j in range(dimCol):
                oparray[i].append(OpLaplacianOfGaussian(self.graph))
                oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                oparray[i][j].inputs["scale"].setValue(self.scales[j])
            i = 2
            for j in range(dimCol):
                oparray[i].append(OpStructureTensorEigenvalues(self.graph))
                oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                oparray[i][j].inputs["innerScale"].setValue(self.scales[j])
                oparray[i][j].inputs["outerScale"].setValue(self.scales[j]*0.5)
            i = 3
            for j in range(dimCol):   
                oparray[i].append(OpHessianOfGaussianEigenvalues(self.graph))
                oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                oparray[i][j].inputs["scale"].setValue(self.scales[j])
            
            i= 4
            for j in range(dimCol): 
                oparray[i].append(OpGaussianGradientMagnitude(self.graph))
                oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                oparray[i][j].inputs["sigma"].setValue(self.scales[j])
            
            i= 5
            for j in range(dimCol): 
                oparray[i].append(OpDifferenceOfGaussians(self.graph))
                oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                oparray[i][j].inputs["sigma0"].setValue(self.scales[j])            
                oparray[i][j].inputs["sigma1"].setValue(self.scales[j]*0.66)
            

                
            
            
            self.outputs["ArrayOfOperators"][0] = oparray
            
            #disconnecting all Operators
            for i in range(dimRow):
                for j in range(dimCol):
                    self.multi.inputs["Input%02d" %(i*dimRow+j)].disconnect() 
            
            #connect individual operators
            for i in range(dimRow):
                for j in range(dimCol):
                    val=self.matrix[i,j]
                    if val:
                        self.multi.inputs["Input%02d" %(i*dimRow+j)].connect(oparray[i][j].outputs["Output"])
            
            #additional connection with FakeOperator
            if (self.matrix==0).all():
                fakeOp = OpGaussianSmoothing(self.graph)
                fakeOp.inputs["Input"].connect(self.source.outputs["Output"])
                fakeOp.inputs["sigma"].setValue(10)
                self.multi.inputs["Input%02d" %(i*dimRow+j+1)].connect(fakeOp.outputs["Output"])
                self.multi.inputs["Input%02d" %(i*dimRow+j+1)].disconnect() 
                self.stacker.outputs["Output"].shape=()
                return
         
            
            index = len(self.source.outputs["Output"].shape) - 1
            self.stacker.inputs["AxisFlag"].setValue('c')
            self.stacker.inputs["AxisIndex"].setValue(self.source.outputs["Output"]._axistags.index('c'))
            self.stacker.inputs["Images"].connect(self.multi.outputs["Outputs"])
            
    
    def getInnerInputs(self):
        inputs = {}
        inputs["Input"] = self.source.inputs["Input"]
        return inputs
        
    def getInnerOutputs(self):
        outputs = {}
        outputs["Output"] = self.stacker.outputs["Output"]
        return outputs



class OpPixelFeaturesPresmoothed(OperatorGroup):
    name="OpPixelFeaturesPresmoothed"
    category = "Vigra filter"
    
    inputSlots = [MultiInputSlot("Input", level = 1), MultiInputSlot("inputSigmas", level = 1), InputSlot("Matrix"), InputSlot("Scales")]
    outputSlots = [OutputSlot("Output"), OutputSlot("ArrayOfOperators")]
    
    def _createInnerOperators(self):
        # this method must setup the
        # inner operators and connect them (internally)
        
        self.source = OpArrayPiper(self.graph)
        
        self.stacker = OpMultiArrayStacker(self.graph)
        
        self.multi = Op20ToMulti(self.graph)
        
        
        self.stacker.inputs["Images"].connect(self.multi.outputs["Outputs"])

        self._inputSigmas = []
        self._sigma = 0
       
           
    def _bestIndexForScale(self, scale):
        i = 0
        while(i < len(self._inputSigmas) and self._inputSigmas[i] < scale):          
            i += 1
        
        bestIndex = i-1
        bestInputSigma = math.sqrt(scale**2 - self._inputSigmas[bestIndex]**2)
        return bestIndex, bestInputSigma         
       
    def notifyConnectAll(self):

        self._inputSigmas = []            
        for i,s in enumerate(self.inputs["inputSigmas"]):
            self._inputSigmas.append(s.value)
            

        numChannels  = 1
        

        inputSlot = self.inputs["Input"][0]
        if inputSlot.axistags.axisTypeCount(vigra.AxisType.Channels) > 0:
            channelIndex = inputSlot.axistags.channelIndex
            numChannels = inputSlot.shape[channelIndex]
            inShapeWithoutChannels = inputSlot.shape[:-1]
        else:
            inShapeWithoutChannels = inputSlot.shape
                            

        self.stacker.inputs["Images"].disconnect()
        self.scales = self.inputs["Scales"].value
        self.matrix = self.inputs["Matrix"].value 
        
        if type(self.matrix)!=numpy.ndarray:
          raise RuntimeError("OpPixelFeaturesPresmoothed: Please input a numpy.ndarray as 'Matrix'")
        
        dimCol = len(self.scales)
        dimRow = self.matrix.shape[0]
        
        assert dimCol== self.matrix.shape[1], "Please check the matrix or the scales they are not the same"
        assert dimRow==4, "Right now the features are fixed"

        oparray = []
        for j in range(dimCol):
            oparray.append([])

        i = 0
        for j in range(dimCol):
            oparray[i].append(OpGaussianSmoothing(self.graph))
            bestIndex, bestSigma = self._bestIndexForScale(self.scales[j])
            oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"][bestIndex])
            oparray[i][j].inputs["sigma"].setValue(bestSigma)
            print "OpPixelFeaturesPresmoothed : selected index %d with scale %f for scale %d, new sigma: %f" %(bestIndex,self._inputSigmas[bestIndex],self.scales[j],bestSigma)
        i = 1
        for j in range(dimCol):
            oparray[i].append(OpLaplacianOfGaussian(self.graph))
            bestIndex, bestSigma = self._bestIndexForScale(self.scales[j])
            oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"][bestIndex])
            oparray[i][j].inputs["scale"].setValue(bestSigma)
        i = 2
        for j in range(dimCol):
            oparray[i].append(OpHessianOfGaussian(self.graph))
            bestIndex, bestSigma = self._bestIndexForScale(self.scales[j])
            oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"][bestIndex])
            oparray[i][j].inputs["sigma"].setValue(bestSigma)
        i = 3
        for j in range(dimCol):   
            oparray[i].append(OpHessianOfGaussianEigenvalues(self.graph))
            bestIndex, bestSigma = self._bestIndexForScale(self.scales[j])
            oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"][bestIndex])
            oparray[i][j].inputs["scale"].setValue(bestSigma)
        
        self.outputs["ArrayOfOperators"][0] = oparray
        
        #disconnecting all Operators
        for i in range(dimRow):
            for j in range(dimCol):
                self.multi.inputs["Input%02d" %(i*dimRow+j)].disconnect() 
        
        #connect individual operators
        for i in range(dimRow):
            for j in range(dimCol):
                val=self.matrix[i,j]
                if val:
                    self.multi.inputs["Input%02d" %(i*dimRow+j)].connect(oparray[i][j].outputs["Output"])
        
        #additional connection with FakeOperator
        if (self.matrix==0).all():
            fakeOp = OpGaussianSmoothing(self.graph)
            fakeOp.inputs["Input"].connect(self.source.outputs["Output"])
            fakeOp.inputs["sigma"].setValue(10)
            self.multi.inputs["Input%02d" %(i*dimRow+j+1)].connect(fakeOp.outputs["Output"])
            self.multi.inputs["Input%02d" %(i*dimRow+j+1)].disconnect() 
            self.stacker.outputs["Output"].shape=()
            return
     
        
        index = len(self.source.outputs["Output"][0].shape) - 1
        self.stacker.inputs["AxisFlag"].setValue('c')
        self.stacker.inputs["AxisIndex"].setValue(index)
        self.stacker.inputs["Images"].connect(self.multi.outputs["Outputs"])
            
    
    def getInnerInputs(self):
        inputs = {}
        inputs["Input"] = self.source.inputs["Input"]
        return inputs
        
    def getInnerOutputs(self):
        outputs = {}
        outputs["Output"] = self.stacker.outputs["Output"]
        return outputs


def getAllExceptAxis(ndim,index,slicer):
    res= [slice(None, None, None)] * ndim
    res[index] = slicer
    return tuple(res)

class OpBaseVigraFilter(OpArrayPiper):
    inputSlots = [InputSlot("Input"), InputSlot("sigma", stype = "float")]
    outputSlots = [OutputSlot("Output")]    
    
    name = "OpBaseVigraFilter"
    category = "Vigra filter"
    
    vigraFilter = None
    outputDtype = numpy.float32 
    inputDtype = numpy.float32
    supportsOut = True
    window_size=2
    supportsRoi = False
    supportsWindow = False
    
    def __init__(self, graph, register = True):
        OpArrayPiper.__init__(self, graph, register = register)
        self.supportsOut = False
        
    def getOutSlot(self, slot, key, result):
        
        kwparams = {}        
        for islot in self.inputs.values():
            if islot.name != "Input":
                kwparams[islot.name] = islot.value
        
        if self.inputs.has_key("sigma"):
            sigma = self.inputs["sigma"].value
        elif self.inputs.has_key("scale"):
            sigma = self.inputs["scale"].value
        elif self.inputs.has_key("sigma1"):
            sigma = self.inputs["sigma1"].value
        elif self.inputs.has_key("innerScale"):
            sigma = self.inputs["innerScale"].value

        windowSize = 4.0
        if self.supportsWindow:
            kwparams['window_size']=self.window_size
            windowSize = self.window_size
            
        largestSigma = sigma*windowSize #ensure enough context for the vigra operators
                
        shape = self.outputs["Output"].shape
        
        axistags = self.inputs["Input"].axistags
        
        channelAxis=self.inputs["Input"].axistags.index('c')
        hasTimeAxis = self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Time)
        timeAxis=self.inputs["Input"].axistags.index('t')

        subkey = popFlagsFromTheKey(key,axistags,'c')
        subshape=popFlagsFromTheKey(shape,axistags,'c')
        at2 = copy.copy(axistags)
        at2.dropChannelAxis()
        subshape=popFlagsFromTheKey(subshape,at2,'t')
        subkey = popFlagsFromTheKey(subkey,at2,'t')
        
        oldstart, oldstop = roi.sliceToRoi(key, shape)
        
        start, stop = roi.sliceToRoi(subkey,subkey)
        newStart, newStop = roi.extendSlice(start, stop, subshape, largestSigma)
        readKey = roi.roiToSlice(newStart, newStop)
        
        
        writeNewStart = start - newStart
        writeNewStop = writeNewStart +  stop - start
        
        if (writeNewStart == 0).all() and (newStop == writeNewStop).all():
            fullResult = True
        else:
            fullResult = False
        
        writeKey = roi.roiToSlice(writeNewStart, writeNewStop)
        writeKey = list(writeKey)
        writeKey.insert(channelAxis, slice(None,None,None))
        writeKey = tuple(writeKey)         
                
        channelsPerChannel = self.resultingChannels()
        
        if self.supportsRoi is False and largestSigma > 5:
            print "WARNING: operator", self.name, "does not support roi !!"
        
        
        i2 = 0          
        for i in range(int(numpy.floor(1.0 * oldstart[channelAxis]/channelsPerChannel)),int(numpy.ceil(1.0 * oldstop[channelAxis]/channelsPerChannel))):
            treadKey=list(readKey)
            
            if hasTimeAxis:
                treadKey.insert(timeAxis, key[timeAxis])
            
            treadKey.insert(channelAxis, slice(i,i+1,None))
            treadKey=tuple(treadKey)

            req = self.inputs["Input"][treadKey].allocate()
            t = req.wait()
            
            t = numpy.require(t, dtype=self.inputDtype)
            
            t = t.view(vigra.VigraArray)
            t.axistags = copy.copy(axistags)
            t = t.insertChannelAxis()
            

            sourceBegin = 0
            if oldstart[channelAxis] > i * channelsPerChannel:
                sourceBegin = oldstart[channelAxis] - i * channelsPerChannel
            sourceEnd = channelsPerChannel
            if oldstop[channelAxis] < (i+1) * channelsPerChannel:
                sourceEnd = channelsPerChannel - ((i+1) * channelsPerChannel - oldstop[channelAxis])
            
            destBegin = i2
            destEnd = i2 + sourceEnd - sourceBegin
            
            if channelsPerChannel>1:
                tkey=getAllExceptAxis(len(shape),channelAxis,slice(destBegin,destEnd,None))                   
                resultArea = result[tkey]
            else:
                tkey=getAllExceptAxis(len(shape),channelAxis,slice(i2,i2+1,None)) 
                resultArea = result[tkey]

            
            for step,image in enumerate(t.timeIter()):
                if self.supportsRoi:
                    vroi = (tuple(writeNewStart._asint()), tuple(writeNewStop._asint()))
                    temp = self.vigraFilter(image, roi = vroi, **kwparams)
                else:
                    temp = self.vigraFilter(image, **kwparams)
                    temp=temp[writeKey]

                nChannelAxis = channelAxis - 1
                if timeAxis > channelAxis:
                    nChannelAxis = channelAxis 
                twriteKey=getAllExceptAxis(temp.ndim, nChannelAxis, slice(sourceBegin,sourceEnd,None))
                
                if hasTimeAxis > 0:
                    tresKey  = getAllExceptAxis(resultArea.ndim, timeAxis, step)
                else:
                    tresKey  = slice(None, None,None)
                
                #print tresKey, twriteKey, resultArea.shape, temp.shape
                try:
                    resultArea[tresKey] = temp[twriteKey]
                except:
                    print resultArea.shape,  tresKey, temp.shape, twriteKey
                    print "step, t.shape", step, t.shape, timeAxis
                    assert 1==2
                
            i2 += channelsPerChannel

            
    def notifyConnectAll(self):
        numChannels  = 1
        inputSlot = self.inputs["Input"]
        if inputSlot.axistags.axisTypeCount(vigra.AxisType.Channels) > 0:
            channelIndex = self.inputs["Input"].axistags.channelIndex
            numChannels = self.inputs["Input"].shape[channelIndex]
            inShapeWithoutChannels = popFlagsFromTheKey( self.inputs["Input"].shape,self.inputs["Input"].axistags,'c')
        else:
            inShapeWithoutChannels = inputSlot.shape
            channelIndex = len(inputSlot.shape)
                
        self.outputs["Output"]._dtype = self.outputDtype
        p = self.inputs["Input"].partner
        at = copy.copy(inputSlot.axistags)

        if at.axisTypeCount(vigra.AxisType.Channels) == 0:
            at.insertChannelAxis()
            
        self.outputs["Output"]._axistags = at 
        
        channelsPerChannel = self.resultingChannels()
        inShapeWithoutChannels = list(inShapeWithoutChannels)
        inShapeWithoutChannels.insert(channelIndex,numChannels * channelsPerChannel)        
        self.outputs["Output"]._shape = tuple(inShapeWithoutChannels)
        
        if self.outputs["Output"]._axistags.axisTypeCount(vigra.AxisType.Channels) == 0:
            self.outputs["Output"]._axistags.insertChannelAxis()


    def resultingChannels(self):
        raise RuntimeError('resultingChannels() not implemented')
        

#difference of Gaussians
def differenceOfGausssians(image,sigma0, sigma1,window_size, roi, out = None):
    """ difference of gaussian function""" 
    return (vigra.filters.gaussianSmoothing(image,sigma0,window_size=window_size,roi = roi)-vigra.filters.gaussianSmoothing(image,sigma1,window_size=window_size,roi = roi))


def firstHessianOfGaussianEigenvalues(image, sigmas, roi):
    return vigra.filters.hessianOfGaussianEigenvalues(image, sigmas,roi = roi)[...,0]

def coherenceOrientationOfStructureTensor(image,sigma0, sigma1, out = None):
    """
    coherence Orientation of Structure tensor function:
    input:  M*N*1ch VigraArray
            sigma corresponding to the inner scale of the tensor
            scale corresponding to the outher scale of the tensor
    
    output: M*N*2 VigraArray, the firest channel correspond to coherence
                              the second channel correspond to orientation
    """
    
    #FIXME: make more general
    
    #assert image.spatialDimensions==2, "Only implemented for 2 dimensional images"
    assert len(image.shape)==2 or (len(image.shape)==3 and image.shape[2] == 1), "Only implemented for 2 dimensional images"
    
    st=vigra.filters.structureTensor(image, sigma0, sigma1)
    i11=st[:,:,0]
    i12=st[:,:,1]
    i22=st[:,:,2]
    
    if out is not None:
        assert out.shape[0] == image.shape[0] and out.shape[1] == image.shape[1] and out.shape[2] == 2
        res = out
    else:
        res=numpy.ndarray((image.shape[0],image.shape[1],2))
    
    res[:,:,0]=numpy.sqrt( (i22-i11)**2+4*(i12**2))/(i11-i22)
    res[:,:,1]=numpy.arctan(2*i12/(i22-i11))/numpy.pi +0.5
    
    
    return res



class OpDifferenceOfGaussians(OpBaseVigraFilter):
    name = "DifferenceOfGaussians"
    vigraFilter = staticmethod(differenceOfGausssians)
    outputDtype = numpy.float32 
    supportsOut = False
    supportsWindow = True   
    supportsRoi = True
    inputSlots = [InputSlot("Input"), InputSlot("sigma0", stype = "float"), InputSlot("sigma1", stype = "float")]
    
    def resultingChannels(self):
        return 1

class OpCoherenceOrientation(OpBaseVigraFilter):
    name = "CoherenceOrientationOfStructureTensor"
    vigraFilter = staticmethod(coherenceOrientationOfStructureTensor)
    outputDtype = numpy.float32 
    supportsWindow = True
    inputSlots = [InputSlot("Input"), InputSlot("sigma0", stype = "float"), InputSlot("sigma1", stype = "float")]
    
    def resultingChannels(self):
        return 2    


class OpGaussianSmoothing(OpBaseVigraFilter):
    name = "GaussianSmoothing"
    vigraFilter = staticmethod(vigra.filters.gaussianSmoothing)
    outputDtype = numpy.float32 
    supportsRoi = True
    supportsWindow = True
        

    def resultingChannels(self):
        return 1

    
    def notifyConnectAll(self):
        OpBaseVigraFilter.notifyConnectAll(self)

    
class OpHessianOfGaussianEigenvalues(OpBaseVigraFilter):
    name = "HessianOfGaussianEigenvalues"
    vigraFilter = staticmethod(vigra.filters.hessianOfGaussianEigenvalues)
    outputDtype = numpy.float32 
    supportsRoi = True
    supportsWindow = True
    inputSlots = [InputSlot("Input"), InputSlot("scale", stype = "float")]

    def resultingChannels(self):
        temp = self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space)
        return temp


class OpStructureTensorEigenvalues(OpBaseVigraFilter):
    name = "StructureTensorEigenvalues"
    vigraFilter = staticmethod(vigra.filters.structureTensorEigenvalues)
    outputDtype = numpy.float32 
    supportsRoi = True    
    supportsWindow = True
    inputSlots = [InputSlot("Input"), InputSlot("innerScale", stype = "float"),InputSlot("outerScale", stype = "float")]

    def resultingChannels(self):
        temp = self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space)
        return temp
    


class OpHessianOfGaussianEigenvaluesFirst(OpBaseVigraFilter):
    name = "First Eigenvalue of Hessian Matrix"
    vigraFilter = staticmethod(firstHessianOfGaussianEigenvalues)
    outputDtype = numpy.float32 
    supportsOut = False
    supportsWindow = True
    supportsRoi = True
    inputSlots = [InputSlot("Input"), InputSlot("scale", stype = "float")]

    def resultingChannels(self):
        return 1



class OpHessianOfGaussian(OpBaseVigraFilter):
    name = "HessianOfGaussian"
    vigraFilter = staticmethod(vigra.filters.hessianOfGaussian)
    outputDtype = numpy.float32 
    supportsWindow = True
    supportsRoi = True
    
    def resultingChannels(self):
        temp = self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space)*(self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space) + 1) / 2
        return temp
    
class OpGaussianGradientMagnitude(OpBaseVigraFilter):
    name = "GaussianGradientMagnitude"
    vigraFilter = staticmethod(vigra.filters.gaussianGradientMagnitude)
    outputDtype = numpy.float32 
    supportsRoi = True
    supportsWindow = True

    def resultingChannels(self):        
        return 1

class OpLaplacianOfGaussian(OpBaseVigraFilter):
    name = "LaplacianOfGaussian"
    vigraFilter = staticmethod(vigra.filters.laplacianOfGaussian)
    outputDtype = numpy.float32 
    supportsOut = False
    supportsRoi = True
    supportsWindow = True
    inputSlots = [InputSlot("Input"), InputSlot("scale", stype = "float")]

    
    def resultingChannels(self):
        return 1

class OpOpening(OpBaseVigraFilter):
    name = "Opening"
    vigraFilter = staticmethod(vigra.filters.multiGrayscaleOpening)
    outputDtype = numpy.float32
    inputDtype = numpy.float32
    

    def resultingChannels(self):
        return 1

class OpClosing(OpBaseVigraFilter):
    name = "Closing"
    vigraFilter = staticmethod(vigra.filters.multiGrayscaleClosing)
    outputDtype = numpy.float32
    inputDtype = numpy.float32

    def resultingChannels(self):
        return 1

class OpErosion(OpBaseVigraFilter):
    name = "Erosion"
    vigraFilter = staticmethod(vigra.filters.multiGrayscaleErosion)
    outputDtype = numpy.float32
    inputDtype = numpy.float32

    def resultingChannels(self):
        return 1

class OpDilation(OpBaseVigraFilter):
    name = "Dilation"
    vigraFilter = staticmethod(vigra.filters.multiGrayscaleDilation)
    outputDtype = numpy.float32
    inputDtype = numpy.float32

    def resultingChannels(self):
        return 1



class OpImageReader(Operator):
    name = "Image Reader"
    category = "Input"
    
    inputSlots = [InputSlot("Filename", stype = "filestring")]
    outputSlots = [OutputSlot("Image")]
    
    def notifyConnectAll(self):
        filename = self.inputs["Filename"].value

        if filename is not None:
            info = vigra.impex.ImageInfo(filename)
            
            oslot = self.outputs["Image"]
            oslot._shape = info.getShape()
            oslot._dtype = info.getDtype()
            oslot._axistags = info.getAxisTags()
        else:
            oslot = self.outputs["Image"]
            oslot._shape = None
            oslot._dtype = None
            oslot._axistags = None

    def getOutSlot(self, slot, key, result):
        filename = self.inputs["Filename"].value
        temp = vigra.impex.readImage(filename)

        result[:] = temp[key]
        #self.outputs["Image"][:]=temp[:]
    
import glob
class OpFileGlobList(Operator):
    name = "Glob filenames to 1D-String Array"
    category = "Input"
    
    inputSlots = [InputSlot("Globstring", stype = "string")]
    outputSlots = [MultiOutputSlot("Filenames", stype = "filestring")]
    
    def notifyConnectAll(self):
        globstring = self.inputs["Globstring"].value
        
        self.filenames = glob.glob(globstring)        
        
        oslot = self.outputs["Filenames"]
        oslot.resize(len(self.filenames))
        for slot in oslot:
            slot._shape = (1,)
            slot._dtype = object
            slot._axistags = None
    
    def getSubOutSlot(self, slots, indexes, key, result):
        result[0] = self.filenames[indexes[0]]
    
    
    
    
    
class OpOstrichReader(Operator):
    name = "Ostrich Reader"
    category = "Input"
    
    inputSlots = []
    outputSlots = [OutputSlot("Image")]

    
    
    def __init__(self, g):
        Operator.__init__(self,g)
        #filename = self.filename = "/home/lfiaschi/graph-christoph/tests/ostrich.jpg"
        filename = self.filename = "/home/cstraehl/Projects/eclipse-workspace/graph/tests/ostrich.jpg"
        info = vigra.impex.ImageInfo(filename)
        
        oslot = self.outputs["Image"]
        oslot._shape = info.getShape()
        oslot._dtype = info.getDtype()
        oslot._axistags = info.getAxisTags()
    
    def getOutSlot(self, slot, key, result):
        temp = vigra.impex.readImage(self.filename)
        result[:] = temp[key]


class OpImageWriter(Operator):
    name = "Image Writer"
    category = "Output"
    
    inputSlots = [InputSlot("Filename", stype = "filestring" ), InputSlot("Image")]
    
    def notifyConnectAll(self):
        filename = self.inputs["Filename"].value

        imSlot = self.inputs["Image"]
        
        assert len(imSlot.shape) == 2 or len(imSlot.shape) == 3, "OpImageWriter: wrong image shape %r vigra can only write 2D images, with 1 or 3 channels" %(imSlot.shape,)

        axistags = copy.copy(imSlot.axistags)
        
        image = numpy.ndarray(imSlot.shape, dtype=imSlot.dtype)
        
        def closure(result):
            dtype = imSlot.dtype
            vimage = vigra.VigraArray(image, dtype = dtype, axistags = axistags)
            vigra.impex.writeImage(image, filename)

        self.inputs["Image"][:].writeInto(image).notify(closure)
    

class OpH5Reader(Operator):
    name = "H5 File Reader"
    category = "Input"
    
    inputSlots = [InputSlot("Filename", stype = "filestring"), InputSlot("hdf5Path", stype = "string")]
    outputSlots = [OutputSlot("Image")]
    
        
    def notifyConnectAll(self):
        filename = self.inputs["Filename"].value
        hdf5Path = self.inputs["hdf5Path"].value
        
        f = h5py.File(filename, 'r')
    
        d = f[hdf5Path]
        
        
        self.outputs["Image"]._dtype = d.dtype
        self.outputs["Image"]._shape = d.shape
        
        if len(d.shape) == 2:
            axistags=vigra.AxisTags(vigra.AxisInfo('x',vigra.AxisType.Space),vigra.AxisInfo('y',vigra.AxisType.Space))   
        else:
            axistags= vigra.VigraArray.defaultAxistags(len(d.shape))
        self.outputs["Image"]._axistags=axistags
        self.f=f
        self.d=self.f[hdf5Path]    
        
        
        #f.close()
        
        #FOR DEBUG DUMPING REQUEST TO A FILE
        #import os
        #logfile='readerlog.txt'
        #if os.path.exists(logfile): os.remove(logfile)
        
        #self.ff=open(logfile,'a')
        
        
    def getOutSlot(self, slot, key, result):
        filename = self.inputs["Filename"].value
        hdf5Path = self.inputs["hdf5Path"].value
        
        #f = h5py.File(filename, 'r')
    
        #d = f[hdf5Path]
        
        
        
        
        
        result[:] = self.d[key]
        #f.close()
        
        #Debug DUMPING REQUEST TO FILE
        #start,stop=roi.sliceToRoi(key,self.d.shape)
        #dif=numpy.array(stop)-numpy.array(start)
        
        #self.ff.write(str(start)+'   '+str(stop)+'   ***  '+str(dif)+' \n')
        

        
class OpH5Writer(Operator):
    name = "H5 File Writer"
    category = "Output"
    
    inputSlots = [InputSlot("Filename", stype = "filestring"), InputSlot("hdf5Path", stype = "string"), InputSlot("Image")]
    outputSlots = [OutputSlot("WriteImage")]

    def notifyConnectAll(self):        
        self.outputs["WriteImage"]._shape = (1,)
        self.outputs["WriteImage"]._dtype = object
#            filename = self.inputs["Filename"][0].allocate().wait()[0]
#            hdf5Path = self.inputs["hdf5Path"][0].allocate().wait()[0]
#
#            imSlot = self.inputs["Image"]
#            
#            axistags = copy.copy(imSlot.axistags)
#            
#            image = numpy.ndarray(imSlot.shape, dtype=imSlot.dtype)
#                        
#            def closure():
#                f = h5py.File(filename, 'w')
#                g = f
#                pathElements = hdf5Path.split("/")
#                for s in pathElements[:-1]:
#                    g = g.create_group(s)
#                g.create_dataset(pathElements[-1],data = image)
#                f.close()
#    
#            self.inputs["Image"][:].writeInto(image).notify(closure)
    
    def getOutSlot(self, slot, key, result):
        filename = self.inputs["Filename"].value
        hdf5Path = self.inputs["hdf5Path"].value

        imSlot = self.inputs["Image"]
        
        axistags = copy.copy(imSlot.axistags)
        
        image = numpy.ndarray(imSlot.shape, dtype=imSlot.dtype)
                    

        self.inputs["Image"][:].writeInto(image).wait()
        
        
        f = h5py.File(filename, 'w')
        g = f
        pathElements = hdf5Path.split("/")
        for s in pathElements[:-1]:
            g = g.create_group(s)
        g.create_dataset(pathElements[-1],data = image)
        f.close()
        
        result[0] = True
        
        
        
class OpH5WriterBigDataset(Operator):
    name = "H5 File Writer BigDataset"
    category = "Output"
    
    inputSlots = [InputSlot("Filename", stype = "filestring"), InputSlot("hdf5Path", stype = "string"), InputSlot("Image")]
    outputSlots = [OutputSlot("WriteImage")]

    def notifyConnectAll(self):    
        self.outputs["WriteImage"]._shape = (1,)
        self.outputs["WriteImage"]._dtype = object
        
        
        
        filename = self.inputs["Filename"].value
        import os
        if os.path.exists(filename): os.remove(filename)
        
        hdf5Path = self.inputs["hdf5Path"].value
        self.f = h5py.File(filename, 'w')
        
        g=self.f
        pathElements = hdf5Path.split("/")
        for s in pathElements[:-1]:
            g = g.create_group(s)
        
        shape=self.inputs['Image'].shape
        
        self.d=g.create_dataset(pathElements[-1],shape=shape,dtype=numpy.float32, chunks=(1,128,128,1,1),\
                                compression='gzip', compression_opts=4)

    
    def getOutSlot(self, slot, key, result):
        
        requests=self.computeRequests()
        
        
        imSlot = self.inputs["Image"]
        
        tmp=[]
                    
        for r in requests:
            
            tmp.append(self.inputs["Image"][r].allocate())
         
        for i,t in enumerate(tmp):
            r=requests[i]
            self.d[r]=t.wait()
            print "request ", i, "out of ", len(tmp), "executed"
        result[0] = True
        
        
    def computeRequests(self):
        
        #TODO: reimplement the request better
        shape=numpy.asarray(self.inputs['Image'].shape)
        

        shift=numpy.asarray((10,200,200,64,10))
        shift=numpy.minimum(shift,shape)
        start=numpy.asarray([0]*len(shape))
        
        
        
        
        stop=shift
        reqList=[]
        
        #shape = shape - (numpy.mod(numpy.asarray(shape), 
        #                  shift))
        from itertools import product
        
        for indices in product(*[range(0, stop, step) 
                        for stop,step in zip(shape, shift)]):
                            
                            start=numpy.asarray(indices)
                            stop=numpy.minimum(start+shift,shape)
                            reqList.append(roiToSlice(start,stop))
        
     
        
        
   
        
        return reqList
    
    def close(self):
        self.f.close()
        
        
        
        
        
        
                

class OpH5ReaderBigDataset(Operator):
    
    name = "H5 File Reader For Big Datasets"
    category = "Input"
    
    inputSlots = [InputSlot("Filenames"), InputSlot("hdf5Path", stype = "string")]
    outputSlots = [OutputSlot("Output")]
    
    def __init__(self, graph):
        Operator.__init__(self, graph)
        
        self._lock = Lock()
        
    def notifyConnectAll(self):
        filename = str(self.inputs["Filenames"].value[0])
        hdf5Path = self.inputs["hdf5Path"].value
        
        f = h5py.File(filename, 'r')
    
        d = f[hdf5Path]
        
        self.shape=d.shape
        
        self.outputs["Output"]._dtype = d.dtype
        self.outputs["Output"]._shape = d.shape
        
        if len(d.shape) == 5:
            axistags= vigra.VigraArray.defaultAxistags('txyzc')
        else:
            raise RuntimeError("OpH5ReaderBigDataset: Not implemented for shape=%r" % d.shape)
        self.outputs["Output"]._axistags=axistags
            
        f.close()
        
        self.F=[]
        self.D=[]
        self.ChunkList=[]
        
        for filename in self.inputs["Filenames"].value:
            filename = str(filename)
            f=h5py.File(filename, 'r')
            d=f[hdf5Path]
            
            assert (numpy.array(self.shape)==numpy.array(self.shape)).all(), "Some files have a different shape, this is not allowed man!"
            
            
            self.ChunkList.append(d.chunks)
            self.F.append(f)
            self.D.append(d)
        
    def getOutSlot(self, slot, key, result):
        filenames = self.inputs["Filenames"].value
        
        hdf5Path = self.inputs["hdf5Path"].value
        F=[]
        D=[]
        ChunkList=[]
        
        start,stop=sliceToRoi(key,self.shape)
        diff=numpy.array(stop)-numpy.array(start)

        maxError=sys.maxint
        index=0

        self._lock.acquire()
        #lock access to self.ChunkList,
        #               self.D
        for i,chunks in enumerate(self.ChunkList):
            cs = numpy.array(chunks)
            
            error = numpy.sum(numpy.abs(diff -cs))
            if error<maxError:
                index = i
                maxError = error
        
        result[:]=self.D[index][key]
        self._lock.release()
    """
    def notifyDisconnect(self, slot):
        for f in self.F:
            f.close()
        self.D=[]
        self.ChunkList=[]
    """


class OpH5ReaderSmoothedDataset(Operator):
    
    name = "H5FileReaderForMultipleScaleDatasets"
    category = "Input"
    
    inputSlots = [InputSlot("Filenames"), InputSlot("hdf5Path", stype = "string")]
    outputSlots = [MultiOutputSlot("Outputs"),MultiOutputSlot("Sigmas")]
    
        
    def notifyConnectAll(self):
        
        #get the shape and other stuff from the first dataset
        self.sigmas=[]
        self.shape=None
        self._setTheOutPutSlotsAndSigmas()    
        
        
        #get the chunks and the references to the files for all other datasets
        self.ChunkList=[]
        self.D=[]
        self.F=[]
        
        self._setChunksAndDatasets()
            
    def getSubOutSlot(self, slots, indexes, key, result):
        
        slot=slots[0]
        index=indexes[0]
        
        if slot.name=='Outputs':
            indexFile=self._getFileIndex(key)
            result[:]=self.D[indexFile][index][key]
        elif slot.name=='Sigmas':
            result[:]=self.sigmas[index]
           
          
    def _setTheOutPutSlotsAndSigmas(self):
        firstfile = self.inputs["Filenames"].value[0]
        print "GUAGA",firstfile
        
        hdf5Path = self.inputs["hdf5Path"].value
        
        f = h5py.File(firstfile, 'r')
        g = f[hdf5Path]
        
        count=len(g.keys())
        self.outputs['Outputs'].resize(count)
        self.outputs['Sigmas'].resize(count)
        
        self.shape=f['volume/data'].shape
        
        for i,el in enumerate(sorted(g.keys())):
            self.outputs["Sigmas"][i]._dtype = numpy.float32
            self.outputs["Sigmas"][i]._shape = (1,)
            self.sigmas.append(g[el].attrs['sigma'])
            self.outputs["Outputs"][i]._dtype = g[el].dtype
            self.outputs["Outputs"][i]._shape = g[el].shape
            if len(g[el].shape):
                self.outputs["Outputs"][i]._axistags=vigra.VigraArray.defaultAxistags('txyzc')
            else:
                raise RuntimeError("OpH5ReaderSmoothedDataset: not implemented for non 5d dataset due to non serialization of axistags")
        f.close()
    
    def _setChunksAndDatasets(self):
        hdf5Path = self.inputs["hdf5Path"].value
        for filename in self.inputs["Filenames"].value:
            f=h5py.File(filename, 'r')
            self.F.append(f)
            g=f[hdf5Path]
            tmplist=[]
            self.ChunkList.append(f['volume/data'].chunks)
            for i,el in enumerate(sorted(g.keys())):
                assert (g[el].attrs['sigma'] in self.sigmas), "A new unexpected sigma was found %s %s" %(g[el].attr['sigma'],self.sigmas) 
                assert (g[el].chunks==self.ChunkList[-1]), "chunks are not consistent through the dataset %s %s"%(g[el].chunks,self.ChunkList[-1])
                assert (g[el].shape==self.shape), "shape is not consistent"
                tmplist.append(g[el])
            
            self.D.append(tmplist)
    
    def _getFileIndex(self,key):
        start,stop=sliceToRoi(key,self.shape)
        diff=numpy.array(stop)-numpy.array(start)
        maxError=sys.maxint
        indexFile=0
        for i,chunks in enumerate(self.ChunkList):
               cs = numpy.array(chunks)
        
               error = numpy.sum(numpy.abs(diff -cs))
               if error<maxError:
                   indexFile = i
                   maxError = error
        
        return indexFile
    
                
                
           
        
        
