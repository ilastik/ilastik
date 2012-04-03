import numpy, vigra, h5py
import traceback
from lazyflow.graph import *
import gc
from lazyflow import roi
import copy

from operators import OpArrayPiper, OpMultiArrayPiper

from generic import OpMultiArrayStacker, getSubKeyWithFlags, popFlagsFromTheKey

import math

from threading import Lock
from lazyflow.roi import roiToSlice



class OpXToMulti(Operator):

    inputSlots = []
    outputSlots = []
        
    def setupOutputs(self):
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

    def getSubOutSlot(self, slots, indexes, key, result):
        i = 0
        for sname in sorted(self.inputs.keys()):
            slot = self.inputs[sname]
            if slot.connected():
                if i == indexes[0]:
                    result[:] = slot[key].allocate().wait()
                    break
                i += 1                

    def propagateDirty(self, islot, roi):
        i = 0
        for sname in sorted(self.inputs.keys()):
            slot = self.inputs[sname]
            if slot == islot:
              self.outputs["Outputs"][i].setDirty(roi)
              break
            if slot.connected():
                self.outputs["Outputs"][i]._dtype = slot.dtype
                self.outputs["Outputs"][i]._axistags = copy.copy(slot.axistags)
                self.outputs["Outputs"][i]._shape = slot.shape
                i += 1       
 

class Op5ToMulti(OpXToMulti):
    name = "5 Elements to Multislot"
    category = "Misc"

    inputSlots = []
    for i in xrange(5):
        inputSlots.append(InputSlot("Input%.1d"%(i), optional = True))
    outputSlots = [MultiOutputSlot("Outputs")]
    

class Op10ToMulti(OpXToMulti):
    name = "10 Elements to Multislot"
    category = "Misc"

    inputSlots = []
    for i in xrange(10):
        inputSlots.append(InputSlot("Input%.1d"%(i), optional = True))
    outputSlots = [MultiOutputSlot("Outputs")]


class Op20ToMulti(OpXToMulti):
    name = "20 Elements to Multislot"
    category = "Misc"

    inputSlots = []
    for i in xrange(20):
        inputSlots.append(InputSlot("Input%.2d"%(i), optional = True))
    outputSlots = [MultiOutputSlot("Outputs")]




class Op50ToMulti(OpXToMulti):
    
    name = "N Elements to Multislot"
    category = "Misc"

    inputSlots = []
    for i in xrange(50):
        inputSlots.append(InputSlot("Input%.2d"%(i), optional = True))
    outputSlots = [MultiOutputSlot("Outputs")]

                


class OpPixelFeatures(Operator):
    name="OpPixelFeatures"
    category = "Vigra filter"
    
    inputSlots = [InputSlot("Input"), InputSlot("Matrix"), InputSlot("Scales")]
    outputSlots = [OutputSlot("Output"), OutputSlot("ArrayOfOperators")]
    
    def __init__(self, parent):
        Operator.__init__(self, parent)
        self.oparray = []
        
        self.stacker = OpMultiArrayStacker(self)
        
        self.multi = Op50ToMulti(self)
        
        
        self.stacker.inputs["Images"].connect(self.multi.outputs["Outputs"])
        
        
    def setupOutputs(self):

        # disconnect previous operators
        for r in self.oparray:
          for o in r:
            o.disconnect()

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
                oparray[i].append(OpGaussianSmoothing(self))
                oparray[i][j].inputs["Input"].connect(self.inputs["Input"])
                oparray[i][j].inputs["sigma"].setValue(self.scales[j])
            i = 1
            for j in range(dimCol):
                oparray[i].append(OpLaplacianOfGaussian(self))
                oparray[i][j].inputs["Input"].connect(self.inputs["Input"])
                oparray[i][j].inputs["scale"].setValue(self.scales[j])
            i = 2
            for j in range(dimCol):
                oparray[i].append(OpStructureTensorEigenvalues(self))
                oparray[i][j].inputs["Input"].connect(self.inputs["Input"])
                oparray[i][j].inputs["innerScale"].setValue(self.scales[j])
                oparray[i][j].inputs["outerScale"].setValue(self.scales[j]*0.5)
            i = 3
            for j in range(dimCol):   
                oparray[i].append(OpHessianOfGaussianEigenvalues(self))
                oparray[i][j].inputs["Input"].connect(self.inputs["Input"])
                oparray[i][j].inputs["scale"].setValue(self.scales[j])
            
            i= 4
            for j in range(dimCol): 
                oparray[i].append(OpGaussianGradientMagnitude(self))
                oparray[i][j].inputs["Input"].connect(self.inputs["Input"])
                oparray[i][j].inputs["sigma"].setValue(self.scales[j])
            
            i= 5
            for j in range(dimCol): 
                oparray[i].append(OpDifferenceOfGaussians(self))
                oparray[i][j].inputs["Input"].connect(self.inputs["Input"])
                oparray[i][j].inputs["sigma0"].setValue(self.scales[j])            
                oparray[i][j].inputs["sigma1"].setValue(self.scales[j]*0.66)
            

                
            
            self.oparray = oparray

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
                fakeOp = OpGaussianSmoothing(self)
                fakeOp.inputs["Input"].connect(self.inputs["Input"])
                fakeOp.inputs["sigma"].setValue(10)
                self.multi.inputs["Input%02d" %(i*dimRow+j+1)].connect(fakeOp.outputs["Output"])
                self.multi.inputs["Input%02d" %(i*dimRow+j+1)].disconnect() 
                self.stacker.outputs["Output"].shape=()
                return
         
            
            index = len(self.inputs["Input"]) - 1
            self.stacker.inputs["AxisFlag"].setValue('c')
            self.stacker.inputs["AxisIndex"].setValue(self.inputs["Input"]._axistags.index('c'))
            self.stacker.inputs["Images"].connect(self.multi.outputs["Outputs"])
            
    
    def getInnerInputs(self):
        inputs = {}
        inputs["Input"] = self.source.inputs["Input"]
        return inputs
        
    def getInnerOutputs(self):
        outputs = {}
        outputs["Output"] = self.stacker.outputs["Output"]
        return outputs




class OpPixelFeaturesPresmoothed(Operator):
    name="OpPixelFeaturesPresmoothed"
    name="OpPixelFeatures"
    category = "Vigra filter"
    
    inputSlots = [InputSlot("Input"), InputSlot("Matrix"), InputSlot("Scales")]
    outputSlots = [OutputSlot("Output"), OutputSlot("ArrayOfOperators")]
    
    def __init__(self, parent):         
        Operator.__init__(self, parent)   
        self.source = OpArrayPiper(self)
        self.source.inputs["Input"].connect(self.inputs["Input"])        
                
        self.stacker = OpMultiArrayStacker(self)
        
        self.multi = Op50ToMulti(self)
        
        self.stacker.inputs["Images"].connect(self.multi.outputs["Outputs"])
        
     
        
    def setupOutputs(self):
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
    
            self.newScales = []
            for j in range(dimCol):
                destSigma = 1.0
                if self.scales[j] > destSigma:
                    self.newScales.append(destSigma)
                else:
                    self.newScales.append(self.scales[j])
                    
                print "Replacing scale %f with new scale %f" %(self.scales[j], self.newScales[j])
                
    
            i = 0
            for j in range(dimCol):
                oparray[i].append(OpGaussianSmoothing(self))
                oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                oparray[i][j].inputs["sigma"].setValue(self.newScales[j])
            i = 1
            for j in range(dimCol):
                oparray[i].append(OpLaplacianOfGaussian(self))
                oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                oparray[i][j].inputs["scale"].setValue(self.newScales[j])
            i = 2
            for j in range(dimCol):
                oparray[i].append(OpStructureTensorEigenvalues(self))
                oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                oparray[i][j].inputs["innerScale"].setValue(self.newScales[j])
                oparray[i][j].inputs["outerScale"].setValue(self.newScales[j]*0.5)
            i = 3
            for j in range(dimCol):   
                oparray[i].append(OpHessianOfGaussianEigenvalues(self))
                oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                oparray[i][j].inputs["scale"].setValue(self.newScales[j])
            
            i= 4
            for j in range(dimCol): 
                oparray[i].append(OpGaussianGradientMagnitude(self))
                oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                oparray[i][j].inputs["sigma"].setValue(self.newScales[j])
            
            i= 5
            for j in range(dimCol): 
                oparray[i].append(OpDifferenceOfGaussians(self))
                oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                oparray[i][j].inputs["sigma0"].setValue(self.newScales[j])            
                oparray[i][j].inputs["sigma1"].setValue(self.newScales[j]*0.66)
            

                
            
            
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
                        print "connected  Input%02d of self.multi" %(i*dimRow+j)
            
            #additional connection with FakeOperator
            if (self.matrix==0).all():
                fakeOp = OpGaussianSmoothing(self)
                fakeOp.inputs["Input"].connect(self.source.outputs["Output"])
                fakeOp.inputs["sigma"].setValue(10)
                self.multi.inputs["Input%02d" %(i*dimRow+j+1)].connect(fakeOp.outputs["Output"])
                self.multi.inputs["Input%02d" %(i*dimRow+j+1)].disconnect() 
                self.stacker.outputs["Output"]._shape=()
                return
         
            
            index = len(self.source.outputs["Output"].shape) - 1
            self.stacker.inputs["AxisFlag"].setValue('c')
            self.stacker.inputs["AxisIndex"].setValue(self.source.outputs["Output"]._axistags.index('c'))
            self.stacker.inputs["Images"].connect(self.multi.outputs["Outputs"])


            self.maxSigma = 0
            #determine maximum sigma
            for i in range(dimRow):
                for j in range(dimCol):
                    val=self.matrix[i,j]
                    if val:
                        self.maxSigma = max(self.scales[j],self.maxSigma)
    
            self.featureOps = oparray
    
                
            self.outputs["Output"]._dtype = numpy.float32            
            self.outputs["Output"]._axistags = self.stacker.outputs["Output"]._axistags            
            self.outputs["Output"]._shape = self.stacker.outputs["Output"]._shape            
    
    def execute(self, slot, rroi, result): 
        key = rroi.toSlice()
        if slot == self.outputs["Output"]:
            cnt = 0
            written = 0
            start = rroi.start
            stop = rroi.stop
            assert (stop<=self.outputs["Output"].shape).all()
            flag = 'c'
            __channelAxis=self.inputs["Input"].axistags.index('c')
            axisindex = __channelAxis
            oldkey = list(key)
            oldkey.pop(axisindex)
            
            
            
            
            
            
            __inShape  = self.inputs["Input"].shape
            
            __shape = self.outputs["Output"].shape
            
            __axistags = self.inputs["Input"].axistags

            result = result.view(vigra.VigraArray)
            result.axistags = copy.copy(__axistags)
            
            
            __hasTimeAxis = self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Time)
            __timeAxis=self.inputs["Input"].axistags.index('t')
    
            __subkey = popFlagsFromTheKey(key,__axistags,'c')
            __subshape=popFlagsFromTheKey(__shape,__axistags,'c')
            __at2 = copy.copy(__axistags)
            __at2.dropChannelAxis()
            __subshape=popFlagsFromTheKey(__subshape,__at2,'t')
            __subkey = popFlagsFromTheKey(__subkey,__at2,'t')
            
            __oldstart, __oldstop = roi.sliceToRoi(key, __shape)
            
            __start, __stop = roi.sliceToRoi(__subkey,__subkey)
            __maxSigma = max(0.7,self.maxSigma)
        
            __newStart, __newStop = roi.extendSlice(__start, __stop, __subshape, __maxSigma, window = 3.5)
            
            __vigOpSourceStart, __vigOpSourceStop = roi.extendSlice(__start, __stop, __subshape, 0.7, window = 2)
            
            __vigOpSourceStart = roi.TinyVector(__vigOpSourceStart - __newStart)
            __vigOpSourceStop = roi.TinyVector(__vigOpSourceStop - __newStart)
            
            __readKey = roi.roiToSlice(__newStart, __newStop)
        
        
            __writeNewStart = __start - __newStart
            __writeNewStop = __writeNewStart +  __stop - __start
            
            
            treadKey=list(__readKey)
            
            if __hasTimeAxis:
                if __timeAxis < __channelAxis:
                    treadKey.insert(__timeAxis, key[__timeAxis])
                else:
                    treadKey.insert(__timeAxis-1, key[__timeAxis])
            treadKey.insert(__channelAxis, slice(None,None,None))
            treadKey=tuple(treadKey)
            
            req = self.inputs["Input"][treadKey].allocate()
            
            __sourceArray = req.wait()

            req.destination = None
            if __sourceArray.dtype is not numpy.float32:
                __sourceArrayF = __sourceArray.astype(numpy.float32)
                __sourceArray.resize((1,))
                del __sourceArray
                __sourceArray = __sourceArrayF
            __sourceArrayV = __sourceArray.view(vigra.VigraArray) 
            __sourceArrayV.axistags =  copy.copy(__axistags)

            
            
            
            
            dimCol = len(self.scales)
            dimRow = self.matrix.shape[0]


            sourceArraysForSigmas = [None]*dimCol

            #connect individual operators
            for j in range(dimCol):
                hasScale = False
                for i in range(dimRow):
                    if self.matrix[i,j]:
                        hasScale = True
                if not hasScale:
                    continue
                destSigma = 1.0
                if self.scales[j] > destSigma:
                    tempSigma = math.sqrt(self.scales[j]**2 - destSigma**2)
                else:
                    destSigma = 0.0
                    tempSigma = self.scales[j]
                __vigOpSourceShape = list(__vigOpSourceStop - __vigOpSourceStart)
                if __hasTimeAxis:

                    if __timeAxis < __channelAxis:
                        __vigOpSourceShape.insert(__timeAxis, ( __oldstop - __oldstart)[__timeAxis])
                    else:
                        __vigOpSourceShape.insert(__timeAxis-1, ( __oldstop - __oldstart)[__timeAxis]) 
                    __vigOpSourceShape.insert(__channelAxis, __inShape[__channelAxis])
                                        
                    sourceArraysForSigmas[j] = numpy.ndarray(tuple(__vigOpSourceShape),numpy.float32)
                    for i,vsa in enumerate(__sourceArrayV.timeIter()):
                        droi = (tuple(__vigOpSourceStart._asint()), tuple(__vigOpSourceStop._asint()))
                        tmp_key = getAllExceptAxis(len(sourceArraysForSigmas[j].shape),__timeAxis, i)
                        sourceArraysForSigmas[j][tmp_key] = vigra.filters.gaussianSmoothing(vsa,tempSigma, roi = droi, window_size = 3.5 )
                else:
                    droi = (tuple(__vigOpSourceStart._asint()), tuple(__vigOpSourceStop._asint()))
                    #print droi, __sourceArray.shape, tempSigma,self.scales[j]
                    sourceArraysForSigmas[j] = vigra.filters.gaussianSmoothing(__sourceArrayV, sigma = tempSigma, roi = droi, window_size = 3.5)                         
                    #__sourceArrayForSigma = __sourceArrayForSigma.view(numpy.ndarray)

            del __sourceArrayV
            __sourceArray.resize((1,), refcheck = False)
            del __sourceArray
            
            #connect individual operators
            for i in range(dimRow):
                for j in range(dimCol):
                    val=self.matrix[i,j]
                    if val:
                        vop= self.featureOps[i][j]
                        oslot = vop.outputs["Output"]
                        req = None
                        inTagKeys = [ax.key for ax in oslot._axistags]
                        if flag in inTagKeys:
                            slices = oslot._shape[axisindex]
                            if cnt + slices >= start[axisindex] and start[axisindex]-cnt<slices and start[axisindex]+written<stop[axisindex]:
                                begin = 0
                                if cnt < start[axisindex]:
                                    begin = start[axisindex] - cnt
                                end = slices
                                if cnt + end > stop[axisindex]:
                                    end -= cnt + end - stop[axisindex]
                                key_ = copy.copy(oldkey)
                                key_.insert(axisindex, slice(begin, end, None))
                                reskey = [slice(None, None, None) for x in range(len(result.shape))]
                                reskey[axisindex] = slice(written, written+end-begin, None)
                                
                                destArea = result[tuple(reskey)]
                                oslot.operator.getOutSlot(oslot,tuple(key_),destArea, sourceArray = sourceArraysForSigmas[j])
                                written += end - begin
                            cnt += slices
                        else:
                            if cnt>=start[axisindex] and start[axisindex] + written < stop[axisindex]:
                                reskey = copy.copy(oldkey)
                                reskey.insert(axisindex, written)
                                #print "key: ", key, "reskey: ", reskey, "oldkey: ", oldkey
                                #print "result: ", result.shape, "inslot:", inSlot.shape
                                
                                destArea = result[tuple(reskey)]
                                oslot.operator.getOutSlot(oslot,tuple(oldkey),destArea, sourceArray = sourceArraysForSigmas[j])
                                written += 1
                            cnt += 1

    
            for i in range(len(sourceArraysForSigmas)):
                if sourceArraysForSigmas[i] is not None:
                    try:
                        sourceArraysForSigmas[i].resize((1,))
                    except:
                        sourceArraysForSigmas[i] = None




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
    
    def __init__(self, parent):
        OpArrayPiper.__init__(self, parent)
        
    def getOutSlot(self, slot, key, result, sourceArray = None):
        kwparams = {}        
        for islot in self.inputs.values():
            if islot.name != "Input":
                kwparams[islot.name] = islot.value
        
        if self.inputs.has_key("sigma"):
            sigma = self.inputs["sigma"].value
        elif self.inputs.has_key("scale"):
            sigma = self.inputs["scale"].value
        elif self.inputs.has_key("sigma0"):
            sigma = self.inputs["sigma0"].value
        elif self.inputs.has_key("innerScale"):
            sigma = self.inputs["innerScale"].value

        windowSize = 4.0
        if self.supportsWindow:
            kwparams['window_size']=self.window_size
            windowSize = self.window_size
            
        largestSigma = sigma #ensure enough context for the vigra operators
                
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
        newStart, newStop = roi.extendSlice(start, stop, subshape, largestSigma, window = windowSize)
        readKey = roi.roiToSlice(newStart, newStop)
        
        writeNewStart = start - newStart
        writeNewStop = writeNewStart +  stop - start
        
        if (writeNewStart == 0).all() and (newStop == writeNewStop).all():
            fullResult = True
        else:
            fullResult = False
        
        writeKey = roi.roiToSlice(writeNewStart, writeNewStop)
        writeKey = list(writeKey)
        if timeAxis < channelAxis:
            writeKey.insert(channelAxis-1, slice(None,None,None))
        else:
            writeKey.insert(channelAxis, slice(None,None,None))
        writeKey = tuple(writeKey)         
                
        channelsPerChannel = self.resultingChannels()
        
        if self.supportsRoi is False and largestSigma > 5:
            print "WARNING: operator", self.name, "does not support roi !!"
        
        
        i2 = 0          
        for i in range(int(numpy.floor(1.0 * oldstart[channelAxis]/channelsPerChannel)),int(numpy.ceil(1.0 * oldstop[channelAxis]/channelsPerChannel))):
            treadKey=list(readKey)
            
            if hasTimeAxis:
                if channelAxis > timeAxis:
                    treadKey.insert(timeAxis, key[timeAxis])
                else:
                    treadKey.insert(timeAxis-1, key[timeAxis])
            treadKey.insert(channelAxis, slice(i,i+1,None))
            treadKey=tuple(treadKey)
            
            if sourceArray is None:
                req = self.inputs["Input"][treadKey].allocate()
                t = req.wait()
            else:
                #t = sourceArray[...,i:i+1]
                t = sourceArray[getAllExceptAxis(len(treadKey),channelAxis,slice(i,i+1,None) )]
                req = self.inputs["Input"][treadKey].allocate()
                t2 = req.wait()
                
                t3 = t.view(numpy.ndarray)
                #assert (t3==t2).all()
                #assert t.shape == t2.shape, "Vigra Filter %r: shape difference !! sigm = %f, window = %r, %r, %r" %( self.name, largestSigma, windowSize,  t.shape, t2.shape)
                
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

            i2 += destEnd-destBegin
            
            supportsOut = self.supportsOut
            if (destEnd-destBegin != channelsPerChannel):
                supportsOut = False

            supportsOut= False #disable for now due to vigra crashes!
            for step,image in enumerate(t.timeIter()):   
                nChannelAxis = channelAxis - 1
                
                if timeAxis > channelAxis or not hasTimeAxis:
                    nChannelAxis = channelAxis 
                twriteKey=getAllExceptAxis(image.ndim, nChannelAxis, slice(sourceBegin,sourceEnd,None))

                if hasTimeAxis > 0:
                    tresKey  = getAllExceptAxis(resultArea.ndim, timeAxis, step)
                else:
                    tresKey  = slice(None, None,None)
                
                #print tresKey, twriteKey, resultArea.shape, temp.shape
                vres = resultArea[tresKey]
                if supportsOut:
                    print "SSSSSSSSSSSSSSSSSSS"
                    if self.supportsRoi:
                        vroi = (tuple(writeNewStart._asint()), tuple(writeNewStop._asint()))
                        try:
                            vres = vres.view(vigra.VigraArray)
                            vres.axistags = copy.copy(image.axistags)
                            print "FAST LANE", self.name, vres.shape, image[twriteKey].shape, vroi
                            temp = self.vigraFilter(image[twriteKey], roi = vroi,out=vres, **kwparams)
                        except:
                            print self.name, image.shape, vroi, kwparams
                    else:
                        try:
                            temp = self.vigraFilter(image, **kwparams)
                        except:
                            print self.name, image.shape, vroi, kwparams
                        temp=temp[writeKey]
                else:
                    if self.supportsRoi:
                        vroi = (tuple(writeNewStart._asint()), tuple(writeNewStop._asint()))
                        try:                            
                            temp = self.vigraFilter(image, roi = vroi, **kwparams)
                        except Exception, e:
                            print "EXCEPT 2.1", self.name, image.shape, vroi, kwparams
                            traceback.print_exc(e)
                            sys.exit(1)
                    else:
                        try:
                            temp = self.vigraFilter(image, **kwparams)
                        except Exception, e:
                            print "EXCEPT 2.2", self.name, image.shape, kwparams
                            traceback.print_exc(e)
                            sys.exit(1)
                        temp=temp[writeKey]
    

                    try:
                        vres[:] = temp[twriteKey]
                    except:
                        print "EXCEPT3", vres.shape, temp.shape, twriteKey
                        print "EXCEPT3", resultArea.shape,  tresKey, twriteKey
                        print "EXCEPT3", step, t.shape, timeAxis
                        assert 1==2
                

            
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


def firstHessianOfGaussianEigenvalues(image, **kwargs):
    return vigra.filters.hessianOfGaussianEigenvalues(image, **kwargs)[...,0:1]

def coherenceOrientationOfStructureTensor(image,sigma0, sigma1, window_size, out = None):
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
    
    st=vigra.filters.structureTensor(image, sigma0, sigma1, window_size = window_size)
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
    supportsRoi = False
    inputSlots = [InputSlot("Input"), InputSlot("sigma0", stype = "float"), InputSlot("sigma1", stype = "float")]
    
    def resultingChannels(self):
        return 2    


class OpGaussianSmoothing(OpBaseVigraFilter):
    name = "GaussianSmoothing"
    vigraFilter = staticmethod(vigra.filters.gaussianSmoothing)
    outputDtype = numpy.float32 
    supportsRoi = True
    supportsWindow = True
    supportsOut = True    

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
    supportsOut = True    
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
    supportsOut = True    
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
    supportsOut = True    
  
    def resultingChannels(self):
        temp = self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space)*(self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space) + 1) / 2
        return temp
    
class OpGaussianGradientMagnitude(OpBaseVigraFilter):
    name = "GaussianGradientMagnitude"
    vigraFilter = staticmethod(vigra.filters.gaussianGradientMagnitude)
    outputDtype = numpy.float32 
    supportsRoi = True
    supportsWindow = True
    supportsOut = True    

    def resultingChannels(self):        
        return 1

class OpLaplacianOfGaussian(OpBaseVigraFilter):
    name = "LaplacianOfGaussian"
    vigraFilter = staticmethod(vigra.filters.laplacianOfGaussian)
    outputDtype = numpy.float32 
    supportsOut = True
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
        filename = self.filename = os.path.dirname(lazyflow.__file__)+"/../tests/ostrich.jpg"
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
        elif len(d.shape) == 3:
            if(d.shape[2]>3):
              axistags=vigra.AxisTags( vigra.AxisInfo('x',vigra.AxisType.Space),vigra.AxisInfo('y',vigra.AxisType.Space), vigra.AxisInfo('z', vigra.AxisType.Space))   
            else:
              axistags=vigra.AxisTags( vigra.AxisInfo('x',vigra.AxisType.Space),vigra.AxisInfo('y',vigra.AxisType.Space), vigra.AxisInfo('c', vigra.AxisType.Channels))   

        elif len(d.shape) == 4:
            axistags=vigra.AxisTags( vigra.AxisInfo('x',vigra.AxisType.Space),vigra.AxisInfo('y',vigra.AxisType.Space), vigra.AxisInfo('z', vigra.AxisType.Space), vigra.AxisInfo('c', vigra.AxisType.Channels))   
        elif len(d.shape) == 5:
            axistags=vigra.AxisTags(vigra.AxisInfo('t',vigra.AxisType.Time), vigra.AxisInfo('x',vigra.AxisType.Space),vigra.AxisInfo('y',vigra.AxisType.Space), vigra.AxisInfo('z', vigra.AxisType.Space), vigra.AxisInfo('c', vigra.AxisType.Channels))   
            print "OpH5Reader 5-Axistags", axistags
        else:
            axistags= vigra.VigraArray.defaultAxistags(len(d.shape))
            print "OpH5Reader DEFAULT AXISTAGS: ", axistags
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
    
    def __init__(self, parent):
        Operator.__init__(self, parent)
        
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
    

class OpGrayscaleInverter(Operator):
    name = "Grayscale Inversion Operator"
    category = "" #Pls set some standard categories

    inputSlots = [InputSlot("input", stype = "array")]
    outputSlots = [OutputSlot("output")]

    def notifyConnectAll(self):

        inputSlot = self.inputs["input"]

        oslot = self.outputs["output"]
        oslot._shape = inputSlot.shape
        oslot._dtype = inputSlot.dtype
        oslot._axistags = copy.copy(inputSlot.axistags)

    def getOutSlot(self, slot, key, result):
        
        #this assumes that the last dimension is the channel. 
        image = self.inputs["input"][:].allocate().wait()
        result[:,:,:,:] = 255-image[:,:,:,:]

class OpToUint8(Operator):
    name = "UInt8 Conversion Operator"
    category = "" #Pls set some standard categories
    
    inputSlots = [InputSlot("input", stype = "array")]
    outputSlots = [OutputSlot("output")]
    
    
    def notifyConnectAll(self):

        inputSlot = self.inputs["input"]

        oslot = self.outputs["output"]

        oslot._shape = inputSlot.shape
        oslot._dtype = numpy.uint8
        oslot._axistags = copy.copy(inputSlot.axistags)

        def getOutSlot(self, slot, key, result):
        
            image = self.inputs["input"][:].allocate().wait()
            result[:] = image.numpy.astype('uint8')


class OpRgbToGraysacle(Operator):
    name = "Convert RGB Images to Grayscale"
    category = "" 

    inputSlots = [InputSlot("input", stype = "array")]
    outputSlots = [OutputSlot("output")]

    def setupOutputs(self):

        inputSlot = self.inputs["input"]

        oslot = self.outputs["output"]
        oslot._shape = inputSlot.shape[:-1] + (1,)
        oslot._dtype = inputSlot.dtype
        oslot._axistags = copy.copy(inputSlot.axistags)
    
    def execute(self, slot, roi, result):
        
        
        image = self.inputs["input"](roi).wait()
        channelKey = self.outputs["output"]._axistags.channelIndex
        if image.shape[channelKey] > 1:
            #this assumes that the last dimension is the channel. 
            result[:,:,:,0] = (numpy.round(0.299*image[:,:,:,0] + 0.587*image[:,:,:,1] + 0.114*image[:,:,:,2])).astype(int)
        else:
            result[:] = image
        return result
                
           
        
        
