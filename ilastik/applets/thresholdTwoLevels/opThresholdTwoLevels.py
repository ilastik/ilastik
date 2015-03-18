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
import vigra

# ilastik
from ilastik.applets.base.applet import DatasetConstraintError
import ilastik.config

# Lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpPixelOperator, OpLabelVolume,\
    OpCompressedCache, OpColorizeLabels,\
    OpSingleChannelSelector, OperatorWrapper,\
    OpMultiArrayStacker, OpMultiArraySlicer,\
    OpReorderAxes, OpFilterLabels
from lazyflow.rtype import SubRegion
from lazyflow.request import Request, RequestPool

# local
from thresholdingTools import OpAnisotropicGaussianSmoothing5d

from thresholdingTools import OpSelectLabels

from opGraphcutSegment import haveGraphCut

if haveGraphCut():
    from opGraphcutSegment import OpObjectsSegment, OpGraphCut


logger = logging.getLogger(__name__)

# determine labeling implementation
try:
    _labeling_impl = ilastik.config.cfg.get("ilastik", "labeling")
except NoOptionError:
    _labeling_impl = "vigra"
#FIXME check validity of implementation
logger.info("Using '{}' labeling implemetation".format(_labeling_impl))


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

    ## Graph-Cut options ##

    SingleThresholdGC = InputSlot(stype='float', value=0.5)

    Beta = InputSlot(value=.2)

    # apply thresholding before graph-cut
    UsePreThreshold = InputSlot(stype='bool', value=True)

    # margin around single object (only graph-cut)
    Margin = InputSlot(value=numpy.asarray((20,20,20)))

    ## Output slots ##

    Output = OutputSlot()

    CachedOutput = OutputSlot()  # For the GUI (blockwise-access)

    # For serialization
    InputHdf5 = InputSlot(optional=True)

    CleanBlocks = OutputSlot()

    OutputHdf5 = OutputSlot()

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
        self._cache = _OpCacheWrapper(parent=self)
        self._cache.name = "OpThresholdTwoLevels.OpCacheWrapper"
        self._cache.Input.connect(self.Output)
        self.CachedOutput.connect(self._cache.Output)

        # Serialization slots
        self._cache.InputHdf5.connect(self.InputHdf5)
        self.CleanBlocks.connect(self._cache.CleanBlocks)
        self.OutputHdf5.connect(self._cache.OutputHdf5)

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
        else:
            raise ValueError(
                "Unknown index {} for current tab.".format(curIndex))

        self._opReorder2.Input.connect(outputSlot)
        # force the cache to emit a dirty signal
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
        threshOp.InputImage.connect(self.Smoothed)
        return threshOp.Output

    def _connectForTwoLevelThreshold(self):
        # connect the operators for TwoLevelThreshold
        self.BigRegions.connect(self.opThreshold2.BigRegions)
        self.SmallRegions.connect(self.opThreshold2.SmallRegions)
        self.FilteredSmallLabels.connect(self.opThreshold2.FilteredSmallLabels)
        for slot in [self.BigRegions, self.SmallRegions,
                     self.FilteredSmallLabels]:
            slot.meta.NOTREADY = None
        self.opThreshold2.InputImage.connect(self.Smoothed)

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

        # Output is already connected internally -- don't reassign new metadata
        # self.Output.meta.assignFrom(self.InputImage.meta)

        # Blockshape is the entire spatial volume (hysteresis thresholding is
        # a global operation)
        tagged_shape = self.Output.meta.getTaggedShape()
        tagged_shape['c'] = 1
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

