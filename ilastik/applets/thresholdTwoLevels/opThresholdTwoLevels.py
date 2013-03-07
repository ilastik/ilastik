from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpMultiArraySlicer2, OpPixelOperator, OpVigraLabelVolume, OpFilterLabels, OpCompressedCache, OpColorizeLabels
from lazyflow.roi import extendSlice, TinyVector

import numpy
import vigra
import warnings

class OpAnisotropicGaussianSmoothing(Operator):
    Input = InputSlot()
    Sigmas = InputSlot( value={'x':3.5, 'y':3.5, 'z':1.0} )
    
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        self._sigmas = self.Sigmas.value
    
    def execute(self, slot, subindex, roi, result):
        # Determine how much input data we'll need, and where the result will be relative to that input roi
        inputRoi, computeRoi = self._getInputComputeRois(roi)

        # Obtain the input data
        data = self.Input( *inputRoi ).wait()
        
        axiskeys = self.Input.meta.getAxisKeys()
        spatialkeys = filter( lambda k: k in 'xyz', axiskeys )
        sigma = map( self._sigmas.get, spatialkeys )
        
        # Smooth the input data
        smoothed = vigra.filters.gaussianSmoothing(data.astype(numpy.float32), sigma, window_size=2.0, roi=computeRoi, out=result[...,0]) # FIXME: Assumes channel is last axis
        expectedShape = tuple(TinyVector(computeRoi[1]) - TinyVector(computeRoi[0]))
        assert tuple(smoothed.shape) == expectedShape, "Smoothed data shape {} didn't match expected shape {}".format( smoothed.shape, roi.stop - roi.start )
        return result
    
    def _getInputComputeRois(self, roi):
        axiskeys = self.Input.meta.getAxisKeys()
        spatialkeys = filter( lambda k: k in 'xyz', axiskeys )
        sigma = map( self._sigmas.get, spatialkeys )
        inputSpatialShape = self.Input.meta.getTaggedShape()
        if 'c' in inputSpatialShape:
            del inputSpatialShape['c']

        spatialRoi = ( TinyVector(roi.start), TinyVector(roi.stop) )
        spatialRoi[0].pop( axiskeys.index('c') )
        spatialRoi[1].pop( axiskeys.index('c') )
        
        inputSpatialRoi = extendSlice(spatialRoi[0], spatialRoi[1], inputSpatialShape.values(), sigma, window=2.0)
        
        # Determine the roi within the input data we're going to request
        inputRoiOffset = spatialRoi[0] - inputSpatialRoi[0]
        computeRoi = (inputRoiOffset, inputRoiOffset + spatialRoi[1] - spatialRoi[0])
        
        # For some reason, vigra.filters.gaussianSmoothing will raise an exception if this parameter doesn't have the correct integer type.
        # (for example, if we give it as a numpy.ndarray with dtype=int64, we get an error)
        computeRoi = ( tuple(map(lambda x: int(x), computeRoi[0])),
                       tuple(map(lambda x: int(x), computeRoi[1])) )
        
        inputRoi = (list(inputSpatialRoi[0]), list(inputSpatialRoi[1]))
        inputRoi[0].insert( axiskeys.index('c'), 0 )
        inputRoi[1].insert( axiskeys.index('c'), 1 )

        return inputRoi, computeRoi
        
    def propagateDirty(self, slot, subindex, roi):
        # Halo calculation is bidirectional, so we can re-use the function that computes the halo during execute()
        inputRoi, _ = self._getInputComputeRois(roi)
        self.Output.setDirty( inputRoi[0], inputRoi[1] )

class OpSelectLabels(Operator):
    """
    Given two label images, produce a copy of BigLabels, EXCEPT first remove all labels 
    from BigLabels that do not overlap with any labels in SmallLabels.
    """
    SmallLabels = InputSlot()
    BigLabels = InputSlot()
    
    Output = OutputSlot()
    
    def setupOutputs(self):
        self.Output.meta.assignFrom( self.BigLabels.meta )
        self.Output.meta.dtype = numpy.uint8
        self.Output.meta.drange = (0,1)
    
    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output

        smallLabelReq = self.SmallLabels(roi.start, roi.stop)
        bigLabelReq = self.BigLabels(roi.start, roi.stop)
        
        smallLabelReq.submit()
        bigLabelReq.submit()
        
        smallLabels = smallLabelReq.wait()
        bigLabels = bigLabelReq.wait()
        
        prod = (smallLabels != 0) * bigLabels
        passed = numpy.unique(prod)
        
        all_label_values = numpy.zeros( (bigLabels.max()+1,), dtype=numpy.uint8 )
        for l in passed:
            all_label_values[l] = 1
        all_label_values[0] = 0
        
        result[:] = all_label_values[ bigLabels ]
        return result        

    def propagateDirty(self, slot, subindex, roi):
        warnings.warn("FIXME")

class OpThresholdTwoLevels(Operator):
    name = "opThresholdTwoLevels"
    
    RawInput = InputSlot(optional=True) # Display only
    
    InputImage = InputSlot()
    MinSize = InputSlot(stype='int', value=100)
    MaxSize = InputSlot(stype='int', value=1000000)
    HighThreshold = InputSlot(stype='float', value=0.5)
    LowThreshold = InputSlot(stype='float', value=0.1)
    SmootherSigma = InputSlot(value={ 'x':3.5, 'y':3.5, 'z':1.0})
    Channel = InputSlot(value=2)
    
    Output = OutputSlot()
    CachedOutput = OutputSlot() # For the GUI (blockwise-access)
    
    # Debug outputs
    InputChannels = OutputSlot(level=1)
    Smoothed = OutputSlot()
    BigRegions = OutputSlot()
    SmallRegions = OutputSlot()
    FilteredSmallLabels = OutputSlot()

    # Schematic:
    #
    #                                 HighThreshold                         MinSize,MaxSize                       --(cache)--> opColorize -> FilteredSmallLabels
    #                                              \                                       \                     /
    #        Channel       SmootherSigma            opHighThresholder --> opHighLabeler --> opHighLabelSizeFilter                  Output
    #               \                   \          /                 \                                            \               /
    # InputImage --> opChannelSlicer --> opSmoother -> Smoothed       --(cache)--> SmallRegions                    opSelectLabels --> opCache --> CachedOutput
    #                                              \                                                              /              
    #                                               opLowThresholder ----> opLowLabeler --------------------------                
    #                                              /                \
    #                                  LowThreshold                  --(cache)--> BigRegions
    
    def __init__(self, *args, **kwargs):
        super(OpThresholdTwoLevels, self).__init__(*args, **kwargs)
        
        self._opChannelSlicer = OpMultiArraySlicer2( parent=self )
        self._opChannelSlicer.Input.connect( self.InputImage )
        self._opChannelSlicer.AxisFlag.setValue('c')
        
        self._opSmoother = OpAnisotropicGaussianSmoothing(parent=self)
        self._opSmoother.Sigmas.connect( self.SmootherSigma )
        
        self._opLowThresholder = OpPixelOperator( parent=self )
        self._opLowThresholder.Input.connect( self._opSmoother.Output )

        self._opHighThresholder = OpPixelOperator( parent=self )
        self._opHighThresholder.Input.connect( self._opSmoother.Output )
        
        self._opLowLabeler = OpVigraLabelVolume( parent=self )
        self._opLowLabeler.Input.connect( self._opLowThresholder.Output )
        
        self._opHighLabeler = OpVigraLabelVolume( parent=self )
        self._opHighLabeler.Input.connect( self._opHighThresholder.Output )
        
        self._opHighLabelSizeFilter = OpFilterLabels( parent=self )
        self._opHighLabelSizeFilter.Input.connect( self._opHighLabeler.Output )
        self._opHighLabelSizeFilter.MinLabelSize.connect( self.MinSize )
        self._opHighLabelSizeFilter.MaxLabelSize.connect( self.MaxSize )

        self._opSelectLabels = OpSelectLabels( parent=self )        
        self._opSelectLabels.BigLabels.connect( self._opLowLabeler.Output )
        self._opSelectLabels.SmallLabels.connect( self._opHighLabeler.Output )

        self._opCache = OpCompressedCache( parent=self )
        self._opCache.Input.connect( self._opSelectLabels.Output )

        # Connect our own outputs
        self.Output.connect( self._opSelectLabels.Output )
        self.CachedOutput.connect( self._opCache.Output )
        
        # Debug outputs.
        self.Smoothed.connect( self._opSmoother.Output )
        self.InputChannels.connect( self._opChannelSlicer.Slices )
        
        # More debug outputs.  These all go through their own caches
        self._opBigRegionCache = OpCompressedCache( parent=self )
        self._opBigRegionCache.Input.connect( self._opLowThresholder.Output )
        self.BigRegions.connect( self._opBigRegionCache.Output )
                
        self._opSmallRegionCache = OpCompressedCache( parent=self )
        self._opSmallRegionCache.Input.connect( self._opHighThresholder.Output )
        self.SmallRegions.connect( self._opSmallRegionCache.Output )
        
        self._opFilteredSmallLabelsCache = OpCompressedCache( parent=self )
        self._opFilteredSmallLabelsCache.Input.connect( self._opHighLabelSizeFilter.Output )
        self._opColorizeSmallLabels = OpColorizeLabels( parent=self )
        self._opColorizeSmallLabels.Input.connect( self._opFilteredSmallLabelsCache.Output )
        self.FilteredSmallLabels.connect( self._opColorizeSmallLabels.Output )

    def setupOutputs(self):
        assert len(self.InputImage.meta.shape) <= 4, "This operator doesn't support 5D data."

        self._opSmoother.Input.connect( self._opChannelSlicer.Slices[ self.Channel.value ] )
        self._opLowThresholder.Function.setValue( lambda a: (a > self.LowThreshold.value).astype( numpy.uint8 ) )
        self._opHighThresholder.Function.setValue( lambda a: (a > self.HighThreshold.value).astype( numpy.uint8 ) )

        # Copy the input metadata to the output
        self.Output.meta.assignFrom( self.InputImage.meta )
        self.Output.meta.dtype=numpy.uint32
    
    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here..."

    def propagateDirty(self, slot, subindex, roi):
        pass # Nothing to do here

