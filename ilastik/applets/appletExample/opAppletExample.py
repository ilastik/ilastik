
from collections import OrderedDict
import numpy as np

from wsdt import wsDtSegmentation as segmentationAlgo #TODO 

from lazyflow.utility import OrderedSignal
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice, sliceToRoi
from lazyflow.operators import OpBlockedArrayCache, OpValueCache
from lazyflow.operators.generic import OpPixelOperator, OpSingleChannelSelector

class OpAppletExample(Operator): #TODO
    Input = InputSlot() # Can be multi-channel (but you'll have to choose which channel you want to use)
    ChannelSelection = InputSlot(value=0)

    # Parameters
    Pmin = InputSlot(value=0.5)
    MinMembraneSize = InputSlot(value=0)
    MinSegmentSize = InputSlot(value=0)
    SigmaMinima = InputSlot(value=3.0)
    SigmaWeights = InputSlot(value=0.0)
    GroupSeeds = InputSlot(value=False)

    EnableDebugOutputs = InputSlot(value=False)
    
    Superpixels = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpAppletExample, self ).__init__(*args, **kwargs) #TODO 
        self.debug_results = None
        self.algorithm_completed = OrderedSignal() #TODO replace algorithm with anything else

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
        segmentationAlgo( pmap[...,0], #TODO
                          self.Pmin.value,
                          self.MinMembraneSize.value,
                          self.MinSegmentSize.value,
                          self.SigmaMinima.value,
                          self.SigmaWeights.value,
                          self.GroupSeeds.value,
                          out_debug_image_dict=self.debug_results,
                          out=result[...,0] )
        
        self.algorithm_completed() #TODO 
        
    def propagateDirty(self, slot, subindex, roi):
        if slot is not self.EnableDebugOutputs:
            self.Superpixels.setDirty()

class OpCachedAppletExample(Operator): #TODO
    RawData = InputSlot(optional=True) # Used by the GUI for display only
    FreezeCache = InputSlot(value=True)
    
    Input = InputSlot() # Can be multi-channel (but you'll have to choose which channel you want to use)
    ChannelSelection = InputSlot(value=0)

    # Parameters
    Pmin = InputSlot(value=0.5)
    MinMembraneSize = InputSlot(value=0)
    MinSegmentSize = InputSlot(value=0)
    SigmaMinima = InputSlot(value=3.0)
    SigmaWeights = InputSlot(value=0.0)
    GroupSeeds = InputSlot(value=False)

    EnableDebugOutputs = InputSlot(value=False)
    
    Superpixels = OutputSlot()
    
    SuperpixelCacheInput = InputSlot(optional=True)
    CleanBlocks = OutputSlot()

    # Thresholding is cheap and best done interactively,
    # so expose an uncached slot just for it
    ThresholdedInput = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpCachedAppletExample, self ).__init__(*args, **kwargs) #TODO
        my_slot_names = set(map(lambda slot: slot.name, self.inputSlots + self.outputSlots))
        appletExample_slot_names = \
                set(map(lambda slot: slot.name, OpAppletExample.inputSlots + OpAppletExample.outputSlots)) #TODO
        assert appletExample_slot_names.issubset(my_slot_names), \
            "OpCachedAppletExample should have all of the slots that OpAppletExample has (and maybe more). "\
            "Did you add a slot to OpAppletExample and forget to add it to OpCachedAppletExample?" #TODO
        #TODO
        self._opAppletExample = OpAppletExample( parent=self )
        self._opAppletExample.Input.connect( self.Input )
        self._opAppletExample.ChannelSelection.connect( self.ChannelSelection )
        self._opAppletExample.Pmin.connect( self.Pmin )
        self._opAppletExample.MinMembraneSize.connect( self.MinMembraneSize )
        self._opAppletExample.MinSegmentSize.connect( self.MinSegmentSize )
        self._opAppletExample.SigmaMinima.connect( self.SigmaMinima )
        self._opAppletExample.SigmaWeights.connect( self.SigmaWeights )
        self._opAppletExample.GroupSeeds.connect( self.GroupSeeds )
        self._opAppletExample.EnableDebugOutputs.connect( self.EnableDebugOutputs )
        
        self._opCache = OpBlockedArrayCache( parent=self )
        self._opCache.fixAtCurrent.connect( self.FreezeCache )
        self._opCache.Input.connect( self._opAppletExample.Superpixels )
        self.Superpixels.connect( self._opCache.Output )
        self.CleanBlocks.connect( self._opCache.CleanBlocks )

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
        return self._opAppletExample.debug_results #TODO
    
    @property
    def algorithm_completed(self):
        return self._opAppletExample.algorithm_completed #TODO
    
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
