###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
# Built-in
import warnings
import logging
from functools import partial
from ConfigParser import NoOptionError

# numerics
import numpy
import numpy as np
import vigra

# ilastik
from ilastik.applets.base.applet import DatasetConstraintError
import ilastik.config
from ipht import identity_preserving_hysteresis_thresholding, threshold_from_cores

# Lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpPixelOperator, OpLabelVolume,\
    OpBlockedArrayCache, OpColorizeLabels,\
    OpSingleChannelSelector, OperatorWrapper,\
    OpMultiArrayStacker, OpMultiArraySlicer,\
    OpReorderAxes, OpFilterLabels
from lazyflow.rtype import SubRegion
from lazyflow.request import Request, RequestPool

# local
from thresholdingTools import OpAnisotropicGaussianSmoothing5d, OpSelectLabels, select_labels

from opGraphcutSegment import haveGraphCut
from scipy.stats.mstats_basic import threshold

if haveGraphCut():
    from opGraphcutSegment import OpObjectsSegment, OpGraphCut, segmentGC


logger = logging.getLogger(__name__)

# determine labeling implementation
try:
    _labeling_impl = ilastik.config.cfg.get("ilastik", "labeling")
except NoOptionError:
    _labeling_impl = "vigra"
#FIXME check validity of implementation
logger.info("Using '{}' labeling implemetation".format(_labeling_impl))


class ThresholdMethod(object):
    SIMPLE = 0      # single-threshold
    HYSTERESIS = 1  # hysteresis, a.k.a "two-level"
    GRAPHCUT = 2    # single, but tuned by graphcut
    IPHT = 3        # identity-preserving hysteresis thresholding
    
class OpLabeledThreshold(Operator):
    Input = InputSlot() # Must have exactly 1 channel
    CoreLabels = InputSlot(optional=True) # Not used for 'Simple' method.

    Method = InputSlot(value=ThresholdMethod.SIMPLE)
    FinalThreshold = InputSlot(value=0.2)
    #UseSparseMode = InputSlot(value=False)
    #MarginAroundCores = InputSlot(value=(20,20,20)) # xyz

    GraphcutBeta = InputSlot(value=0.2) # Graphcut only

    Output = OutputSlot()
    
    def setupOutputs(self):
        assert self.Input.meta.getAxisKeys() == list("txyzc")
        assert self.Input.meta.shape[-1] == 1
        if self.CoreLabels.ready():
            assert self.CoreLabels.meta.getAxisKeys() == list("txyzc")
        
        self.Output.meta.assignFrom( self.Input.meta )
        self.Output.meta.dtype = np.uint32

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty()

    def execute(self, slot, subindex, roi, result):
        execute_funcs = {}
        execute_funcs[ThresholdMethod.SIMPLE]     = self._execute_SIMPLE
        execute_funcs[ThresholdMethod.HYSTERESIS] = self._execute_HYSTERESIS
        execute_funcs[ThresholdMethod.GRAPHCUT]   = self._execute_GRAPHCUT
        execute_funcs[ThresholdMethod.IPHT]       = self._execute_IPHT

        # Iterate over time slices to avoid connected component problems.
        for t_index, t in enumerate(range(roi.start[0], roi.stop[0])):
            t_slice_roi = roi.copy()
            t_slice_roi.start[0] = t
            t_slice_roi.stop[0] = t+1

            result_slice = result[t_index:t_index+1]

            # Execute            
            execute_funcs[self.Method.value](t_slice_roi, result_slice)
        
    def _execute_SIMPLE(self, roi, result):
        assert result.shape[0] == 1
        assert tuple(roi.stop - roi.start) == result.shape

        final_threshold = self.FinalThreshold.value

        data = self.Input(roi.start, roi.stop).wait()
        data = vigra.taggedView(data, self.Input.meta.axistags)
        
        result = vigra.taggedView(result, self.Output.meta.axistags)
        
        binary = (data >= final_threshold).view(np.uint8)
        vigra.analysis.labelMultiArrayWithBackground(binary[0,...,0], out=result[0,...,0])

    def _execute_HYSTERESIS(self, roi, result):
        self._execute_SIMPLE(roi, result)
        final_labels = vigra.taggedView( result, self.Output.meta.axistags )

        core_labels = self.CoreLabels(roi.start, roi.stop).wait()
        core_labels = vigra.taggedView( core_labels, self.CoreLabels.meta.axistags )
        
        select_labels(core_labels, final_labels) # Edits final_labels in-place

    def _execute_IPHT(self, roi, result):
        core_labels = self.CoreLabels(roi.start, roi.stop).wait()
        core_labels = vigra.taggedView( core_labels, self.CoreLabels.meta.axistags )
        
        data = self.Input(roi.start, roi.stop).wait()
        data = vigra.taggedView(data, self.Input.meta.axistags)

        final_threshold = self.FinalThreshold.value
        result = vigra.taggedView( result, self.Output.meta.axistags )
        threshold_from_cores(data[0,...,0], core_labels[0,...,0], final_threshold, out=result[0,...,0])

    def _execute_GRAPHCUT(self, roi, result):
        data = self.Input(roi.start, roi.stop).wait()
        data = vigra.taggedView(data, self.Input.meta.axistags)
        data_xyz = data[0,...,0]

        beta = self.GraphcutBeta.value

        # FIXME: segmentGC() should also use FinalThreshold...
        binary_seg_xyz = segmentGC( data_xyz, beta ).astype(np.uint8)
        vigra.analysis.labelMultiArrayWithBackground(binary_seg_xyz, out=result[0,...,0])


class OpThresholdTwoLevels(Operator):
    RawInput = InputSlot(optional=True)  # Display only
    InputChannelColors = InputSlot(optional=True) # Display only

    InputImage = InputSlot()
    MinSize = InputSlot(stype='int', value=10)
    MaxSize = InputSlot(stype='int', value=1000000)
    HighThreshold = InputSlot(stype='float', value=0.5)
    LowThreshold = InputSlot(stype='float', value=0.2)
    SmootherSigma = InputSlot(value={'x': 1.0, 'y': 1.0, 'z': 1.0})
    Channel = InputSlot(value=0)
    CurOperator = InputSlot(stype='int', value=ThresholdMethod.SIMPLE) # This slot would be better named 'method',
                                                                       # but we're keeping this slot name for backwards
                                                                       # compatibility with old project files

    ## Graph-Cut options ##
    Beta = InputSlot(value=.2)

    # apply thresholding before graph-cut
    UsePreThreshold = InputSlot(stype='bool', value=True)
    SingleThresholdGC = InputSlot(stype='float', value=0.5)
    Margin = InputSlot(value=numpy.asarray((20,20,20))) # margin around single object (only graph-cut)

    ## Output slots ##
    Output = OutputSlot()
    CachedOutput = OutputSlot()  # For the GUI (blockwise-access)

    # For serialization
    CacheInput = InputSlot(optional=True)
    CleanBlocks = OutputSlot()

    ## Debug outputs

    InputChannel = OutputSlot()
    Smoothed = OutputSlot()
    BigRegions = OutputSlot()
    SmallRegions = OutputSlot()
    FilteredSmallLabels = OutputSlot()
    BeforeSizeFilter = OutputSlot()
    
    ## Basic schematic (debug outputs not shown)
    ## 
    ## InputImage -> opReorder -> opSmoother -> opSmootherCache -> opChannelSelector -------------------------------------> opFinalThreshold -> opFinalFilter -> opReorder -> Output
    ##                                                                              \                                      /                                              \
    ##                                                                               --> opCoreThreshold -> opCoreFilter --                                                opCache -> CachedOutput
    ##                                                                                                                                                                            `-> CleanBlocks
    def __init__(self, *args, **kwargs):
        super(OpThresholdTwoLevels, self).__init__(*args, **kwargs)

        self.opReorderInput = OpReorderAxes(parent=self)
        self.opReorderInput.AxisOrder.setValue('txyzc')
        self.opReorderInput.Input.connect(self.InputImage)
        
        self.opSmoother = OpAnisotropicGaussianSmoothing5d(parent=self)
        self.opSmoother.Sigmas.connect( self.SmootherSigma )
        self.opSmoother.Input.connect( self.opReorderInput.Output )
        
        self.opSmootherCache = OpBlockedArrayCache(parent=self)
        self.opSmootherCache.BlockShape.setValue((1, None, None, None, 1))
        self.opSmootherCache.Input.connect( self.opSmoother.Output )
        
        self.opChannelSelector = OpSingleChannelSelector(parent=self)
        self.opChannelSelector.Index.connect( self.Channel )
        self.opChannelSelector.Input.connect( self.opSmootherCache.Output )
        
        self.opCoreThreshold = OpLabeledThreshold(parent=self)
        self.opCoreThreshold.Method.setValue( ThresholdMethod.SIMPLE )
        self.opCoreThreshold.FinalThreshold.connect( self.HighThreshold )
        self.opCoreThreshold.Input.connect( self.opChannelSelector.Output )

        self.opCoreFilter = OpFilterLabels(parent=self)
        self.opCoreFilter.BinaryOut.setValue(False)
        self.opCoreFilter.MinLabelSize.connect( self.MinSize )
        self.opCoreFilter.MaxLabelSize.connect( self.MaxSize )
        self.opCoreFilter.Input.connect( self.opCoreThreshold.Output )
        
        self.opFinalThreshold = OpLabeledThreshold(parent=self)
        self.opFinalThreshold.Method.connect( self.CurOperator )
        self.opFinalThreshold.FinalThreshold.connect( self.LowThreshold )
        self.opFinalThreshold.GraphcutBeta.connect( self.Beta )
        self.opFinalThreshold.CoreLabels.connect( self.opCoreFilter.Output )
        self.opFinalThreshold.Input.connect( self.opChannelSelector.Output )
        
        self.opFinalFilter = OpFilterLabels(parent=self)
        self.opFinalFilter.BinaryOut.setValue(False)
        self.opFinalFilter.MinLabelSize.connect( self.MinSize )
        self.opFinalFilter.MaxLabelSize.connect( self.MaxSize )
        self.opFinalFilter.Input.connect( self.opFinalThreshold.Output )

        self.opReorderOutput = OpReorderAxes(parent=self)
        #self.opReorderOutput.AxisOrder.setValue('txyzc') # See setupOutputs()
        self.opReorderOutput.Input.connect(self.opFinalFilter.Output)

        self.Output.connect( self.opReorderOutput.Output )

        self.opCache = OpBlockedArrayCache(parent=self)
        self.opCache.CompressionEnabled.setValue(True)
        self.opCache.Input.connect( self.opReorderOutput.Output )
        
        self.CachedOutput.connect( self.opCache.Output )
        self.CleanBlocks.connect( self.opCache.CleanBlocks )
        
        ## Debug outputs
        self.Smoothed.connect( self.opSmootherCache.Output )
        self.InputChannel.connect( self.opChannelSelector.Output )
        self.SmallRegions.connect( self.opCoreThreshold.Output )
        self.FilteredSmallLabels.connect( self.opCoreFilter.Output )
        self.BeforeSizeFilter.connect( self.opFinalThreshold.Output )

        # Since hysteresis thresholding creates the big regions and immediately discards the bad ones,
        # we have to recreate it here if the user wants to view it as a debug layer 
        self.opBigRegionsThreshold = OpLabeledThreshold(parent=self)
        self.opBigRegionsThreshold.Method.setValue( ThresholdMethod.SIMPLE )
        self.opBigRegionsThreshold.FinalThreshold.connect( self.LowThreshold )
        self.opBigRegionsThreshold.Input.connect( self.opChannelSelector.Output )
        self.BigRegions.connect( self.opBigRegionsThreshold.Output )

    def setupOutputs(self):
        axes = self.InputImage.meta.getAxisKeys()
        self.opReorderOutput.AxisOrder.setValue(axes)

        # Cache individual t,c slices
        blockshape = tuple(1 if k in 'tc' else None for k in axes)
        self.opCache.BlockShape.setValue(blockshape)

    def setInSlot(self, slot, subindex, roi, value):
        self.opCache.setInSlot(self.opCache.Input, subindex, key, value)

    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."

    def propagateDirty(self, slot, subindex, roi):
        pass # dirtiness propagation is handled in the sub-operators

## High level operator for one/two level threshold
class _OpThresholdTwoLevels(Operator):
    name = "OpThresholdTwoLevels"

    RawInput = InputSlot(optional=True)  # Display only
    InputChannelColors = InputSlot(optional=True) # Display only

    InputImage = InputSlot()
    MinSize = InputSlot(stype='int', value=10)
    MaxSize = InputSlot(stype='int', value=1000000)
    HighThreshold = InputSlot(stype='float', value=0.5)
    LowThreshold = InputSlot(stype='float', value=0.2)
    SingleThreshold = InputSlot(stype='float', value=0.5)
    SmootherSigma = InputSlot(value={'x': 1.0, 'y': 1.0, 'z': 1.0})
    Channel = InputSlot(value=0)
    CurOperator = InputSlot(stype='int', value=0)

    ## Graph-Cut options ##
    Beta = InputSlot(value=.2)

    # apply thresholding before graph-cut
    UsePreThreshold = InputSlot(stype='bool', value=True)

    # margin around single object (only graph-cut)
    Margin = InputSlot(value=numpy.asarray((20,20,20)))

    ## Output slots ##

    Output = OutputSlot()

    CachedOutput = OutputSlot()  # For the GUI (blockwise-access)

    # For serialization
    CacheInput = InputSlot(optional=True)
    CleanBlocks = OutputSlot()

    ## Debug outputs

    InputChannel = OutputSlot()
    Smoothed = OutputSlot()
    BigRegions = OutputSlot()
    SmallRegions = OutputSlot()
    FilteredSmallLabels = OutputSlot()
    BeforeSizeFilter = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpThresholdTwoLevels, self).__init__(*args, **kwargs)

        self.InputImage.notifyReady( self.checkConstraints )

        self._opReorder1 = OpReorderAxes(parent=self)
        self._opReorder1.AxisOrder.setValue('txyzc')
        self._opReorder1.Input.connect(self.InputImage)

        self._opChannelSelector = OpSingleChannelSelector(parent=self)
        self._opChannelSelector.Input.connect(self._opReorder1.Output)
        self._opChannelSelector.Index.connect(self.Channel)

        # anisotropic gauss
        self._opSmoother = OpAnisotropicGaussianSmoothing5d(parent=self)
        self._opSmoother.Sigmas.connect(self.SmootherSigma)
        self._opSmoother.Input.connect(self._opChannelSelector.Output)

        # debug output
        self.Smoothed.connect(self._opSmoother.Output)

        # single threshold operator
        self.opThreshold1 = _OpThresholdOneLevel(parent=self)
        self.opThreshold1.Threshold.connect(self.SingleThreshold)
        self.opThreshold1.MinSize.connect(self.MinSize)
        self.opThreshold1.MaxSize.connect(self.MaxSize)

        # double threshold operator
        self.opThreshold2 = _OpThresholdTwoLevels(parent=self)
        self.opThreshold2.MinSize.connect(self.MinSize)
        self.opThreshold2.MaxSize.connect(self.MaxSize)
        self.opThreshold2.LowThreshold.connect(self.LowThreshold)
        self.opThreshold2.HighThreshold.connect(self.HighThreshold)

        # Identity-preserving hysteresis thresholding
        self.opIpht = OpIpht(parent=self)
        self.opIpht.MinSize.connect(self.MinSize)
        self.opIpht.MaxSize.connect(self.MaxSize)
        self.opIpht.LowThreshold.connect(self.LowThreshold)
        self.opIpht.HighThreshold.connect(self.HighThreshold)
        self.opIpht.InputImage.connect( self._opSmoother.Output )

        if haveGraphCut():
            self.opThreshold1GC = _OpThresholdOneLevel(parent=self)
            self.opThreshold1GC.Threshold.connect(self.SingleThresholdGC)
            self.opThreshold1GC.MinSize.connect(self.MinSize)
            self.opThreshold1GC.MaxSize.connect(self.MaxSize)

            self.opObjectsGraphCut = OpObjectsSegment(parent=self)
            self.opObjectsGraphCut.Prediction.connect(self.Smoothed)
            self.opObjectsGraphCut.LabelImage.connect(self.opThreshold1GC.Output)
            self.opObjectsGraphCut.Beta.connect(self.Beta)
            self.opObjectsGraphCut.Margin.connect(self.Margin)

            self.opGraphCut = OpGraphCut(parent=self)
            self.opGraphCut.Prediction.connect(self.Smoothed)
            self.opGraphCut.Beta.connect(self.Beta)

        self._op5CacheOutput = OpReorderAxes(parent=self)

        self._opReorder2 = OpReorderAxes(parent=self)
        self.Output.connect(self._opReorder2.Output)

        #cache our own output, don't propagate from internal operator
        self._cache = OpBlockedArrayCache(parent=self)
        self._cache.name = "OpThresholdTwoLevels.OpCacheWrapper"
        self.CachedOutput.connect(self._cache.Output)

        self.CleanBlocks.connect(self._cache.CleanBlocks)

        #Debug outputs
        self.InputChannel.connect(self._opChannelSelector.Output)

    def setupOutputs(self):

        self._opReorder2.AxisOrder.setValue(self.InputImage.meta.getAxisKeys())

        # propagate drange
        self.opThreshold1.InputImage.meta.drange = self.InputImage.meta.drange
        if haveGraphCut():
            self.opThreshold1GC.InputImage.meta.drange = self.InputImage.meta.drange
        self.opThreshold2.InputImage.meta.drange = self.InputImage.meta.drange

        self._disconnectAll()

        curIndex = self.CurOperator.value

        if curIndex == 0:
            outputSlot = self._connectForSingleThreshold(self.opThreshold1)
        elif curIndex == 1:
            outputSlot = self._connectForTwoLevelThreshold()
        elif curIndex == 2:
            outputSlot = self._connectForGraphCut()
        elif curIndex == 3:
            outputSlot = self.opIpht.Output
        else:
            raise ValueError(
                "Unknown index {} for current tab.".format(curIndex))

        # set the cache block shape
        tagged_shape = self._opReorder1.Output.meta.getTaggedShape()
        tagged_shape['t'] = 1
        tagged_shape['c'] = 1
        blockshape = tagged_shape.values()
        if _labeling_impl == "lazy":
            #HACK hardcoded block shape
            blockshape = numpy.minimum(blockshape, 256)
        self._cache.BlockShape.setValue(tuple(blockshape))

        self._opReorder2.Input.connect(outputSlot)
        # force the cache to emit a dirty signal
        self._cache.Input.connect(outputSlot)
        self._cache.Input.setDirty(slice(None))

    def checkConstraints(self, *args):
        if self._opReorder1.Output.ready():
            numChannels = self._opReorder1.Output.meta.getTaggedShape()['c']
            if self.Channel.value >= numChannels:
                raise DatasetConstraintError(
                    "Two-Level Thresholding",
                    "Your project is configured to select data from channel"
                    " #{}, but your input data only has {} channels."
                    .format(self.Channel.value, numChannels))

    def _disconnectAll(self):
        # start from back
        for slot in [self.BigRegions, self.SmallRegions,
                     self.FilteredSmallLabels, self.BeforeSizeFilter]:
            slot.disconnect()
            slot.meta.NOTREADY = True
        self._opReorder2.Input.disconnect()
        if haveGraphCut():
            self.opThreshold1GC.InputImage.disconnect()
        self.opThreshold1.InputImage.disconnect()
        self.opThreshold2.InputImage.disconnect()

    def _connectForSingleThreshold(self, threshOp):
        # connect the operators for SingleThreshold
        self.BeforeSizeFilter.connect(threshOp.BeforeSizeFilter)
        self.BeforeSizeFilter.meta.NOTREADY = None
        threshOp.InputImage.connect(self._opSmoother.Output)
        return threshOp.Output

    def _connectForTwoLevelThreshold(self):
        # connect the operators for TwoLevelThreshold
        self.BigRegions.connect(self.opThreshold2.BigRegions)
        self.SmallRegions.connect(self.opThreshold2.SmallRegions)
        self.FilteredSmallLabels.connect(self.opThreshold2.FilteredSmallLabels)
        for slot in [self.BigRegions, self.SmallRegions,
                     self.FilteredSmallLabels]:
            slot.meta.NOTREADY = None
        self.opThreshold2.InputImage.connect(self._opSmoother.Output)

        return self.opThreshold2.Output

    def _connectForGraphCut(self):
        assert haveGraphCut(), "Module for graph cut is not available"
        if self.UsePreThreshold.value:
            self._connectForSingleThreshold(self.opThreshold1GC)
            return self.opObjectsGraphCut.Output
        else:
            return self.opGraphCut.Output

    # raise an error if setInSlot is called, we do not pre-cache input
    #def setInSlot(self, slot, subindex, roi, value):
        #pass

    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."

    def propagateDirty(self, slot, subindex, roi):
        # dirtiness propagation is handled in the sub-operators
        pass

    def setInSlot(self, slot, subindex, roi, value):
        assert slot == self.InputHdf5,\
            "[{}] Wrong slot for setInSlot(): {}".format(self.name,
                                                         slot)
        pass
        # InputHDF5 is connected to the cache so we don't have to do
        # anything, all other slots are rejected


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

        self._opLabeler = OpLabelVolume(parent=self)
        self._opLabeler.Method.setValue(_labeling_impl)
        self._opLabeler.Input.connect(self._opThresholder.Output)

        self.BeforeSizeFilter.connect( self._opLabeler.Output )

        self._opFilter = OpFilterLabels( parent=self )
        self._opFilter.Input.connect(self._opLabeler.Output )
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

        # self.Output already has metadata: it is directly connected to self._opFilter.Output

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
# Input is processed on a what-you-request-is-what-you-get basis: You have to
# make sure that the ROI for slot 'Output' matches the input shape at least in
# the spatial dimensions, or you will get inconsistent results. All requests to
# slot 'CachedOutput' are guaranteed to be consistent though.
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
        self._opLowLabeler.Method.setValue(_labeling_impl)
        self._opLowLabeler.Input.connect(self._opLowThresholder.Output)

        self._opHighLabeler = OpLabelVolume(parent=self)
        self._opHighLabeler.Method.setValue(_labeling_impl)
        self._opHighLabeler.Input.connect(self._opHighThresholder.Output)

        self._opHighLabelSizeFilter = OpFilterLabels(parent=self)
        self._opHighLabelSizeFilter.Input.connect(self._opHighLabeler.Output)
        self._opHighLabelSizeFilter.MinLabelSize.connect(self.MinSize)
        self._opHighLabelSizeFilter.MaxLabelSize.connect(self.MaxSize)
        self._opHighLabelSizeFilter.BinaryOut.setValue(False)  # we do the binarization in opSelectLabels
                                                               # this way, we get to display pretty colors

        self._opSelectLabels = OpSelectLabels( parent=self )        
        self._opSelectLabels.BigLabels.connect( self._opLowLabeler.Output )
        self._opSelectLabels.SmallLabels.connect( self._opHighLabelSizeFilter.Output )

        # remove the remaining very large objects -
        # they might still be present in case a big object
        # was split into many small ones for the higher threshold
        # and they got reconnected again at lower threshold
        self._opFinalLabelSizeFilter = OpFilterLabels( parent=self )
        self._opFinalLabelSizeFilter.Input.connect(self._opSelectLabels.Output )
        self._opFinalLabelSizeFilter.MinLabelSize.connect( self.MinSize )
        self._opFinalLabelSizeFilter.MaxLabelSize.connect( self.MaxSize )
        self._opFinalLabelSizeFilter.BinaryOut.setValue(False)

        self._opCache = OpBlockedArrayCache( parent=self )
        self._opCache.name = "_OpThresholdTwoLevels._opCache"
        self._opCache.CompressionEnabled.setValue(True)
        self._opCache.Input.connect( self._opFinalLabelSizeFilter.Output )

        # Connect our own outputs
        self.Output.connect( self._opFinalLabelSizeFilter.Output )
        self.CachedOutput.connect( self._opCache.Output )

        # Serialization (See also: setInSlot(), below)
        self.CleanBlocks.connect( self._opCache.CleanBlocks )

        # More debug outputs.  These all go through their own caches
        self._opBigRegionCache = OpBlockedArrayCache( parent=self )
        self._opBigRegionCache.name = "_OpThresholdTwoLevels._opBigRegionCache"
        self._opBigRegionCache.CompressionEnabled.setValue(True)
        self._opBigRegionCache.Input.connect( self._opLowThresholder.Output )
        self.BigRegions.connect( self._opBigRegionCache.Output )

        self._opSmallRegionCache = OpBlockedArrayCache( parent=self )
        self._opSmallRegionCache.name = "_OpThresholdTwoLevels._opSmallRegionCache"
        self._opSmallRegionCache.CompressionEnabled.setValue(True)
        self._opSmallRegionCache.Input.connect( self._opHighThresholder.Output )
        self.SmallRegions.connect( self._opSmallRegionCache.Output )

        self._opFilteredSmallLabelsCache = OpBlockedArrayCache( parent=self )
        self._opFilteredSmallLabelsCache.name = "_OpThresholdTwoLevels._opFilteredSmallLabelsCache"
        self._opFilteredSmallLabelsCache.CompressionEnabled.setValue(True)
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

        # Output is already connected internally -- don't reassign new metadata
        # self.Output.meta.assignFrom(self.InputImage.meta)

        # Blockshape is the entire spatial volume (hysteresis thresholding is
        # a global operation)
        tagged_shape = self.Output.meta.getTaggedShape()
        tagged_shape['c'] = 1
        tagged_shape['t'] = 1
        blockshape = tuple(tagged_shape.values())
        self._opCache.BlockShape.setValue( blockshape )
        self._opBigRegionCache.BlockShape.setValue( blockshape )
        self._opSmallRegionCache.BlockShape.setValue( blockshape )
        self._opFilteredSmallLabelsCache.BlockShape.setValue( blockshape )

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here..."

    def propagateDirty(self, slot, subindex, roi):
        pass  # Nothing to do here

    def setInSlot(self, slot, subindex, roi, value):
        """
        Overridden from Operator
        Called during deserialization, to load the cache with saved data.
        """
        # Forward the data to our cache
        assert slot is self.CacheInput
        self._opCache.Input.setInSlot(slot, subindex, roi, value)


class OpIpht(Operator):
    """
    Identity-preserving Hysteresis Thresholding.
    Requires 5D input, txyzc order, with only 1-channel input.
    """
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

    def __init__(self, *args, **kwargs):
        super(OpIpht, self).__init__(*args, **kwargs)
        self._opIpht = OpIphtNoCache(parent=self)
        self._opIpht.InputImage.connect( self.InputImage )
        self._opIpht.MinSize.connect( self.MinSize )
        self._opIpht.MaxSize.connect( self.MaxSize )
        self._opIpht.HighThreshold.connect( self.HighThreshold )
        self._opIpht.LowThreshold.connect( self.LowThreshold )
        self.Output.connect( self._opIpht.Output )
        
        self._opCache = OpBlockedArrayCache(parent=self)
        self._opCache.CompressionEnabled.setValue(True)
        self._opCache.Input.connect( self._opIpht.Output )
        self.CachedOutput.connect( self._opCache.Output )
    
    def setupOutputs(self):
        assert self.InputImage.meta.getAxisKeys() == list('txyzc')
        # Blockshape is the entire spatial volume (hysteresis thresholding is
        # a global operation)
        tagged_shape = self.Output.meta.getTaggedShape()
        tagged_shape['c'] = 1
        tagged_shape['t'] = 1
        self._opCache.BlockShape.setValue( tuple(tagged_shape.values()) )

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here..."

    def propagateDirty(self, slot, subindex, roi):
        pass  # Nothing to do here

class OpIphtNoCache(Operator):
    InputImage = InputSlot()
    MinSize = InputSlot(stype='int', value=0)
    MaxSize = InputSlot(stype='int', value=1000000)
    HighThreshold = InputSlot(stype='float', value=0.5)
    LowThreshold = InputSlot(stype='float', value=0.2)

    Output = OutputSlot()
    
    def setupOutputs(self):
        assert self.InputImage.meta.getAxisKeys() == list('txyzc')
        assert self.InputImage.meta.shape[-1] == 1
        self.Output.meta.assignFrom(self.InputImage.meta)
        self.Output.meta.dtype = numpy.uint32
    
    def execute(self, slot, subindex, roi, result):
        # Input is required to be in txyzc order
        result = vigra.taggedView( result, 'txyzc' )
        t_start, t_stop = roi.start[0], roi.stop[0]
        for t in range(t_start, t_stop):
            roi_t = numpy.array( (roi.start, roi.stop) )
            roi_t[:,0] = (t, t+1)
            image = self.InputImage(*roi_t).wait()
            image = vigra.taggedView(image, 'txyzc')
            identity_preserving_hysteresis_thresholding( image[0,...,0],
                                                         self.HighThreshold.value,
                                                         self.LowThreshold.value,
                                                         self.MinSize.value,
                                                         self.MaxSize.value,
                                                         out=result[t-t_start,...,0] )

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty()

#HACK this ensures backwards compatibility by providing serialization slots
# with xyzct axes
class _OpCacheWrapper(Operator):
    name = "OpCacheWrapper"
    Input = InputSlot()

    Output = OutputSlot()

    InputHdf5 = InputSlot(optional=True)
    CleanBlocks = OutputSlot()
    OutputHdf5 = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(_OpCacheWrapper, self).__init__(*args, **kwargs)
        op1 = OpReorderAxes(parent=self)
        op1.name = "op1"
        op2 = OpReorderAxes(parent=self)
        op2.name = "op2"

        op1.AxisOrder.setValue('xyzct')
        op2.AxisOrder.setValue('txyzc')

        op1.Input.connect(self.Input)
        self.Output.connect(op2.Output)

        self._op1 = op1
        self._op2 = op2
        self._cache = None

    def setupOutputs(self):
        self._disconnectInternals()

        # we need a new cache
        cache = OpCompressedCache(parent=self)
        cache.name = self.name + "WrappedCache"

        # connect cache outputs
        self.CleanBlocks.connect(cache.CleanBlocks)
        self.OutputHdf5.connect(cache.OutputHdf5)
        self._op2.Input.connect(cache.Output)

        # connect cache inputs
        cache.InputHdf5.connect(self.InputHdf5)
        cache.Input.connect(self._op1.Output)

        # set the cache block shape
        tagged_shape = self._op1.Output.meta.getTaggedShape()
        tagged_shape['t'] = 1
        tagged_shape['c'] = 1
        cacheshape = map(lambda k: tagged_shape[k], 'xyzct')
        if _labeling_impl == "lazy":
            #HACK hardcoded block shape
            blockshape = numpy.minimum(cacheshape, 256)
        else:
            # use full spatial volume if not lazy
            blockshape = cacheshape
        cache.BlockShape.setValue(tuple(blockshape))

        self._cache = cache

    def execute(self, slot, subindex, roi, result):
        assert False

    def propagateDirty(self, slot, subindex, roi):
        pass

    def setInSlot(self, slot, subindex, key, value):
        assert slot == self.InputHdf5,\
            "setInSlot not implemented for slot {}".format(slot.name)
        assert self._cache is not None,\
            "setInSlot called before input was configured"
        self._cache.setInSlot(self._cache.InputHdf5, subindex, key, value)

    def _disconnectInternals(self):
        self.CleanBlocks.disconnect()
        self.OutputHdf5.disconnect()
        self._op2.Input.disconnect()

        if self._cache is not None:
            self._cache.InputHdf5.disconnect()
            self._cache.Input.disconnect()
            del self._cache

