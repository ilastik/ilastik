# Built-in
import gc
import warnings
import logging
from functools import partial

# Third-party
import numpy
import vigra
import psutil

# Lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpMultiArraySlicer2, OpPixelOperator, OpVigraLabelVolume, OpFilterLabels, \
                               OpCompressedCache, OpColorizeLabels, OpSingleChannelSelector, OperatorWrapper, \
                               OpMultiArrayStacker, OpMultiArraySlicer
from lazyflow.roi import extendSlice, TinyVector

# ilastik
from ilastik.utility.timer import Timer

logger = logging.getLogger(__name__)

def getMemoryUsageMb():
    """
    Get the current memory usage for the whole system (not just python).
    """
    # Collect garbage first
    gc.collect()
    vmem = psutil.virtual_memory()
    mem_usage_mb = (vmem.total - vmem.available) / 1e6
    return mem_usage_mb


class OpAnisotropicGaussianSmoothing(Operator):
    Input = InputSlot()
    Sigmas = InputSlot( value={'x':1.0, 'y':1.0, 'z':1.0} )
    
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        #if there is a time of dim 1, output won't have that
        timeIndex = self.Output.meta.axistags.index('t')
        if timeIndex<len(self.Output.meta.shape):
            newshape = list(self.Output.meta.shape)
            newshape.pop(timeIndex)
            self.Output.meta.shape = tuple(newshape)
            del self.Output.meta.axistags[timeIndex]
        self.Output.meta.dtype = numpy.float32 # vigra gaussian only supports float32
        self._sigmas = self.Sigmas.value
        assert isinstance(self.Sigmas.value, dict), "Sigmas slot expects a dict"
        assert set(self._sigmas.keys()) == set('xyz'), "Sigmas slot expects three key-value pairs for x,y,z"
        
        self.Output.setDirty( slice(None) )
    
    def execute(self, slot, subindex, roi, result):
        assert all(roi.stop <= self.Input.meta.shape), "Requested roi {} is too large for this input image of shape {}.".format( roi, self.Input.meta.shape )
        # Determine how much input data we'll need, and where the result will be relative to that input roi
        inputRoi, computeRoi = self._getInputComputeRois(roi)

        # Obtain the input data
        with Timer() as resultTimer:
            data = self.Input( *inputRoi ).wait()
        logger.debug("Obtaining input data took {} seconds for roi {}".format( resultTimer.seconds(), inputRoi ))
        
        # Must be float32
        if data.dtype != numpy.float32:
            data = data.astype(numpy.float32)
        
        axiskeys = self.Input.meta.getAxisKeys()
        spatialkeys = filter( lambda k: k in 'xyz', axiskeys )
        sigma = map( self._sigmas.get, spatialkeys )
        
        
        # Smooth the input data
        smoothed = vigra.filters.gaussianSmoothing(data, sigma, window_size=2.0, roi=computeRoi, out=result[...,0]) # FIXME: Assumes channel is last axis
        expectedShape = tuple(TinyVector(computeRoi[1]) - TinyVector(computeRoi[0]))
        assert tuple(smoothed.shape) == expectedShape, "Smoothed data shape {} didn't match expected shape {}".format( smoothed.shape, roi.stop - roi.start )
        return result
    
    def _getInputComputeRois(self, roi):
        axiskeys = self.Input.meta.getAxisKeys()
        spatialkeys = filter( lambda k: k in 'xyz', axiskeys )
        sigma = map( self._sigmas.get, spatialkeys )
        inputSpatialShape = self.Input.meta.getTaggedShape()
        spatialRoi = ( TinyVector(roi.start), TinyVector(roi.stop) )
        if 'c' in inputSpatialShape:
            del inputSpatialShape['c']
        if 't' in inputSpatialShape.keys():
            assert inputSpatialShape['t'] == 1
            spatialRoi[0].pop( axiskeys.index('t') )
            spatialRoi[1].pop( axiskeys.index('t') )

        if 'z' in inputSpatialShape.keys() and inputSpatialShape['z']==1:
            #2D image, avoid kernel longer than line exception
            spatialRoi[0].pop( axiskeys.index('z'))
            spatialRoi[1].pop( axiskeys.index('z'))
            
        
        spatialRoi[0].pop( axiskeys.index('c') )
        spatialRoi[1].pop( axiskeys.index('c') )
        
        inputSpatialRoi = extendSlice(spatialRoi[0], spatialRoi[1], inputSpatialShape.values(), sigma, window=2.0)
        
        # Determine the roi within the input data we're going to request
        inputRoiOffset = spatialRoi[0] - inputSpatialRoi[0]
        computeRoi = (inputRoiOffset, inputRoiOffset + spatialRoi[1] - spatialRoi[0])
        
        # For some reason, vigra.filters.gaussianSmoothing will raise an exception if this parameter doesn't have the correct integer type.
        # (for example, if we give it as a numpy.ndarray with dtype=int64, we get an error)
        computeRoi = ( tuple(map(int, computeRoi[0])),
                       tuple(map(int, computeRoi[1])) )
        
        inputRoi = (list(inputSpatialRoi[0]), list(inputSpatialRoi[1]))
        inputRoi[0].insert( axiskeys.index('c'), 0 )
        inputRoi[1].insert( axiskeys.index('c'), 1 )

        return inputRoi, computeRoi
        
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Input:
            # Halo calculation is bidirectional, so we can re-use the function that computes the halo during execute()
            inputRoi, _ = self._getInputComputeRois(roi)
            self.Output.setDirty( inputRoi[0], inputRoi[1] )
        elif slot == self.Sigmas:
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown input slot: {}".format( slot.name )

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

        # This operator is typically used with very big rois, so be extremely memory-conscious:
        # - Don't request the small and big inputs in parallel. 
        # - Clean finished requests immediately (don't wait for this function to exit)
        # - Delete intermediate results as soon as possible.
        
        if logger.isEnabledFor(logging.DEBUG):
            dtypeBytes = self.SmallLabels.meta.getDtypeBytes()
            roiShape = roi.stop - roi.start
            logger.debug( "Roi shape is {} = {} MB".format( roiShape, numpy.prod(roiShape) * dtypeBytes / 1e6 ) )
            starting_memory_usage_mb = getMemoryUsageMb()
            logger.debug("Starting with memory usage: {} MB".format( starting_memory_usage_mb ))

        def logMemoryIncrease(msg):
            """Log a debug message about the RAM usage compared to when this function started execution."""
            if logger.isEnabledFor(logging.DEBUG):
                memory_increase_mb = getMemoryUsageMb() - starting_memory_usage_mb
                logger.debug("{}, memory increase is: {} MB".format( msg, memory_increase_mb ))

        smallLabelsReq = self.SmallLabels(roi.start, roi.stop)
        smallLabels = smallLabelsReq.wait()
        smallLabelsReq.clean()
        logMemoryIncrease("After obtaining small labels")

        smallNonZero = numpy.ndarray(shape=smallLabels.shape, dtype=bool)
        smallNonZero[...] = (smallLabels != 0)
        del smallLabels

        logMemoryIncrease("Before obtaining big labels")
        bigLabels = self.BigLabels(roi.start, roi.stop).wait()
        logMemoryIncrease("After obtaining big labels")
        
        prod = smallNonZero * bigLabels
        
        del smallNonZero
        
        passed = numpy.unique(prod)
        logMemoryIncrease("After taking product")
        del prod
        
        all_label_values = numpy.zeros( (bigLabels.max()+1,), dtype=numpy.uint8 )
        for i, l in enumerate(passed):
            all_label_values[l] = i+1
        all_label_values[0] = 0
        
        result[:] = all_label_values[ bigLabels ]
        
        logMemoryIncrease("Just before return")
        return result        

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.SmallLabels or slot == self.BigLabels:
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown input slot: {}".format( slot.name )

class OpThresholdTwoLevels(Operator):
    name = "opThresholdTwoLevels5d"
    
    RawInput = InputSlot(optional=True) # Display only
    
    InputImage = InputSlot()
    MinSize = InputSlot(stype='int', value=100)
    MaxSize = InputSlot(stype='int', value=1000000)
    HighThreshold = InputSlot(stype='float', value=0.5)
    LowThreshold = InputSlot(stype='float', value=0.2)
    SingleThreshold = InputSlot(stype='float', value=0.5)
    SmootherSigma = InputSlot(value={ 'x':1.0, 'y':1.0, 'z':1.0})
    Channel = InputSlot(value=0)
    CurOperator = InputSlot(stype='int', value=0)
    
    Output = OutputSlot()
    
    CachedOutput = OutputSlot() # For the GUI (blockwise-access)
    
    # For serialization
    InputHdf5 = InputSlot(optional=True)
    
    CleanBlocks = OutputSlot()
    
    OutputHdf5 = OutputSlot()
    
    # Debug outputs
    InputChannel = OutputSlot()
    Smoothed = OutputSlot()
    BigRegions = OutputSlot()
    SmallRegions = OutputSlot()
    FilteredSmallLabels = OutputSlot()
    BeforeSizeFilter = OutputSlot()
    
    
    def __init__(self, *args, **kwargs):
        super(OpThresholdTwoLevels, self).__init__(*args, **kwargs)
        
        self._opTimeSlicer = OpMultiArraySlicer(parent=self)
        self._opTimeSlicer.AxisFlag.setValue('t')
        self._opTimeSlicer.Input.connect( self.InputImage )
        assert self._opTimeSlicer.Slices.level == 1
        
        self._opChannelSelector = OperatorWrapper(OpSingleChannelSelector, parent = self )
        self._opChannelSelector.Input.connect( self._opTimeSlicer.Slices )
        
        self._opSmoother = OperatorWrapper(OpAnisotropicGaussianSmoothing, parent=self)
        self._opSmoother.Sigmas.connect( self.SmootherSigma )
        
        self.opThreshold1 = OperatorWrapper(OpThresholdOneLevel, parent=self)
        self.opThreshold1.InputImage.connect(self._opSmoother.Output)
        self.opThreshold1.Threshold.connect(self.SingleThreshold)
        self.opThreshold1.MinSize.connect(self.MinSize)
        self.opThreshold1.MaxSize.connect(self.MaxSize)
        
        
        self.opThreshold2 = OperatorWrapper(OpThresholdTwoLevels4d, parent = self)
        self.opThreshold2.InputImage.connect(self._opSmoother.Output)
        self.opThreshold2.MinSize.connect(self.MinSize)
        self.opThreshold2.MaxSize.connect(self.MaxSize)
        self.opThreshold2.LowThreshold.connect(self.LowThreshold)
        self.opThreshold2.HighThreshold.connect(self.HighThreshold)
        
        self._opTimeStacker2 = OpMultiArrayStacker(parent=self)
        self._opTimeStacker2.AxisFlag.setValue('t')
        self._opTimeStacker2.Images.connect(self.opThreshold2.Output)
        assert self._opTimeStacker2.Output.level==0
        
        self._opTimeStacker1 = OpMultiArrayStacker(parent=self)
        self._opTimeStacker1.AxisFlag.setValue('t')
        self._opTimeStacker1.Images.connect(self.opThreshold1.Output)
        assert self._opTimeStacker1.Output.level==0
        
        
        #cache our own output, don't propagate from internal operator
        self._opCache = OpCompressedCache( parent=self )
        self._opCache.InputHdf5.connect( self.InputHdf5 )
        
        self.CachedOutput.connect(self._opCache.Output)
        
        # Serialization outputs
        self.CleanBlocks.connect( self._opCache.CleanBlocks )
        self.OutputHdf5.connect( self._opCache.OutputHdf5 )
        
        #Debug outputs
        self._smoothStacker = OpMultiArrayStacker(parent=self)
        self._smoothStacker.AxisFlag.setValue('t')
        self._smoothStacker.Images.connect(self._opSmoother.Output)
        self.Smoothed.connect(self._smoothStacker.Output)
        
        self._inputStacker = OpMultiArrayStacker(parent=self)
        self._inputStacker.AxisFlag.setValue('t')
        self._inputStacker.Images.connect(self._opChannelSelector.Output)
        self.InputChannel.connect(self._inputStacker.Output)
        
        #Debug 2 level operator
        self._bigRegionsStacker = OpMultiArrayStacker(parent=self)
        self._bigRegionsStacker.AxisFlag.setValue('t')
        self.BigRegions.connect(self._bigRegionsStacker.Output)
        
        self._smallRegionsStacker = OpMultiArrayStacker(parent=self)
        self._smallRegionsStacker.AxisFlag.setValue('t')
        self.SmallRegions.connect(self._smallRegionsStacker.Output)
        
        
        self._filSmallRegionsStacker = OpMultiArrayStacker(parent=self)
        self._filSmallRegionsStacker.AxisFlag.setValue('t')
        self.FilteredSmallLabels.connect(self._filSmallRegionsStacker.Output)
        
        
        #Debug 1 level operator
        self._beforeFilterStacker = OpMultiArrayStacker(parent=self)
        self._beforeFilterStacker.AxisFlag.setValue('t')
        
        self.BeforeSizeFilter.connect(self._beforeFilterStacker.Output)
        
    def setupOutputs(self):
        #FIXME: this happens when someone deletes the other prediction channels to save space
        #we should find a better way to handle this
        channelAxis = self.InputImage.meta.axistags.index('c')
        hackChannel = self.Channel.value
        if hackChannel > self.InputImage.meta.shape[channelAxis]:
            hackChannel = 0

        self._opChannelSelector.Index.setValue(hackChannel)
        self._opSmoother.Input.connect( self._opChannelSelector.Output )
        
        curIndex = self.CurOperator.value
        if curIndex==0:
            self.Output.connect(self._opTimeStacker1.Output)
            self._opCache.Input.connect( self._opTimeStacker1.Output )
            
            self._bigRegionsStacker.Images.disconnect()
            self._smallRegionsStacker.Images.disconnect()
            self._filSmallRegionsStacker.Images.disconnect()
            
            self._beforeFilterStacker.Images.connect(self.opThreshold1.BeforeSizeFilter)
            
            assert self.Output.ready()
            assert self.BeforeSizeFilter.ready()
            #FIXME: these asserts fail because there is no way to make an operator "partially ready"
            #assert self.BigRegions.ready()==False
            
        elif curIndex==1:
            self.Output.connect(self._opTimeStacker2.Output)
            self._opCache.Input.connect( self._opTimeStacker2.Output )
            
            self._bigRegionsStacker.Images.connect(self.opThreshold2.BigRegions)
            self._smallRegionsStacker.Images.connect(self.opThreshold2.SmallRegions)
            self._filSmallRegionsStacker.Images.connect(self.opThreshold2.FilteredSmallLabels)
            
            self._beforeFilterStacker.Images.disconnect()
            
            assert self.Output.ready()
            assert self.BigRegions.ready()
            #FIXME: these asserts fail because there is no way to make an operator "partially ready"
            #assert self._beforeFilterStacker.Output.ready()==False
            #assert self.BeforeSizeFilter.ready()==False
        else:
            #we only have two tabs
            return
        
    def setInSlot(self, slot, subindex, roi, value):
        pass
    
    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."
    
    def propagateDirty(self, slot, subindex, roi):
        pass # Nothing to do...
        

class OpThresholdTwoLevels4d(Operator):
    name = "opThresholdTwoLevels4d"
    
    InputImage = InputSlot()
    MinSize = InputSlot(stype='int', value=100)
    MaxSize = InputSlot(stype='int', value=1000000)
    HighThreshold = InputSlot(stype='float', value=0.5)
    LowThreshold = InputSlot(stype='float', value=0.2)
    
    Output = OutputSlot()
    CachedOutput = OutputSlot() # For the GUI (blockwise-access)
    
    # For serialization
    InputHdf5 = InputSlot(optional=True)
    OutputHdf5 = OutputSlot()
    CleanBlocks = OutputSlot()
    
    # Debug outputs
    BigRegions = OutputSlot()
    SmallRegions = OutputSlot()
    FilteredSmallLabels = OutputSlot()

    # Schematic:
    #
    #           HighThreshold                         MinSize,MaxSize                       --(cache)--> opColorize -> FilteredSmallLabels
    #                   \                                       \                     /
    #           opHighThresholder --> opHighLabeler --> opHighLabelSizeFilter                           Output
    #          /                   \          /                 \                                            \                         /
    # InputImage        --(cache)--> SmallRegions                    opSelectLabels -->opFinalLabelSizeFilter--> opCache --> CachedOutput
    #          \                                                              /                                           /       \
    #           opLowThresholder ----> opLowLabeler --------------------------                                       InputHdf5     --> OutputHdf5
    #                   /                \                                                                                        -> CleanBlocks
    #           LowThreshold            --(cache)--> BigRegions
    
    def __init__(self, *args, **kwargs):
        super(OpThresholdTwoLevels4d, self).__init__(*args, **kwargs)
        
        self._opLowThresholder = OpPixelOperator(parent=self )
        self._opLowThresholder.Input.connect( self.InputImage )

        self._opHighThresholder = OpPixelOperator(parent=self )
        self._opHighThresholder.Input.connect( self.InputImage )
        
        self._opLowLabeler = OpVigraLabelVolume(parent=self )
        self._opLowLabeler.Input.connect( self._opLowThresholder.Output )
        
        self._opHighLabeler = OpVigraLabelVolume(parent=self )
        self._opHighLabeler.Input.connect( self._opHighThresholder.Output )
        
        self._opHighLabelSizeFilter = OpFilterLabels(parent=self )
        self._opHighLabelSizeFilter.Input.connect( self._opHighLabeler.Output )
        self._opHighLabelSizeFilter.MinLabelSize.connect( self.MinSize )
        self._opHighLabelSizeFilter.MaxLabelSize.connect( self.MaxSize )
        self._opHighLabelSizeFilter.BinaryOut.setValue(False) #we do the binarization in opSelectLabels
                                                              #this way, we get to display pretty colors

        self._opSelectLabels = OpSelectLabels( parent=self )        
        self._opSelectLabels.BigLabels.connect( self._opLowLabeler.Output )
        self._opSelectLabels.SmallLabels.connect( self._opHighLabelSizeFilter.Output )
        
        #remove the remaining very large objects - 
        #they might still be present in case a big object
        #was split into many small ones for the higher threshold
        #and they got reconnected again at lower threshold
        self._opFinalLabelSizeFilter = OpFilterLabels( parent=self )
        self._opFinalLabelSizeFilter.Input.connect(self._opSelectLabels.Output )
        self._opFinalLabelSizeFilter.MinLabelSize.connect( self.MinSize )
        self._opFinalLabelSizeFilter.MaxLabelSize.connect( self.MaxSize )
        self._opFinalLabelSizeFilter.BinaryOut.setValue(True)

        self._opCache = OpCompressedCache( parent=self )
        self._opCache.InputHdf5.connect( self.InputHdf5 )
        self._opCache.Input.connect( self._opFinalLabelSizeFilter.Output )

        # Connect our own outputs
        self.Output.connect( self._opFinalLabelSizeFilter.Output )
        self.CachedOutput.connect( self._opCache.Output )

        # Serialization outputs
        self.CleanBlocks.connect( self._opCache.CleanBlocks )
        self.OutputHdf5.connect( self._opCache.OutputHdf5 )
        
        # Debug outputs.
        #self.Smoothed.connect( self._opSmoother.Output )
        
        #self.InputChannel.connect( self._opChannelSelector.Output )
        
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
        timeIndex = self.InputImage.meta.axistags.index('t')
        
        if timeIndex<len(self.InputImage.meta.shape):
            assert self.InputImage.meta.shape[timeIndex]==1, "This operator doesn't support 5D data."
        
        def thresholdToUint8(thresholdValue, a):
            drange = self.InputImage.meta.drange
            if drange is not None:
                assert drange[0] == 0, "Don't know how to threshold data with this drange."
                thresholdValue *= drange[1]
            if a.dtype == numpy.uint8:
                # In-place (does numpy optimize cases like this?)
                a[:] = (a > thresholdValue)
                return a
            else:
                return (a > thresholdValue).astype(numpy.uint8)
        
        self._opLowThresholder.Function.setValue( partial( thresholdToUint8, self.LowThreshold.value ) )
        self._opHighThresholder.Function.setValue( partial( thresholdToUint8, self.HighThreshold.value ) )

        # Copy the input metadata to the output
        self.Output.meta.assignFrom( self.InputImage.meta )
        self.Output.meta.dtype=numpy.uint8
    
    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here..."

    def propagateDirty(self, slot, subindex, roi):
        pass # Nothing to do here

    def setInSlot(self, slot, subindex, roi, value):
        assert slot == self.InputHdf5, "Invalid slot for setInSlot(): {}".format( slot.name )
        # Nothing to do here.
        # Our Input slots are directly fed into the cache, 
        #  so all calls to __setitem__ are forwarded automatically 
        
        
class OpThresholdOneLevel(Operator):
    name = "OpThresholdOneLevel"
    
    InputImage = InputSlot()
    MinSize = InputSlot(stype='int', value=100)
    MaxSize = InputSlot(stype='int', value=1000000)
    Threshold = InputSlot(stype='float', value=0.5)
    
    Output = OutputSlot()
    
    #debug output
    BeforeSizeFilter = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpThresholdOneLevel, self).__init__(*args, **kwargs)
        
        self._opThresholder = OpPixelOperator(parent=self )
        self._opThresholder.Input.connect( self.InputImage )
        
        self._opLabeler = OpVigraLabelVolume( parent=self )
        self._opLabeler.Input.connect(self._opThresholder.Output)
        
        self.BeforeSizeFilter.connect(self._opLabeler.Output)
        
        self._opFilter = OpFilterLabels( parent=self )
        self._opFilter.Input.connect(self._opLabeler.Output )
        self._opFilter.MinLabelSize.connect( self.MinSize )
        self._opFilter.MaxLabelSize.connect( self.MaxSize )
        self._opFilter.BinaryOut.setValue(True)
        
        self.Output.connect(self._opFilter.Output)
        
    def setupOutputs(self):
        timeIndex = self.InputImage.meta.axistags.index('t')
        
        if timeIndex<len(self.InputImage.meta.shape):
            assert self.InputImage.meta.shape[timeIndex]==1, "This operator doesn't support 5D data."
        
        def thresholdToUint8(thresholdValue, a):
            drange = self.InputImage.meta.drange
            if drange is not None:
                assert drange[0] == 0, "Don't know how to threshold data with this drange."
                thresholdValue *= drange[1]
            if a.dtype == numpy.uint8:
                # In-place (does numpy optimize cases like this?)
                a[:] = (a > thresholdValue)
                return a
            else:
                return (a > thresholdValue).astype(numpy.uint8)
        
        self._opThresholder.Function.setValue( partial( thresholdToUint8, self.Threshold.value ) )
        # Copy the input metadata to the output
        self.Output.meta.assignFrom( self.InputImage.meta )
        self.Output.meta.dtype=numpy.uint8
        
    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here..."

    def propagateDirty(self, slot, subindex, roi):
        pass # Nothing to do here

    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here.
        # Our Input slots are directly fed into the cache, 
        #  so all calls to __setitem__ are forwarded automatically 
        pass
