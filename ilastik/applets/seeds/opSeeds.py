import numpy as np
import numpy 
import vigra

#from ilastik.applets.Seeds.seedsGui import SmoothingMethods, ComputeMethods
from seedsGui import SmoothingMethods, ComputeMethods

from lazyflow.graph import Operator,Slot, InputSlot, OutputSlot
#for caching the data of the generating seeds
from ilastik.applets.thresholdTwoLevels.opThresholdTwoLevels import _OpCacheWrapper

from ilastik.utility.VigraIlastikConversionFunctions import removeChannelAxis, addChannelAxis, getArray, evaluateSlicing, removeTimeAxis, addTimeAxis

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


    # Tests
    TestMe              = OutputSlot()

    #Layer for displaying, not cached TODO maybe do caching
    Smoothing           = InputSlot(optional=True)
    Compute             = InputSlot(optional=True)
    
    # transmit the WSMethod to the WatershedSegmentationApplet (see Workflow)
    #WSMethodIn          = InputSlot()
    WSMethod            = OutputSlot()

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


    def __init__(self, *args, **kwargs):
        super( OpSeeds, self ).__init__(*args, **kwargs)


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
        # set the Watershed Method
        if self.Unseeded.value:
            wsMethod = "UnionFind"
        else:
            if (self.Boundaries.meta.dtype == numpy.uint8):
                wsMethod = "Turbo"
            else:
                wsMethod = "RegionGrowing" 
        self.WSMethod.setValue( wsMethod )


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

        print "zeros"

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
        pass

        # TestMe dimensions
        self.TestMe.meta.assignFrom(self.Boundaries.meta)
    
    def execute(self, slot, subindex, roi, result):

        if slot == self.TestMe:
            #print "generate Seeds start"
            #print roi
            #print self.Boundaries.meta

            # get boundaries
            boundaries              = self.Boundaries(roi.start, roi.stop).wait()
            sigma                   = self.SmoothingSigma.value
            smoothingMethodIndex    = self.SmoothingMethod.value
            computeMethodIndex      = self.ComputeMethod.value

            print boundaries.shape
            # TODO cut off the time and channel dimension
            boundaries              = removeChannelAxis(boundaries)

            #TODO
            tUsed = True
            if tUsed:
                boundaries          = removeTimeAxis(boundaries)

            # Smoothing
            smoothedBoundaries= self.getAndUseSmoothingMethod(boundaries, smoothingMethodIndex, sigma)
            
            # for distance transform: seeds.dtype === uint32 or float? but not uint8
            smoothedBoundaries  = smoothedBoundaries.astype(numpy.float32)

            # Compute 
            seeds               = self.getAndUseComputeMethod(smoothedBoundaries, computeMethodIndex, sigma)

            # label the seeds 
            seeds  = seeds.astype(numpy.uint8)
            labeled_seeds = vigra.analysis.labelMultiArrayWithBackground(seeds)

            #out = smoothedBoundaries
            out = seeds

            #TODO
            out = addChannelAxis(out)
            #TODO
            if tUsed:
                out = addTimeAxis(out)

            # write the result into the result array. with result[...] you can write directly 
            # into the region of interest (roi) of the given slot-values
            result[...] = out
        else:
            pass

        
    def propagateDirty(self, slot, subindex, roi):
        # if something changes, the watershed Method must be evaluated newly
        # and all other things too
        for slot in self.outputs.values():
            slot.setDirty()


    def setInSlot(self, slot, subindex, roi, value):
        pass



    ############################################################
    # smoothing and compute functions, e.g. distance transformation
    ############################################################

    def getAndUseComputeMethod(self, smoothedBoundaries, computeMethodIndex, sigma):
        """
        Looks for the compute method and computes binary seeds from the smoothed Boundaries

        :param smoothedBoundaries: input-array that shall be used for Seeds (without labeling)
        :param computeMethodIndex: Index of compute Method 
            (see class ComputeMethods for their definite method)
        :type computeMethodIndex: int
        :param sigma: gaussian smoothing sigma after option: distance transform
        :type sigma: float
        :returns: binary seeds
        :rtype: array
        """
        methodList = ComputeMethods()
        index = computeMethodIndex #op.ComputeMethod.value 
        method = methodList.methods[index] 

        if ( method == "DistanceTransform"):
            #TODO threshold for dt
            threshold = 0.91

            # compute distance transform
            distance_to_membrane = self.signed_distance_transform(smoothedBoundaries, threshold)

            # smooth with gaussian after dt to receive less maxima
            smoothed_distance_to_membrane = \
                    vigra.filters.gaussianSmoothing(distance_to_membrane, sigma)

            # get the Maximum
            seeds           = self.MinOrMax(smoothed_distance_to_membrane, "Maximum")

        elif ( method == "HeightMap Min"):
            # Minima
            seeds           = self.MinOrMax(smoothedBoundaries, "Minimum")
            seeds           = seeds.astype(numpy.float32)

        elif ( method == "HeightMap Max"):
            # Maxima
            seeds           = self.MinOrMax(smoothedBoundaries, "Maximum")
            seeds           = seeds.astype(numpy.float32)
        else: 
            raise NotImplementedError

        return seeds



    def getAndUseSmoothingMethod(self, boundaries, smoothingMethodIndex, sigma):
        """
        Smoothes the given boundaries with the method of interest

        :param boundaries: input-array that shall be smoothed
        :param smoothingMethodIndex: Index of smoothing Method 
            (see class SmoothingMethods for their definite method)
        :type smoothingMethodIndex: int
        :param sigma: smoothing parameter sigma
        :type sigma: float
        :returns: smoothed boundaries
        :rtype: array
        """
        # method
        methodList = SmoothingMethods()
        index = smoothingMethodIndex #op.SmoothingMethod.value 
        method = methodList.methods[index] 

        if ( method == "Gaussian"):
            function = vigra.filters.gaussianSmoothing

        elif ( method == "MedianFilter"):
            #TODO
            raise NotImplementedError
        else: 
            raise NotImplementedError

        # smooth
        smoothedBoundaries           = function(boundaries, sigma)

        return smoothedBoundaries



    #copied from wsDT, but with a some changes 
    def signed_distance_transform(self, pmap, pmax):
        """
        Performs a threshold on the given image 'pmap' < pmax, and performs
        a distance transform to the threshold region border for all pixels outside the
        threshold boundaries (positive distances) and also all pixels *inside*
        the boundary (negative distances).

        The result is a signed float32 image.
        """
        # get the thresholded pmap
        # black parts = 255 are not interesting
        binary_membranes = (pmap <= pmax).view(numpy.uint8)


        #TODO why labeling before?
        # delete small CCs
        labeled = vigra.analysis.labelMultiArrayWithBackground(binary_membranes)
        del binary_membranes

        # perform signed dt on mask
        distance_to_membrane = vigra.filters.distanceTransform(labeled)

        # Save RAM with a sneaky trick:
        # Use distanceTransform in-place, despite the fact that the input and output don't have the same types!
        # (We can just cast labeled as a float32, since uint32 and float32 are the same size.)
        distance_to_nonmembrane = labeled.view(numpy.float32)
        vigra.filters.distanceTransform(labeled, background=False, out=distance_to_nonmembrane)
        del labeled # Delete this name, not the array

        # Combine the inner/outer distance transforms
        distance_to_nonmembrane[distance_to_nonmembrane>0] -= 1
        distance_to_membrane[:] -= distance_to_nonmembrane

        return distance_to_membrane



    ############################################################
    # Min or Max
    ############################################################

    def MinOrMax(self, array, functionName="Minimum"):
        """
        Compute the extended Local Minima/Maxima 

        :param array: of which the min or max shall be taken
        :param functionName: Minimum or Maximum
        :type functionName: str
        :returns: min/max array
        :rtype: array
        """
        if functionName == "Minimum":
            if (array.ndim == 2):
                function = vigra.analysis.extendedLocalMinima
            else:
                function = vigra.analysis.extendedLocalMinima3D
        else:
            if (array.ndim == 2):
                function = vigra.analysis.extendedLocalMaxima
            else:
                function = vigra.analysis.extendedLocalMaxima3D

        # the value, the binary Min or Max will have afterwards
        marker = 1
        return function(array, marker=marker)



