
from collections import OrderedDict
import numpy as np

from wsdt import wsDtSegmentation

from lazyflow.utility import OrderedSignal
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.operators import OpBlockedArrayCache, OpValueCache
from lazyflow.operators.generic import OpPixelOperator, OpSingleChannelSelector

class OpWsdt(Operator):
    Input = InputSlot() # Can be multi-channel (but you'll have to choose which channel you want to use)
    ChannelSelection = InputSlot(value=0)

    # Parameters
    Pmin = InputSlot(value=0.5)
    MinMembraneSize = InputSlot(value=0)
    MinSegmentSize = InputSlot(value=0)
    SigmaMinima = InputSlot(value=0.0)
    SigmaWeights = InputSlot(value=0.0)
    GroupSeeds = InputSlot(value=False)

    EnableDebugOutputs = InputSlot(value=False)
    
    Superpixels = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpWsdt, self ).__init__(*args, **kwargs)
        self.debug_results = None
        self.watershed_completed = OrderedSignal()

    def setupOutputs(self):
        assert self.Input.meta.getAxisKeys()[-1] == 'c', \
            "This operator assumes that channel is the last axis."
        self.Superpixels.meta.assignFrom( self.Input.meta )
        self.Superpixels.meta.shape = self.Input.meta.shape[:-1] + (1,)
        self.Superpixels.meta.dtype = np.uint32
        self.Superpixels.meta.display_mode = "random-colortable"
        
        self.debug_results = None
        if self.EnableDebugOutputs.value:
            self.debug_results = OrderedDict()
    
    def execute(self, slot, subindex, roi, result):
        assert slot is self.Superpixels, "Unknown or unconnected output slot: {}".format( slot )
        channel_index = self.ChannelSelection.value

        pmap_roi = roi.copy()
        pmap_roi.start[-1] = channel_index
        pmap_roi.stop[-1] = channel_index+1

        # TODO: We could be sneaky and use the result array as a temporary here...
        pmap = self.Input(pmap_roi.start, pmap_roi.stop).wait()

        if self.debug_results:
            self.debug_results.clear()
        wsDtSegmentation( pmap[...,0],
                          self.Pmin.value,
                          self.MinMembraneSize.value,
                          self.MinSegmentSize.value,
                          self.SigmaMinima.value,
                          self.SigmaWeights.value,
                          self.GroupSeeds.value,
                          out_debug_image_dict=self.debug_results,
                          out=result[...,0] )
        
        self.watershed_completed()
        
    def propagateDirty(self, slot, subindex, roi):
        if slot is not self.EnableDebugOutputs:
            self.Superpixels.setDirty()

class OpCachedWsdt(Operator):
    RawData = InputSlot(optional=True) # Used by the GUI for display only
    FreezeCache = InputSlot(value=True)
    
    Input = InputSlot() # Can be multi-channel (but you'll have to choose which channel you want to use)
    ChannelSelection = InputSlot(value=0)

    # Parameters
    Pmin = InputSlot(value=0.5)
    MinMembraneSize = InputSlot(value=0)
    MinSegmentSize = InputSlot(value=0)
    SigmaMinima = InputSlot(value=0.0)
    SigmaWeights = InputSlot(value=0.0)
    GroupSeeds = InputSlot(value=False)

    EnableDebugOutputs = InputSlot(value=False)
    
    Superpixels = OutputSlot()

    # Thresholding is cheap and best done interactively,
    # so expose an uncached slot just for it
    ThresholdedInput = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpCachedWsdt, self ).__init__(*args, **kwargs)
        my_slot_names = set(map(lambda slot: slot.name, self.inputSlots + self.outputSlots))
        wsdt_slot_names = set(map(lambda slot: slot.name, OpWsdt.inputSlots + OpWsdt.outputSlots))
        assert wsdt_slot_names.issubset(my_slot_names), \
            "OpCachedWsdt should have all of the slots that OpWsdt has (and maybe more). "\
            "Did you add a slot to OpWsdt and forget to add it to OpCachedWsdt?"
        
        self._opWsdt = OpWsdt( parent=self )
        self._opWsdt.Input.connect( self.Input )
        self._opWsdt.ChannelSelection.connect( self.ChannelSelection )
        self._opWsdt.Pmin.connect( self.Pmin )
        self._opWsdt.MinMembraneSize.connect( self.MinMembraneSize )
        self._opWsdt.MinSegmentSize.connect( self.MinSegmentSize )
        self._opWsdt.SigmaMinima.connect( self.SigmaMinima )
        self._opWsdt.SigmaWeights.connect( self.SigmaWeights )
        self._opWsdt.GroupSeeds.connect( self.GroupSeeds )
        self._opWsdt.EnableDebugOutputs.connect( self.EnableDebugOutputs )
        
        self._opCache = OpBlockedArrayCache( parent=self )
        self._opCache.fixAtCurrent.connect( self.FreezeCache )
        self._opCache.Input.connect( self._opWsdt.Superpixels )
        self.Superpixels.connect( self._opCache.Output )

        self._opSelectedInput = OpSingleChannelSelector( parent=self )
        self._opSelectedInput.Index.connect( self.ChannelSelection )
        self._opSelectedInput.Input.connect( self.Input )

        self._opThreshold = OpPixelOperator( parent=self )
        self._opThreshold.Input.connect( self._opSelectedInput.Output )
        self.ThresholdedInput.connect( self._opThreshold.Output )

    def setupOutputs(self):
        self._opThreshold.Function.setValue( lambda a: (a >= self.Pmin.value).astype(np.uint8) )

    @property
    def debug_results(self):
        return self._opWsdt.debug_results
    
    @property
    def watershed_completed(self):
        return self._opWsdt.watershed_completed
    
    def execute(self, slot, subindex, roi, result):
        assert False

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.EnableDebugOutputs and self.EnableDebugOutputs.value:
            # Force a refresh so the debug outputs will be updated.
            self._opCache.Input.setDirty()
