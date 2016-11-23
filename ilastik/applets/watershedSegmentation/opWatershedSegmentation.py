from collections import OrderedDict
import numpy as np

#for wsDtSegmentation
from ilastik.applets.wsdt.wsdtApplet import WsdtApplet
#for OpLabelPipeline
from lazyflow.roi import determineBlockShape


from lazyflow.utility import OrderedSignal
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice, sliceToRoi
from lazyflow.operators import OpBlockedArrayCache, OpValueCache
from lazyflow.operators.generic import OpPixelOperator, OpSingleChannelSelector
#for the LabelPipeline
from lazyflow.operators import OpCompressedUserLabelArray
from ilastik.applets.pixelClassification.opPixelClassification import OpLabelPipeline


import logging
logger = logging.getLogger(__name__)


class OpWatershedSegmentation(Operator):
    """
    Initialize the parameters for the calculations (and Gui)
    Provide execution function for the execution of the watershed algorithm
    """

    ############################################################
    # Inputslots for inputs from other applets
    ############################################################
    RawData         = InputSlot() # Used by the GUI for display only
    Boundaries      = InputSlot() 
    Seeds           = InputSlot(optional=True) 
    #CorrectedSeedsIn is a ndarray, which has the value of the Seeds-InputSlot, 
    #which can be reseted every time the user wants this to do
    #also ideal to use for drawing Labels into
    CorrectedSeedsIn            = InputSlot(optional=True) 
    #CorrectedSeedsOut           = InputSlot() 

    #for testing
    #CorrectedSeedsInTemp            = InputSlot(optional=True) 

    #CorrectedSeedsIn = InputSlot(value=0)

    ############################################################
    # Inputslots for Internal Parameter Usage
    ############################################################
    ChannelSelection    = InputSlot(value=0)
    BrushValue          = InputSlot(value=0)


    ############################################################
    # Output Slots
    ############################################################
    #for the labeling
    #CorrectedSeedsOut    = OutputSlot(level=1) # Labels from the user
    CorrectedSeedsOut   = OutputSlot() # Labels from the user
    NonzeroLabelBlocks  = OutputSlot() # A list if slices that contain non-zero label values

    Projection2D        = OutputSlot()

    #for testing
    #CorrectedSeedsOutTemp   = OutputSlot() # Labels from the user

    # GUI-only (not part of the pipeline, but saved to the project)
    LabelNames = OutputSlot()
    LabelColors = OutputSlot()
    PmapColors = OutputSlot()

    NumClasses = OutputSlot()



    '''
    Pmin = InputSlot(value=0.5)
    MinMembraneSize = InputSlot(value=0)
    MinSegmentSize = InputSlot(value=0)
    SigmaMinima = InputSlot(value=3.0)
    SigmaWeights = InputSlot(value=0.0)
    GroupSeeds = InputSlot(value=False)

    EnableDebugOutputs = InputSlot(value=False)
    
    Superpixels = OutputSlot()
    '''
    def __init__(self, *args, **kwargs):
        super( OpWatershedSegmentation, self ).__init__(*args, **kwargs)
        self.debug_results = None
        '''
        self.watershed_completed = OrderedSignal()
        '''

        # Default values for some input slots
        self.LabelNames.setValue( [] )
        self.LabelColors.setValue( [] )
        self.PmapColors.setValue( [] )







        '''
        # Check if all necessary InputSlots are available and ready
        # and set CorrectedSeedsIn if not supplied
        lst = [ self.RawData , self.Boundaries , self.Seeds , self.CorrectedSeedsIn ]
        lst_seeds = [ self.Seeds , self.CorrectedSeedsIn ]
        #show a debug information, so that the user knows that not all data is supplied, that is needed
        for operator in lst:
            if not operator.ready():
                logger.info( "InputData: " + operator.name + " not ready")


        for operator in lst_seeds:
            if not operator.ready():
                self._existingSeedsSlot = False
                #if (not self.CorrectedSeedsIn.ready() and self.CorrectedSeedsIn.meta.shape == None ):
                if self.Boundaries.ready():
                    # copy the meta-data from boandaries
                    #default_seeds_volume = self.Boundaries[:].wait()
                    operator.meta = self.Boundaries.meta
                    operator._value =  np.zeros(self.Boundaries.meta.shape)
                    #print self.operator._value
                else:
                    logger.info( "Boundaries are not ready," +
                        "can't init seeds and CorrectedSeedsIn with default zeros" )

        '''
        '''
        #for debug
        for operator in lst:
            if operator.ready():
                logger.info( "InputData: " + operator.name + " is ready now")
        '''




        ############################################################
        # OpLabelPipeline setup
        ############################################################
        # Hook up Labeling Pipeline
        #Input
        self.opLabelPipeline = OpLabelPipeline(parent=self)
        self.opLabelPipeline.RawImage.connect( self.RawData )
        self.opLabelPipeline.LabelInput.connect( self.CorrectedSeedsIn )
        self.opLabelPipeline.DeleteLabel.setValue( -1 )

        #print self.CorrectedSeedsIn.ready()
        #print self.opLabelPipeline.LabelInput.ready()

        #Output
        self.CorrectedSeedsOut.connect(     self.opLabelPipeline.Output )
        self.NonzeroLabelBlocks.connect(    self.opLabelPipeline.nonzeroBlocks )


    def setupOutputs(self):
        self.LabelNames.meta.dtype = object
        self.LabelNames.meta.shape = (1,)
        self.LabelColors.meta.dtype = object
        self.LabelColors.meta.shape = (1,)
        self.PmapColors.meta.dtype = object
        self.PmapColors.meta.shape = (1,)
        #TODO
        pass
        #assert self.Input.meta.getAxisKeys()[-1] == 'c', \
        "This operator assumes that channel is the last axis."
        '''
        self.Superpixels.meta.assignFrom( self.Input.meta )
        self.Superpixels.meta.shape = self.Input.meta.shape[:-1] + (1,)
        self.Superpixels.meta.dtype = np.uint32
        self.Superpixels.meta.display_mode = "random-colortable"
        
        self.debug_results = None
        if self.EnableDebugOutputs.value:
            self.debug_results = OrderedDict()
        '''
    
    def execute(self, slot, subindex, roi, result):
        #assert slot is self.Superpixels, "Unknown or unconnected output slot: {}".format( slot )
        channel_index = self.ChannelSelection.value

        '''
        pmap_roi = roi.copy()
        pmap_roi.start[-1] = channel_index
        pmap_roi.stop[-1] = channel_index+1

        # TODO: We could be sneaky and use the result array as a temporary here...
        pmap = self.Input(pmap_roi.start, pmap_roi.stop).wait()
        '''

        if self.debug_results:
            self.debug_results.clear()
        #execute the actual watershed Segmentation
        '''
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
        '''
        
    def propagateDirty(self, slot, subindex, roi):
        pass
        #TODO for watershed calculations
        #if slot is not self.EnableDebugOutputs:
            #self.Superpixels.setDirty()

    def setInSlot(self, slot, subindex, roi, value):
        pass

'''
class OpCachedWatershedSegmentation(Operator):
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
        super( OpCachedWatershedSegmentation, self ).__init__(*args, **kwargs)
        my_slot_names = set(map(lambda slot: slot.name, self.inputSlots + self.outputSlots))
        wsdt_slot_names = set(map(lambda slot: slot.name, OpWatershedSegmentation.inputSlots + OpWatershedSegmentation.outputSlots))
        assert wsdt_slot_names.issubset(my_slot_names), \
            "OpCachedWatershedSegmentation should have all of the slots that OpWatershedSegmentation has (and maybe more). "\
            "Did you add a slot to OpWatershedSegmentation and forget to add it to OpCachedWatershedSegmentation?"
        
        # connect the slots for the input of the gui with the internal handling, or something equal
        self._opWatershedSegmentation = OpWatershedSegmentation( parent=self )
        self._opWatershedSegmentation.Input.connect( self.Input )
        self._opWatershedSegmentation.ChannelSelection.connect( self.ChannelSelection )
        self._opWatershedSegmentation.Pmin.connect( self.Pmin )
        self._opWatershedSegmentation.MinMembraneSize.connect( self.MinMembraneSize )
        self._opWatershedSegmentation.MinSegmentSize.connect( self.MinSegmentSize )
        self._opWatershedSegmentation.SigmaMinima.connect( self.SigmaMinima )
        self._opWatershedSegmentation.SigmaWeights.connect( self.SigmaWeights )
        self._opWatershedSegmentation.GroupSeeds.connect( self.GroupSeeds )
        self._opWatershedSegmentation.EnableDebugOutputs.connect( self.EnableDebugOutputs )
        
        self._opCache = OpBlockedArrayCache( parent=self )
        self._opCache.fixAtCurrent.connect( self.FreezeCache )
        self._opCache.Input.connect( self._opWatershedSegmentation.Superpixels )
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
        return self._opWatershedSegmentation.debug_results


    @property 
    def watershed_completed(self):
        return self._opWatershedSegmentation.watershed_completed
    
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

#TODO change this to fit our operator
class OpWatershedSegmentationLabelPipeline( Operator ):
    RawImage = InputSlot()
    LabelInput = InputSlot()
    DeleteLabel = InputSlot()
    
    Output = OutputSlot()
    nonzeroBlocks = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( OpLabelPipeline, self ).__init__( *args, **kwargs )
        

        self.opLabelArray = OpCompressedUserLabelArray( parent=self )
        self.opLabelArray.Input.connect( self.LabelInput )
        self.opLabelArray.eraser.setValue(100)

        self.opLabelArray.deleteLabel.connect( self.DeleteLabel )

        # Connect external outputs to their internal sources
        self.Output.connect( self.opLabelArray.Output )
        self.nonzeroBlocks.connect( self.opLabelArray.nonzeroBlocks )

    def setupOutputs(self):
        tagged_shape = self.RawImage.meta.getTaggedShape()
        # labels are created for one channel (i.e. the label) and only in the
        # current time slice, so we can set both c and t to 1

        #TODO has no effect to CorrectedSeedsOut right now
        tagged_shape['c'] = 1
        if 't' in tagged_shape:
            tagged_shape['t'] = 1
        # Aim for blocks that are roughly 1MB
        block_shape = determineBlockShape( tagged_shape.values(), 1e6 )
        self.opLabelArray.blockShape.setValue( block_shape )
        

    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"

    def propagateDirty(self, slot, subindex, roi):
        # Our output changes when the input changed shape, not when it becomes dirty.
        pass    
        self.Output.setDirty()



'''

#copied form pixelclassification
class OpLabelPipeline( Operator ):
    RawImage = InputSlot()
    LabelInput = InputSlot()
    DeleteLabel = InputSlot()
    
    Output = OutputSlot()
    nonzeroBlocks = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( OpLabelPipeline, self ).__init__( *args, **kwargs )
        

        self.opLabelArray = OpCompressedUserLabelArray( parent=self )
        self.opLabelArray.Input.connect( self.LabelInput )
        self.opLabelArray.eraser.setValue(100)

        self.opLabelArray.deleteLabel.connect( self.DeleteLabel )

        # Connect external outputs to their internal sources
        self.Output.connect( self.opLabelArray.Output )
        self.nonzeroBlocks.connect( self.opLabelArray.nonzeroBlocks )

    def setupOutputs(self):
        tagged_shape = self.RawImage.meta.getTaggedShape()
        # labels are created for one channel (i.e. the label) and only in the
        # current time slice, so we can set both c and t to 1

        #TODO has no effect to CorrectedSeedsOut right now
        tagged_shape['c'] = 1
        if 't' in tagged_shape:
            tagged_shape['t'] = 1
        # Aim for blocks that are roughly 1MB
        block_shape = determineBlockShape( tagged_shape.values(), 1e6 )
        self.opLabelArray.blockShape.setValue( block_shape )
        

    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"

    def propagateDirty(self, slot, subindex, roi):
        # Our output changes when the input changed shape, not when it becomes dirty.
        pass    
        self.Output.setDirty()
'''
