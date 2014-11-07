
from abc import abstractmethod

import numpy as np
import vigra

from lazyflow.operator import Operator, InputSlot, OutputSlot
from lazyflow.rtype import SubRegion
from lazyflow.request import RequestLock
from lazyflow.operators import OpReorderAxes, OpCompressedCache

from opImplementationChoice import OpImplementationChoice


import logging
logger = logging.getLogger(__name__)


# this operator wraps multiple implementations of smoothing algorithms while
# also taking care of caching and reordering
class OpSmoothedArgMax(Operator):
    Input = InputSlot()
    Configuration = InputSlot()
    Method = InputSlot()

    Smoothed = OutputSlot()
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpSmoothedArgMax, self).__init__(*args, **kwargs)

        self._opIn = OpReorderAxes(parent=self)
        self._opIn.Input.connect(self.Input)
        self._opIn.AxisOrder.setValue('txyzc')

        self._op = OpImplementationChoice(OpSmoothingImplementation,
                                          parent=self)
        self._op.implementations = smoothers_available
        self._op.Input.connect(self._opIn.Output)
        self._op.Configuration.connect(self.Configuration)
        self._op.Implementation.connect(self.Method)

        self._opArgMax= OpMriArgmax(parent=self)
        self._opArgMax.Input.connect(self.Smoothed)

        self._opOut = OpReorderAxes(parent=self)
        self._opOut.Input.connect(self._opArgMax.Output)
        self.Output.connect(self._opOut.Output)

        self._cache = None

    def setupOutputs(self):
        self._destroyCache()
        self._createCache()

        self._opOut.AxisOrder.setValue(self.Input.meta.getAxisKeys())

        ts = self.Input.meta.getTaggedShape()

    def execute(self, slot, subindex, roi, result):
        raise NotImplementedError(
            "All executes must be handled by internal operators")

    def propagateDirty(self, slot, subindex, roi):
        # all dirty handling is done by internal operators
        pass

    def _destroyCache(self):
        if self._cache is None:
            return
        self.Smoothed.disconnect()
        self._cache.Input.disconnect()
        self._cache = None

    def _createCache(self):
        self._cache = OpCompressedCache(parent=self)
        ts = self.Input.meta.getTaggedShape()
        # parallelizable axes
        pa = 't'  # only t, because argmax operator needs all channels
        for k in pa:
            if k in ts:
                ts[k] = 1
        # FIXME should probably be two caches, one at Smoothed and
        # one at Output
        self._cache.Input.connect(self._op.Output)
        self._cache.BlockShape.setValue([ts[k] for k in ts])
        self.Smoothed.connect(self._cache.Output)


# this dict stores the available smoothing methods in the format
#   'nickname': ChildOfOpSmoothingImplementation
# add your implementation to the dict (see below for how to do that)
smoothers_available = dict()


# parent class for all smoothing implementations
#
# A smoothing implementation is supposed to smooth the input volume per time
# slice (smoothing over space AND channels). An example implementation can be
# found below (OpCostVolumeFilter).
class OpSmoothingImplementation(Operator):

    # input is guaranteed to be 'txyzc'
    Input = InputSlot()

    # configuration comes as dictionary, use Configuration.value to access it
    Configuration = InputSlot()

    # output must also be 'txyzc', with the same dimensions
    # requests to this slot will always be
    #   * full xyzc volume
    #   * single time slice
    # e.g. Output[2:3, :, :, :, :]
    Output = OutputSlot()

    class ConfigurationError(Exception):
        pass

    def __init__(self, *args, **kwargs):
        super(OpSmoothingImplementation, self).__init__(*args, **kwargs)

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)

    def execute(self, slot, subindex, roi, result):
        raise NotImplementedError("This method must not be called")

    def propagateDirty(self, slot, subindex, roi):
        # We assume that smoothing is global and set the whole spatial volume
        # dirty. If this is not the case for your implementation you can
        # override this method.

        if slot is self.Configuration:
            # config changed, set the whole output dirty
            self.Output.setDirty(slice(None))
        elif slot is self.Input:
            # set dirty per time and channel slice
            shape = np.asarray(self.Input.meta.shape, dtype=np.int)
            start = np.asarray(roi.start, dtype=np.int)
            stop = np.asarray(roi.stop, dtype=np.int)
            start[1:5] = (0,)*4
            stop[1:5] = shape[1:5]

            newroi = SubRegion(self.Output, start=start, stop=stop)
            self.Output.setDirty(newroi)

    @abstractmethod
    def isAvailable(self):
        return True


# Implements gaussian smoothing
class OpCostVolumeFilter(OpSmoothingImplementation):
    name = "Cost Volume Filter"

    # inherited slots
    # Input = InputSlot()
    # Output = OutputSlot()

    # configuration for this slot should be {'sigma': 1.0}
    # Configuration = InputSlot()

    # implementation of abstract method
    def isAvailable(self):
        # we are implementing it right here, so it is indeed available
        return True

    def __init__(self, *args, **kwargs):
        super(OpCostVolumeFilter, self).__init__(*args, **kwargs)

    def setupOutputs(self):
        super(OpCostVolumeFilter, self).setupOutputs()
        self.Output.meta.dtype = np.float32

    @staticmethod
    def _costVolumeFilter(vol, filterSize=2.0, normalize=True):
        """
        Cost Volume Filtering: Smoothes the probabilities with a
        Gaussian of sigma 'size', each label layer separately.
        If normalize is true, the channels will sum up to 1.
        """
        if filterSize > 0:
            for t in xrange(vol.shape[0]):
                for c in xrange(vol.shape[-1]):
                    vol[t, ..., c] = vigra.gaussianSmoothing(
                        vol[t, ..., c], float(filterSize))
        if normalize:
            z = np.sum(vol, axis=-1, keepdims=True)
            vol /= z

    def execute(self, slot, subindex, roi, result):
        # http://ukoethe.github.io/vigra/doc/vigra/classvigra_1_1Gaussian
        # required filter radius for a discrete approximation
        # of the Gaussian
        # TODO the equation might actually not be what the code is doing
        # check and update accordingly

        logger.debug("Gaussian on roi {}".format(roi))

        conf = self.Configuration.value
        if 'sigma' not in conf:
            raise self.ConfigurationError(
                "expected key 'sigma' in configuration")
        sigma = conf['sigma']

        result[...] = self.Input.get(roi).wait().astype(self.Output.meta.dtype)
        self._costVolumeFilter(result, sigma, normalize=True)

# add this smoother to the global smoothers table
smoothers_available['gaussian'] = OpCostVolumeFilter


# Implements guided filter smoothing
class OpGuidedFilter(OpSmoothingImplementation):
    """
    Operator that performs guided filtering on the probability map 
    as proposed by
    He, K., Sun, J., Tang, X.: Guided image filtering. 
    IEEE Trans Pattern Anal Mach Intell 35(6), 1397-409 (Jun 2013)
    """
    name = "Guided Filter"

    # inherited slots
    # Input = InputSlot()
    # Output = OutputSlot()

    # configuration for this slot should be like {'sigma': 2.0, 'eps': 0.2}
    # Configuration = InputSlot()

    # implementation of abstract method
    def isAvailable(self):
        # we are implementing it right here, so it is indeed available
        return True

    def __init__(self, *args, **kwargs):
        super(OpGuidedFilter, self).__init__(*args, **kwargs)

    def setupOutputs(self):
        super(OpGuidedFilter, self).setupOutputs()
        self.Output.meta.dtype = np.float32

    def execute(self, slot, subindex, roi, result):
        logger.debug("Guided on roi {}".format(roi))

        conf = self.Configuration.value
        if 'sigma' not in conf:
            raise self.ConfigurationError(
                "expected key 'sigma' in configuration")
        sigma = conf['sigma']

        if 'eps' not in conf:
            raise self.ConfigurationError(
                "expected key 'eps' in configuration")
        epsilon = conf['eps']

        if 'guided' not in conf:
            raise self.ConfigurationError(
                "expected key 'guided' in configuration")
        guided = conf['guided']

        result[...] = self.Input.get(roi).wait().astype(self.Output.meta.dtype)
        self._guidedFilterWrapper(result, sigma, epsilon, normalize=True,
                                  uncertaintyGuideImage=guided)

    def _guidedFilterWrapper(self, vol, filter_size, epsilon, 
                             normalize=True, uncertaintyGuideImage=True):
        if filter_size > 0:
            if uncertaintyGuideImage:
                pfiltered = np.zeros_like(vol[0])
                for c in xrange(vol.shape[-1]):
                    pfiltered[...,c] = vigra.gaussianSmoothing( vol[0,...,c], 
                                                                float(1.2))
                pmap = np.sort(pfiltered, axis=-1)
                uncertainties  = pmap[...,-1]-pmap[...,-2] 

            for c in xrange(vol.shape[-1]):
                if uncertaintyGuideImage:
                    guide_img = uncertainties
                else:
                    guide_img = vol[0, ..., c]
                vol[0, ..., c] = self._guidedFilter3D(vol[0, ..., c],
                                                      guide_img,
                                                      float(filter_size),
                                                      float(epsilon))
        if normalize:
            z = np.sum(vol, axis=-1, keepdims=True)
            vol /= z

    @staticmethod
    def _guidedFilter3D(img_p, img_I, filter_size, epsilon):
        """
        algorithm as proposed in:
        Kaiming He et al., "Guided Image Filtering", ECCV 2010

        img_p   -   filtering input image
        img_I   -   guidance image (can be the same as img_p)
        filter_size  -   filter size
        epsilon -   regularization parameter

        good parameters for structural (eg t1c) r=1.2, epsilon=0.03

        """
        assert img_p.shape == img_I.shape
        if not img_p.dtype == np.float32:
            img_p = img_p.astype(np.float32)
        if not img_I.dtype == np.float32:
            img_I = img_I.astype(np.float32)

        mean_I = vigra.gaussianSmoothing( img_I, np.float(filter_size))
        corr_I = vigra.gaussianSmoothing( img_I*img_I, 
                                          np.float(filter_size))
        mean_p = vigra.gaussianSmoothing( img_p, np.float(filter_size))
        corr_Ip = vigra.gaussianSmoothing( img_I*img_p, 
                                           np.float(filter_size))

        var_I = corr_I - mean_I*mean_I
        cov_Ip = corr_Ip - mean_I*mean_p

        a = cov_Ip / (var_I + epsilon)
        b = mean_p - a * mean_I

        mean_a = vigra.gaussianSmoothing( a, np.float(filter_size))
        mean_b = vigra.gaussianSmoothing( b, np.float(filter_size))

        q = mean_a * img_I + mean_b
    
        return q

# add this smoother to the global smoothers table
smoothers_available['guided'] = OpGuidedFilter


class OpMriArgmax(Operator):
    """
    Operator that compute argmax across the channels

    TODO Integrate Threshold? (for filtering predition probabilities prior
    to argmax)
    """

    name = "Argmax Operator"

    # accepts 5D data only, 'txyzc'
    Input = InputSlot()
    Output = OutputSlot()

    Threshold = InputSlot(optional=True, stype='float', value=0.0)

    def __init__(self, *args, **kwargs):
        super(OpMriArgmax, self).__init__(*args, **kwargs)

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        tagged_shape = self.Input.meta.getTaggedShape()
        tagged_shape['c'] = 1
        self.Output.meta.shape = tuple(tagged_shape.values())

    @staticmethod
    def _globalArgmax(vol):
        """
        computes an argmax of the prediction maps (hard segmentation)
        """
        return np.argmax(vol, axis=-1)+1

    def execute(self, slot, subindex, roi, result):
        tmp_roi = roi.copy()
        tmp_roi.setDim(-1,0,self.Input.meta.shape[-1])
        tmp_data = self.Input.get(tmp_roi).wait().astype(np.float32)

        assert tmp_data.shape[-1] == \
            self.Input.meta.getTaggedShape()['c'],\
            'Not all channels are used for argmax'
        result[...,0]  = self._globalArgmax(tmp_data)
        
    def propagateDirty(self, inputSlot, subindex, roi):
         if inputSlot is self.Input:
             start = np.asarray(roi.start, dtype=int)
             stop = np.asarray(roi.stop, dtype=int)
             start[-1] = 0
             stop[-1] = 1
             newroi = SubRegion(self.Output, start=start, stop=stop)
             self.Output.setDirty(newroi)
         if inputSlot is self.Threshold:
             self.Output.setDirty(slice(None))
