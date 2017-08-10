from collections import OrderedDict
import numpy as np

#for wsDtSegmentation
#from ilastik.applets.wsdt.wsdtApplet import WsdtApplet


from lazyflow.utility import OrderedSignal
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice, sliceToRoi
from lazyflow.operators import OpBlockedArrayCache, OpValueCache
from lazyflow.operators.generic import OpPixelOperator, OpSingleChannelSelector

class OpChannelSelection(Operator):
    ############################################################
    # Define Inputslots for Internal
    ############################################################
    #define slots and give a default value, not external input
    Visibility  = InputSlot(value=1.0)
    Utilize     = InputSlot(value=1.0) #value 1.0 sets the checkbox to checked
    Seed        = InputSlot(value=0.0) 
    Label       = InputSlot(value=0.0) 


    #Image Inputs
    Probability = InputSlot(optional=False) 
    RawData     = InputSlot(optional=True) # Used by the GUI for display only

    #Outputs
    Seed_Channel= OutputSlot()

    InputB      = InputSlot()

    Output      = OutputSlot()

    #TODO ab hier bis unten
    def setupOutputs(self):
        self.Seed_Channel.meta.assignFrom(self.InputA.meta)


        assert self.Input.meta.getAxisKeys()[-1] == 'c', \
            "This operator assumes that channel is the last axis."
        self.Superpixels.meta.assignFrom( self.Input.meta )
        self.Superpixels.meta.shape = self.Input.meta.shape[:-1] + (1,)
        self.Superpixels.meta.dtype = np.uint32
        self.Superpixels.meta.display_mode = "random-colortable"


    def execute(self, slot, subindex, roi, result):
        a = self.InputA.get(roi).wait()
        b = self.InputB.get(roi).wait()
        result[...] = a+b
        return result

    def propagateDirty(self, dirtySlot, subindex, roi):
        self.Output.setDirty(roi)
    pass

'''
class OpSingleChannelSelector(Operator):
    name = "SingleChannelSelector"
    description = "Select One channel from a Multichannel Image"

    inputSlots = [InputSlot("Input"),InputSlot("Index",stype='integer')]
    outputSlots = [OutputSlot("Output")]

    def setupOutputs(self):
        
        channelAxis = self.Input.meta.axistags.channelIndex
        inshape     = list(self.Input.meta.shape)
        outshape    = list(inshape)
        outshape.pop(channelAxis)
        outshape.insert(channelAxis, 1)
        outshape    = tuple(outshape)

        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.shape = outshape

        ideal = self.Output.meta.ideal_blockshape
        if ideal is not None and len(ideal) == len(inshape):
            ideal = numpy.asarray(ideal, dtype=numpy.int)
            ideal[channelAxis] = 1
            self.Output.meta.ideal_blockshape = tuple(ideal)

        max_blockshape = self.Output.meta.max_blockshape
        if max_blockshape is not None and len(max_blockshape) == len(inshape):
            max_blockshape = numpy.asarray(max_blockshape, dtype=numpy.int)
            max_blockshape[channelAxis] = 1
            self.Output.meta.max_blockshape = tuple(max_blockshape)

        # Output can't be accessed unless the input has enough channels
        # We can't assert here because it's okay to configure this slot incorrectly as long as it is never accessed.
        # Because the order of callbacks isn't well defined, people may not disconnect this operator from its 
        #  upstream partner until after it has already been configured.
        # Again, that's okay as long as it isn't accessed.
        #assert self.Input.meta.getTaggedShape()['c'] > self.Index.value, \
        #        "Requested channel {} is out of range of input data (shape {})".format(self.Index.value, self.Input.meta.shape)
        if self.Input.meta.getTaggedShape()['c'] <= self.Index.value:
            self.Output.meta.NOTREADY = True
        
    def execute(self, slot, subindex, roi, result):
        index=self.inputs["Index"].value
        channelIndex = self.Input.meta.axistags.channelIndex
        assert self.inputs["Input"].meta.shape[channelIndex] > index, \
            "Requested channel, {}, is out of Range (input shape is {})".format( index, self.Input.meta.shape )

        # Only ask for the channel we need
        key = roiToSlice(roi.start,roi.stop)
        newKey = list(key)
        newKey[channelIndex] = slice(index, index+1, None)
        #newKey = key[:-1] + (slice(index,index+1),)
        self.inputs["Input"][tuple(newKey)].writeInto(result).wait()
        return result

    def propagateDirty(self, slot, subindex, roi):
        key = roi.toSlice()
        if slot == self.Input:
            channelIndex = self.Input.meta.axistags.channelIndex
            newKey = list(key)
            newKey[channelIndex] = slice(0, 1, None)
            #key = key[:-1] + (slice(0,1,None),)
            self.outputs["Output"].setDirty(tuple(newKey))
        else:
            self.Output.setDirty(slice(None))
'''





class OpCachedChannelSelection(Operator):
    pass

    """
    Initialize the parameters for the calculations (and Gui)
    Provide execution function for the execution of the watershed algorithm
    """

'''
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
        super( OpChannelSelection, self ).__init__(*args, **kwargs)
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
        #execute the actual watershed Segmentation
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

class OpCachedChannelSelection(Operator):
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
        super( OpCachedChannelSelection, self ).__init__(*args, **kwargs)
        my_slot_names = set(map(lambda slot: slot.name, self.inputSlots + self.outputSlots))
        wsdt_slot_names = set(map(lambda slot: slot.name, OpChannelSelection.inputSlots + OpChannelSelection.outputSlots))
        assert wsdt_slot_names.issubset(my_slot_names), \
            "OpCachedChannelSelection should have all of the slots that OpChannelSelection has (and maybe more). "\
            "Did you add a slot to OpChannelSelection and forget to add it to OpCachedChannelSelection?"
        
        # connect the slots for the input of the gui with the internal handling, or something equal
        self._opChannelSelection = OpChannelSelection( parent=self )
        self._opChannelSelection.Input.connect( self.Input )
        self._opChannelSelection.ChannelSelection.connect( self.ChannelSelection )
        self._opChannelSelection.Pmin.connect( self.Pmin )
        self._opChannelSelection.MinMembraneSize.connect( self.MinMembraneSize )
        self._opChannelSelection.MinSegmentSize.connect( self.MinSegmentSize )
        self._opChannelSelection.SigmaMinima.connect( self.SigmaMinima )
        self._opChannelSelection.SigmaWeights.connect( self.SigmaWeights )
        self._opChannelSelection.GroupSeeds.connect( self.GroupSeeds )
        self._opChannelSelection.EnableDebugOutputs.connect( self.EnableDebugOutputs )
        
        self._opCache = OpBlockedArrayCache( parent=self )
        self._opCache.fixAtCurrent.connect( self.FreezeCache )
        self._opCache.Input.connect( self._opChannelSelection.Superpixels )
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
        return self._opChannelSelection.debug_results


    @property 
    def watershed_completed(self):
        return self._opChannelSelection.watershed_completed
    
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

'''
