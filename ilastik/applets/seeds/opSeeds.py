#from collections import OrderedDict
#for wsDtSegmentation
#from ilastik.applets.wsdt.wsdtApplet import WsdtApplet
#for OpLabelPipeline
#from lazyflow.roi import determineBlockShape

#from lazyflow.utility import OrderedSignal
#from lazyflow.roi import roiToSlice, sliceToRoi
#from lazyflow.operators import OpBlockedArrayCache, OpValueCache
#from lazyflow.operators.generic import OpPixelOperator, OpSingleChannelSelector
#for the LabelPipeline
#from lazyflow.operators import OpCompressedUserLabelArray

import numpy as np
import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot
from ilastik.applets.pixelClassification.opPixelClassification import OpLabelPipeline
#for caching the data of the watershed algorithm
from ilastik.applets.thresholdTwoLevels.opThresholdTwoLevels import _OpCacheWrapper

import logging
logger = logging.getLogger(__name__)


class OpSeeds(Operator):
    """
    Initialize the parameters for the calculations (and Gui)

    The names of slots are explained below
    """

    ############################################################
    # Inputslots for inputs from other applets
    ############################################################
    RawData             = InputSlot() # Used by the GUI for display only
    Boundaries          = InputSlot() # for displaying as layer and as input for the watershed algorithm 
    Seeds               = InputSlot(optional=True) #for displaying in layer only

    Output              = OutputSlot()
    '''
    CorrectedSeedsIn    = InputSlot(optional=True) #deals as input for the LabelChange stuff 


    ############################################################
    # Inputslots for Internal Parameter Usage (don't change anything here)
    ############################################################
    ShowWatershedLayer  = InputSlot(value=False)
    UseCachedLabels     = InputSlot(value=False)

    ############################################################
    # watershed algorithm parameters (optional)
    ############################################################
    # a list of options can be found in function: prepareInputParameter
    WSNeighbors         = InputSlot(value="direct")
    WSMethod            = InputSlot(value="RegionGrowing")
    # default values
    WSTerminate         = InputSlot(value=vigra.analysis.SRGType.CompleteGrow)
    WSMaxCost           = InputSlot(value=0)


    ############################################################
    # Output Slots
    ############################################################
    #for the labeling
    CorrectedSeedsOut   = OutputSlot() # Labels from the user, used as seeds for the watershed algorithm
    WatershedCalc       = OutputSlot()
    #Cached Output of watershed should be the output in a layer, nothing more
    WSCCOCachedOutput   = OutputSlot()  # For the GUI (blockwise-access)

    ############################################################
    # Watershed: For serialization (saving in cache) of the watershed Output
    ############################################################
    WSCCOInputHdf5      = InputSlot(optional=True)
    WSCCOOutputHdf5     = OutputSlot()
    WSCCOCleanBlocks    = OutputSlot()


    ############################################################
    # Label slots (for the LabelListModel)
    ############################################################

    # GUI-only (not part of the pipeline, but saved to the project)
    LabelNames          = OutputSlot()
    LabelColors         = OutputSlot()
    PmapColors          = OutputSlot()

    NonZeroBlocks       = OutputSlot()

    '''


    def __init__(self, *args, **kwargs):
        super( OpSeeds, self ).__init__(*args, **kwargs)


        '''
        # Default values for the slots, where the Names of the Labels for the 
        # LabelListModel, the color and the pixelMap is saved in
        self.LabelNames.setValue( [] )
        self.LabelColors.setValue( [] )
        self.PmapColors.setValue( [] )

        ############################################################
        # Label-Pipeline setup = WSLP
        ############################################################
        self.opWSLP = OpSeedsLabelPipeline(parent=self)
        #Input
        self.opWSLP.RawData     .connect( self.RawData )
        self.opWSLP.SeedInput   .connect( self.CorrectedSeedsIn )
        #Output
        self.CorrectedSeedsOut  .connect( self.opWSLP.SeedOutput )
        # (optional)
        self.NonZeroBlocks      .connect( self.opWSLP.NonZeroBlocks )

        ############################################################
        # watershed calculations = WSC
        ############################################################
        self.opWSC  = OpSeedsCalculation( parent=self)
        #Input
        self.opWSC.Boundaries   .connect( self.Boundaries )
        self.opWSC.Seeds        .connect( self.CorrectedSeedsOut )
        #Input Parameters (optional)
        self.opWSC.Neighbors    .connect( self.WSNeighbors )
        self.opWSC.Method       .connect( self.WSMethod )
        self.opWSC.MaxCost      .connect( self.WSMaxCost )
        self.opWSC.Terminate    .connect( self.WSTerminate )
        #Output
        self.WatershedCalc.connect( self.opWSC.Output )

        ############################################################
        # watershed calculations cached output = WSCCO
        ############################################################
        #cache our own output, don't propagate from internal operator
        self._cache = _OpCacheWrapper(parent=self)
        self._cache.name = "OpSeeds.OpCacheWrapper"
        # use this output of the cache for displaying in a layer only
        self.WSCCOCachedOutput.connect(self._cache.Output)

        # Serialization slots
        self._cache.InputHdf5.connect(self.WSCCOInputHdf5)
        self.WSCCOCleanBlocks.connect(self._cache.CleanBlocks)
        self.WSCCOOutputHdf5.connect(self._cache.OutputHdf5)

        # the crux, where to define the Cache-Data
        self._cache.Input.connect(self.WatershedCalc)
        '''


    def setupOutputs(self):
        '''
        self.LabelNames.meta.dtype  = object
        #self.LabelNames.meta.shape = (1,)
        self.LabelNames.meta.shape  = (1,)
        self.LabelColors.meta.dtype = object
        self.LabelColors.meta.shape = (1,)
        self.PmapColors.meta.dtype  = object
        self.PmapColors.meta.shape  = (1,)


        ############################################################
        # For serialization 
        ############################################################
        # force the cache to emit a dirty signal 
        # (just taken from applet thresholdTwoLevel)
        self._cache.Input.connect(self.WatershedCalc)
        self._cache.Input.setDirty(slice(None))
        '''
        pass

    
    def execute(self, slot, subindex, roi, result):
        pass
        
    def propagateDirty(self, slot, subindex, roi):
        pass

    def setInSlot(self, slot, subindex, roi, value):
        pass


