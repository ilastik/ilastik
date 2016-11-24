#from collections import OrderedDict
#import numpy as np

#for wsDtSegmentation
#from ilastik.applets.wsdt.wsdtApplet import WsdtApplet
#for OpLabelPipeline
#from lazyflow.roi import determineBlockShape

#from lazyflow.utility import OrderedSignal
#from lazyflow.roi import roiToSlice, sliceToRoi
#from lazyflow.operators import OpBlockedArrayCache, OpValueCache
#from lazyflow.operators.generic import OpPixelOperator, OpSingleChannelSelector


from lazyflow.graph import Operator, InputSlot, OutputSlot

#for the LabelPipeline
#from lazyflow.operators import OpCompressedUserLabelArray
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
    #TODO don't need them
    ChannelSelection    = InputSlot(value=0)
    BrushValue          = InputSlot(value=0)


    ############################################################
    # Output Slots
    ############################################################
    #for the labeling
    CorrectedSeedsOut   = OutputSlot() # Labels from the user
    #NonzeroLabelBlocks  = OutputSlot() # A list if slices that contain non-zero label values

    Projection2D        = OutputSlot()


    # GUI-only (not part of the pipeline, but saved to the project)
    LabelNames = OutputSlot()
    LabelColors = OutputSlot()
    PmapColors = OutputSlot()

    NumClasses = OutputSlot()

    '''
    EnableDebugOutputs = InputSlot(value=False)
    Superpixels = OutputSlot()
    '''

    def __init__(self, *args, **kwargs):
        super( OpWatershedSegmentation, self ).__init__(*args, **kwargs)
        #self.debug_results = None
        #self.watershed_completed = OrderedSignal()

        # Default values for some input slots
        self.LabelNames.setValue( [] )
        self.LabelColors.setValue( [] )
        self.PmapColors.setValue( [] )

        ############################################################
        # Label-Pipeline setup
        ############################################################
        self.opWSLP = OpWatershedSegmentationLabelPipeline(parent=self)
        #Input
        self.opWSLP.RawData.connect(    self.RawData )
        self.opWSLP.SeedInput.connect(  self.CorrectedSeedsIn )
        #Output
        self.CorrectedSeedsOut.connect( self.opWSLP.SeedOutput )


    def setupOutputs(self):
        self.LabelNames.meta.dtype = object
        self.LabelNames.meta.shape = (1,)
        self.LabelColors.meta.dtype = object
        self.LabelColors.meta.shape = (1,)
        self.PmapColors.meta.dtype = object
        self.PmapColors.meta.shape = (1,)
    
    def execute(self, slot, subindex, roi, result):
        pass
        
    def propagateDirty(self, slot, subindex, roi):
        pass
        #for watershed calculations
        #if slot is not self.EnableDebugOutputs:
            #self.Superpixels.setDirty()

    def setInSlot(self, slot, subindex, roi, value):
        pass


class OpWatershedSegmentationLabelPipeline( Operator ):
    """
    operator class, that handles the Label Pipeline and the connections to it
    """
    RawData    = InputSlot()
    SeedInput   = InputSlot()
    SeedOutput  = OutputSlot()
    
    
    def __init__(self, *args, **kwargs):
        super( OpWatershedSegmentationLabelPipeline, self ).__init__( *args, **kwargs )
        
        self.opLabelPipeline = OpLabelPipeline(parent=self)
        self.opLabelPipeline.RawImage.connect( self.RawData )
        self.opLabelPipeline.LabelInput.connect( self.SeedInput )
        self.opLabelPipeline.DeleteLabel.setValue( -1 )

        #Output
        self.SeedOutput.connect(            self.opLabelPipeline.Output )


    def setupOutputs(self):
        pass

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"

    def propagateDirty(self, slot, subindex, roi):
        pass    






