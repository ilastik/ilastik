from lazyflow.graph import Operator,InputSlot,OutputSlot
from lazyflow.operators.obsolete.valueProviders import OpArrayPiper
from lazyflow.helpers import AxisIterator
from lazyflow.operators.obsolete.generic import OpMultiArrayStacker
from lazyflow.operators.obsolete.vigraOperators import Op50ToMulti
import numpy,vigra
from math import sqrt
from functools import partial

class OpBaseVigraFilter(OpArrayPiper):
    
    inputSlots = []
    outputSlots = [OutputSlot("Output")]
    
    name = 'OpBaseVigraFilter'
    category = 'Image Filter'
    
    vigraFilter = None
    windowSize = 4.0
    
    def __init__(self, parent):
        OpArrayPiper.__init__(self, parent)
        self.iterator = None
        
    def resultingChannels(self):
        pass
    
    def setupFilter(self):
        pass
    
    def setupIterator(self,source,result):
        self.iterator = AxisIterator(source,'spatialc',result,'spatialc',[(),(1,1,1,1,self.resultingChannels())])
    
    def setupOutputs(self):
        
        inputSlot = self.inputs["Input"]
        outputSlot = self.outputs["Output"]
        channelNum = self.resultingChannels()
        outputSlot.copyConfig(inputSlot)
        outputSlot.setShapeAtAxisTo('c', channelNum)
        
    def execute(self,slot,roi,result):
        axistags = self.inputs["Input"].axistags
        inputShape  = self.inputs["Input"].shape
        #Set up roi 
        roi.setAxistags(axistags)
        roi.setInputShape(inputShape)
        #setup filter ONLY WHEN SIGMAS ARE SET and get MaxSigma for 
        sigma = self.setupFilter()
        #get srcRoi to retrieve neccessary sourcedata
        srcRoi = roi.expandByShape(sigma*self.windowSize)
        source = self.inputs["Input"](srcRoi.start,srcRoi.stop).wait()
        source = vigra.VigraArray(source,axistags=axistags)
        #Setup iterator to meet the special needs of each filter
        self.setupIterator(source, result)
        #get vigraRois to work with vigra filter
        vigraRoi = roi.centerIn(source.shape).popAxis('ct')
        for srckey,trgtkey in self.iterator:
            mask = roi.setStartToZero().maskWithShape(result[trgtkey].shape).toSlice()
            result[trgtkey] = self.vigraFilter(source=source[srckey],roi=vigraRoi)[mask]
        return result
    
class OpGaussianSmoothing(OpBaseVigraFilter):
    inputSlots = [InputSlot("Input"),InputSlot("Sigma")]
    name = "GaussianSmoothing"
    
    def __init__(self,parent):
        OpBaseVigraFilter.__init__(self,parent)
        self.vigraFilter = None
        
    def setupIterator(self,source,result):
        self.iterator = AxisIterator(source,'spatialc',result,'spatialc',[(),({'c':self.channelsPerChannel()})])   
    
    def setupFilter(self):
        sigma = self.inputs["Sigma"].value
        
        def tmpFilter(source,sigma,roi):
            tmpfilter = vigra.filters.gaussianSmoothing
            return tmpfilter(array=source,sigma=sigma,roi=(roi.start,roi.stop))

        self.vigraFilter = partial(tmpFilter,sigma=sigma)
        return sigma
        
    def resultingChannels(self):
        return self.inputs["Input"]._shape[self.inputs["Input"]._axistags.index('c')]
    
    def channelsPerChannel(self):
        return 1
        
class OpHessianOfGaussian(OpBaseVigraFilter):
    inputSlots = [InputSlot("Input"),InputSlot("Sigma")]
    name = "OpHessianOfGaussian"
    
    def __init__(self,parent):
        OpBaseVigraFilter.__init__(self,parent)
        self.vigraFilter = None
        
    def setupIterator(self,source,result):
        self.iterator = AxisIterator(source,'spatial',result,'spatial',[(),({'c':self.resultingChannels()})])   
    
    def setupFilter(self):
        sigma = self.inputs["Sigma"].value
        
        def tmpFilter(source,sigma,roi):
            tmpfilter = vigra.filters.hessianOfGaussian
            if source.axistags.axisTypeCount(vigra.AxisType.Space) == 2:
                return tmpfilter(image=source,sigma=sigma,roi=(roi.start,roi.stop))
            elif source.axistags.axisTypeCount(vigra.AxisType.Space) == 3:
                return tmpfilter(volume=source,sigma=sigma,roi=(roi.start,roi.stop))
            
        self.vigraFilter = partial(tmpFilter,sigma=sigma)
        return sigma
        
    def resultingChannels(self):
        return self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space)*(self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space) + 1) / 2
    
    def channelsPerChannel(self):
        return self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space)*(self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space) + 1) / 2
    
class OpDifferenceOfGaussians(OpBaseVigraFilter):
    inputSlots = [InputSlot("Input"), InputSlot("Sigma", stype = "float"), InputSlot("Sigma2", stype = "float")]
    name = "DifferenceOfGaussians"
    
    def __init__(self,parent):
        OpBaseVigraFilter.__init__(self,parent)
        self.vigraFilter = None
        
    def setupFilter(self):
        sigma0 = self.inputs["Sigma"].value
        sigma1 = self.inputs["Sigma2"].value
        
        def tmpFilter(s0,s1,source,roi):
            tmpfilter = vigra.filters.gaussianSmoothing
            return tmpfilter(source,s0,roi=(roi.start,roi.stop))-tmpfilter(source,s1,roi=(roi.start,roi.stop))

        self.vigraFilter = partial(tmpFilter,s0=sigma0,s1=sigma1)
        
        return max(sigma0,sigma1)
    
    def resultingChannels(self):
        return self.inputs["Input"]._shape[self.inputs["Input"]._axistags.index('c')]
    
    def channelsPerChannel(self):
        return 1
    
class OpLaplacianOfGaussian(OpBaseVigraFilter):
    inputSlots = [InputSlot("Input"), InputSlot("Sigma", stype = "float")]
    name = "LaplacianOfGaussian"
    
    def __init__(self,parent):
        OpBaseVigraFilter.__init__(self,parent)
        self.vigraFilter = None
        
    def setupFilter(self):
        scale = self.inputs["Sigma"].value
        
        def tmpFilter(source,scale,roi):
            tmpfilter = vigra.filters.laplacianOfGaussian
            return tmpfilter(array=source,scale=scale,roi=(roi.start,roi.stop))

        self.vigraFilter = partial(tmpFilter,scale=scale)

        return scale
    
    def resultingChannels(self):
        return self.inputs["Input"]._shape[self.inputs["Input"]._axistags.index('c')]

class OpStructureTensorEigenvalues(OpBaseVigraFilter):
    inputSlots = [InputSlot("Input"), InputSlot("Sigma", stype = "float"),InputSlot("Sigma2", stype = "float")]
    name = "StructureTensorEigenvalues"
    
    def __init__(self,parent):
        OpBaseVigraFilter.__init__(self,parent)
        self.vigraFilter = None
        
    def setupFilter(self):
        innerScale = self.inputs["Sigma2"].value
        outerScale = self.inputs["Sigma"].value
        
        def tmpFilter(source,innerScale,outerScale,roi):
            tmpfilter = vigra.filters.structureTensorEigenvalues
            return tmpfilter(image=source,innerScale=innerScale,outerScale=outerScale,roi=(roi.start,roi.stop))

        self.vigraFilter = partial(tmpFilter,innerScale=innerScale,outerScale=outerScale)

        return max(innerScale,outerScale)
    
    def setupIterator(self, source, result):
        self.iterator = AxisIterator(source,'spatial',result,'spatial',[(),({'c':self.channelsPerChannel()})])   
        
    def resultingChannels(self):
        return self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space)*self.inputs["Input"].shape[self.inputs["Input"].axistags.channelIndex]
    
    def channelsPerChannel(self):
        return self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space)
    
class OpHessianOfGaussianEigenvalues(OpBaseVigraFilter):
    inputSlots = [InputSlot("Input"), InputSlot("Sigma", stype = "float")]
    name = "HessianOfGaussianEigenvalues"
    
    def __init__(self,parent):
        OpBaseVigraFilter.__init__(self,parent)
        self.vigraFilter = None
        
    def setupFilter(self):
        scale = self.inputs["Sigma"].value
        
        def tmpFilter(source,scale,roi):
            tmpfilter = vigra.filters.hessianOfGaussianEigenvalues
            return tmpfilter(image=source,scale=scale,roi=(roi.start,roi.stop))

        self.vigraFilter = partial(tmpFilter,scale=scale)
        
        return scale
    
    def setupIterator(self, source, result):
        self.iterator = AxisIterator(source,'spatial',result,'spatial',[(),({'c':self.channelsPerChannel()})])   
  
    def resultingChannels(self):
        return self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space)*self.inputs["Input"].shape[self.inputs["Input"].axistags.channelIndex]
    
    def channelsPerChannel(self):
        return self.inputs["Input"].axistags.axisTypeCount(vigra.AxisType.Space)
    
class OpGaussianGradientMagnitude(OpBaseVigraFilter):
    inputSlots = [InputSlot("Input"), InputSlot("Sigma", stype = "float")]
    name = "GaussianGradientMagnitude"
    
    def __init__(self,parent):
        OpBaseVigraFilter.__init__(self,parent)
        self.vigraFilter = None
        
    def setupFilter(self):
        sigma = self.inputs["Sigma"].value
                
        def tmpFilter(source,sigma,roi):
            tmpfilter = vigra.filters.gaussianGradientMagnitude
            return tmpfilter(source,sigma=sigma,roi=(roi.start,roi.stop))

        self.vigraFilter = partial(tmpFilter,sigma=sigma)
        return sigma

    def resultingChannels(self):
        return self.inputs["Input"]._shape[self.inputs["Input"]._axistags.index('c')]
    

class OpPixelFeaturesPresmoothed(Operator):
    
    name="OpPixelFeaturesPresmoothed"
    inputSlots = [InputSlot("Input"), InputSlot("Matrix"), InputSlot("Scales")]
    outputSlots = [OutputSlot("Output"), OutputSlot("arrayOfOperators")]
    
    def __init__(self,parent):
        Operator.__init__(self, parent, register=True)
        
        self.source = OpArrayPiper(self.graph)
        self.multi = Op50ToMulti(self.graph)
        self.stacker = OpMultiArrayStacker(self.graph)
        self.smoother = OpGaussianSmoothing(self.graph)
        self.destSigma = 1.0
        self.windowSize = 4
        self.operatorList = [OpGaussianSmoothing,OpLaplacianOfGaussian,\
                        OpStructureTensorEigenvalues,OpHessianOfGaussianEigenvalues,\
                        OpGaussianGradientMagnitude,OpDifferenceOfGaussians]
        
    def setupOutputs(self):
        
        #TODO: Different assertions and stuff.
        self.source.inputs["Input"].connect(self.inputs["Input"])
        self.inMatrix = self.inputs["Matrix"].value
        self.inScales = self.inputs["Scales"].value
        self.modSigmas = [0]*len(self.inScales)
        self.maxSigma = numpy.max(self.inScales)
        self.incrSigmas = [0]*len(self.inScales)
        
        #set modified sigmas
        for i in xrange(len(self.inScales)):
            if self.inScales[i] > self.destSigma:
                self.modSigmas[i]=(sqrt(self.inScales[i]**2-self.destSigma**2))
                
        self.modSigmas.insert(0,0)
        for i in xrange(len(self.modSigmas)-1):
            self.incrSigmas[i]=sqrt(self.modSigmas[i+1]**2-self.modSigmas[i]**2)
        self.modSigmas.remove(0)
            
        #set Operators
        operatorList = self.operatorList
        
        scaleMultiplyList = [False,False,0.5,False,False,0.66]
        
        self.operatorMatrix = [[None]*len(self.inMatrix[i]) for i in xrange(len(self.inMatrix))]
        
        
        k=0
        for i in xrange(len(self.inMatrix)): #Cycle through operators == i
            for j in xrange(len(self.inMatrix[i])): #Cycle through sigmas == j
                if self.inMatrix[i][j]:
                    self.operatorMatrix[i][j] = operatorList[i](self.graph)
                    self.operatorMatrix[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                    self.operatorMatrix[i][j].inputs["Sigma"].setValue(self.destSigma)
                    if scaleMultiplyList[i]:
                        self.operatorMatrix[i][j].inputs["Sigma2"].setValue(self.destSigma*scaleMultiplyList[i])
                    self.multi.inputs["Input%02d"%(k)].connect(self.operatorMatrix[i][j].outputs["Output"])
                    k += 1
                    
        self.stacker.inputs["AxisFlag"].setValue('c')
        self.stacker.inputs["AxisIndex"].setValue(self.source.outputs["Output"]._axistags.index('c'))
        self.stacker.inputs["Images"].connect(self.multi.outputs["Outputs"])
        
        self.outputs["Output"]._axistags = self.stacker.outputs["Output"]._axistags
        self.outputs["Output"]._shape = self.stacker.outputs["Output"]._shape
        self.outputs["Output"]._dtype = numpy.float32 
        
        #transpose operatorMatrix for better handling
        opMatrix = self.operatorMatrix
        newOpMatrix = [[None]*len(opMatrix) for i in xrange(len(opMatrix[0]))]
        opList = []
        for l in opMatrix:
            opList += l
        for i in xrange(len(opList)):
            newOpMatrix[i/len(opMatrix)][i%len(opMatrix)] = opList[i]
        self.operatorMatrix = newOpMatrix
        
        
    def execute(self,slot,roi,result):
        
        #Get axistags and inputShape
        axistags = self.inputs["Input"].axistags
        inputShape  = self.inputs["Input"].shape
        resultCIndex = self.outputs["Output"].axistags.channelIndex
        
        #Set up roi 
        roi.setAxistags(axistags)
        roi.setInputShape(inputShape)

        #Request Required Region
        srcRoi = roi.expandByShape(self.maxSigma*self.windowSize)
        source = self.source.outputs["Output"](srcRoi.start,srcRoi.stop).wait()
        
        #disconnect all operators
        opM = self.operatorMatrix
        cIter = 0
        for sig in xrange(len(opM)):#for each sigma
            self.smoother.inputs["Sigma"].setValue(self.incrSigmas[sig])
            self.smoother.inputs["Input"].setValue(source)
            source = self.smoother.outputs["Output"]().wait()
            for op in xrange(len(opM[sig])):#for each operator with this sigma
                if opM[sig][op] is not None:
                    opM[sig][op].inputs["Input"].disconnect()
                    opM[sig][op].inputs["Input"].setValue(source)
                    cIndex = opM[sig][op].outputs["Output"].axistags.channelIndex
                    cSize  = opM[sig][op].outputs["Output"].shape[cIndex]
                    slicing = [slice(0,result.shape[i],None) if i != resultCIndex \
                               else slice(cIter,cIter+cSize,None) for i in \
                               range(len(result.shape))]
                    result[slicing] = opM[sig][op].outputs["Output"]().wait()
                    cIter += cSize
        return result     
    
from lazyflow.graph import Graph
import vigra

if __name__ == "__main__":
    
    v = vigra.VigraArray((20,20,10))
    g = Graph()
    op = OpHessianOfGaussianEigenvalues(g)
    op.inputs["Sigma"].setValue(2.0)
    op.inputs["Input"].setValue(v)
    print op.outputs["Output"]().wait().shape