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
import numpy as np
import vigra
import psutil
from itertools import izip

# Lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import enlargeRoiForHalo, TinyVector

# ilastik
from lazyflow.utility import Timer, vigra_bincount

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
    # raw volume, in 5d 'tzyxc' order
    Input = InputSlot()
    Sigmas = InputSlot(value={'z': 1.0, 'y': 1.0, 'x': 1.0})

    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = numpy.float32 # vigra gaussian only supports float32
        self._sigmas = self.Sigmas.value
        assert isinstance(self.Sigmas.value, dict), "Sigmas slot expects a dict"
        assert set(self._sigmas.keys()) == set('zyx'), "Sigmas slot expects three key-value pairs for z,y,x"

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
        data = vigra.taggedView(data, axistags='tzyxc')

        # input is in tzyxc order
        tIndex = 0
        cIndex = 4

        # Must be float32
        if data.dtype != numpy.float32:
            data = data.astype(numpy.float32)

        # we need to remove a singleton z axis, otherwise we get 
        # 'kernel longer than line' errors
        ts = self.Input.meta.getTaggedShape()
        tags = [k for k in 'zyx' if ts[k] > 1]
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
                                           axistags='zyx')
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
        sigma = [0] + map(self._sigmas.get, 'zyx') + [0]
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
    Sigmas = InputSlot( value={'z':1.0, 'y':1.0, 'x':1.0} )
    
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
        assert set(self._sigmas.keys()) == set('zyx'), "Sigmas slot expects three key-value pairs for z,y,x"
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
        
        zIndex = self.Input.meta.axistags.index('z') if self.Input.meta.axistags.index('z')<len(self.Input.meta.shape) else None
        xIndex = self.Input.meta.axistags.index('x')
        yIndex = self.Input.meta.axistags.index('y')
        cIndex = self.Input.meta.axistags.index('c') if self.Input.meta.axistags.index('c')<len(self.Input.meta.shape) else None
        
        # Must be float32
        if data.dtype != numpy.float32:
            data = data.astype(numpy.float32)
        
        axiskeys = self.Input.meta.getAxisKeys()
        spatialkeys = filter( lambda k: k in 'zyx', axiskeys )

        # we need to remove a singleton z axis, otherwise we get 
        # 'kernel longer than line' errors
        reskey = [slice(None, None, None)]*len(self.Input.meta.shape)
        reskey[cIndex]=0
        if zIndex and self.Input.meta.shape[zIndex]==1:
            removedZ = True
            data = data.reshape((data.shape[xIndex], data.shape[yIndex]))
            reskey[zIndex]=0
            spatialkeys = filter( lambda k: k in 'yx', axiskeys )
        else:
            removedZ = False

        sigma = map(self._sigmas.get, spatialkeys)
        #Check if we need to smooth
        if any([x < 0.1 for x in sigma]):
            if removedZ:
                resultYX = vigra.taggedView(result, axistags="".join(axiskeys))
                resultYX = resultYX.withAxes(*'yx')
                resultYX[:] = data
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
        spatialkeys = filter( lambda k: k in 'zyx', axiskeys )
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
        assert self.BigLabels.meta.getTaggedShape()['c'] == 1

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output
        small_labels = self.SmallLabels(roi.start, roi.stop).wait()
        small_labels = vigra.taggedView(small_labels, self.SmallLabels.meta.axistags)

        big_labels = result
        self.BigLabels(roi.start, roi.stop).writeInto(big_labels).wait()
        big_labels = vigra.taggedView(big_labels, self.BigLabels.meta.axistags)

        # Writes into big_labels a.k.a. result
        select_labels(small_labels, big_labels)

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.SmallLabels or slot == self.BigLabels:
            self.Output.setDirty(slice(None))
        else:
            assert False, "Unknown input slot: {}".format(slot.name)

def select_labels( small_labels, big_labels ):
    """
    Given label images small_labels and big_labels, remove (overwrite with zero) objects
    from big_labels which don't overlap with any non-zero pixels in small_labels.

    ** Works IN-PLACE (to save RAM) **
    
    Both inputs are modified: small_labels for temporary storage, big_labels for the result
    """
    assert hasattr(small_labels, 'axistags')
    assert hasattr(big_labels, 'axistags')
    assert small_labels.shape == big_labels.shape

    small_labels = small_labels.withAxes('tzyx')
    big_labels = big_labels.withAxes('tzyx')

    for small_labels_3d, big_labels_3d in izip(small_labels, big_labels):
        # For each non-zero small label pixel, replace it with the corresponding big label pixel
        np.copyto(small_labels_3d, big_labels_3d, where=(small_labels_3d != 0))
    
        # Construct mapping to relabel big_labels
        # By default, big labels map to 0
        orig_big_values = vigra.analysis.unique( big_labels_3d )    
        mapping = { v:0 for v in orig_big_values }
        
        # But big labels that pass the filter map to themselves.
        filtered_big_values = vigra.analysis.unique( small_labels_3d )
        mapping.update( { v:v for v in filtered_big_values } )
    
        vigra.analysis.applyMapping(big_labels_3d, mapping, out=big_labels_3d)


if __name__ == "__main__":
    small_labels = np.zeros((100,100), dtype=np.uint32)
    small_labels[10:20, 10:20] = 1
    small_labels[40:50, 10:20] = 2 # Won't be used.

    big_labels = np.zeros((100,100), dtype=np.uint32)
    big_labels[10:30, 10:30] = 2 # Should be preserved
    big_labels[10:30, 40:50] = 3 # Should get dropped

    small_labels_orig = small_labels.copy()
    big_labels_orig = big_labels.copy()

    select_labels(small_labels, big_labels)

    expected_result = big_labels_orig.copy()
    expected_result[10:30, 40:50] = 0
    assert (big_labels == expected_result).all()
    print 'DONE'
