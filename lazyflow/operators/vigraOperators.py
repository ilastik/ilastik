import numpy, vigra, h5py

from lazyflow.graph import *
import gc
from lazyflow import roi
import copy

from operators import OpArrayPiper, OpMultiArrayPiper

from generic import OpMultiArrayStacker




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
                    #print "########################", inSlot.shape, inSlot.axistags
                    if cnt >= start[-1] and start[-1] + written < stop[-1]:
                        #print "OOOOOOOOOOOOOOOOO1", i, cnt, start[-1], stop[-1], result[..., cnt].shape
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

                        #print "OOOOOOOOOOOOOO2", i, cnt, start[-1],stop[-1],inSlot.shape[-1], begin, end, key_, result.shape, result[...,written:written+end-begin].shape, written,written+end-begin
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
        
        self.multi = Op20ToMulti(self.graph)
        
        
        self.stacker.inputs["Images"].connect(self.multi.outputs["Outputs"])
        
        
    def notifyConnectAll(self):
        if self.inputs["Scales"].connected() and self.inputs["Matrix"].connected():
            
            self.stacker.inputs["Images"].disconnect()
            self.scales = self.inputs["Scales"].value
            self.matrix = self.inputs["Matrix"].value 
            
            dimCol = len(self.scales)
            dimRow = len(self.matrix)
            for i in range(dimRow):
                if not dimCol == len(self.matrix[i]):
                    return
    
            oparray = []
            for j in range(dimCol):
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
                oparray[i].append(OpHessianOfGaussian(self.graph))
                oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                oparray[i][j].inputs["sigma"].setValue(self.scales[j])
            i = 3
            for j in range(dimCol):
                oparray[i].append(OpHessianOfGaussianEigenvalues(self.graph))
                oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                oparray[i][j].inputs["scale"].setValue(self.scales[j])
            
            self.outputs["ArrayOfOperators"]= oparray
            
            for i in range(dimRow):
                for j, val in enumerate(self.matrix[i]):
                    print (i*dimRow+j)
                    if val:
                        self.multi.inputs["Input%02d" %(i*dimRow+j)].connect(oparray[i][j].outputs["Output"])
                    else:
                        self.multi.inputs["Input%02d" %(i*dimRow+j)].disconnect()
            
            index = len(self.source.outputs["Output"].shape) - 1
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






class OpBaseVigraFilter(OpArrayPiper):
    inputSlots = [InputSlot("Input"), InputSlot("sigma", stype = "float")]
    outputSlots = [OutputSlot("Output")]    
    
    name = "OpBaseVigraFilter"
    category = "Vigra filter"
    
    vigraFilter = None
    outputDtype = numpy.float32 
    inputDtype = numpy.float32
    supportsOut = True
    
    def __init__(self, graph):
        OpArrayPiper.__init__(self, graph)
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
            
        largestSigma = sigma*3.5 #ensure enough context for the vigra operators
                
        shape = self.outputs["Output"].shape
        

        subkey = key[0:-1]

        oldstart, oldstop = roi.sliceToRoi(key, shape)
        start, stop = roi.sliceToRoi(subkey,shape[:-1])
        newStart, newStop = roi.extendSlice(start, stop, shape[:-1], largestSigma)
        
        
        
        readKey = roi.roiToSlice(newStart, newStop)
        
        writeNewStart = start - newStart
        writeNewStop = writeNewStart +  stop - start
        
        if (writeNewStart == 0).all() and (newStop == writeNewStop).all():
            fullResult = True
        else:
            fullResult = False
        
        writeKey = roi.roiToSlice(writeNewStart, writeNewStop)
                            
        channelsPerChannel = self.resultingChannels()
        
        axistags = self.inputs["Input"].axistags
        
        i2 = 0          
        for i in range(int(numpy.floor(1.0 * oldstart[-1]/channelsPerChannel)),int(numpy.ceil(1.0 * oldstop[-1]/channelsPerChannel))):
            
            req = self.inputs["Input"][readKey + (slice(i,i+1,None),)].allocate()
            t = req.wait()
            t = numpy.require(t, dtype=self.inputDtype)
            
            t = t.view(vigra.VigraArray)
            t.axistags = copy.copy(axistags)
            t = t.squeeze() #vigra.VigraArray(t, dtype = self.inputDtype,axistags = copy.copy(axistags))

            sourceBegin = 0
            if oldstart[-1] > i * channelsPerChannel:
                sourceBegin = oldstart[-1] - i * channelsPerChannel
            sourceEnd = channelsPerChannel
            if oldstop[-1] < (i+1) * channelsPerChannel:
                sourceEnd = channelsPerChannel - ((i+1) * channelsPerChannel - oldstop[-1])
            
            destBegin = i2
            destEnd = i2 + sourceEnd - sourceBegin
            
            if channelsPerChannel>1:                    
                resultArea = result[...,destBegin:destEnd]
            else:
                resultArea = result[...,i2]

            if not fullResult or not self.supportsOut:
                temp = self.vigraFilter(t, **kwparams)
                if channelsPerChannel>1:
                    try:
                        resultArea[:] = temp[writeKey + (slice(sourceBegin,sourceEnd,None),)]
                    except:
                        print "ERROR: destination and request shapes differ !", resultArea.shape, temp.shape, writeKey, destBegin, destEnd, sourceBegin, sourceEnd
                else:
                    resultArea[:] = temp[writeKey]
            else:
                #resultArea = resultArea.view(vigra.VigraArray)
                #resultArea.axistags = copy.copy(axistags)
                
                self.vigraFilter(t,sigma, out = resultArea)
            i2 += channelsPerChannel

            
    def notifyConnectAll(self):
        numChannels  = 1
        inputSlot = self.inputs["Input"]
        if inputSlot.axistags.axisTypeCount(vigra.AxisType.Channels) > 0:
            channelIndex = self.inputs["Input"].axistags.channelIndex
            numChannels = self.inputs["Input"].shape[channelIndex]
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

    def resultingChannels(self):
        raise RuntimeError('resultingChannels() not implemented')
        

#difference of Gaussians
def differenceOfGausssians(image,sigma0, sigma1, out = None):
    """ difference of gaussian function"""        
    return (vigra.filters.gaussianSmoothing(image,sigma0)-vigra.filters.gaussianSmoothing(image,sigma1))


def firstHessianOfGaussianEigenvalues(image, sigmas):
    return vigra.filters.hessianOfGaussianEigenvalues(image, sigmas)[...,0]

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
    inputSlots = [InputSlot("Input"), InputSlot("sigma0", stype = "float"), InputSlot("sigma1", stype = "float")]
    
    def resultingChannels(self):
        return 1

class OpCoherenceOrientation(OpBaseVigraFilter):
    name = "CoherenceOrientationOfStructureTensor"
    vigraFilter = staticmethod(coherenceOrientationOfStructureTensor)
    outputDtype = numpy.float32 
    inputSlots = [InputSlot("Input"), InputSlot("sigma0", stype = "float"), InputSlot("sigma1", stype = "float")]
    
    def resultingChannels(self):
        return 2    


class OpGaussianSmoothing(OpBaseVigraFilter):
    name = "GaussianSmoothing"
    vigraFilter = staticmethod(vigra.filters.gaussianSmoothing)
    outputDtype = numpy.float32 
        

    def resultingChannels(self):
        return 1

    
    def notifyConnectAll(self):
        OpBaseVigraFilter.notifyConnectAll(self)

    
class OpHessianOfGaussianEigenvalues(OpBaseVigraFilter):
    name = "HessianOfGaussianEigenvalues"
    vigraFilter = staticmethod(vigra.filters.hessianOfGaussianEigenvalues)
    outputDtype = numpy.float32 
    inputSlots = [InputSlot("Input"), InputSlot("scale", stype = "float")]

    def resultingChannels(self):
        temp = self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space)
        return temp



class OpHessianOfGaussianEigenvaluesFirst(OpBaseVigraFilter):
    name = "First Eigenvalue of Hessian Matrix"
    vigraFilter = staticmethod(firstHessianOfGaussianEigenvalues)
    outputDtype = numpy.float32 
    supportsOut = False
    inputSlots = [InputSlot("Input"), InputSlot("scale", stype = "float")]

    def resultingChannels(self):
        return 1



class OpHessianOfGaussian(OpBaseVigraFilter):
    name = "HessianOfGaussian"
    vigraFilter = staticmethod(vigra.filters.hessianOfGaussian)
    outputDtype = numpy.float32 

    def resultingChannels(self):
        temp = self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space)*(self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space) + 1) / 2
        return temp
    
class OpGaussianGradientMagnitude(OpBaseVigraFilter):
    name = "GaussianGradientMagnitude"
    vigraFilter = staticmethod(vigra.filters.gaussianGradientMagnitude)
    outputDtype = numpy.float32 

    def resultingChannels(self):
        
        return 1

class OpLaplacianOfGaussian(OpBaseVigraFilter):
    name = "LaplacianOfGaussian"
    vigraFilter = staticmethod(vigra.filters.laplacianOfGaussian)
    outputDtype = numpy.float32 
    supportsOut = False
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
        
        
        self.outputs["Image"]._dtyoe = d.dtype
        self.outputs["Image"]._shape = d.shape
        
        if len(d.shape) == 2:
            axistags=vigra.AxisTags(vigra.AxisInfo('x',vigra.AxisType.Space),vigra.AxisInfo('y',vigra.AxisType.Space))   
        else:
            axistags= vigra.VigraArray.defaultAxistags(len(d.shape))
        self.outputs["Image"]._axistags=axistags
            
        f.close()
        
    def getOutSlot(self, slot, key, result):
        filename = self.inputs["Filename"].value
        hdf5Path = self.inputs["hdf5Path"].value
        
        f = h5py.File(filename, 'r')
    
        d = f[hdf5Path]
        
        result[:] = d[key]
        f.close()


        
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