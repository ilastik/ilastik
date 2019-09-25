from collections import OrderedDict
import numpy as np

from wsdt import wsDtSegmentation

from lazyflow.utility import OrderedSignal
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice, sliceToRoi
from lazyflow.operators import OpBlockedArrayCache, OpValueCache
from lazyflow.operators.generic import OpPixelOperator, OpSingleChannelSelector


class OpWsdt(Operator):
    # Can be multi-channel (but you'll have to choose which channels you want to use)
    Input = InputSlot()

    # List input channels to use as the boundary map
    # (They'll be summed.)
    ChannelSelections = InputSlot(value=[0])

    # Parameters
    Pmin = InputSlot(value=0.5)
    MinMembraneSize = InputSlot(value=0)
    MinSegmentSize = InputSlot(value=0)
    SigmaMinima = InputSlot(value=3.0)
    SigmaWeights = InputSlot(value=0.0)
    GroupSeeds = InputSlot(value=False)
    PreserveMembranePmaps = InputSlot(value=False)

    EnableDebugOutputs = InputSlot(value=False)

    Superpixels = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpWsdt, self).__init__(*args, **kwargs)
        self.debug_results = None
        self.watershed_completed = OrderedSignal()

        self._opSelectedInput = OpSumChannels(parent=self)
        self._opSelectedInput.ChannelSelections.connect(self.ChannelSelections)
        self._opSelectedInput.Input.connect(self.Input)

    def setupOutputs(self):
        if not self._opSelectedInput.Output.ready():
            self.Superpixels.meta.NOTREADY = True
            return

        assert self.Input.meta.getAxisKeys()[-1] == "c", "This operator assumes that channel is the last axis."
        self.Superpixels.meta.assignFrom(self.Input.meta)
        self.Superpixels.meta.shape = self.Input.meta.shape[:-1] + (1,)
        self.Superpixels.meta.dtype = np.uint32
        self.Superpixels.meta.display_mode = "random-colortable"

        self.debug_results = None
        if self.EnableDebugOutputs.value:
            self.debug_results = OrderedDict()

    def execute(self, slot, subindex, roi, result):
        assert slot is self.Superpixels, "Unknown or unconnected output slot: {}".format(slot)

        pmap = self._opSelectedInput.Output(roi.start, roi.stop).wait()

        if self.debug_results:
            self.debug_results.clear()
        ws, max_label = wsDtSegmentation(
            pmap[..., 0],
            self.Pmin.value,
            self.MinMembraneSize.value,
            self.MinSegmentSize.value,
            self.SigmaMinima.value,
            self.SigmaWeights.value,
            self.GroupSeeds.value,
            self.PreserveMembranePmaps.value,
            out_debug_image_dict=self.debug_results,
            out=result[..., 0],
        )

        self.watershed_completed()

    def propagateDirty(self, slot, subindex, roi):
        if slot is not self.EnableDebugOutputs:
            self.Superpixels.setDirty()


class OpCachedWsdt(Operator):
    RawData = InputSlot(optional=True)  # Used by the GUI for display only
    FreezeCache = InputSlot(value=True)

    Input = InputSlot()  # Can be multi-channel (but you'll have to choose which channel you want to use)
    ChannelSelections = InputSlot(value=[0])

    # Parameters
    Pmin = InputSlot(value=0.5)
    MinMembraneSize = InputSlot(value=0)
    MinSegmentSize = InputSlot(value=0)
    SigmaMinima = InputSlot(value=3.0)
    SigmaWeights = InputSlot(value=0.0)
    GroupSeeds = InputSlot(value=False)
    PreserveMembranePmaps = InputSlot(value=False)

    EnableDebugOutputs = InputSlot(value=False)

    Superpixels = OutputSlot()

    SuperpixelCacheInput = InputSlot(optional=True)
    CleanBlocks = OutputSlot()

    SelectedInput = OutputSlot()

    # Thresholding is cheap and best done interactively,
    # so expose an uncached slot just for it
    ThresholdedInput = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpCachedWsdt, self).__init__(*args, **kwargs)
        my_slot_names = set([slot.name for slot in self.inputSlots + self.outputSlots])
        wsdt_slot_names = set([slot.name for slot in OpWsdt.inputSlots + OpWsdt.outputSlots])
        assert wsdt_slot_names.issubset(my_slot_names), (
            "OpCachedWsdt should have all of the slots that OpWsdt has (and maybe more). "
            "Did you add a slot to OpWsdt and forget to add it to OpCachedWsdt?"
        )

        self._opWsdt = OpWsdt(parent=self)
        self._opWsdt.Input.connect(self.Input)
        self._opWsdt.ChannelSelections.connect(self.ChannelSelections)
        self._opWsdt.Pmin.connect(self.Pmin)
        self._opWsdt.MinMembraneSize.connect(self.MinMembraneSize)
        self._opWsdt.MinSegmentSize.connect(self.MinSegmentSize)
        self._opWsdt.SigmaMinima.connect(self.SigmaMinima)
        self._opWsdt.SigmaWeights.connect(self.SigmaWeights)
        self._opWsdt.GroupSeeds.connect(self.GroupSeeds)
        self._opWsdt.PreserveMembranePmaps.connect(self.PreserveMembranePmaps)
        self._opWsdt.EnableDebugOutputs.connect(self.EnableDebugOutputs)

        self._opCache = OpBlockedArrayCache(parent=self)
        self._opCache.fixAtCurrent.connect(self.FreezeCache)
        self._opCache.Input.connect(self._opWsdt.Superpixels)
        self.Superpixels.connect(self._opCache.Output)
        self.CleanBlocks.connect(self._opCache.CleanBlocks)

        self._opSelectedInput = OpSumChannels(parent=self)
        self._opSelectedInput.ChannelSelections.connect(self.ChannelSelections)
        self._opSelectedInput.Input.connect(self.Input)
        self.SelectedInput.connect(self._opSelectedInput.Output)

        self._opThreshold = OpPixelOperator(parent=self)
        self._opThreshold.Input.connect(self._opSelectedInput.Output)
        self.ThresholdedInput.connect(self._opThreshold.Output)

    def setupOutputs(self):
        self._opThreshold.Function.setValue(lambda a: (a >= self.Pmin.value).astype(np.uint8))

    @property
    def debug_results(self):
        return self._opWsdt.debug_results

    @property
    def watershed_completed(self):
        return self._opWsdt.watershed_completed

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here"

    def setInSlot(self, slot, subindex, roi, value):
        # Write the data into the cache
        assert slot is self.SuperpixelCacheInput
        slicing = roiToSlice(roi.start, roi.stop)
        self._opCache.Input[slicing] = value

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.EnableDebugOutputs and self.EnableDebugOutputs.value:
            # Force a refresh so the debug outputs will be updated.
            self._opCache.Input.setDirty()


class OpSumChannels(Operator):
    Input = InputSlot()
    ChannelSelections = InputSlot(value=[0])
    Output = OutputSlot()

    def setupOutputs(self):
        if len(self.ChannelSelections.value) == 0:
            self.Output.meta.NOTREADY = True
            return

        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.shape = self.Input.meta.shape[:-1] + (1,)
        # Assume naming pattern NAME-{1,2,3,...}
        # Do not keep old channel names.
        self.Output.meta.channel_names = self.Input.meta.channel_names[0].split('-')[0]

    def execute(self, slot, subindex, roi, result):
        channel_indexes = np.array(self.ChannelSelections.value)
        channel_indexes.sort()

        input_roi = roi.copy()
        input_roi.start[-1] = channel_indexes[0]
        input_roi.stop[-1] = channel_indexes[-1] + 1

        if len(channel_indexes) == 1:
            # Fetch in-place
            self.Input(input_roi.start, input_roi.stop).writeInto(result).wait()
        else:
            fetched_data = self.Input(input_roi.start, input_roi.stop).wait()
            channel_indexes = channel_indexes - channel_indexes[0]
            selected_data = fetched_data[..., tuple(channel_indexes)]
            selected_data.sum(axis=-1, out=result[..., 0])

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.ChannelSelections:
            # Everything is dirty
            self.Output.setDirty()
        elif slot == self.Input:
            # If any of the channels we care about became dirty, our output is dirty.
            channel_indexes = np.array(self.ChannelSelections.value).sort()
            first_channel = channel_indexes[0]
            last_channel = channel_indexes[-1]
            if roi.start[-1] > last_channel or roi.stop[-1] <= first_channel:
                return
            self.Output.setDirty(roi.start, roi.stop)
        else:
            assert False, "Unhandled input slot: {}".format(slot.name)
