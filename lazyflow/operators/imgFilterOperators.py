from lazyflow.graph import Operator,InputSlot,OutputSlot
from lazyflow.helpers import newIterator
from lazyflow.operators.obsolete.generic import OpMultiArrayStacker
from lazyflow.operators.obsolete.vigraOperators import Op50ToMulti
from lazyflow.rtype import SubRegion
import numpy
import vigra
from math import sqrt
from functools import partial
from lazyflow.roi import roiToSlice,sliceToRoi
import collections
import warnings

class OpBaseVigraFilter(Operator):
    
    inputSlots = []
    outputSlots = [OutputSlot("Output")]
    
    name = 'OpBaseVigraFilter'
    
    vigraFilter = None
    windowSize = 4
    
    def __init__(self, *args, **kwargs):
        super(OpBaseVigraFilter, self).__init__(*args, **kwargs)
        self.iterator = None
    
    def getChannelResolution(self):
        """
        returns how the number of source channels which get mapped on one unit
        of result channels
        """
        return 1
     
    def resultingChannels(self):
        """
        returns the resulting channels
        """
        pass
    
    def setupFilter(self):
        """
        setups the vigra filter and returns the maximum sigma
        """
        pass
    
    def calculateHalo(self,sigma):
        """
        calculates halo, depends on the filter
        """
        return 2*numpy.ceil(sigma*self.windowSize)+1
    
    def propagateDirty(self,slot,subindex,roi):
        if slot == self.Input:
            cIndex = self.Input.meta.axistags.channelIndex
            retRoi = roi.copy()
            retRoi.start[cIndex] *= self.channelsPerChannel()
            retRoi.stop[cIndex] *= self.channelsPerChannel()
            self.Output.setDirty(retRoi)
    
    def setupIterator(self,source,result):
        self.iterator = AxisIterator(source,'spatialc',result,'spatialc',[(),(1,1,1,1,self.resultingChannels())])
    
    def setupOutputs(self):
        inputSlot = self.Input
        outputSlot = self.Output
        channelNum = self.resultingChannels()
        outputSlot.meta.assignFrom(inputSlot.meta)
        outputSlot.setShapeAtAxisTo('c', channelNum)
        
    def execute(self, slot, subindex, roi, result):
        
        #request,set or compute the necessary parameters
        axistags = self.Input.meta.axistags
        inputShape  = self.Input.meta.shape
        channelIndex = axistags.index('c')
        channelsPerC = self.channelsPerChannel()
        channelRes = self.getChannelResolution()
        timeIndex = axistags.index('t')
        if timeIndex >= roi.dim:
            timeIndex = None
        roi.setInputShape(inputShape)
        origRoi = roi.copy()
        sigma = self.setupFilter()
        halo = self.calculateHalo(sigma)
        
        #set up the roi to get the necessary source
        roi.expandByShape(halo,channelIndex,timeIndex).adjustChannel(channelsPerC,channelIndex,channelRes)
        source = self.Input(roi.start,roi.stop).wait()
        source = vigra.VigraArray(source,axistags=axistags)
        
        #set up the grid for the iterator, and the iterator
        srcGrid = [source.shape[i] if i!= channelIndex else channelRes for i in range(len(source.shape))]
        trgtGrid = [inputShape[i]  if i != channelIndex else self.channelsPerChannel() for i in range(len(source.shape))]
        if timeIndex is not None:
            srcGrid[timeIndex] = 1
            trgtGrid[timeIndex] = 1
        nIt = newIterator(origRoi,srcGrid,trgtGrid,timeIndex=timeIndex,channelIndex = channelIndex)
        
        #set up roi to work with vigra filters
        if timeIndex > channelIndex and timeIndex is not None:
            origRoi.popDim(timeIndex)
            origRoi.popDim(channelIndex)
        elif timeIndex < channelIndex and timeIndex is not None:
            origRoi.popDim(channelIndex)
            origRoi.popDim(timeIndex)
        else:
            origRoi.popDim(channelIndex)
        origRoi.adjustRoi(halo)
        
        #iterate over the requested volumes
        
        warnings.warn("FIXME: This loop could be parallelized for better performance.")
        for src,trgt,mask in nIt:
            result[trgt] = self.vigraFilter(source = source[src],window_size=self.windowSize,roi=origRoi)[mask]
        return result
    
class OpGaussianSmoothing(OpBaseVigraFilter):
    inputSlots = [InputSlot("Input"),InputSlot("Sigma")]
    name = "GaussianSmoothing"
    
    def __init__(self, *args, **kwargs):
        super(OpGaussianSmoothing, self).__init__(*args, **kwargs)
        
    def setupIterator(self,source,result):
        self.iterator = AxisIterator(source,'spatialc',result,'spatialc',[(),({'c':self.channelsPerChannel()})])   
    
    def setupFilter(self):
        sigma = self.inputs["Sigma"].value
        
        def tmpFilter(source,sigma,window_size,roi):
            tmpfilter = vigra.filters.gaussianSmoothing
            return tmpfilter(array=source,sigma=sigma,window_size=window_size,roi=(roi.start,roi.stop))
    
        self.vigraFilter = partial(tmpFilter,sigma=sigma,window_size=self.windowSize)
        return sigma
        
    def resultingChannels(self):
        return self.Input.meta.shape[self.Input.meta.axistags.index('c')]
    
    def channelsPerChannel(self):
        return 1
    
class OpDifferenceOfGaussians(OpBaseVigraFilter):
    inputSlots = [InputSlot("Input"), InputSlot("Sigma", stype = "float"), InputSlot("Sigma2", stype = "float")]
    name = "DifferenceOfGaussians"
    
    def __init__(self, *args, **kwargs):
        super(OpDifferenceOfGaussians, self).__init__(*args, **kwargs)
        
    def setupFilter(self):
        sigma0 = self.inputs["Sigma"].value
        sigma1 = self.inputs["Sigma2"].value
        
        def tmpFilter(s0,s1,source,window_size,roi):
            tmpfilter = vigra.filters.gaussianSmoothing
            return tmpfilter(source,s0,window_size=window_size,roi=(roi.start,roi.stop))-tmpfilter(source,s1,window_size=window_size,roi=(roi.start,roi.stop))
        
        self.vigraFilter = partial(tmpFilter,s0=sigma0,s1=sigma1,window_size=self.windowSize)
        return max(sigma0,sigma1)
    
    def resultingChannels(self):
        return self.Input.meta.shape[self.Input.meta.axistags.index('c')]
    
    def channelsPerChannel(self):
        return 1

        
class OpHessianOfGaussian(OpBaseVigraFilter):
    inputSlots = [InputSlot("Input"),InputSlot("Sigma")]
    name = "OpHessianOfGaussian"
    
    def __init__(self, *args, **kwargs):
        super(OpHessianOfGaussian, self).__init__(*args, **kwargs)
        
    def setupIterator(self,source,result):
        self.iterator = AxisIterator(source,'spatial',result,'spatial',[(),({'c':self.resultingChannels()})])   
    
    def setupFilter(self):
        sigma = self.inputs["Sigma"].value
        
        def tmpFilter(source,sigma,window_size,roi):
            tmpfilter = vigra.filters.hessianOfGaussian
            return tmpfilter(source,sigma=sigma,window_size=window_size,roi=(roi.start,roi.stop))
            
        self.vigraFilter = partial(tmpFilter,sigma=sigma,window_size=self.windowSize)
        return sigma
        
    def resultingChannels(self):
        return self.Input.meta.axistags.axisTypeCount(vigra.AxisType.Space)*(self.Input.meta.axistags.axisTypeCount(vigra.AxisType.Space) + 1) / 2
    
    def channelsPerChannel(self):
        return self.Input.meta.axistags.axisTypeCount(vigra.AxisType.Space)*(self.Input.meta.axistags.axisTypeCount(vigra.AxisType.Space) + 1) / 2
    
class OpLaplacianOfGaussian(OpBaseVigraFilter):
    inputSlots = [InputSlot("Input"), InputSlot("Sigma", stype = "float")]
    name = "LaplacianOfGaussian"
    
    def __init__(self, *args, **kwargs):
        super(OpLaplacianOfGaussian, self).__init__(*args, **kwargs)
        
    def setupFilter(self):
        scale = self.inputs["Sigma"].value
        
        def tmpFilter(source,scale,window_size,roi):
            tmpfilter = vigra.filters.laplacianOfGaussian
            return tmpfilter(array=source,scale=scale,window_size=window_size,roi=(roi.start,roi.stop))

        self.vigraFilter = partial(tmpFilter,scale=scale,window_size=self.windowSize)
        return scale
    
    def resultingChannels(self):
        return self.Input.meta.shape[self.Input.meta.axistags.index('c')]
    
    def channelsPerChannel(self):
        return 1

class OpStructureTensorEigenvaluesSummedChannels(OpBaseVigraFilter):
    inputSlots = [InputSlot("Input"), InputSlot("Sigma", stype = "float"),InputSlot("Sigma2", stype = "float")]
    name = "StructureTensorEigenvalues"
    
    def __init__(self, *args, **kwargs):
        super(OpStructureTensorEigenvaluesSummedChannels, self).__init__(*args, **kwargs)
    
    def getChannelResolution(self):
        return self.Input.meta.shape[self.Input.meta.axistags.channelIndex]
    
    def calculateHalo(self, sigma):
        sigma1 = self.Sigma.value
        sigma2 = self.Sigma2.value
        return int(numpy.ceil(sigma1*self.windowSize))+int(numpy.ceil(sigma2*self.windowSize))
        
    def setupFilter(self):
        innerScale = self.Sigma.value
        outerScale = self.inputs["Sigma2"].value
        
        def tmpFilter(source,innerScale,outerScale,window_size,roi):
            tmpfilter = vigra.filters.structureTensorEigenvalues
            return tmpfilter(image=source,innerScale=innerScale,outerScale=outerScale,window_size=window_size,roi=(roi.start,roi.stop))

        self.vigraFilter = partial(tmpFilter,innerScale=innerScale,outerScale=outerScale,window_size=self.windowSize)

        return max(innerScale,outerScale)
    
    def setupIterator(self, source, result):
        self.iterator = AxisIterator(source,'spatial',result,'spatial',[(),({'c':self.channelsPerChannel()})])   
        
    def resultingChannels(self):
        return self.Input.meta.axistags.axisTypeCount(vigra.AxisType.Space)
    
    def channelsPerChannel(self):
        return self.Input.meta.axistags.axisTypeCount(vigra.AxisType.Space)
    
class OpStructureTensorEigenvalues(OpBaseVigraFilter):
    inputSlots = [InputSlot("Input"), InputSlot("Sigma", stype = "float"),InputSlot("Sigma2", stype = "float")]
    name = "StructureTensorEigenvalues"
    
    def __init__(self, *args, **kwargs):
        super(OpStructureTensorEigenvalues, self).__init__(*args, **kwargs)
    
    def calculateHalo(self, sigma):
        sigma1 = self.Sigma.value
        sigma2 = self.Sigma2.value
        return int(numpy.ceil(sigma1*self.windowSize))+int(numpy.ceil(sigma2*self.windowSize))
        
    def setupFilter(self):
        innerScale = self.Sigma.value
        outerScale = self.inputs["Sigma2"].value
        
        def tmpFilter(source,innerScale,outerScale,window_size,roi):
            tmpfilter = vigra.filters.structureTensorEigenvalues
            return tmpfilter(image=source,innerScale=innerScale,outerScale=outerScale,window_size=window_size,roi=(roi.start,roi.stop))

        self.vigraFilter = partial(tmpFilter,innerScale=innerScale,outerScale=outerScale,window_size=self.windowSize)

        return max(innerScale,outerScale)
    
    def setupIterator(self, source, result):
        self.iterator = AxisIterator(source,'spatial',result,'spatial',[(),({'c':self.channelsPerChannel()})])   
        
    def resultingChannels(self):
        return self.Input.meta.axistags.axisTypeCount(vigra.AxisType.Space)*self.Input.meta.shape[self.Input.meta.axistags.channelIndex]
    
    def channelsPerChannel(self):
        return self.Input.meta.axistags.axisTypeCount(vigra.AxisType.Space)


class OpHessianOfGaussianEigenvalues(OpBaseVigraFilter):
    inputSlots = [InputSlot("Input"), InputSlot("Sigma", stype = "float")]
    name = "HessianOfGaussianEigenvalues"
    
    def __init__(self, *args, **kwargs):
        super(OpHessianOfGaussianEigenvalues, self).__init__(*args, **kwargs)
        
    def setupFilter(self):
        scale = self.inputs["Sigma"].value
        
        def tmpFilter(source,scale,window_size,roi):
            tmpfilter = vigra.filters.hessianOfGaussianEigenvalues
            return tmpfilter(source,scale=scale,window_size=window_size,roi=(roi.start,roi.stop))

        self.vigraFilter = partial(tmpFilter,scale=scale)
        
        return scale
    
    def setupIterator(self, source, result):
        self.iterator = AxisIterator(source,'spatial',result,'spatial',[(),({'c':self.channelsPerChannel()})])   
  
    def resultingChannels(self):
        return self.Input.meta.axistags.axisTypeCount(vigra.AxisType.Space)*self.Input.meta.shape[self.Input.meta.axistags.channelIndex]
    
    def channelsPerChannel(self):
        return self.Input.meta.axistags.axisTypeCount(vigra.AxisType.Space)
    
class OpGaussianGradientMagnitude(OpBaseVigraFilter):
    inputSlots = [InputSlot("Input"), InputSlot("Sigma", stype = "float")]
    name = "GaussianGradientMagnitude"
    
    def __init__(self, *args, **kwargs):
        super(OpGaussianGradientMagnitude, self).__init__(*args, **kwargs)
        
    def setupFilter(self):
        sigma = self.inputs["Sigma"].value
                
        def tmpFilter(source,sigma,window_size,roi):
            tmpfilter = vigra.filters.gaussianGradientMagnitude
            return tmpfilter(source,sigma=sigma,window_size=window_size,roi=(roi.start,roi.stop),accumulate=False)

        self.vigraFilter = partial(tmpFilter,sigma=sigma,window_size=self.windowSize)
        return sigma

    def resultingChannels(self):
        return self.Input.meta.shape[self.Input.meta.axistags.index('c')]
    
    def channelsPerChannel(self):
        return 1
    


class OpPixelFeaturesPresmoothed(Operator):
    name="OpPixelFeaturesPresmoothed"
    category = "Vigra filter"

    inputSlots = [InputSlot("Input"),
                  InputSlot("Matrix"),
                  InputSlot("Scales"),
                  InputSlot("FeatureIds")] # The selection of features to compute

    outputSlots = [OutputSlot("Output"), # The entire block of features as a single image (many channels)
                   OutputSlot("Features", level=1)] # Each feature image listed separately, with feature name provided in metadata

    # Specify a default set & order for the features we compute
    DefaultFeatureIds = [ 'GaussianSmoothing',
                          'LaplacianOfGaussian',
                          'StructureTensorEigenvalues',
                          'HessianOfGaussianEigenvalues',
                          'GaussianGradientMagnitude',
                          'DifferenceOfGaussians' ]
    #set Operators
    FeatureInfos = collections.OrderedDict(
                    # FeatureId : (Operator class, sigma2, name format)
                    [ ('GaussianSmoothing' , (OpGaussianSmoothing, False, "Gaussian Smoothing (s={})")),
                      ('LaplacianOfGaussian' , (OpLaplacianOfGaussian, False, "Laplacian of Gaussian (s={})")),
                      ('StructureTensorEigenvalues' , (OpStructureTensorEigenvalues, 0.5, "Structure Tensor Eigenvalues (s={})")),
                      ('HessianOfGaussianEigenvalues' , (OpHessianOfGaussianEigenvalues, False, "Hessian of Gaussian Eigenvalues (s={})")),
                      ('GaussianGradientMagnitude' , (OpGaussianGradientMagnitude, False, "Gaussian Gradient Magnitude (s={})")),
                      ('DifferenceOfGaussians' , (OpDifferenceOfGaussians, 0.66, "Difference of Gaussians (s={})")) ] )
    
    def __init__(self, *args, **kwargs):
        super(OpPixelFeaturesPresmoothed, self).__init__(*args, **kwargs)

        #set up basic operators
        self.stacker = OpMultiArrayStacker(parent=self)
        self.multi = Op50ToMulti(parent=self)
        self.stacker.Images.connect(self.multi.Outputs)
        self.smoother = OpGaussianSmoothing(parent=self)
        self.smoother.Input.connect(self.Input)
        
        # Defaults
        self.inputs["FeatureIds"].setValue( self.DefaultFeatureIds )
        self.destSigma = 1.0
        self.windowSize = 4.0
        
    def setupOutputs(self):
        
        self.features = self.FeatureIds.value
        self.inScales = self.Scales.value
        self.inMatrix = self.Matrix.value
        
        #####
        #    check the input
        #####
        
        #Check for the correct type of the input
        if not isinstance(self.inMatrix, numpy.ndarray):
            raise RuntimeError("OpPixelFeatures: Please input a numpy.ndarray as 'Matrix'")
        if not isinstance(self.inScales, list):
            raise RuntimeError("OpPixelFeatures: Please input a list as 'Scales'")
        if not isinstance(self.features, list):
            raise RuntimeError("OpPixelFeatures: Please input a list as 'FeatureIds'")
        
        #Check for the correct form of the input
        if not self.inMatrix.shape == (len(self.features),len(self.inScales)):
            raise RuntimeError("OpPixelFeatures: Please input numpy.ndarray as 'Matrix', which has the form %sx%s."%(len(self.inScales),len(self.features)))
        
        #Check for the correct content of the input
        if not reduce(lambda x,y: True if x and y else False,[True if fId in self.DefaultFeatureIds else False for fId in self.features],True):
            raise RuntimeError("OpPixelFeatures: Please use only one of the following strings as a featureId:\n%s)"%(self.DefaultFeatureIds))
        if not reduce(lambda x,y: True if x and y else False,[True if type(s) in [float,int] else False for s in self.inScales],True):
            raise RuntimeError("OpPixelFeatures: Please use only one of the following types as a scale:\n int,float")
        if not reduce(lambda x,y: True if x and y else False,[True if m in [1.0,0.0] else False for m in self.inMatrix.flatten()],True):
            raise RuntimeError("OpPixelFeatures: Please use only one of the following values as a matrix entry:\n 0,1")
        
        #####
        #    calculate and set the meta data for the output slot
        #####
        
        #this matrix will contain the instances of the operators
        self.operatorMatrix = [[None]*len(self.inMatrix[0]) for i in xrange(len(self.inMatrix))]
        #this matrix will contain the start and stop position in the channel dimension of the ouput
        #for each op/sig combination. Roughly equivalent to self.featureOutputChannels
        self.positionMatrix = numpy.zeros_like(self.operatorMatrix)

        
        #fill the operatorMatrix according to self.inMatrix
        channelCount = 0
        featureCount = 0
        self.featureOutputChannels = []
        k=0

        totalFeatureCount = (self.inMatrix == True).sum()
        self.Features.resize( totalFeatureCount )

        for i in xrange(len(self.inMatrix)): #Cycle through operators == i
            for j in xrange(len(self.inMatrix[i])): #Cycle through sigmas == j
                if self.inMatrix[i][j]:
                    self.operatorMatrix[i][j] = self.FeatureInfos[self.features[i]][0](graph=self.graph)
                    self.operatorMatrix[i][j].Input.connect(self.Input)
                    self.operatorMatrix[i][j].Sigma.setValue(self.inScales[i])
                    if self.FeatureInfos[self.features[i]][1]:
                        self.operatorMatrix[i][j].Sigma2.setValue(self.inScales[i]*self.FeatureInfos[self.features[i]][1])
                    self.multi.inputs["Input%02d"%(k)].connect(self.operatorMatrix[i][j].Output)
                    k += 1
                    
                    # Prepare the individual features
                    featureCount += 1

                    featureMeta = self.operatorMatrix[i][j].Output.meta
                    featureChannels = featureMeta.shape[ featureMeta.axistags.index('c') ]
                    self.Features[featureCount-1].meta.assignFrom( featureMeta )
                    self.Features[featureCount-1].meta.description = self.FeatureInfos[self.features[i]][2].format(self.inScales[j])
                    self.featureOutputChannels.append( (channelCount, channelCount + featureChannels) )
                    self.positionMatrix[i][j] = [channelCount,None]
                    channelCount += featureChannels
                    self.positionMatrix[i][j][1] = channelCount
                else:
                    self.positionMatrix[i][j] = [0,0]
        
        for index, slot in enumerate(self.Features):
            assert slot.meta.description is not None, "Feature {} has no description!".format(index)
        
        self.stacker.AxisFlag.setValue('c')
        self.stacker.AxisIndex.setValue(self.Input.meta.axistags.index('c'))
        self.stacker.Images.connect(self.multi.Outputs)
        
        self.Output.meta.axistags = self.stacker.Output.meta.axistags
        self.Output.meta.shape = self.stacker.Output.meta.shape
        self.Output.meta.dtype = numpy.float32
        
        
        #####
        #    preparations for the execute method
        #####
        
        #transpose operatorMatrix and positionMatrix for better handling
        self.operatorMatrix = zip(*self.operatorMatrix)
        self.operatorMatrix = [list(t) for t in self.operatorMatrix]
        self.positionMatrix = zip(*self.positionMatrix)
        self.positionMatrix = [list(t) for t in self.positionMatrix]
        
        #cast the scales to float
        self.inScales = [float(s) for s in self.inScales]
        
        #calculate the sigmas
        self.maxSigma = numpy.max(self.inScales)
        self.incrSigmas = [0]*len(self.inScales)
        self.modSigmas = [0]*len(self.inScales)
        
        #set modified sigmas
        for i in xrange(len(self.inScales)):
            if self.inScales[i] > self.destSigma:
                self.modSigmas[i]=(sqrt(self.inScales[i]**2-self.destSigma**2))
            else:
                self.modSigmas[i]=self.inScales[i]
        
        self.modSigmas.insert(0,0)
        for i in xrange(len(self.modSigmas)-1):
            self.incrSigmas[i]=sqrt(self.modSigmas[i+1]**2-self.modSigmas[i]**2)
        self.modSigmas.remove(0)
        
    def execute(self,slot,subindex,roi,result):

        #####
        #    OutputSlot: "Output"
        #####
        
        if slot == self.Output:
            
            #Get axistags, inputShape, cIndex and if possible tIndex
            axistags = self.Input.meta.axistags
            inputShape  = self.Input.meta.shape
            cIndex = self.Output.meta.axistags.index('c')
            if axistags.axisTypeCount(vigra.AxisType.Time) > 0:
                tIndex = self.Output.meta.axistags.index('t')
            else:
                tIndex = None
            
            #Set up roi 
            roi.setInputShape(inputShape)
    
            ################ Request Required Source Region ##################
            
            origRoi = roi.copy()
            #get the maximum halo 
            halo = 0
            opM = self.operatorMatrix
            for sig in xrange(len(opM)):#for each sigma
                for op in xrange(len(opM[sig])): #for each operator with this sig
                    if opM[sig][op] is not None:
                        halo=max(halo,opM[sig][op].calculateHalo(opM[sig][op].setupFilter()))
            #check smoothing operations halo
            halo = max(halo,self.smoother.calculateHalo(max(self.incrSigmas)))
            roi.expandByShape(halo,cIndex,tIndex)
            roi.setDim(cIndex,0,inputShape[cIndex])
            source = self.Input(roi.start,roi.stop).wait()
            source = vigra.VigraArray(source,axistags=axistags)

            opM = self.operatorMatrix
            resIter = 0
            cstart,cstop = origRoi.start[cIndex],origRoi.stop[cIndex]
            for sig in xrange(len(opM)):#for each sigma

                warnings.warn("FIXME: Can't use an operator like this in execute!  This won't work for parallel calls to execute()")                
                self.smoother.Sigma.setValue(self.incrSigmas[sig])
                
                if self.smoother.Input.connected: 
                    self.smoother.Input.disconnect()

                warnings.warn("FIXME: Can't use an operator like this in execute!  This won't work for parallel calls to execute()")                
                self.smoother.Input.setValue(source)
                
                warnings.warn("FIXME: Parallelize these requests for better performance.")
                source = self.smoother.Output().wait()
                
                
                source = vigra.VigraArray(source,axistags=axistags)
                for op in xrange(len(opM[sig])): #for each operator with this sigma
                    try:
                        pos = self.positionMatrix[sig][op]
                    except:
                        print sig,op
                    if opM[sig][op] is not None and pos[1] > cstart and pos[0] < cstop:
                        if opM[sig][op].Input.connected():
                            opM[sig][op].Input.disconnect()
                            
                            warnings.warn("FIXME: Can't use an operator like this in execute!  This won't work for parallel calls to execute()")                
                            opM[sig][op].Input.setValue(source)
                            
                        currCStart,currCStop = max(cstart,pos[0]),min(cstop,pos[1])
                        currCRange = currCStop-currCStart
                        resSlicing = list(origRoi.copy().toSlice())
                        resSlicing = [ slice(resIter,resIter+currCRange,None) if i == cIndex\
                                      else slice(0,None) for i in range(len(resSlicing))]
                        resIter += currCRange
                        opCStart = currCStart - pos[0]
                        opCStop = currCStop - pos[0]
                        opRoi = origRoi.copy()
                        opRoi.start[cIndex],opRoi.stop[cIndex] = opCStart,opCStop
                        
                        warnings.warn("FIXME: Parallelize these requests for better performance.")
                        result[resSlicing] = opM[sig][op].Output(opRoi.start,opRoi.stop).wait()
            return result
        
        #####
        #    OutputSlot: "Features"
        #####
        
        elif slot == self.Features:
            index = subindex[0]
            cIndex = self.Input.meta.axistags.index('c')
            roi.setDim(cIndex,self.featureOutputChannels[index][0] + roi.start[cIndex],\
                              self.featureOutputChannels[index][0] + roi.stop[cIndex])
            return self.execute(self.Output,(), roi, result)

    def propagateDirty(self,slot,subindex,roi):
   
        if slot == self.Input:
            channelAxis = self.Input.meta.axistags.index('c')
            numChannels = self.Input.meta.shape[channelAxis]
            dirtyChannels = roi.stop[channelAxis] - roi.start[channelAxis]
            
            # If all the input channels were dirty, the dirty output region is a contiguous block
            if dirtyChannels == numChannels:
                dirtyKey = roiToSlice(roi.start, roi.stop)
                dirtyKey[channelAxis] = slice(None)
                dirtyRoi = sliceToRoi(dirtyKey, self.Output.meta.shape)
                self.Output.setDirty(dirtyRoi[0], dirtyRoi[1])
            else:
                # Only some input channels were dirty,
                # so we must mark each dirty output region separately.
                numFeatures = self.Output.meta.shape[channelAxis] / numChannels
                for featureIndex in range(numFeatures):
                    startChannel = numChannels*featureIndex + roi.start[channelAxis]
                    stopChannel = startChannel + roi.stop[channelAxis]
                    dirtyRoi = copy.copy(roi)
                    dirtyRoi.start[channelAxis] = startChannel
                    dirtyRoi.stop[channelAxis] = stopChannel
                    self.Output.setDirty(dirtyRoi)

        elif (slot == self.Matrix
              or slot == self.Scales
              or slot == self.FeatureIds):
            self.Output.setDirty(slice(None))
        else:
            assert False, "Unknown dirty input slot."

if __name__ == "__main__":
    from lazyflow.graph import Graph
    
    g = Graph()
    v = vigra.VigraArray(1000*numpy.random.rand(10,10,4),axistags = vigra.defaultAxistags('xyc'))
    op = OpPixelFeaturesPresmoothed(graph = g)
    op.FeatureIds.setValue(["GaussianSmoothing","StructureTensorEigenvalues"])
    op.Scales.setValue([1.5,2.0])
    op.Input.setValue(v)
    n = numpy.ndarray((2,2))
    n[:] = [[1,1],[1,1]] 
    op.Matrix.setValue(n)
    w = op.Output([0,0,9],[10,10,10]).wait()
    f = op.Features[2]([0,0,1],[10,10,2]).wait()