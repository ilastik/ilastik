
from threading import Lock as ThreadLock
from functools import partial
from abc import ABCMeta, abstractmethod, abstractproperty
import logging

import numpy as np
import vigra

from lazyflow.operator import Operator
from lazyflow.slot import InputSlot, OutputSlot
from lazyflow.rtype import SubRegion
from lazyflow.metaDict import MetaDict
from lazyflow.request import Request, RequestPool
from lazyflow.operators import OpCompressedCache, OpReorderAxes

logger = logging.getLogger(__name__)


## OpLabelVolume - the **unified** connected components operator
#
# This operator computes the connected component labeling of the input volume.
# The labeling is computed **seperately** per time slice and per channel.
class OpLabelVolume(Operator):

    ## provide the volume to label here
    # (arbitrary shape, dtype could be restricted #TODO)
    Input = InputSlot()

    ## provide labels that are treated as background
    # the shape of the background labels must match the shape of the volume in
    # channel and in time axis, and must have no spatial axes.
    # E.g.: volume.taggedShape = {'x': 10, 'y': 12, 'z': 5, 'c': 3, 't': 100}
    # ==>
    # background.taggedShape = {'c': 3, 't': 100}
    #TODO relax requirements (single value is already working)
    Background = InputSlot(optional=True)

    ## decide which CCL method to use
    #
    # currently available:
    # * 'vigra': use the fast algorithm from ukoethe/vigra
    # * 'blocked': use the memory saving algorithm from thorbenk/blockedarray
    Method = InputSlot(value='vigra')

    ## Labeled volume
    # Axistags and shape are the same as on the Input, dtype is an integer
    # datatype.
    # Note: This output is just an alias for CachedOutput, because all
    # implementations use internal caches.
    Output = OutputSlot()

    ## Cached label image
    # Axistags and shape are the same as on the Input, dtype is an integer
    # datatype.
    CachedOutput = OutputSlot()

    name = "OpLabelVolume"

    def __init__(self, *args, **kwargs):
        super(OpLabelVolume, self).__init__(*args, **kwargs)

        # we just want to have 5d data internally
        op5 = OpReorderAxes(parent=self)
        op5.Input.connect(self.Input)
        op5.AxisOrder.setValue('xyzct')
        self._op5 = op5

        self._opLabel = None

        self._op5_2 = OpReorderAxes(parent=self)
        self._op5_2_cached = OpReorderAxes(parent=self)

        self.Output.connect(self._op5_2.Output)
        self.CachedOutput.connect(self._op5_2_cached.Output)

        # available OpLabelingABCs:
        self._labelOps = {'vigra': _OpLabelVigra, 'blocked': _OpLabelBlocked}

    def setupOutputs(self):

        if self._opLabel is not None:
            # fully remove old labeling operator
            self._op5_2.Input.disconnect()
            self._op5_2_cached.Input.disconnect()
            self._opLabel.Input.disconnect()
            del self._opLabel

        method = self.Method.value
        if not isinstance(method, str):
            method = method[0]

        self._opLabel = self._labelOps[method](parent=self)
        self._opLabel.Input.connect(self._op5.Output)

        # connect reordering operators
        self._op5_2.Input.connect(self._opLabel.Output)
        self._op5_2_cached.Input.connect(self._opLabel.CachedOutput)

        # set the final reordering operator's AxisOrder to that of the input
        origOrder = self.Input.meta.getAxisKeys()
        self._op5_2.AxisOrder.setValue(origOrder)
        self._op5_2_cached.AxisOrder.setValue(origOrder)

        # set background values
        self._setBG()

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Method:
            # We are changing the labeling method. In principle, the labelings
            # are equivalent, but not neccessary the same!
            self.Output.setDirty(slice(None))
        elif slot == self.Input:
            # handled by internal operator
            pass
        elif slot == self.Background:
            # propagate the background values, output will be set dirty in 
            # internal operator
            self._setBG()

    ## set the background values of inner operator
    def _setBG(self):
        if self.Background.ready():
            val = self.Background.value
        else:
            val = 0
        bg = np.asarray(val)
        if bg.size == 1:
            bg = np.zeros(self._op5.Output.meta.shape[3:])
            bg[:] = val
            bg = vigra.taggedView(bg, axistags='ct')
        else:
            bg = vigra.taggedView(val, axistags=self.Background.meta.axistags)
            bg = bg.withAxes(*'ct')
        bg = bg.withAxes(*'xyzct')
        self._opLabel.Background.setValue(bg)


## parent class for all connected component labeling implementations
class OpLabelingABC(Operator):
    __metaclass__ = ABCMeta

    ## input with axes 'xyzct'
    Input = InputSlot()

    ## background with axes 'xyzct', spatial axes must be singletons
    Background = InputSlot()

    Output = OutputSlot()
    CachedOutput = OutputSlot()

    ## list of supported dtypes
    @abstractproperty
    def supportedDtypes(self):
        pass

    def __init__(self, *args, **kwargs):
        super(OpLabelingABC, self).__init__(*args, **kwargs)
        self._cache = None
        self._metaProvider = _OpMetaProvider(parent=self)

    def setupOutputs(self):
        labelType = np.uint32

        # check if the input dtype is valid
        if self.Input.ready():
            dtype = self.Input.meta.dtype
            if dtype not in self.supportedDtypes:
                msg = "{}: dtype '{}' not supported "\
                    "with method 'vigra'. Supported types: {}"
                msg = msg.format(self.name, dtype, self.supportedDtypes)
                raise ValueError(msg)

        # remove unneeded old cache
        if self._cache is not None:
            self._cache.Input.disconnect()
            del self._cache

        m = self.Input.meta
        self._metaProvider.setMeta(
            MetaDict({'shape': m.shape, 'dtype': labelType,
                      'axistags': m.axistags}))

        self._cache = OpCompressedCache(parent=self)
        self._cache.name = "OpLabelVolume.OutputCache"
        self._cache.Input.connect(self._metaProvider.Output)
        shape = np.asarray(self.Input.meta.shape)
        shape[3:5] = 1
        self._cache.BlockShape.setValue(tuple(shape))
        self.Output.meta.assignFrom(self._cache.Output.meta)
        self.CachedOutput.meta.assignFrom(self._cache.Output.meta)

        # prepare locks for each channel and time slice
        s = self.Input.meta.getTaggedShape()
        shape = (s['c'], s['t'])
        locks = np.empty(shape, dtype=np.object)
        for c in range(s['c']):
            for t in range(s['t']):
                locks[c, t] = ThreadLock()
        self._locks = locks

    def propagateDirty(self, slot, subindex, roi):
        # a change in either input or background makes the whole
        # time-channel-slice dirty (CCL is a global operation)
        self._cached[roi.start[3]:roi.stop[3],
                     roi.start[4]:roi.stop[4]] = 0
        outroi = roi.copy()
        outroi.start[:3] = (0, 0, 0)
        outroi.stop[:3] = self.Input.meta.shape[:3]
        self.Output.setDirty(outroi)
        self.CachedOutput.setDirty(outroi)

    def execute(self, slot, subindex, roi, result):
        #FIXME we don't care right now which slot is requested, just return
        # cached CC (all implementations cache anyways)

        # get the background values
        bg = self.Background[...].wait()
        bg = vigra.taggedView(bg, axistags=self.Background.meta.axistags)
        bg = bg.withAxes(*'ct')
        assert np.all(self.Background.meta.shape[3:] ==
                      self.Input.meta.shape[3:]),\
            "Shape of background values incompatible to shape of Input"

        # do labeling in parallel over channels and time slices
        pool = RequestPool()

        ## function for request ##
        def singleSliceRequest(start3d, stop3d, c, t, bg):
            # computing CC is a critical section
            self._locks[c, t].acquire()

            # update the slice
            self._updateCache(start3d, stop3d, c, t, bg)

            # leave the critical section
            self._locks[c, t].release()
        ## end function for request ##

        for t in range(roi.start[4], roi.stop[4]):
            for c in range(roi.start[3], roi.stop[3]):
                # update the whole slice
                req = Request(partial(singleSliceRequest,
                                      roi.start[:3], roi.stop[:3],
                                      c, t, bg[c, t]))
                pool.add(req)

        logger.debug("{}: Computing connected components for ROI {}".format(
            self.name, roi))
        pool.wait()
        pool.clean()

        req = self._cache.Output.get(roi)
        req.writeInto(result)
        req.block()

    ## compute the requested roi and put the results into self._cache
    #
    @abstractmethod
    def _updateCache(self, start3d, stop3d, c, t, bg):
        pass


class OpNonLazyCC(OpLabelingABC):

    def setupOutputs(self):
        if self.Input.ready():
            s = self.Input.meta.getTaggedShape()
            shape = (s['c'], s['t'])
            self._cached = np.zeros(shape, dtype=np.bool)
        super(OpNonLazyCC, self).setupOutputs()

    ## wraps the childrens' updateSlice function to check if recomputation is
    ## needed
    def _updateCache(self, start3d, stop3d, c, t, bg):
        # we compute the whole slice, regardless of actual roi, if needed
        if self._cached[c, t]:
            return
        self._updateSlice(c, t, bg)
        self._cached[c, t] = True

    @abstractmethod
    def _updateSlice(self, c, t, bg):
        pass


## vigra connected components
class _OpLabelVigra(OpNonLazyCC):
    name = "OpLabelVigra"
    supportedDtypes = [np.uint8, np.uint32, np.float32]

    def propagateDirty(self, slot, subindex, roi):
        # set the cache to dirty
        self._cached[roi.start[3]:roi.stop[3],
                     roi.start[4]:roi.stop[4]] = 0
        super(_OpLabelVigra, self).propagateDirty(slot, subindex, roi)

    def _updateSlice(self, c, t, bg):
        source = vigra.taggedView(self.Input[..., c, t].wait(),
                                  axistags='xyzct')
        source = source.withAxes(*'xyz')
        if source.shape[2] > 1:
            result = vigra.analysis.labelVolumeWithBackground(
                source, background_value=int(bg))
        else:
            result = vigra.analysis.labelImageWithBackground(
                source[..., 0], background_value=int(bg))
        result = result.withAxes(*'xyzct')

        stop = np.asarray(self.Input.meta.shape)
        start = 0*stop
        start[3:] = (c, t)
        stop[3:] = (c+1, t+1)
        roi = SubRegion(self._cache.Input, start=start, stop=stop)

        self._cache.setInSlot(self._cache.Input, (), roi, result)


# try to import the blockedarray module, fail only if neccessary
try:
    from blockedarray import OpBlockedConnectedComponents
except ImportError as e:
    _blockedarray_module_available = False
    _importMsg = str(e)
    class OpBlockedConnectedComponents(object):
        pass
else:
    _blockedarray_module_available = True
    _importMsg = "No error, importing blockedarray worked."

def haveBlocked():
    return _blockedarray_module_available


## Wrapper for blockedarray.OpBlockedConnectedComponents
# This wrapper takes care that the module is indeed imported, and sets the
# block shape for the cache.
class _OpLabelBlocked(OpBlockedConnectedComponents):
    name = "OpLabelBlocked"

    def _updateSlice(self, c, t, bg):
        assert _blockedarray_module_available,\
            "Failed to import blockedarray. Message was: {}".format(_importMsg)

        blockShape = _findBlockShape(self.Input.meta.shape[:3]) + (1, 1)
        logger.debug("{}: Using blockshape {}".format(self.name, blockShape))
        self._cache.BlockShape.setValue(blockShape)
        super(_OpLabelBlocked, self)._updateSlice(c, t, bg)



## Feeds meta data into OpCompressedCache
#
# This operator is needed because we
#   - don't connect OpCompressedCache directly to a real InputSlot
#   - feed data to cache by setInSlot()
class _OpMetaProvider(Operator):
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        # Configure output with given metadata.
        super(_OpMetaProvider, self).__init__(*args, **kwargs)

    def setupOutputs(self):
        pass

    def execute(self, slot, subindex, roi, result):
        assert False,\
            "The cache asked for data which should not happen."

    def setMeta(self, meta):
        self.Output.meta.assignFrom(meta)


## find a good block shape for given input shape
# Set the block shape such that it
#  (a) divides the volume shape evenly
#  (b) is smaller than a given maximum (500 == 1GB per xyz-block)
#  (c) is maximal for all block shapes satisfying (a) and (b)
#
# + This problem is guaranteed to have a solution
# - The solution might be (1,1,1), in case your volume has a prime-number shape
#   in all axes and these are larger than blockMax.
#
# @param inshape array with size 3
# @param blockMax single integer (see above)
def _findBlockShape(inshape, blockMax=500):
    shape = [1, 1, 1]
    for i in range(3):
        n = inshape[i]
        facts = _combine(_factorize(n))
        facts.sort()
        m = 1
        for f in facts:
            if f < blockMax:
                m = f
            else:
                break

            shape[i] = m
    return tuple(shape)


_primes = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
    73, 79, 83, 89, 97, 101,    103, 107, 109, 113, 127, 131, 137, 139, 149,
    151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229,
    233, 239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313,
    317, 331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389, 397, 401, 409,
    419, 421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479, 487, 491, 499]


def _factorize(n):
    '''
    factorize an integer, return list of prime factors (up to 499)
    '''
    maxP = int(np.sqrt(n))
    for p in _primes:
        if p > maxP:
            return [n]
        if n % p == 0:
            ret = _factorize(n//p)
            ret.append(p)
            return ret
    assert False, "How did you get here???"


def _combine(f):
    '''
    possible combinations of factors of f
    '''

    if len(f) < 2:
        return f
    ret = []
    for i in range(len(f)):
        n = f.pop(0)
        sub = _combine(f)
        ret += sub
        for s in sub:
            ret.append(s*n)
        f.append(n)
    return ret
