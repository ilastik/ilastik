from lazyflow.graph import Operator, InputSlot, OutputSlot

import numpy
import vigra

class OpThresholdTwoLevels(Operator):
    name = "opThresholdTwoLevels"
    
    InputImage = InputSlot()
    MinSize = InputSlot(stype='int', value=100)
    MaxSize = InputSlot(stype='int', value=1000)
    HighThreshold = InputSlot(stype='float', value=0.5)
    LowThreshold = InputSlot(stype='float', value=0.1)
    SmootherSigma = InputSlot(optional=True, value=(3.5, 3.5, 1))
    Channel = InputSlot(optional=True, value=2)
    
    Output = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpThresholdTwoLevels, self).__init__(*args, **kwargs)
        
    def setupOutputs(self):
        # Copy the input metadata to the output
        self.Output.meta.assignFrom( self.InputImage.meta )
        self.Output.meta.dtype=numpy.uint8

        assert self.InputImage.meta.axistags is not None
        axistags = self.InputImage.meta.axistags
        hasChannels = axistags.axisTypeCount(vigra.AxisType.Channels)
        self.channelSlice=None
        if hasChannels and self.InputImage.meta.shape[axistags.channelIndex]>1:
            self.channelSlice = slice(self.Channel.value, self.Channel.value+1, None)
        elif hasChannels and self.InputImage.meta.shape[axistags.channelIndex]==1:
            self.channelSlice = slice(None, None, None)
        shape = list(self.InputImage.meta.shape)
        shape[axistags.channelIndex]=1
        self.Output.meta.shape = tuple(shape)
    
    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()
        
        axistags = self.InputImage.meta.axistags
        #nchannels = axistags.axisTypeCount(vigra.AxisType.Channels)
        if self.channelSlice is not None:
            keylist = list(key)
            keylist[axistags.channelIndex]=self.channelSlice
            key = tuple(keylist)
        
        data = self.InputImage[key].wait()
        
        sigma = self.SmootherSigma.value
        smoothed = vigra.filters.gaussianSmoothing(data.astype(numpy.float32), sigma)
        cc_high = self.extractCC(smoothed, self.HighThreshold.value)
        cc_low = self.extractCC(smoothed, self.LowThreshold.value)
        
        th_high = self.filterCC(cc_high)
        
        maxregion = numpy.max(cc_low)

        cc_low = cc_low.view(numpy.ndarray)
        prod = th_high * cc_low
        
        passed = numpy.unique(prod)
        
        newsizes = numpy.zeros((maxregion+2,), dtype=numpy.uint32)
        ngood = 1
        for index in passed:
            newsizes[index] = 1  #ngood, if we wanted to relabel
            ngood = ngood+1
        
        newsizes[0]=0
        result[:] = newsizes[cc_low]
        
        
    def propagateDirty(self, slot, subindex, roi):
        key = [slice(None, None, None)]*len(self.InputImage.meta.shape)
        self.Output.setDirty(key)
    
    def filterCC(self, data):
        
        sizes = numpy.bincount(data.flat)
        numgood=1
        newsizes = numpy.zeros((len(sizes),), dtype=numpy.uint32)
        for i, s in enumerate(sizes):
            if s>self.MinSize.value and s<self.MaxSize.value:
                newsizes[i]=1 #numgood, if we want to relabel the cc. 1 for just thresholding
                numgood=numgood+1
                
        data_filtered = newsizes[data].astype(numpy.uint8)
        return data_filtered
        
        
    def extractCC(self, data, threshold):
        #move this function here, so that the memory from threshold array gets freed up
        thresholded = data>threshold
        cc = vigra.analysis.labelVolumeWithBackground(thresholded.astype(numpy.uint8))
        return cc
        
        