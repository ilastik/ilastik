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

from ilastik.utility.VigraIlastikConversionFunctions import removeLastAxis, addLastAxis, getArray, evaluateSlicing, removeFirstAxis, addFirstAxis

import volumina.colortables as colortables

from opWatershedSegmentationCalculation import OpWatershedSegmentationCalculation



import logging
logger = logging.getLogger(__name__)



class OpWatershedSegmentationLabelPipeline( Operator ):
    """
    operator class, that handles the Label Pipeline and the connections to it.
    the opLabelPipeline handles the connections to the opCompressedUserLabelArray, 
    which is responsable for everything of the caching and so on
    """
    RawData     = InputSlot()
    SeedInput   = InputSlot()
    SeedOutput  = OutputSlot()
    NonZeroBlocks = OutputSlot()
    
    
    def __init__(self, *args, **kwargs):
        super( OpWatershedSegmentationLabelPipeline, self ).__init__( *args, **kwargs )
        
        self.opLabelPipeline = OpLabelPipeline(parent=self)
        self.opLabelPipeline.RawImage.connect( self.RawData )
        self.opLabelPipeline.LabelInput.connect( self.SeedInput )
        self.opLabelPipeline.DeleteLabel.setValue( -1 )

        #Output
        self.SeedOutput.connect( self.opLabelPipeline.Output )
        self.NonZeroBlocks.connect( self.opLabelPipeline.nonzeroBlocks )

    def setupOutputs(self):
        '''
        self.SeedOutput.meta.assignFrom(self.SeedInput.meta)
        # output of the vigra.analysis.watershedNew is uint32, therefore it should be uint 32 as
        # well, otherwise it will break with the cached image 
        self.SeedOutput.meta.dtype = np.uint8
        #only one channel as output
        #self.SeedOutput.meta.shape = self.Boundaries.meta.shape[:-1] + (1,)
        #TODO maybe bad with more than 255 labels
        #self.SeedOutput.meta.drange = (0,255)
        '''
        pass

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"


    def propagateDirty(self, slot, subindex, roi):
        print "LabelPipeline dirty: " + slot.name
        self.SeedOutput.setDirty()
        pass    


class OpWatershedSegmentation(Operator):
    """
    Initialize the parameters for the calculations (and Gui)
    Provide execution function for the execution of the watershed algorithm

    The names of slots are explained below


    Pretending the axisorders are txyzc like in watershedSegmentationWorkflow
    """


    ############################################################
    # Inputslots for inputs from other applets
    ############################################################
    RawData             = InputSlot() # Used by the GUI for display only
    Boundaries          = InputSlot() # for displaying as layer and as input for the watershed algorithm 
    Seeds               = InputSlot(optional=True) #for displaying in layer only
    CorrectedSeedsIn    = InputSlot(optional=True) #deals as input for the LabelChange stuff 

    SeedsExist          = InputSlot(optional=True, value=True) #default that seeds exist

    ############################################################
    # Inputslots for Internal Parameter Usage (don't change anything here)
    ############################################################
    ShowWatershedLayer  = InputSlot(value=False)
    # not used anymore
    #UseCachedLabels     = InputSlot(value=False)

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



    def __init__(self, *args, **kwargs):
        super( OpWatershedSegmentation, self ).__init__(*args, **kwargs)

        # Default values for the slots, where the Names of the Labels for the 
        # LabelListModel, the color and the pixelMap is saved in
        self.LabelNames.setValue( [] )
        self.LabelColors.setValue( [] )
        self.PmapColors.setValue( [] )

        ############################################################
        # Label-Pipeline setup = WSLP
        ############################################################
        self.opWSLP = OpWatershedSegmentationLabelPipeline(parent=self)
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
        self.opWSC  = OpWatershedSegmentationCalculation( parent=self)
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
        self._cache.name = "OpWatershedSegmentation.OpCacheWrapper"
        # use this output of the cache for displaying in a layer only
        self.WSCCOCachedOutput.connect(self._cache.Output)

        # Serialization slots
        self._cache.InputHdf5.connect(self.WSCCOInputHdf5)
        self.WSCCOCleanBlocks.connect(self._cache.CleanBlocks)
        self.WSCCOOutputHdf5.connect(self._cache.OutputHdf5)

        # the crux, where to define the Cache-Data
        self._cache.Input.connect(self.WatershedCalc)


        #TODO 
        print "Init opWatershedSegmentation"


        #TODO this is tooo slow, because it is dirty more than once
        #self.CorrectedSeedsIn.notifyDirty(self.onSeedsDirty)

    def onSeedsDirty(self, x, y):
        """
        """
        print "onSeedsDirty WS"

        self.resetLabelsToSlot()
        '''
        print self.CorrectedSeedsIn.ready()
        if not self.Seeds.ready():

            for slot in self.outputs.values():
                slot.setDirty()
                #TODO remove after testing
                print "set this slot dirty: " + slot.name
        '''


    def setupOutputs(self):
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


        #TODO for testing 
        print self.WSMethod.value

    
    def execute(self, slot, subindex, roi, result):
        pass
        print "Main" + str( slot.name)
        #print "Main" + str(roi)
        
    def propagateDirty(self, slot, subindex, roi):
        # set all outputSlots dirty
        for slot in self.outputs.values():
            slot.setDirty()
        #print "propagteDirty in opWatershedSegmentation"
        #print "Main: "+ slot.name

    def setInSlot(self, slot, subindex, roi, value):
        pass








    ############################################################
    # Labelmanagement: Import, Delete, Reset
    ############################################################

    def resetLabelsToSlot(self):
        """
        """
        if self.SeedsExist.value:
            self.removeLabelsFromCache()
            #remove LabelListModel not necessary. Resetting the LabelNames is enough

            # Finally, import the labels from the original slot
            self.importLabels()

        else:
            self.removeLabelsFromCache()



    def removeLabelsFromCache(self):
        """
        Remove every Label that is in the Cache all at once
        """

        '''
        import time
        print "start remove Labels"
        start = time.time()
        end = time.time()
        print  "removed Labels: "+ str(end - start)
        '''

        # this function could be improved drastically
        self.opWSLP.opLabelPipeline.opLabelArray.clearAllLabels( )

    '''
    def removeLabelsFromList(self):
        rows = self._labelListModel.rowCount()
        for i in range( rows ):
            self._labelListModel.removeRowWithoutEmittingSignal(0)
    '''


    def importLabels(self):
        """
        original version from: pixelClassificationGui.importLabels
        Add the data included in the slot to the LabelArray by ingestData
        Only use this when the colors and Labels are reset. 
        The LabelColors, Pmaps and ListNames are reset and added with the default 
        properties to the list and slots
        
        """
        # Load the data into the cache
        # Returns: the max label found in the slot.
        new_max = self.opWSLP.opLabelPipeline.opLabelArray.ingestData(self.CorrectedSeedsIn)

        # Add to the list of label names 
        new_names = map( lambda x: "Seed" + " {}".format(x), 
                                         range(1, new_max+1) )
        #add the new Labelnames
        self.LabelNames.setValue(new_names)

        #set the colorvalue and the color that is displayed in the labellist to the correct color

        # Use the given colortable that is used everywhere else
        # means: for new labels, for layer displaying etc

        default_colors = colortables.create_random_8bit_zero_transparent() 
        self.LabelColors.setValue( default_colors[:new_max] )
        self.PmapColors.setValue( default_colors[:new_max] )




