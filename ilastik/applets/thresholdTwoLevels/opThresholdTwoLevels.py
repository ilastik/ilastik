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
import warnings
import logging
from functools import partial

# numerics
import numpy
import vigra

# Lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpPixelOperator, OpLabelVolume,\
    OpCompressedCache, OpColorizeLabels,\
    OpSingleChannelSelector, OperatorWrapper,\
    OpMultiArrayStacker, OpMultiArraySlicer,\
    OpReorderAxes
from lazyflow.rtype import SubRegion
from lazyflow.request import Request, RequestPool

# local
from thresholdingTools import OpFilterLabels5d
from thresholdingTools import OpAnisotropicGaussianSmoothing
from thresholdingTools import OpSelectLabels

from opGraphcutSegment import haveGraphCut

if haveGraphCut():
    from opGraphcutSegment import OpObjectsSegment, OpGraphCut


logger = logging.getLogger(__name__)


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
    SingleThresholdGC = InputSlot(stype='float', value=0.5)
    Beta = InputSlot(value=.2)
    CurOperator = InputSlot(stype='int', value=0)

    # apply thresholding before graph-cut
    UsePreThreshold = InputSlot(stype='bool', value=True)

    # margin around single object (only graph-cut)
    Margin = InputSlot(value=numpy.asarray((20,20,20)))

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
        self._opSmoother = OperatorWrapper(OpAnisotropicGaussianSmoothing,
                                           parent=self,
                                           broadcastingSlotNames=['Sigmas'])
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

        if haveGraphCut():
            self.opThreshold1GC = _OpThresholdOneLevel(parent=self)
            self.opThreshold1GC.InputImage.connect(self._smoothStacker.Output)
            self.opThreshold1GC.Threshold.connect(self.SingleThresholdGC)
            self.opThreshold1GC.MinSize.connect(self.MinSize)
            self.opThreshold1GC.MaxSize.connect(self.MaxSize)

            self.opObjectsGraphCut = OpObjectsSegment(parent=self)
            self.opObjectsGraphCut.Prediction.connect(self._smoothStacker.Output)
            #FIXME get rid of channel here
            self.opObjectsGraphCut.Channel.setValue(0)
            self.opObjectsGraphCut.LabelImage.connect(self.opThreshold1.Output)
            self.opObjectsGraphCut.Beta.connect(self.Beta)
            self.opObjectsGraphCut.Margin.connect(self.Margin)

            self.opGraphCut = OpGraphCut(parent=self)
            self.opGraphCut.Prediction.connect(self._smoothStacker.Output)
            self.opGraphCut.Beta.connect(self.Beta)

        # HACK: For backwards compatibility with old projects,
        #       the cache must by in xyzct order,
        #       because the cache is loaded directly from the serializer
        self._op5CacheInput = OpReorderAxes(parent=self)
        self._op5CacheInput.AxisOrder.setValue("xyzct")

        #cache our own output, don't propagate from internal operator
        self._opCache = OpCompressedCache(parent=self)
        self._opCache.name = "OpThresholdTwoLevels._opCache"
        self._opCache.InputHdf5.connect(self.InputHdf5)
        self._opCache.Input.connect(self._op5CacheInput.Output)

        self._op5CacheOutput = OpReorderAxes(parent=self)
        self._op5CacheOutput.Input.connect(self._opCache.Output)

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
        self._op5CacheInput.Input.connect(outputSlot)
        self._op5CacheOutput.AxisOrder.setValue(
            self._op5CacheInput.Input.meta.getAxisKeys())
        self._setBlockShape()

    def _disconnectAll(self):
        # start from back
        for slot in [self.BigRegions, self.SmallRegions,
                     self.FilteredSmallLabels, self.BeforeSizeFilter]:
            slot.disconnect()
            slot.meta.NOTREADY = True
        self._op5CacheInput.Input.disconnect()
        self._opReorder2.Input.disconnect()

    def _connectForSingleThreshold(self, threshOp):
        # connect the operators for SingleThreshold
        self.BeforeSizeFilter.connect(threshOp.BeforeSizeFilter)
        self.BeforeSizeFilter.meta.NOTREADY = None
        return threshOp.Output

    def _connectForTwoLevelThreshold(self):
        # connect the operators for TwoLevelThreshold
        self.BigRegions.connect(self.opThreshold2.BigRegions)
        self.SmallRegions.connect(self.opThreshold2.SmallRegions)
        self.FilteredSmallLabels.connect(self.opThreshold2.FilteredSmallLabels)
        for slot in [self.BigRegions, self.SmallRegions,
                     self.FilteredSmallLabels]:
            slot.meta.NOTREADY = None

        return self.opThreshold2.Output

    def _connectForGraphCut(self):
        assert haveGraphCut(), "Module for graph cut is not available"
        if self.UsePreThreshold.value:
            self._connectForSingleThreshold(self.opThreshold1GC)
            return self.opObjectsGraphCut.Output
        else:
            return self.opGraphCut.Output

    def _setBlockShape(self):
        # Blockshape is the entire block, except only 1 time slice
        tagged_shape = self._opCache.Input.meta.getTaggedShape()
        tagged_shape['t'] = 1

        # Blockshape must correspond to cache input order
        blockshape = map(lambda k: tagged_shape[k], 'xyzct')
        self._opCache.BlockShape.setValue(tuple(blockshape))

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

        self._opFilter = OpFilterLabels5d( parent=self )
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

        self._opHighLabelSizeFilter = OpFilterLabels5d(parent=self)
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
        self._opFinalLabelSizeFilter = OpFilterLabels5d( parent=self )
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
