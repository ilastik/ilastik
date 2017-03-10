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

import numpy as np
import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot

from ilastik.utility.VigraIlastikConversionFunctions import removeLastAxis, addLastAxis, getArray, evaluateSlicing, removeFirstAxis, addFirstAxis

import logging
logger = logging.getLogger(__name__)



class OpWatershedSegmentationCalculation( Operator ):
    """
    operator class, that handles the input and output of calculation
    and the calculation itself
    """
    #input slot
    Boundaries  = InputSlot()
    Seeds       = InputSlot()


    # controlling slot
    SeedsExist  = InputSlot(optional=True, value=False)

    #optional parameter input slots
    Neighbors   = InputSlot(optional=True)
    Method      = InputSlot(optional=True)
    MaxCost     = InputSlot(optional=True)
    Terminate   = InputSlot(optional=True)
    # if not connected, use the default-values. 
    # for more information, see function: prepareInputParameter 

    #output slot
    Output      = OutputSlot()


    def __init__(self, *args, **kwargs):
        super( OpWatershedSegmentationCalculation, self ).__init__( *args, **kwargs )


    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Boundaries.meta)
        # output of the vigra.analysis.watershedNew is uint32, therefore it should be uint 32 as
        # well, otherwise it will break with the cached image 
        # UPDATE: actually, this behaviour changed during development, so that uint8 is correct 
        self.Output.meta.dtype = np.uint8
        #only one channel as output
        self.Output.meta.shape = self.Boundaries.meta.shape[:-1] + (1,)
        self.Output.meta.drange = (0,255)

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def execute(self, slot, subindex, roi, result):
        # execute watershed, if WSMethod and SeedsExist fit together
        if self.check_SeedsExist_plus_WSMethod_fit_together():
            self.execWatershedAlgorithm(slot, subindex, roi, result)
        else:
            logger.info("if watersheds unseeded, then seeds need to be supplied")

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty()


    def check_SeedsExist_plus_WSMethod_fit_together(self):
        """
        :returns: True if seeds exist or method is UnionFind
        :rtype: bool
        """
        if self.SeedsExist.value:
            return True
        if self.Method.ready():
            method      = self.Method       [:].wait()[0]
            if method == "UnionFind":
                return True

        return False


    def execWatershedAlgorithm(self, slot, subindex, roi, result):
        """
        handles the execution of the watershed algorithm 
        """
        
        seeds                   = self.Seeds(roi.start, roi.stop).wait()
        boundaries              = self.Boundaries(roi.start, roi.stop).wait()

        # necessary for vigra.analysis.watershedsNew
        boundaries, seeds       = self.arrayConversion(boundaries, seeds)

        # look for the axes used
        shape = self.Boundaries.meta.shape
        zUsed = not(shape[3] == 1)

        # remove time axis (it's always 1 in the roi)
        boundaries              = removeFirstAxis(boundaries)
        seeds                   = removeFirstAxis(seeds)

        # channel dimension
        boundaries              = removeLastAxis(boundaries)
        seeds                   = removeLastAxis(seeds)


        if not zUsed:
            #remove z axis
            boundaries         = removeLastAxis(boundaries)
            seeds              = removeLastAxis(seeds)


        
        (labelImageArray, maxRegionLabel) =\
                self.watershedAlgorithm(boundaries, seeds)

        # needed for ilastik to have a channel axis
        labelImageArray     = addLastAxis(labelImageArray)
        # add time axis
        labelImageArray     = addFirstAxis(labelImageArray)


        if not zUsed:
            # add z axis
            labelImageArray     = addLastAxis(labelImageArray)

        # set the value of the OutputSlot to the calculated array
        result[...] = labelImageArray
    

    ############################################################
    # the function, where the algorithm is executed itself
    ############################################################

    def watershedAlgorithm(self, boundaries, seeds=None):
        """
        :param boundaries: array that contains the boundaries
        :param seeds: array that contains the seeds
        :return: labelImage: (dtype = uint32) the array, that contains the results of the watershed algorithm;
            maxRegionLabel: the number of the watershed areas

        execute the watershed algorithm of vigra on the boundary and seed array
        therefore extract the parameters from InputSlots for the usage in this algorithm

        compare vigra.analysis.watershedsNew for more information on the meaning of the parameters
        """

        # detect the correct dimension for the watershed algorithm
        # if sliced, then the input is only a part of the series, 
        # and therefore the dimension is still correct
        method, neighbors, terminate, maxCost = self.prepareInputParameter(boundaries.ndim)

        #UnionFind doesn't support seeds and max_cost
        if (method == "UnionFind"):
            seeds = None
            maxCost = 0

        #print "neighbors: '" + str(neighbors) + "'\nmethod: '" + str(method) + "'\nterminate: '" + str(terminate) + "'\nmaxCost: '" + str(maxCost) + "'\n"
        # watershedAlgoirthm itself
        (labelImage, maxRegionLabel) = vigra.analysis.watershedsNew(\
                image           = boundaries,
                seeds           = seeds,
                neighborhood    = neighbors,
                method          = method,
                terminate       = terminate,
                max_cost        = maxCost)



        return (labelImage, maxRegionLabel)



    ############################################################
    # helping functions
    ############################################################


    def arrayConversion(self, boundaries, seeds=None):
        """
        :param boundaries: array 1
        :param seeds: array2
        :return: boundaries, seeds
        convert the array in a numpy array that is necessary for vigra.analysis.watershedsNew
        """
        #boundaries
        # input image: uint8 or float32, (float32 includes more information)
        # because Turbo works with unint8 more effective
        if not (boundaries.dtype == np.uint8):
            boundaries     = boundaries.astype(np.float32)

        #for the seeds
        # uint32

        if not (seeds is None):
            seeds          = seeds.astype(np.uint32)
        return boundaries, seeds






    def prepareInputParameter(self, dimension):
        """
        :param dimension: the dimension to set the correct number of neighbors

        get the value of the inputSlots
        declare valid variables and their valid inputs
        check the input for correctness in comparison with the valid variables
        declare default values (if input not correct or unsufficient

        includes a list of correct/valid parameters
        """

        # get the value of the inputSlots
        ############################################################
        # check whether slot is ready (connected)
        # if yes, take its value
        # else use default value (None), conversion to default value later
        neighbors   = None
        method      = None
        terminate   = None
        maxCost     = None

        if self.Neighbors.ready():
            neighbors   = self.Neighbors    [:].wait()[0]
        
        if self.Method.ready():
            method      = self.Method       [:].wait()[0]

        if self.Terminate.ready():
            terminate   = self.Terminate    [:].wait()[0]

        if self.MaxCost.ready():
            maxCost     = self.MaxCost      [:].wait()[0]

        
        # declare valid variables and their valid inputs
        ############################################################

        # None is always allowed and will be transformed to default value later
        method0         = None
        method1         = "RegionGrowing"
        method2         = "Turbo"
        method3         = "UnionFind"
        methodArray     = [method0, method1, method2, method3]
        methodName      = "Method"

        neighbors0      = None
        neighbors1      = "direct"
        neighbors2      = "indirect"
        neighborsArray  = [neighbors0, neighbors1, neighbors2]
        neighborsName   = "Neighbors"

        terminate0      = None
        terminate1      = vigra.analysis.SRGType.CompleteGrow
        terminate2      = vigra.analysis.SRGType.KeepContours
        terminate3      = vigra.analysis.SRGType.StopAtThreshold
        terminateArray  = [terminate0, terminate1, terminate2, terminate3]
        terminateName   = "Terminate"

        #maxCost must be a number: int, long or float

        data =\
            [[method, methodArray, methodName],
            [neighbors, neighborsArray, neighborsName],
            [terminate, terminateArray, terminateName]]
        

        # check the input for correctness
        ############################################################

        #check method, neighbors, terminate for correctness
        for (parameter, array, name) in  data:
            if not (parameter in array):
                logger.info("Input " + name +" is wrong; use default configuration")
                if name == neighborsName:
                    neighbors = None
                elif name == terminateName:
                    terminate = None
                elif name == methodName:
                    method = None
                # this does not work
                #parameter = None


        #maxCost must be a number (int, long, float)
        if (not isinstance(maxCost, (int, long, float))):
            logger.info("Input maxCost is wrong; use default configuration")
            maxCost = None


        # test combinations, that they fit together
        if ((terminate == terminate2 or terminate == terminate3) and not (method == method1)):
            logger.info("the chosen terminate criteria is incompatible with the given method,\
                    reset method and terminate to default")
            terminate   = None
            method      = None

        if ((terminate == terminate3) and maxCost is None):
            logger.info("MaxCost parameter must be set for the StopAtThreshold termination option")
            logger.info("use default termination")
            terminate   = None


        # declare default values
        ############################################################
        # method
        if method == None:
            method = method1

        # neighbors, depending on dimension
        if neighbors == None or neighbors == neighbors1:
            if dimension == 2:
                neighbors = 4
            else:
                neighbors = 6
        else:
            if dimension == 2:
                neighbors = 8
            else:
                neighbors = 26

        # terminate
        if terminate == None:
            terminate = terminate1

        # maxCost
        if maxCost == None:
            maxCost = 0


        return method, neighbors, terminate, maxCost



