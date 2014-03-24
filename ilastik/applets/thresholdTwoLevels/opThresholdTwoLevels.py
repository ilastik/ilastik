# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

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
from lazyflow.operators import OpMultiArraySlicer2, OpPixelOperator, OpLabelVolume, OpFilterLabels, \
                               OpCompressedCache, OpColorizeLabels, OpSingleChannelSelector, OperatorWrapper, \
                               OpMultiArrayStacker, OpMultiArraySlicer, OpReorderAxes
from lazyflow.roi import extendSlice, TinyVector
from lazyflow.rtype import SubRegion
from lazyflow.request import Request, RequestPool

# ilastik
from lazyflow.utility.timer import Timer

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


#TODO: hide this operator somewhere. deep.
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
        
        xIndex = self.Input.meta.axistags.index('x')
        yIndex = self.Input.meta.axistags.index('y')
        zIndex = self.Input.meta.axistags.index('z') if self.Input.meta.axistags.index('z')<len(self.Input.meta.shape) else None
        cIndex = self.Input.meta.axistags.index('c') if self.Input.meta.axistags.index('c')<len(self.Input.meta.shape) else None
        
        # Must be float32
        if data.dtype != numpy.float32:
            data = data.astype(numpy.float32)
        
        axiskeys = self.Input.meta.getAxisKeys()
        spatialkeys = filter( lambda k: k in 'xyz', axiskeys )

        # we need to remove a singleton z axis, otherwise we get 
        # 'kernel longer than line' errors
        reskey = [slice(None, None, None)]*len(self.Input.meta.shape)
        reskey[cIndex]=0
        if zIndex and self.Input.meta.shape[zIndex]==1:
            removedZ = True
            data = data.reshape((data.shape[xIndex], data.shape[yIndex]))
            reskey[zIndex]=0
            spatialkeys = filter( lambda k: k in 'xy', axiskeys )
        else:
            removedZ = False

        sigma = map(self._sigmas.get, spatialkeys)
        #Check if we need to smooth
        if any([x < 0.1 for x in sigma]):
            if removedZ:
                resultXY = vigra.taggedView(result, axistags="".join(axiskeys))
                resultXY = resultXY.withAxes(*'xy')
                resultXY[:] = data
            else:
                result[:] = data
            return result

        # Smooth the input data
        smoothed = vigra.filters.gaussianSmoothing(data, sigma, window_size=2.0, roi=computeRoi, out=result[tuple(reskey)]) # FIXME: Assumes channel is last axis
        expectedShape = tuple(TinyVector(computeRoi[1]) - TinyVector(computeRoi[0]))
        assert tuple(smoothed.shape) == expectedShape, "Smoothed data shape {} didn't match expected shape {}".format( smoothed.shape, roi.stop - roi.start )
        return result
    
    def _getInputComputeRois(self, roi):
        axiskeys = self.Input.meta.getAxisKeys()
        spatialkeys = filter( lambda k: k in 'xyz', axiskeys )
        sigma = map( self._sigmas.get, spatialkeys )
        inputSpatialShape = self.Input.meta.getTaggedShape()
        spatialRoi = ( TinyVector(roi.start), TinyVector(roi.stop) )
        tIndex = None
        cIndex = None
        zIndex = None
        if 'c' in inputSpatialShape:
            del inputSpatialShape['c']
            cIndex = axiskeys.index('c')
        if 't' in inputSpatialShape.keys():
            assert inputSpatialShape['t'] == 1
            tIndex = axiskeys.index('t')

        if 'z' in inputSpatialShape.keys() and inputSpatialShape['z']==1:
            #2D image, avoid kernel longer than line exception
            del inputSpatialShape['z']
            zIndex = axiskeys.index('z')
            
        indices = [tIndex, cIndex, zIndex]
        indices = sorted(indices, reverse=True)
        for ind in indices:
            if ind:
                spatialRoi[0].pop(ind)
                spatialRoi[1].pop(ind)
        
        inputSpatialRoi = extendSlice(spatialRoi[0], spatialRoi[1], inputSpatialShape.values(), sigma, window=2.0)
        
        # Determine the roi within the input data we're going to request
        inputRoiOffset = spatialRoi[0] - inputSpatialRoi[0]
        computeRoi = (inputRoiOffset, inputRoiOffset + spatialRoi[1] - spatialRoi[0])
        
        # For some reason, vigra.filters.gaussianSmoothing will raise an exception if this parameter doesn't have the correct integer type.
        # (for example, if we give it as a numpy.ndarray with dtype=int64, we get an error)
        computeRoi = ( tuple(map(int, computeRoi[0])),
                       tuple(map(int, computeRoi[1])) )
        
        inputRoi = (list(inputSpatialRoi[0]), list(inputSpatialRoi[1]))
        for ind in reversed(indices):
            if ind:
                inputRoi[0].insert( ind, 0 )
                inputRoi[1].insert( ind, 1 )

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


## Combine high and low threshold
# This operator combines the thresholding results. We want the resulting labels to be
# the ones that passed the lower threshold AND that have at least one pixel that passed
# the higher threshold. E.g.:
#
#   Thresholds: High=4, Low=1
#
#     0 2 0        0 2 0 
#     2 5 2        2 3 2
#     0 2 0        0 2 0
#
#   Results:
#
#     0 1 0        0 0 0
#     1 1 1        0 0 0
#     0 1 0        0 0 0
#
#
#   Given two label images, produce a copy of BigLabels, EXCEPT first remove all labels 
#   from BigLabels that do not overlap with any labels in SmallLabels.
class OpSelectLabels(Operator):

    ## The smaller clusters
    # i.e. results of high thresholding
    SmallLabels = InputSlot()

    ## The larger clusters
    # i.e. results of low thresholding
    BigLabels = InputSlot()

    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.BigLabels.meta)
        self.Output.meta.dtype = numpy.uint32
        self.Output.meta.drange = (0, 1)

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output

        # This operator is typically used with very big rois, so be extremely memory-conscious:
        # - Don't request the small and big inputs in parallel.
        # - Clean finished requests immediately (don't wait for this function to exit)
        # - Delete intermediate results as soon as possible.

        if logger.isEnabledFor(logging.DEBUG):
            dtypeBytes = self.SmallLabels.meta.getDtypeBytes()
            roiShape = roi.stop - roi.start
            logger.debug("Roi shape is {} = {} MB".format(roiShape, numpy.prod(roiShape) * dtypeBytes / 1e6 ))
            starting_memory_usage_mb = getMemoryUsageMb()
            logger.debug("Starting with memory usage: {} MB".format(starting_memory_usage_mb))

        def logMemoryIncrease(msg):
            """Log a debug message about the RAM usage compared to when this function started execution."""
            if logger.isEnabledFor(logging.DEBUG):
                memory_increase_mb = getMemoryUsageMb() - starting_memory_usage_mb
                logger.debug("{}, memory increase is: {} MB".format(msg, memory_increase_mb))

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

        # get labels that passed the masking
        passed = numpy.unique(prod)
        # 0 is not a valid label
        passed = numpy.setdiff1d(passed, (0,))

        logMemoryIncrease("After taking product")
        del prod

        all_label_values = numpy.zeros((bigLabels.max()+1,),
                                       dtype=numpy.uint32)

        for i, l in enumerate(passed):
            all_label_values[l] = i+1
        all_label_values[0] = 0

        # tricky: map the old labels to the new ones, labels that didnt pass 
        # are mapped to zero
        result[:] = all_label_values[bigLabels]

        logMemoryIncrease("Just before return")
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.SmallLabels or slot == self.BigLabels:
            self.Output.setDirty(slice(None))
        else:
            assert False, "Unknown input slot: {}".format(slot.name)


## High level operator for one/two level threshold
class OpThresholdTwoLevels(Operator):
    name = "OpThresholdTwoLevels"

    RawInput = InputSlot(optional=True)  # Display only

    InputImage = InputSlot()
    MinSize = InputSlot(stype='int', value=10)
    MaxSize = InputSlot(stype='int', value=1000000)
    HighThreshold = InputSlot(stype='float', value=0.5)
    LowThreshold = InputSlot(stype='float', value=0.2)
    SingleThreshold = InputSlot(stype='float', value=0.5)
    SmootherSigma = InputSlot(value={'x': 1.0, 'y': 1.0, 'z': 1.0})
    Channel = InputSlot(value=0)
    CurOperator = InputSlot(stype='int', value=0)

    Output = OutputSlot()

    CachedOutput = OutputSlot()  # For the GUI (blockwise-access)

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

        self._opReorder1 = OpReorderAxes(parent=self)
        self._opReorder1.AxisOrder.setValue('txyzc')
        self._opReorder1.Input.connect(self.InputImage)

        # slice in time for anisotropic gauss
        self._opTimeSlicer = OpMultiArraySlicer(parent=self)
        self._opTimeSlicer.AxisFlag.setValue('t')
        self._opTimeSlicer.Input.connect(self._opReorder1.Output)
        assert self._opTimeSlicer.Slices.level == 1

        self._opChannelSelector = OperatorWrapper(OpSingleChannelSelector, parent=self)
        self._opChannelSelector.Input.connect(self._opTimeSlicer.Slices)
        self._opChannelSelector.Index.connect(self.Channel)

        # anisotropic gauss
        self._opSmoother = OperatorWrapper(OpAnisotropicGaussianSmoothing, parent=self)
        self._opSmoother.Sigmas.connect(self.SmootherSigma)
        self._opSmoother.Input.connect(self._opChannelSelector.Output)

        # stack output again, everything is now going to work for arbitrary dimensions
        self._smoothStacker = OpMultiArrayStacker(parent=self)
        self._smoothStacker.AxisFlag.setValue('t')
        self._smoothStacker.Images.connect(self._opSmoother.Output)

        # debug output
        self.Smoothed.connect(self._smoothStacker.Output)

        # single threshold operator
        self.opThreshold1 = _OpThresholdOneLevel(parent=self)
        self.opThreshold1.InputImage.connect(self._smoothStacker.Output)
        self.opThreshold1.Threshold.connect(self.SingleThreshold)
        self.opThreshold1.MinSize.connect(self.MinSize)
        self.opThreshold1.MaxSize.connect(self.MaxSize)

        # double threshold operator
        self.opThreshold2 = _OpThresholdTwoLevels(parent=self)
        self.opThreshold2.InputImage.connect(self._smoothStacker.Output)
        self.opThreshold2.MinSize.connect(self.MinSize)
        self.opThreshold2.MaxSize.connect(self.MaxSize)
        self.opThreshold2.LowThreshold.connect(self.LowThreshold)
        self.opThreshold2.HighThreshold.connect(self.HighThreshold)

        # HACK: For backwards compatibility with old projects, 
        #       the cache must by in xyzct order,
        #       because the cache is loaded directly from the serializer
        self._op5CacheInput = OpReorderAxes(parent=self)
        self._op5CacheInput.AxisOrder.setValue( "xyzct" )

        #cache our own output, don't propagate from internal operator
        self._opCache = OpCompressedCache(parent=self)
        self._opCache.name = "OpThresholdTwoLevels._opCache"
        self._opCache.InputHdf5.connect(self.InputHdf5)
        self._opCache.Input.connect( self._op5CacheInput.Output )

        self._op5CacheOutput = OpReorderAxes(parent=self)
        self._op5CacheOutput.Input.connect( self._opCache.Output )

        self._opReorder2 = OpReorderAxes(parent=self)
        self.Output.connect(self._opReorder2.Output)

        self.CachedOutput.connect(self._op5CacheOutput.Output)

        # Serialization outputs
        self.CleanBlocks.connect(self._opCache.CleanBlocks)
        self.OutputHdf5.connect(self._opCache.OutputHdf5)

        #Debug outputs
        #TODO reorder?
        self._inputStacker = OpMultiArrayStacker(parent=self)
        self._inputStacker.AxisFlag.setValue('t')
        self._inputStacker.Images.connect(self._opChannelSelector.Output)
        self.InputChannel.connect(self._inputStacker.Output)

    def setupOutputs(self):

        t_index = self.InputImage.meta.axistags.index('t')
        self._smoothStacker.AxisIndex.setValue(t_index)
        self._inputStacker.AxisIndex.setValue(t_index)
        self._opReorder2.AxisOrder.setValue("".join(self.InputImage.meta.getAxisKeys()))

        # propagate drange
        self.opThreshold1.InputImage.meta.drange = self.InputImage.meta.drange
        self.opThreshold2.InputImage.meta.drange = self.InputImage.meta.drange

        curIndex = self.CurOperator.value
        if curIndex == 0:
            # disconnect all operators that are not needed for SingleThreshold
            # start from back
            for slot in [self.BigRegions, self.SmallRegions,
                         self.FilteredSmallLabels]:
                slot.disconnect()
                slot.meta.NOTREADY = True
            self._op5CacheInput.Input.disconnect()
            self._opReorder2.Input.disconnect()

            # connect the operators for SingleThreshold
            self._opReorder2.Input.connect(self.opThreshold1.Output)
            # Blockshape is the entire block, except only 1 time slice
            tagged_shape = self.opThreshold1.Output.meta.getTaggedShape()
            tagged_shape['t'] = 1
            
            # Blockshape must correspond to cache input order
            blockshape = map( lambda k: tagged_shape[k], 'xyzct' )
            self._opCache.BlockShape.setValue(tuple(blockshape))
            self._op5CacheInput.Input.connect(self.opThreshold1.Output)
            self._op5CacheOutput.AxisOrder.setValue( self._op5CacheInput.Input.meta.getAxisKeys() )

            self.BeforeSizeFilter.connect(self.opThreshold1.BeforeSizeFilter)
            self.BeforeSizeFilter.meta.NOTREADY = None

            # Output may not actually be ready if there aren't any channels yet.
            # assert self.Output.ready()
            # assert self.BeforeSizeFilter.ready()

        elif curIndex == 1:
            # disconnect all operators that are not needed for SingleThreshold
            # start from back
            self.BeforeSizeFilter.disconnect()
            self.BeforeSizeFilter.meta.NOTREADY = True
            self._op5CacheInput.Input.disconnect()
            self._opReorder2.Input.disconnect()

            # connect the operators for TwoLevelThreshold
            self._opReorder2.Input.connect(self.opThreshold2.Output)
            # Blockshape is the entire block, except only 1 time slice
            tagged_shape = self.opThreshold2.Output.meta.getTaggedShape()
            tagged_shape['t'] = 1

            # Blockshape must correspond to cache input order
            blockshape = map( lambda k: tagged_shape[k], 'xyzct' )
            self._opCache.BlockShape.setValue(tuple(blockshape))
            self._op5CacheInput.Input.connect( self.opThreshold2.Output )

            self.BigRegions.connect(self.opThreshold2.BigRegions)
            self.SmallRegions.connect(self.opThreshold2.SmallRegions)
            self.FilteredSmallLabels.connect(self.opThreshold2.FilteredSmallLabels)
            for slot in [self.BigRegions, self.SmallRegions,
                         self.FilteredSmallLabels]:
                slot.meta.NOTREADY = None

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
        pass  # Nothing to do...


## internal operator for one level thresholding
#
# The input must have 5 dimensions.
class _OpThresholdOneLevel(Operator):
    name = "_OpThresholdOneLevel"

    InputImage = InputSlot()
    MinSize = InputSlot(stype='int', value=0)
    MaxSize = InputSlot(stype='int', value=1000000)
    Threshold = InputSlot(stype='float', value=0.5)

    Output = OutputSlot()

    #debug output
    BeforeSizeFilter = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(_OpThresholdOneLevel, self).__init__(*args, **kwargs)

        self._opThresholder = OpPixelOperator(parent=self )
        self._opThresholder.Input.connect( self.InputImage )

        self._opLabeler = OpLabelVolume( parent=self )
        self._opLabeler.Input.connect(self._opThresholder.Output)

        self.BeforeSizeFilter.connect( self._opLabeler.CachedOutput )

        self._opFilter = _OpFilterLabels5d( parent=self )
        self._opFilter.Input.connect(self._opLabeler.CachedOutput )
        self._opFilter.MinLabelSize.connect( self.MinSize )
        self._opFilter.MaxLabelSize.connect( self.MaxSize )
        self._opFilter.BinaryOut.setValue(False)

        self.Output.connect(self._opFilter.Output)

    def setupOutputs(self):

        def thresholdToUint8(thresholdValue, a):
            drange = self.InputImage.meta.drange
            if drange is not None:
                assert drange[0] == 0,\
                    "Don't know how to threshold data with this drange."
                thresholdValue *= drange[1]
            if a.dtype == numpy.uint8:
                # In-place (numpy optimizes this!)
                a[:] = (a > thresholdValue)
                return a
            else:
                return (a > thresholdValue).astype(numpy.uint8)

        self._opThresholder.Function.setValue(
            partial(thresholdToUint8, self.Threshold.value))
        # Copy the input metadata to the output
        self.Output.meta.assignFrom(self.InputImage.meta)
        self.Output.meta.dtype=numpy.uint32

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here..."

    def propagateDirty(self, slot, subindex, roi):
        pass  # nothing to do here

    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here.
        # Our Input slots are directly fed into the cache, 
        #  so all calls to __setitem__ are forwarded automatically 
        pass


## internal operator for two level thresholding
#
# The input must have 5 dimensions.
class _OpThresholdTwoLevels(Operator):
    name = "_OpThresholdTwoLevels"

    InputImage = InputSlot()
    MinSize = InputSlot(stype='int', value=0)
    MaxSize = InputSlot(stype='int', value=1000000)
    HighThreshold = InputSlot(stype='float', value=0.5)
    LowThreshold = InputSlot(stype='float', value=0.2)

    Output = OutputSlot()
    CachedOutput = OutputSlot()  # For the GUI (blockwise-access)

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
        super(_OpThresholdTwoLevels, self).__init__(*args, **kwargs)

        self._opLowThresholder = OpPixelOperator(parent=self)
        self._opLowThresholder.Input.connect(self.InputImage)

        self._opHighThresholder = OpPixelOperator(parent=self)
        self._opHighThresholder.Input.connect(self.InputImage)

        self._opLowLabeler = OpLabelVolume(parent=self)
        self._opLowLabeler.Input.connect(self._opLowThresholder.Output)

        self._opHighLabeler = OpLabelVolume(parent=self)
        self._opHighLabeler.Input.connect(self._opHighThresholder.Output)

        self._opHighLabelSizeFilter = _OpFilterLabels5d(parent=self)
        self._opHighLabelSizeFilter.Input.connect(self._opHighLabeler.CachedOutput)
        self._opHighLabelSizeFilter.MinLabelSize.connect(self.MinSize)
        self._opHighLabelSizeFilter.MaxLabelSize.connect(self.MaxSize)
        self._opHighLabelSizeFilter.BinaryOut.setValue(False)  # we do the binarization in opSelectLabels
                                                               # this way, we get to display pretty colors

        self._opSelectLabels = OpSelectLabels( parent=self )        
        self._opSelectLabels.BigLabels.connect( self._opLowLabeler.CachedOutput )
        self._opSelectLabels.SmallLabels.connect( self._opHighLabelSizeFilter.Output )

        #remove the remaining very large objects - 
        #they might still be present in case a big object
        #was split into many small ones for the higher threshold
        #and they got reconnected again at lower threshold
        self._opFinalLabelSizeFilter = _OpFilterLabels5d( parent=self )
        self._opFinalLabelSizeFilter.Input.connect(self._opSelectLabels.Output )
        self._opFinalLabelSizeFilter.MinLabelSize.connect( self.MinSize )
        self._opFinalLabelSizeFilter.MaxLabelSize.connect( self.MaxSize )
        self._opFinalLabelSizeFilter.BinaryOut.setValue(False)

        self._opCache = OpCompressedCache( parent=self )
        self._opCache.name = "_OpThresholdTwoLevels._opCache"
        self._opCache.InputHdf5.connect( self.InputHdf5 )
        self._opCache.Input.connect( self._opFinalLabelSizeFilter.Output )
       
        # Connect our own outputs
        self.Output.connect( self._opFinalLabelSizeFilter.Output )
        self.CachedOutput.connect( self._opCache.Output )

        # Serialization outputs
        self.CleanBlocks.connect( self._opCache.CleanBlocks )
        self.OutputHdf5.connect( self._opCache.OutputHdf5 )

        #self.InputChannel.connect( self._opChannelSelector.Output )

        # More debug outputs.  These all go through their own caches
        self._opBigRegionCache = OpCompressedCache( parent=self )
        self._opBigRegionCache.name = "_OpThresholdTwoLevels._opBigRegionCache"
        self._opBigRegionCache.Input.connect( self._opLowThresholder.Output )
        self.BigRegions.connect( self._opBigRegionCache.Output )

        self._opSmallRegionCache = OpCompressedCache( parent=self )
        self._opSmallRegionCache.name = "_OpThresholdTwoLevels._opSmallRegionCache"
        self._opSmallRegionCache.Input.connect( self._opHighThresholder.Output )
        self.SmallRegions.connect( self._opSmallRegionCache.Output )

        self._opFilteredSmallLabelsCache = OpCompressedCache( parent=self )
        self._opFilteredSmallLabelsCache.name = "_OpThresholdTwoLevels._opFilteredSmallLabelsCache"
        self._opFilteredSmallLabelsCache.Input.connect( self._opHighLabelSizeFilter.Output )
        self._opColorizeSmallLabels = OpColorizeLabels( parent=self )
        self._opColorizeSmallLabels.Input.connect( self._opFilteredSmallLabelsCache.Output )
        self.FilteredSmallLabels.connect( self._opColorizeSmallLabels.Output )

    def setupOutputs(self):
        def thresholdToUint8(thresholdValue, a):
            drange = self.InputImage.meta.drange
            if drange is not None:
                assert drange[0] == 0,\
                    "Don't know how to threshold data with this drange."
                thresholdValue *= drange[1]
            if a.dtype == numpy.uint8:
                # In-place (numpy optimizes this!)
                a[:] = (a > thresholdValue)
                return a
            else:
                return (a > thresholdValue).astype(numpy.uint8)

        self._opLowThresholder.Function.setValue(
            partial(thresholdToUint8, self.LowThreshold.value))
        self._opHighThresholder.Function.setValue(
            partial(thresholdToUint8, self.HighThreshold.value))

        # Copy the input metadata to the output
        self.Output.meta.assignFrom(self.InputImage.meta)
        self.Output.meta.dtype = numpy.uint32

        # Blockshape is the entire block, except only 1 time slice
        tagged_shape = self.Output.meta.getTaggedShape()
        tagged_shape['t'] = 1
        self._opCache.BlockShape.setValue(
            tuple(tagged_shape.values()))
        self._opBigRegionCache.BlockShape.setValue(
            tuple(tagged_shape.values()))
        self._opSmallRegionCache.BlockShape.setValue(
            tuple(tagged_shape.values()))
        self._opFilteredSmallLabelsCache.BlockShape.setValue(
            tuple(tagged_shape.values()))

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here..."

    def propagateDirty(self, slot, subindex, roi):
        pass  # Nothing to do here

    def setInSlot(self, slot, subindex, roi, value):
        assert slot == self.InputHdf5,\
            "Invalid slot for setInSlot(): {}".format(slot.name)
        # Nothing to do here.
        # Our Input slots are directly fed into the cache,
        #  so all calls to __setitem__ are forwarded automatically


## wrapper for OpFilterLabels
# Wraps OpFilterLabels in time and channel dimension beacuse we want to filer
# objects by size only in spatial dimensions.
# Spawns a new request for each time/channel slice
class _OpFilterLabels5d(Operator):
    name = "OpFilterLabels5d"
    category = "generic"

    # inherited

    Input = InputSlot()
    MinLabelSize = InputSlot(stype='int')
    MaxLabelSize = InputSlot(optional=True, stype='int')
    BinaryOut = InputSlot(optional=True, value=False, stype='bool')

    _ReorderedOutput = OutputSlot()
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(_OpFilterLabels5d, self).__init__(*args, **kwargs)
        #FIXME move the reordering to high-level operator, assume txyzc
        self._reorder1 = OpReorderAxes(parent=self)
        self._reorder1.AxisOrder.setValue('txyzc')
        self._reorder1.Input.connect(self.Input)

        self._op = OpFilterLabels(parent=self)
        self._op.Input.connect(self._reorder1.Output)
        #self._op.Input.connect(self.Input)
        self._op.MinLabelSize.connect(self.MinLabelSize)
        self._op.MaxLabelSize.connect(self.MaxLabelSize)
        self._op.BinaryOut.connect(self.BinaryOut)

        self._reorder2 = OpReorderAxes(parent=self)
        self._reorder2.Input.connect(self._ReorderedOutput)
        self.Output.connect(self._reorder2.Output)
        #self.Output.connect(self._)

    def setupOutputs(self):
        assert len(self._reorder1.Output.meta.shape) == 5
        self.Output.meta.assignFrom(self.Input.meta)
        self._ReorderedOutput.meta.assignFrom(self._reorder1.Output.meta)
        order = "".join(self.Input.meta.getAxisKeys())
        self._reorder2.AxisOrder.setValue(order)

    def execute(self, slot, subindex, roi, result):
        assert slot == self._ReorderedOutput
        pool = RequestPool()

        t_ind = 0
        for t in range(roi.start[0], roi.stop[0]):
            c_ind = 0
            for c in range(roi.start[-1], roi.stop[-1]):
                newroi = roi.copy()
                newroi.start[0] = t
                newroi.stop[0] = t+1
                newroi.start[-1] = c
                newroi.stop[-1] = c+1

                req = self._op.Output.get(newroi)
                resView = result[t_ind:t_ind+1, ..., c_ind:c_ind+1]
                req.writeInto(resView)

                pool.add(req)

                c_ind += 1

            t_ind += 1

        pool.wait()
        pool.clean()

    def propagateDirty(self, slot, subindex, roi):
        inStop = numpy.asarray(self.Input.meta.shape)
        inStart = inStop*0
        if slot == self.Input:
            # upstream dirtiness affects whole volume (per time/channel)
            t_ind = self.Input.meta.axistags.index('t')
            c_ind = self.Input.meta.axistags.index('c')
            inStart[t_ind] = roi.start[t_ind]
            inStop[t_ind] = roi.stop[t_ind]
            inStart[c_ind] = roi.start[c_ind]
            inStop[c_ind] = roi.stop[c_ind]
        elif slot == self.MinLabelSize or slot == self.MaxLabelSize\
                or slot == self.BinaryOut:
            # changes in the size affect the entire volume including all time
            # slices and channels
            # if we change the semantics of the output, we have to set it dirty
            pass
        else:
            assert False, "Invalid slot {}".format(slot)

        roi = SubRegion(self.Output, start=inStart, stop=inStop)
        self.Output.setDirty(roi)


