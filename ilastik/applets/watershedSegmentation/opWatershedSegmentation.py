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





    def watershedAlgorithm(self, boundaries, seeds):
        """
        :param boundaries: array that contains the boundaries
        :param seeds: array that contains the seeds
        :return: labelImage: the array, that contains the results of the watershed algorithm;
            maxRegionLabel: the number of the watershed areas

        execute the watershed algorithm of vigra on the boundary and seed array
        """

        #TODO include the algorithm parameters of slots

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
        (labelImage, maxRegionLabel) = vigra.analysis.watershedsNew(\
                boundaries,\
                seeds=seeds,\
                method="RegionGrowing")
        return (labelImage, maxRegionLabel)

    def removeChannelAxis(self, boundaries, seeds):
        """
        :param boundaries: array 1
        :param seeds: array 2

        Remove the last dimension of array 1 and array 2
        the last dimension should be the channel, but this is tested in evaluateSlicing
        :return: (boundaries, seeds) with removed last axis
        """
        #cut off the channel dimension
        boundaries     = boundaries.reshape(boundaries.shape[0:-1])
        seeds          = seeds.reshape(seeds.shape[0:-1])
        return (boundaries, seeds)

    def addChannelAxis(self, array):
        """
        :param array: array for operation
        add a new dimension as last dimension to the array
        this intends to restore the channel dimension
        :return: the new array with an addtional axis at the end
        """
        # add axis for the channel 
        arrayOut = array[...,np.newaxis]
        return arrayOut


    def evaluateSlicing(self, slot):
        """
        :param slot: use the data of the given slot
        check whether the channel is the last axis
        check whether the time axis is used or not
        :return: tUsed True if time-axis is used, else: False
            tId: the index of the time Axis
        """
        # get dimesions
        tags = slot.meta.axistags
        xId = tags.index('x')
        yId = tags.index('y')
        zId = tags.index('z')
        tId = tags.index('t')
        cId = tags.index('c')
        #number of dimensions
        dims = len(slot.meta.shape)

        # channel dimension must be the last one
        assert cId == dims - 1

        #controlling for 2D, 2D with time, 3D, 3D with slicing 
        tUsed = True if (tId < dims) else False
        # error if x, y, or c can't aren't used
        if (cId >= dims or xId >= dims or yId >= dims):
            logger.info("no channel, x or y used in data; something is probably wrong")

        return (tUsed, tId)

    def slicedWatershedAlgorithm(self, boundaries, seeds, tAxis):
        """
        uses watershedAlgorithm for the main algorithm execution
        but slices the data, sothat that algorithm can be used easily

        :param boundaries: the array, that contains the boundaries data
        :param seeds: the array, that contains the seeds data
        :param tAxis: the dimension number of the time axis
        :return: labelImageArray: the concatenated watershed result of all slices 
        """
        labelImageArray = np.ndarray(shape=seeds.shape, dtype=seeds.dtype)
        for i in range(seeds.shape[tAxis]):
            # iterate over the axis of the time
            boundariesSlice  = boundaries.take( i, axis=tAxis)
            seedsSlice       = seeds.take(      i, axis=tAxis)
            (labelImage, maxRegionLabel) =\
                    self.watershedAlgorithm(boundariesSlice, seedsSlice)

            # write in the correct column of the output array, 
            # because the dimensions must fit
            if (tAxis == 0):
                labelImageArray[i] = labelImage
            elif (tAxis == 1):
                labelImageArray[:,i] = labelImage
            elif (tAxis == 2):
                labelImageArray[:,:,i] = labelImage
            elif (tAxis == 3):
                labelImageArray[:,:,:,i] = labelImage
        return labelImageArray

    def execWatershedAlgorithm(self):
        """
        handles the execution of the watershed algorithm 
        """
        ############################################################
        # BEGIN TODO
        ############################################################
        # maybe checkout into function

        #get the data from boundaries and seeds
        arrayBoundaries    = self.Boundaries[:].wait()
        arraySeeds         = self.Seeds[:].wait()

        #both shapes must be the same, and the axistags (means where x, y,z,t,c are)
        assert arraySeeds.shape == arrayBoundaries.shape
        assert self.Seeds.meta.axistags == self.Boundaries.meta.axistags


        # TODO dataconversion depending on the input-paramter slot for which method to choose
        ######## data conversion #####
        #boundaries
        #input image: uint8 or float32
        arrayBoundaries     = arrayBoundaries.astype(np.float32)

        #for the seeds
        #turbo: uint8, the rest: uint32
        #TODO for turbo choose uint8
        arraySeeds          = arraySeeds.astype(np.uint32)

        #TODO integrate process bar


        ############################################################
        # END TODO
        ############################################################


        ############################################################
        #
        ############################################################

        # check the axes and return, whether the time is used and the number of its axis
        (tUsed, tAxis) = self.evaluateSlicing(self.Seeds)

        # needed for vigra to remove the channel axis
        (arrayBoundaries, arraySeeds) = self.removeChannelAxis(arrayBoundaries, arraySeeds)



        # doesn't matter whether image is 2D or 3D, at least we do slicing over time
        # because 2D or 3D does vigra for us
        if tUsed:
            labelImageArray = self.slicedWatershedAlgorithm(arrayBoundaries, arraySeeds, tAxis)

            # no slicing
        else:
            (labelImageArray, maxRegionLabel) =\
                self.watershedAlgorithm(arrayBoundaries, arraySeeds)


        # needed for ilastik to have a channel axis
        labelImageArray = self.addChannelAxis(labelImageArray)


        # set the value of the OutputSlot to the calculated array
        self.Output.setValue(labelImageArray)

        ''' 
        #for debugging
        tUsed = True if (tId < dims) else False
        zUsed = True if (zId < dims) else False

        if (cId >= dims or xId >= dims or yId >= dims):
            logger.info("no channel, x or y used in data; something is probably wrong")

        if (not tUsed and not zUsed):
            print "only x and y available"
            print "2D with one slice"

        if (not tUsed and zUsed):
            print "time not used, but z"
            print "use the whole dataset for 3D watershed"

        if (tUsed and not zUsed):
            print "time used, but not z"
            print "use the whole data sliced into 2D images for 2D watershed"

        if (tUsed and zUsed):
            print "time and z used"
            print "use 3D watershed with slices, means 3D watershed of each 3d image of the data-set"
        '''
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






