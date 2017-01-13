import numpy as np
import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot
#for caching the data of the generating seeds
from ilastik.applets.thresholdTwoLevels.opThresholdTwoLevels import _OpCacheWrapper

from ilastik.utility.VigraIlastikConversionFunctions import getArray

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

    GeneratedSeeds      = InputSlot(optional=True)
    SeedsOut            = OutputSlot()
    SeedsOutCached      = OutputSlot()

    SeedsExist          = OutputSlot()

    #Layer for displaying, not cached TODO maybe do caching
    Smoothing           = InputSlot(optional=True)
    Computing           = InputSlot(optional=True)
    
    # transmit the WSMethod to the WatershedSegmentationApplet (see Workflow)
    WSMethodIn          = InputSlot()
    WSMethodOut         = OutputSlot()

    #Parameters and their default values
    Unseeded            = InputSlot(value=False)
    SmoothingMethod     = InputSlot(value=0) #index=0
    SmoothingSigma      = InputSlot(value=1.0)
    ComputeMethod       = InputSlot(value=0) #index=0


    ############################################################
    # SeedsOut: For serialization (saving in cache) of the generated/transmitted Seeds
    ############################################################
    SeedsInputHdf5      = InputSlot(optional=True)
    SeedsOutputHdf5     = OutputSlot()
    SeedsCleanBlocks    = OutputSlot()

    '''
    ############################################################
    # Watershed: For serialization (saving in cache) of the watershed Output
    ############################################################
    WSCCOInputHdf5      = InputSlot(optional=True)
    WSCCOOutputHdf5     = OutputSlot()
    WSCCOCleanBlocks    = OutputSlot()
    '''


    def __init__(self, *args, **kwargs):
        super( OpSeeds, self ).__init__(*args, **kwargs)


        '''
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
        ############################################################
        # SeedsOut cached
        ############################################################
        #cache our own output, don't propagate from internal operator
        self._cache = _OpCacheWrapper(parent=self)
        self._cache.name = "OpSeeds.OpCacheWrapper"
        # use this output of the cache for displaying in a layer only
        self.SeedsOutCached.connect(self._cache.Output)

        # Serialization slots
        self._cache.InputHdf5.connect(self.SeedsInputHdf5)
        self.SeedsCleanBlocks.connect(self._cache.CleanBlocks)
        self.SeedsOutputHdf5.connect(self._cache.OutputHdf5)

        # the crux, where to define the Cache-Data
        self._cache.Input.connect(self.SeedsOut)


    def setupOutputs(self):
        self.WSMethodOut.setValue( self.WSMethodIn.value )

        # set the correct value of SeedsExist Operator
        # True if: Seeds | Generated Seeds available
        if self.Seeds.ready():
            self.SeedsExist.setValue( True )
        else:
            if self.GeneratedSeeds.ready(): 
                self.SeedsExist.setValue( True )
            else:
                self.SeedsExist.setValue( False )


        #self.SeedsOut configuration
        self.SeedsOut.meta.assignFrom(self.Boundaries.meta)
        #only one channel as output
        self.SeedsOut.meta.shape = self.Boundaries.meta.shape[:-1] + (1,)
        self.SeedsOut.meta.drange = (0,255)
        self.SeedsOut.meta.dtype = np.uint8
        # value:
        # if Generated: then use Generated
        # if not Generated and Seeds: use Seeds
        # if not Generated and not Seeds: 
        #       then use format of boundaries with zeros for Seeds to the next applet

        if (self.GeneratedSeeds.ready() and not self.GeneratedSeeds.meta.shape == None):
            array       = getArray(self.GeneratedSeeds)
            #print "\n\nGenerateSeeds\n\n"
        elif ( (not self.GeneratedSeeds.ready() and self.GeneratedSeeds.meta.shape == None ) 
            and self.Seeds.ready() and not self.Seeds.meta.shape == None):
            array       = getArray(self.Seeds)
            #print "\n\nSeeds\n\n"
        else:
            shape       = self.Boundaries.meta.shape
            array       = np.zeros(shape, dtype=np.uint8)
            #print "\n\nzeros\n\n"


        # output sets
        array           = array.astype(np.uint8)
        self.SeedsOut.setValue(array)

        ############################################################
        # For serialization 
        ############################################################
        # force the cache to emit a dirty signal 
        # (just taken from applet thresholdTwoLevel)
        self._cache.Input.connect(self.SeedsOut)
        self._cache.Input.setDirty(slice(None))

        #print self.SeedsOut
        #print self.SeedsOut.meta
        #print self.SeedsOutCached
        #print self.SeedsOutCached.meta
        '''
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


