###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2017, the ilastik developers
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
##############################################################################

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
#for caching the data of the watershed algorithm
from lazyflow.operators import OpCompressedCache
from lazyflow.utility import OrderedSignal

from ilastik.utility.VigraIlastikConversionFunctions import removeLastAxis, addLastAxis, getArray, evaluateSlicing, removeFirstAxis, addFirstAxis

import volumina.colortables as colortables

from opWatershedSegmentationCalculation import OpWatershedSegmentationCalculation
from opWatershedSegmentationLabelPipeline import OpWatershedSegmentationLabelPipeline



import logging
logger = logging.getLogger(__name__)



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

    SeedsExist          = InputSlot(optional=True, value=False) #default that seeds don't exist

    ############################################################
    # Inputslots for Internal Parameter Usage (don't change anything here)
    ############################################################
    ShowWatershedLayer  = InputSlot(value=False) # flag for WatershedCalc Layer
    InputSeedsChanged   = InputSlot(value=False) # flag for reset, when applet gets foreground


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
        self.opWSC.SeedsExist   .connect( self.SeedsExist )
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
        self._cache = OpCompressedCache(parent=self)
        self._cache.name = "OpWatershedSegmentation.OpCompressedCache"
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


        self._sig_labels_to_delete = OrderedSignal(hide_cancellation_exceptions=True)

    def notifyLabelsToDelete(self, function, **kwargs):
        """calls the corresponding function when this signal is emitted
        first argument of the function is the slot
        the keyword arguments follow
        """
        self._sig_labels_to_delete.subscribe(function, **kwargs)
    def unregisterLabelsToDelete(self, function):
        """
        unregister a labels to delete callback
        """
        self._sig_labels_to_delete.unsubscribe(function)


        
    def setupOutputs(self):
        self.LabelNames.meta.dtype  = object
        #self.LabelNames.meta.shape = (1,)
        self.LabelNames.meta.shape  = (1,)
        self.LabelColors.meta.dtype = object
        self.LabelColors.meta.shape = (1,)
        self.PmapColors.meta.dtype  = object
        self.PmapColors.meta.shape  = (1,)

        #TODO for testing 
        print self.WSMethod.value


        # FOR PROPER CACHING, SET THE BLOCKSIZE OF THE CACHE FOR WSCALCULATIONS
        # set the cache blocks to have the time as (1,) and 
        # not to be the whole image size
        # otherwise computing something and cutting away the time axis, 
        # will conclude in an error, because the region asked for is e.g. t=1-200, but not t=1 
        shape = self.Boundaries.meta.shape
        blockshape = (1,) + shape[1:]
        self._cache.BlockShape.setValue(blockshape)


    
    def execute(self, slot, subindex, roi, result):
        assert False, "Should never be called!"
        
    def propagateDirty(self, slot, subindex, roi):
        print "in opWS propagate Dirty"
        if slot is self.CorrectedSeedsIn:
            # set flag to True; means remember to reset the labels when the applet gets to foreground
            self.InputSeedsChanged.setValue(True)

    def setInSlot(self, slot, subindex, roi, value):
        pass








    ############################################################
    # Labelmanagement: Import, Delete, Reset
    ############################################################

    def resetLabelsToSlot(self):
        """
        """
        self.removeLabelsFromCache()
        if self.SeedsExist.value:
            #remove LabelListModel not necessary. Resetting the LabelNames is enough

            # Finally, import the labels from the original slot
            self.importLabels()

        else:
            # remove the labels from list
            # this happens in the gui, in showEvent()
            pass



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




