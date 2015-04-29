###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
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

# Built-in
import gc
import logging

# Third-party
import numpy
import vigra
import psutil

# Lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import enlargeRoiForHalo, TinyVector

# ilastik
from lazyflow.utility.timer import Timer

logger = logging.getLogger(__name__)


def getMemoryUsageMb():
    """
    Get the current memory usage for the whole system (not just python).
    """
    # Collect garbage first
    gc.collect()
    vmem = psutil.virtual_memory()
    mem_usage_mb = (vmem.total - vmem.available) / 1e6
    return mem_usage_mb


class OpAnisotropicGaussianSmoothing5d(Operator):
    # raw volume, in 5d 'txyzc' order
    Input = InputSlot()
    Sigmas = InputSlot(value={'x': 1.0, 'y': 1.0, 'z': 1.0})

    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = numpy.float32 # vigra gaussian only supports float32
        self._sigmas = self.Sigmas.value
        assert isinstance(self.Sigmas.value, dict), "Sigmas slot expects a dict"
        assert set(self._sigmas.keys()) == set('xyz'), "Sigmas slot expects three key-value pairs for x,y,z"

    def execute(self, slot, subindex, roi, result):
        assert all(roi.stop <= self.Input.meta.shape),\
            "Requested roi {} is too large for this input image of shape {}.".format(roi, self.Input.meta.shape)

        # Determine how much input data we'll need, and where the result will be
        # relative to that input roi
        # inputRoi is a 5d roi, computeRoi depends on the number of singletons
        # in shape, but is at most 3d
        inputRoi, computeRoi = self._getInputComputeRois(roi)

        # Obtain the input data
        with Timer() as resultTimer:
            data = self.Input(*inputRoi).wait()
        logger.debug("Obtaining input data took {} seconds for roi {}".format(
            resultTimer.seconds(), inputRoi))
        data = vigra.taggedView(data, axistags='txyzc')

        # input is in txyzc order
        tIndex = 0
        cIndex = 4

        # Must be float32
        if data.dtype != numpy.float32:
            data = data.astype(numpy.float32)

        # we need to remove a singleton z axis, otherwise we get 
        # 'kernel longer than line' errors
        ts = self.Input.meta.getTaggedShape()
        tags = [k for k in 'xyz' if ts[k] > 1]
        sigma = [self._sigmas[k] for k in tags]

        # Check if we need to smooth
        if any([x < 0.1 for x in sigma]):
            # just pipe the input through
            result[...] = data
            return

        for i, t in enumerate(xrange(roi.start[tIndex], roi.stop[tIndex])):
            for j, c in enumerate(xrange(roi.start[cIndex], roi.stop[cIndex])):
                # prepare the result as an argument
                resview = vigra.taggedView(result[i, ..., j],
                                           axistags='xyz')
                dataview = data[i, ..., j]
                # TODO make this general, not just for z axis
                resview = resview.withAxes(*tags)
                dataview = dataview.withAxes(*tags)

                # Smooth the input data
                vigra.filters.gaussianSmoothing(
                    dataview, sigma, window_size=2.0,
                    roi=computeRoi, out=resview)

    def _getInputComputeRois(self, roi):
        shape = self.Input.meta.shape
        start = numpy.asarray(roi.start)
        stop = numpy.asarray(roi.stop)
        n = len(stop)
        spatStart = [roi.start[i] for i in range(n) if shape[i] > 1]
        spatStop = [roi.stop[i] for i in range(n) if shape[i] > 1]
        sigma = [0] + map(self._sigmas.get, 'xyz') + [0]
        spatialRoi = (spatStart, spatStop)

        inputSpatialRoi = enlargeRoiForHalo(roi.start, roi.stop, shape,
                                      sigma, window=2.0)

        # Determine the roi within the input data we're going to request
        inputRoiOffset = roi.start - inputSpatialRoi[0]
        computeRoi = [inputRoiOffset, inputRoiOffset + stop - start]
        for i in (0, 1):
            computeRoi[i] = [computeRoi[i][j] for j in range(n)
                             if shape[j] > 1 and j not in (0, 4)]

        # make sure that vigra understands our integer types
        computeRoi = (tuple(map(int, computeRoi[0])),
                      tuple(map(int, computeRoi[1])))

        inputRoi = (list(inputSpatialRoi[0]), list(inputSpatialRoi[1]))

        return inputRoi, computeRoi

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Input:
            # Halo calculation is bidirectional, so we can re-use the function
            # that computes the halo during execute()
            inputRoi, _ = self._getInputComputeRois(roi)
            self.Output.setDirty(inputRoi[0], inputRoi[1])
        elif slot == self.Sigmas:
            self.Output.setDirty(slice(None))
        else:
            assert False, "Unknown input slot: {}".format(slot.name)


class OpAnisotropicGaussianSmoothing(Operator):
    Input = InputSlot()
    Sigmas = InputSlot( value={'x':1.0, 'y':1.0, 'z':1.0} )
    
    Output = OutputSlot()

    def setupOutputs(self):
        
        self.Output.meta.assignFrom(self.Input.meta)
        #if there is a time of dim 1, output won't have that
        timeIndex = self.Output.meta.axistags.index('t')
        if timeIndex<len(self.Output.meta.shape):
            newshape = list(self.Output.meta.shape)
            newshape.pop(timeIndex)
            self.Output.meta.shape = tuple(newshape)
            del self.Output.meta.axistags[timeIndex]
        self.Output.meta.dtype = numpy.float32 # vigra gaussian only supports float32
        self._sigmas = self.Sigmas.value
        assert isinstance(self.Sigmas.value, dict), "Sigmas slot expects a dict"
        assert set(self._sigmas.keys()) == set('xyz'), "Sigmas slot expects three key-value pairs for x,y,z"
        print("Assigning output: {} ====> {}".format(self.Input.meta.getTaggedShape(), self.Output.meta.getTaggedShape()))
        #self.Output.setDirty( slice(None) )
    
    def execute(self, slot, subindex, roi, result):
        assert all(roi.stop <= self.Input.meta.shape), "Requested roi {} is too large for this input image of shape {}.".format( roi, self.Input.meta.shape )
        # Determine how much input data we'll need, and where the result will be relative to that input roi
        inputRoi, computeRoi = self._getInputComputeRois(roi)        
        # Obtain the input data 
        with Timer() as resultTimer:
            data = self.Input( *inputRoi ).wait()
        logger.debug("Obtaining input data took {} seconds for roi {}".format( resultTimer.seconds(), inputRoi ))
        
        xIndex = self.Input.meta.axistags.index('x')
        yIndex = self.Input.meta.axistags.index('y')
        zIndex = self.Input.meta.axistags.index('z') if self.Input.meta.axistags.index('z')<len(self.Input.meta.shape) else None
        cIndex = self.Input.meta.axistags.index('c') if self.Input.meta.axistags.index('c')<len(self.Input.meta.shape) else None
        
        # Must be float32
        if data.dtype != numpy.float32:
            data = data.astype(numpy.float32)
        
        axiskeys = self.Input.meta.getAxisKeys()
        spatialkeys = filter( lambda k: k in 'xyz', axiskeys )

        # we need to remove a singleton z axis, otherwise we get 
        # 'kernel longer than line' errors
        reskey = [slice(None, None, None)]*len(self.Input.meta.shape)
        reskey[cIndex]=0
        if zIndex and self.Input.meta.shape[zIndex]==1:
            removedZ = True
            data = data.reshape((data.shape[xIndex], data.shape[yIndex]))
            reskey[zIndex]=0
            spatialkeys = filter( lambda k: k in 'xy', axiskeys )
        else:
            removedZ = False

        sigma = map(self._sigmas.get, spatialkeys)
        #Check if we need to smooth
        if any([x < 0.1 for x in sigma]):
            if removedZ:
                resultXY = vigra.taggedView(result, axistags="".join(axiskeys))
                resultXY = resultXY.withAxes(*'xy')
                resultXY[:] = data
            else:
                result[:] = data
            return result

        # Smooth the input data
        smoothed = vigra.filters.gaussianSmoothing(data, sigma, window_size=2.0, roi=computeRoi, out=result[tuple(reskey)]) # FIXME: Assumes channel is last axis
        expectedShape = tuple(TinyVector(computeRoi[1]) - TinyVector(computeRoi[0]))
        assert tuple(smoothed.shape) == expectedShape, "Smoothed data shape {} didn't match expected shape {}".format( smoothed.shape, roi.stop - roi.start )
        
        return result
    
    def _getInputComputeRois(self, roi):
        axiskeys = self.Input.meta.getAxisKeys()
        spatialkeys = filter( lambda k: k in 'xyz', axiskeys )
        sigma = map( self._sigmas.get, spatialkeys )
        inputSpatialShape = self.Input.meta.getTaggedShape()
        spatialRoi = ( TinyVector(roi.start), TinyVector(roi.stop) )
        tIndex = None
        cIndex = None
        zIndex = None
        if 'c' in inputSpatialShape:
            del inputSpatialShape['c']
            cIndex = axiskeys.index('c')
        if 't' in inputSpatialShape.keys():
            assert inputSpatialShape['t'] == 1
            tIndex = axiskeys.index('t')

        if 'z' in inputSpatialShape.keys() and inputSpatialShape['z']==1:
            #2D image, avoid kernel longer than line exception
            del inputSpatialShape['z']
            zIndex = axiskeys.index('z')
            
        indices = [tIndex, cIndex, zIndex]
        indices = sorted(indices, reverse=True)
        for ind in indices:
            if ind:
                spatialRoi[0].pop(ind)
                spatialRoi[1].pop(ind)
        
        inputSpatialRoi = enlargeRoiForHalo(spatialRoi[0], spatialRoi[1], inputSpatialShape.values(), sigma, window=2.0)
        
        # Determine the roi within the input data we're going to request
        inputRoiOffset = spatialRoi[0] - inputSpatialRoi[0]
        computeRoi = (inputRoiOffset, inputRoiOffset + spatialRoi[1] - spatialRoi[0])
        
        # For some reason, vigra.filters.gaussianSmoothing will raise an exception if this parameter doesn't have the correct integer type.
        # (for example, if we give it as a numpy.ndarray with dtype=int64, we get an error)
        computeRoi = ( tuple(map(int, computeRoi[0])),
                       tuple(map(int, computeRoi[1])) )
        
        inputRoi = (list(inputSpatialRoi[0]), list(inputSpatialRoi[1]))
        for ind in reversed(indices):
            if ind:
                inputRoi[0].insert( ind, 0 )
                inputRoi[1].insert( ind, 1 )

        return inputRoi, computeRoi
        
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Input:
            # Halo calculation is bidirectional, so we can re-use the function that computes the halo during execute()
            inputRoi, _ = self._getInputComputeRois(roi)
            self.Output.setDirty( inputRoi[0], inputRoi[1] )
        elif slot == self.Sigmas:
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown input slot: {}".format( slot.name )


## Combine high and low threshold
# This operator combines the thresholding results. We want the resulting labels to be
# the ones that passed the lower threshold AND that have at least one pixel that passed
# the higher threshold. E.g.:
#
#   Thresholds: High=4, Low=1
#
#     0 2 0        0 2 0
#     2 5 2        2 3 2
#     0 2 0        0 2 0
#
#   Results:
#
#     0 1 0        0 0 0
#     1 1 1        0 0 0
#     0 1 0        0 0 0
#
#
#   Given two label images, produce a copy of BigLabels, EXCEPT first remove all labels 
#   from BigLabels that do not overlap with any labels in SmallLabels.
class OpSelectLabels(Operator):

    ## The smaller clusters
    # i.e. results of high thresholding
    SmallLabels = InputSlot()

    ## The larger clusters
    # i.e. results of low thresholding
    BigLabels = InputSlot()

    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.BigLabels.meta)
        self.Output.meta.dtype = numpy.uint32
        self.Output.meta.drange = (0, 1)

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output

        # This operator is typically used with very big rois, so be extremely memory-conscious:
        # - Don't request the small and big inputs in parallel.
        # - Clean finished requests immediately (don't wait for this function to exit)
        # - Delete intermediate results as soon as possible.

        if logger.isEnabledFor(logging.DEBUG):
            dtypeBytes = self.SmallLabels.meta.getDtypeBytes()
            roiShape = roi.stop - roi.start
            logger.debug("Roi shape is {} = {} MB".format(roiShape, numpy.prod(roiShape) * dtypeBytes / 1e6 ))
            starting_memory_usage_mb = getMemoryUsageMb()
            logger.debug("Starting with memory usage: {} MB".format(starting_memory_usage_mb))

        def logMemoryIncrease(msg):
            """Log a debug message about the RAM usage compared to when this function started execution."""
            if logger.isEnabledFor(logging.DEBUG):
                memory_increase_mb = getMemoryUsageMb() - starting_memory_usage_mb
                logger.debug("{}, memory increase is: {} MB".format(msg, memory_increase_mb))

        smallLabelsReq = self.SmallLabels(roi.start, roi.stop)
        smallLabels = smallLabelsReq.wait()
        smallLabelsReq.clean()
        logMemoryIncrease("After obtaining small labels")

        smallNonZero = numpy.ndarray(shape=smallLabels.shape, dtype=bool)
        smallNonZero[...] = (smallLabels != 0)
        del smallLabels

        logMemoryIncrease("Before obtaining big labels")
        bigLabels = self.BigLabels(roi.start, roi.stop).wait()
        logMemoryIncrease("After obtaining big labels")

        prod = smallNonZero * bigLabels

        del smallNonZero

        # get labels that passed the masking
        #passed = numpy.unique(prod)
        passed = numpy.bincount(prod.flat).nonzero()[0] # Much faster than unique(), which copies and sorts
        
        # 0 is not a valid label
        if passed[0] == 0:
            passed = passed[1:]

        logMemoryIncrease("After taking product")
        del prod

        all_label_values = numpy.zeros((bigLabels.max()+1,),
                                       dtype=numpy.uint32)

        for i, l in enumerate(passed):
            all_label_values[l] = i+1
        all_label_values[0] = 0

        # tricky: map the old labels to the new ones, labels that didnt pass 
        # are mapped to zero
        result[:] = all_label_values[bigLabels]

        logMemoryIncrease("Just before return")
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.SmallLabels or slot == self.BigLabels:
            self.Output.setDirty(slice(None))
        else:
            assert False, "Unknown input slot: {}".format(slot.name)
