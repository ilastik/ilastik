
from abc import abstractmethod

import numpy as np
import vigra

from lazyflow.operator import Operator, InputSlot, OutputSlot
from lazyflow.rtype import SubRegion
from lazyflow.request import RequestLock
from lazyflow.operators import OpReorderAxes, OpCompressedCache


##### FIX ME Why does the import not work
try:
    from opMriVolFilter import OpMriArgmax
except Exception, e:
    print e

import logging
logger = logging.getLogger(__name__)

import opengm

# this operator wraps multiple implementations of smoothing algorithms while
# also taking care of caching and reordering
class OpSmoothing(Operator):
    Input = InputSlot()
    Configuration = InputSlot()
    Method = InputSlot()

    CachedOutput = OutputSlot()

    # for internal use only
    _Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpSmoothing, self).__init__(*args, **kwargs)

        self._op = None

        self._opIn = OpReorderAxes(parent=self)
        self._opIn.Input.connect(self.Input)
        self._opIn.AxisOrder.setValue('txyzc')

        self._opOut = OpReorderAxes(parent=self)
        self._opOut.Input.connect(self._Output)

        self._cache = None

    def setupOutputs(self):
        method = self.Method.value
        if method not in smoothers_available:
            raise NotImplementedError(
                "unknown smoothing method '{}'".format(method))

        temp_op = smoothers_available[method](parent=self)
        if not temp_op.isAvailable():
            raise RuntimeError(
                "smoothing method '{}' not available".format(method))

        # remove cache so that it does not object on e.g. changed axis
        self._destroyCache()

        # FIXME reuse operators (reusing is known to cause at the moment)
        self._disconnectSmoother()
        self._connectSmoother(temp_op)

        self._createCache()

        self._opOut.AxisOrder.setValue(self.Input.meta.getAxisKeys())

    def execute(self, slot, subindex, roi, result):
        raise NotImplementedError(
            "All executes must be handled by internal operators")

    def propagateDirty(self, slot, subindex, roi):
        # all dirty handling is done by internal operators
        if self._op is None:
            # strange constellation, but we try to do our best
            self.CachedOutput.setDirty(slice(None))

    def _destroyCache(self):
        if self._cache is None:
            return
        self.CachedOutput.disconnect()
        self._cache.Input.disconnect()
        self._cache = None

    def _createCache(self):
        self._cache = OpCompressedCache(parent=self)
        ts = self.Input.meta.getTaggedShape()
        if 't' in ts:
            ts['t'] = 1
        self._cache.Input.connect(self._opOut.Output)
        self._cache.BlockShape.setValue([ts[k] for k in ts])
        self.CachedOutput.connect(self._cache.Output)

    def _disconnectSmoother(self):
        self._Output.disconnect()
        if self._op is not None:
            self._op.Input.disconnect()
            self._op.Configuration.disconnect()
        self._op = None

    def _connectSmoother(self, temp_op):
        self._op = temp_op
        self._op.Input.connect(self._opIn.Output)
        self._op.Configuration.connect(self.Configuration)
        self._Output.connect(self._op.Output)


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

        logger.debug("Smoothing roi {}".format(roi))

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
        logger.debug("Smoothing roi {}".format(roi))

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


# Implements opengm filtering
class OpOpenGMFilter(OpSmoothingImplementation):
    """
    Operator that uses opengm to cleanup labels
    """
    name = "OpenGM Filter"

    RawInput = InputSlot()

    # implementation of abstract method
    def isAvailable(self):
        # we are implementing it right here, so it is indeed available
        return False

    def __init__(self, *args, **kwargs):
        # internal threshold for computing mask and energy offset 
        # to avoid log problems
        self._epsilion = 0.000001 
        # compute mask from raw input channel
        raw_data = self.op.RawInput.get(slice(None)).wait()
        bool_mask = np.ma.masked_less_equal( raw_data[0,...,0],
                                             self._epsilion).mask
        self._mask = np.zeros(raw_data.shape, dtype=np.uint32)
        self._mask[~bool_mask] = 1.0

        super(OpOpenGMFilter, self).__init__(*args, **kwargs)

    def setupOutputs(self):
        super(OpOpenGMFilter, self).setupOutputs()
        self.Output.meta.dtype = np.float32

    def execute(self, slot, subindex, roi, result):
        logger.debug("Smoothing roi {}".format(roi))

        conf = self.Configuration.value
        if 'sigma' not in conf:
            raise self.ConfigurationError(
                "expected key 'sigma' in configuration")
        sigma = conf['sigma']

        if 'unaries' not in conf:
            raise self.ConfigurationError(
                "expected key 'unaries' in configuration")
        unaries = conf['unaries']

        result[...] = self.Input.get(roi).wait().astype( \
                                                    self.Output.meta.dtype)
        self._opengmFilter(result, sigma, unaries)

    @staticmethod
    def _opengmFilter(vol, filter_size, unaries_scale):
        print "TODO implement me"
        print unaries, filter_size
        return vol
        
        # make uncertainty edge image
        pfiltered = np.zeros_like(vol[0])
        for c in xrange(vol.shape[-1]):
            pfiltered[...,c] = vigra.gaussianSmoothing( vol[0,...,c], 
                                                        float(1.2))
        pmap = np.sort(pfiltered, axis=-1)
        uncertainties  = pmap[...,-1]-pmap[...,-2] 
        # set starting point
        init_data = np.argmax(vol[0],axis=-1).astype( np.uint32 )
        init_data = opengm.getStartingPointMasked(init_data, self._mask)      
        unaries = -unaries_scale*np.log(vol[0] + self._epsilon)
        gm = opengm.pottsModel3dMasked(unaries=unaries, 
                                       regularizer=uncertainties, 
                                       mask=self._mask)
        try:
            inf = opengm.inference.FastPd(gm)
            inf.setStartingPoint(init_data)
            inf.infer(inf.verboseVisitor())
        except:
            inf = opengm.inference.AlphaExpansion(gm)
            inf.setStartingPoint(init_data)
            inf.infer(inf.verboseVisitor())
        pred = opengm.makeMaskedState(self._mask, inf.arg(), labelIdx=0)


# add this smoother to the global smoothers table
smoothers_available['opengm'] = OpOpenGMFilter
