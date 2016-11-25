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
    RawData             = InputSlot() # Used by the GUI for display only
    Boundaries          = InputSlot() 
    Seeds               = InputSlot(optional=True) #for displaying in layer only
    CorrectedSeedsIn    = InputSlot(optional=True) #deals as input for the LabelChange stuff 


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
    CorrectedSeedsOut   = OutputSlot() # Labels from the user, used as seeds for the watershed algorithm
    WatershedCalculations = OutputSlot()


    # GUI-only (not part of the pipeline, but saved to the project)
    LabelNames = OutputSlot()
    LabelColors = OutputSlot()
    PmapColors = OutputSlot()

    #NonzeroLabelBlocks  = OutputSlot() # A list if slices that contain non-zero label values
    #NumClasses = OutputSlot()
    #Projection2D        = OutputSlot()


    def __init__(self, *args, **kwargs):
        super( OpWatershedSegmentation, self ).__init__(*args, **kwargs)

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

        ############################################################
        # watershed
        ############################################################


        self.opWSC  = OpWatershedSegmentationCalculation( parent=self)
        self.opWSC.Boundaries.connect(  self.Boundaries )
        self.opWSC.Seeds.connect(       self.CorrectedSeedsOut )
        self.WatershedCalculations.connect( self.opWSC.Output )

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

class OpWatershedSegmentationCalculation( Operator ):
    """
    operator class, that handles the input and output of calculation
    """
    #input slot
    Boundaries  = InputSlot()
    Seeds       = InputSlot()


    #optional parameter input slots
    #default value is 0
    Neighbours  = InputSlot(optional=True, value=0)
    Method      = InputSlot(optional=True, value=0)

    #output slot
    Output      = OutputSlot()
    
    def execWatershedAlgorithm(self):
        """
        handles the execution of the watershed algorithm 
        """
        #print "In OpWatershedSegmentationCalculation in function execWatershedAlgorithm"

        #get the data from boundaries and seeds
        requestBoundaries   = self.Boundaries[:]
        requestSeeds        = self.Seeds[:]
        resultBoundaries    = requestBoundaries.wait()
        resultSeeds         = requestSeeds.wait()
        #print requestBoundaries

        arrayBoundaries = resultBoundaries
        arraySeeds      = resultSeeds
        originalShape   = arraySeeds.shape
        ######## data conversion #####
        #boundaries
        #input image: uint8 or float32

        #for the seeds
        #turbo: uint8, the rest: uint32
        arrayBoundaries = arrayBoundaries.astype(np.uint8)
        arraySeeds      = arraySeeds.astype(np.uint32)


        ######## size fixing #####
        #cut off the channel dimension
        arrayBoundaries = arrayBoundaries.reshape(arrayBoundaries.shape[0:-1])
        arraySeeds      = arraySeeds.reshape(arraySeeds.shape[0:-1])




        #TODO handle channel
        #TODO handle 2D or 3D, means, slicing or nonslicing

        np_seeds=arraySeeds
        labelImageArray = np.ndarray(shape=np_seeds.shape, dtype=np_seeds.dtype)
        #TODO don't set this manually
        timeAxisNum=0
        timeAxis = True
        if (timeAxis):
            for i in range(np_seeds.shape[timeAxisNum]):
                (labelImage, maxRegionLabel) = vigra.analysis.watershedsNew(\
                        arrayBoundaries[i,:,:],\
                    #neighborhood=4, seeds=nucleus[:,:,i-1], method="Turbo")
                    #neighborhood=8, seeds=nucleus[:,:,i-1], method="RegionGrowing")
                    seeds=arraySeeds[i,:,:], method="RegionGrowing")
                labelImageArray[i] = labelImage

        labelImageArrayTemp = np.ndarray(shape=originalShape, dtype=np_seeds.dtype)
        labelImageArrayTemp[:,:,:,0] = labelImageArray


        self.Output.setValue(labelImageArrayTemp)

        '''
        #self.Output.data = labelImage
        import h5py
        with h5py.File("testOutput", "w") as hf:
            hf.create_dataset("exported_data", data=labelImageArray)
        #print self.Seeds
        #print self.Output
        #of the last image
        #print maxRegionLabel
        #print arrayBoundaries.dtype
        #print arraySeeds.dtype
        #print arrayBoundaries.shape
        #print arraySeeds.shape
        '''


    def __init__(self, *args, **kwargs):
        super( OpWatershedSegmentationCalculation, self ).__init__( *args, **kwargs )


    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Boundaries.meta)
        self.Output.meta.dtype = np.uint8
        self.Output.meta.shape = self.Boundaries.meta.shape[:-1] + (1,)
        self.Output.meta.drange = (0,255)

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def execute(self, slot, subindex, roi, result):
        #assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass    


class OpWatershedSegmentationLabelPipeline( Operator ):
    """
    operator class, that handles the Label Pipeline and the connections to it
    """
    RawData     = InputSlot()
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






