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
    #TODO don't need them, also delete them in the serializer and the applet
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
        #Input
        self.opWSC.Boundaries.connect(  self.Boundaries )
        self.opWSC.Seeds.connect(       self.CorrectedSeedsOut )
        #TODO add additional input-connections that can be commented out, 
        #including all necessary parameters
        #Output
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

    def setInSlot(self, slot, subindex, roi, value):
        pass

class OpWatershedSegmentationCalculation( Operator ):
    """
    operator class, that handles the input and output of calculation
    and the calculation itself
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

        arrayBoundaries     = resultBoundaries
        arraySeeds          = resultSeeds

        #both shapes must be the same, and the axistags (means where x, y,z,t,c are)
        assert arraySeeds.shape == arrayBoundaries.shape
        assert self.Seeds.meta.axistags == self.Boundaries.meta.axistags
        originalShape       = arraySeeds.shape


        ######## data conversion #####
        #boundaries
        #input image: uint8 or float32
        arrayBoundaries     = arrayBoundaries.astype(np.float32)

        #for the seeds
        #turbo: uint8, the rest: uint32
        #arrayBoundaries     = arrayBoundaries.astype(np.uint8)
        #TODO for turbo choose uint8
        arraySeeds          = arraySeeds.astype(np.uint32)

        ############################################################
        # get info about 2D, 3D, with slicing or not
        ############################################################

        ######## size fixing #####
        tags = self.Seeds.meta.axistags
        xId = tags.index('x')
        yId = tags.index('y')
        zId = tags.index('z')
        tId = tags.index('t')
        cId = tags.index('c')
        #number of dimensions
        dims = len(self.Seeds.meta.shape)

        ############################################################
        # BEGIN TODO
        ############################################################

        #controlling for 2D, 2D with time, 3D, 3D with slicing 
        if (cId >= dims or xId >= dims or yId >= dims):
            logger.info("no channel, x or y used in data; something is probably wrong")

        if (tId >= dims and zId >= dims):
            print "only x and y available"
            print "2D with one slice"

        if (tId >= dims and zId < dims):
            print "time not used, but z"
            print "use the whole dataset for 3D watershed"

        if (tId < dims and zId >= dims):
            print "time used, but not z"
            print "use the whole data sliced into 2D images for 2D watershed"

        if (tId < dims and zId < dims):
            print "time and z used"
            print "use 3D watershed with slices, means 3D watershed of each 3d image of the data-set"




        for i in range(dims):
            pass






        #cut off the channel dimension
        arrayBoundaries     = arrayBoundaries.reshape(arrayBoundaries.shape[0:-1])
        arraySeeds          = arraySeeds.reshape(arraySeeds.shape[0:-1])




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

        '''
        #watershed algorithm
        (labelImage, maxRegionLabel) = vigra.analysis.watershedsNew(_membrane,\
                    #neighborhood=6, seeds=_seeds, method="Turbo")
                    #neighborhood=26, seeds=_seeds, method="Turbo", 
                    #neighborhood=8, seeds=nucleus[:,:,i-1], method="RegionGrowing")
                    neighborhood=4, seeds=_seeds, method="RegionGrowing")
                    #neighborhood=26, seeds=_seeds, method="RegionGrowing",\
                    #terminate=vigra.analysis.SRGType.CompleteGrow)
                    #terminate=vigra.analysis.SRGType.CompleteGrow,\
                    #max_cost=12) #enables to see all the membrans at ones
                    #together with Keep Contours: enables to see all the membrans
                    #max_cost=100,\
                    #max_cost=12)
                    #terminate=vigra.analysis.SRGType.KeepContours) #leaves 1 pixel black surrounding each found contour
                    #neighborhood=6, method="UnionFind")
                    #neighborhood=26, method="UnionFind")
                    #neighborhood=8: so all surrounding 8 pixel are taken into account

            #output for illustration needs to be converted to uint8, to see anything or so
            #vigra.impex.writeImage(labelImage[:,:].astype(np.uint8), "./output_" + str(i) + ".png")

        #seeds muessen 1, 2, 3 sein, also kann man auch 120 180, etc verwenden, 
        #rest aussen rum muss schwarz=0 sein
        #bei den membranen: die membrane selbst muessen 255 sein und der rest 0=schwarz
        #help(vigra.analysis.watershedsNew)
        '''


        labelImageArrayTemp = np.ndarray(shape=originalShape, dtype=np_seeds.dtype)
        labelImageArrayTemp[:,:,:,0] = labelImageArray



        ############################################################
        # END TODO
        ############################################################

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
    the opLabelPipeline handles the connections to the opCompressedUserLabelArray, 
    which is responsable for everything
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
        self.SeedOutput.connect( self.opLabelPipeline.Output )

    def setupOutputs(self):
        pass

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"

    def propagateDirty(self, slot, subindex, roi):
        pass    






