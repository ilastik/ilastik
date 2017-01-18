from __future__ import absolute_import
from builtins import str
from builtins import range
from builtins import object

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
from lazyflow.operators import OpBlockedArrayCache, OpReorderAxes
from .opLazyConnectedComponents import OpLazyConnectedComponents
from future.utils import with_metaclass

logger = logging.getLogger(__name__)


## OpLabelVolume - the **unified** connected components operator
#
# This operator computes the connected component labeling of the input volume.
# The labeling is computed **seperately** per time slice and per channel.
class OpLabelVolume(Operator):

    name = "OpLabelVolume"

    ## provide the volume to label here
    # (arbitrary shape, dtype could be restricted, see the implementations
    # property supportedDtypes below)
    Input = InputSlot()

    ## provide labels that are treated as background
    # the shape of the background labels must match the shape of the volume in
    # channel and in time axis, and must have no spatial axes.
    # E.g.: volume.taggedShape = {'x': 10, 'y': 12, 'z': 5, 'c': 3, 't': 100}
    # ==>
    # background.taggedShape = {'c': 3, 't': 100}
    #TODO relax requirements (single value is already working)
    Background = InputSlot(optional=True)

    # Bypass cache (for headless mode)
    BypassModeEnabled = InputSlot(value=False)

    ## decide which CCL method to use
    #
    # currently available:
    # * 'vigra': use the fast algorithm from ukoethe/vigra
    # * 'blocked': use the memory saving algorithm from thorbenk/blockedarray
    #
    # A change here deletes all previously cached results.
    Method = InputSlot(value='vigra')

    ## Labeled volume
    # Axistags and shape are the same as on the Input, dtype is an integer
    # datatype.
    # This slot operates on a what-you-request-is-what-you-get basis, if you
    # request a subregion only that subregion will be considered for labeling
    # and no internal caches are used. If you want consistent labels for
    # subsequent requests, use CachedOutput instead.
    # This slot will be set dirty by time and channel if the background or the
    # input changes for the respective time-channel-slice.
    Output = OutputSlot()

    ## Cached label image
    # Axistags and shape are the same as on the Input, dtype is an integer
    # datatype.
    # This slot extends the ROI to the full xyz volume (c and t are unaffected)
    # and computes the labeling for the whole volume. As long as the input does
    # not get dirty, subsequent requests to this slot guarantee consistent
    # labelings. The internal cache in use is an OpCompressedCache.
    # This slot will be set dirty by time and channel if the background or the
    # input changes for the respective time-channel-slice.
    CachedOutput = OutputSlot()

    # cache access, see OpCompressedCache
    CleanBlocks = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpLabelVolume, self).__init__(*args, **kwargs)

        # we just want to have 5d data internally
        op5 = OpReorderAxes(parent=self)
        op5.Input.connect(self.Input)
        op5.AxisOrder.setValue('txyzc')
        self._op5 = op5

        self._opLabel = None

        self._op5_2 = OpReorderAxes(parent=self)
        self._op5_2_cached = OpReorderAxes(parent=self)

        self.Output.connect(self._op5_2.Output)
        self.CachedOutput.connect(self._op5_2_cached.Output)

        # available OpLabelingABCs:
        # TODO: OpLazyConnectedComponents and _OpLabelBlocked does not conform to OpLabelingABC
        self._labelOps = {'vigra': _OpLabelVigra,
                          'blocked': _OpLabelBlocked,
                          'lazy': OpLazyConnectedComponents}

    def setupOutputs(self):
        method = self.Method.value
        if not isinstance(method, basestring):
            method = method[0]

        if self._opLabel is not None and type(self._opLabel) != self._labelOps[method]:
            # fully remove old labeling operator
            self._op5_2.Input.disconnect()
            self._op5_2_cached.Input.disconnect()
            self._opLabel.Input.disconnect()
            self._opLabel = None

        if self._opLabel is None:
            self._opLabel = self._labelOps[method](parent=self)
            self._opLabel.Input.connect(self._op5.Output)
            if method is 'vigra':
                self._opLabel.BypassModeEnabled.connect(self.BypassModeEnabled)
    
        # connect reordering operators
        self._op5_2.Input.connect(self._opLabel.Output)
        self._op5_2_cached.Input.connect(self._opLabel.CachedOutput)

        # set the final reordering operator's AxisOrder to that of the input
        origOrder = self.Input.meta.getAxisKeys()
        self._op5_2.AxisOrder.setValue(origOrder)
        self._op5_2_cached.AxisOrder.setValue(origOrder)
    
        # connect cache access slots
        self.CleanBlocks.connect(self._opLabel.CleanBlocks)

        # set background values
        self._setBG()

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.BypassModeEnabled:
            pass
        elif slot == self.Method:
            # We are changing the labeling method. In principle, the labelings
            # are equivalent, but not necessarily the same!
            self.Output.setDirty(slice(None))
        elif slot == self.Input:
            # handled by internal operator
            pass
        elif slot == self.Background:
            # propagate the background values, output will be set dirty in 
            # internal operator
            self._setBG()

    def setInSlot(self, slot, subindex, roi, value):
        #    "Invalid slot for setInSlot(): {}".format( slot.name )
        # Nothing to do here.
        # Our Input slots are directly fed into the cache,
        #  so all calls to __setitem__ are forwarded automatically
        pass

    ## set the background values of inner operator
    def _setBG(self):
        if self.Background.ready():
            val = self.Background.value
        else:
            val = 0
        bg = np.asarray(val)
        t = self._op5.Output.meta.shape[0]
        c = self._op5.Output.meta.shape[4]
        if bg.size == 1:
            bg = np.zeros((c, t))
            bg[:] = val
            bg = vigra.taggedView(bg, axistags='ct')
        else:
            bg = vigra.taggedView(val, axistags=self.Background.meta.axistags)
            bg = bg.withAxes(*'ct')
        bg = bg.withAxes(*'txyzc')
        self._opLabel.Background.setValue(bg)


## parent class for all connected component labeling implementations
class OpLabelingABC(with_metaclass(ABCMeta, Operator)):
    Input = InputSlot()

    ## background with axes 'txyzc', spatial axes must be singletons
    Background = InputSlot()
    
    # Bypass cache (for headless mode)
    BypassModeEnabled = InputSlot(value=False)

    Output = OutputSlot()
    CachedOutput = OutputSlot()

    # cache access, see OpCompressedCache
    CleanBlocks = OutputSlot()

    # the numeric type that is used for labeling
    labelType = np.uint32

    ## list of supported dtypes
    @abstractproperty
    def supportedDtypes(self):
        pass

    def __init__(self, *args, **kwargs):
        super(OpLabelingABC, self).__init__(*args, **kwargs)
        self._cache = OpBlockedArrayCache(parent=self)
        self._cache.name = "OpLabelVolume.OutputCache"
        self._cache.BypassModeEnabled.connect(self.BypassModeEnabled)
        self._cache.Input.connect(self.Output)
        self.CachedOutput.connect(self._cache.Output)
        self.CleanBlocks.connect(self._cache.CleanBlocks)

    def setupOutputs(self):

        # check if the input dtype is valid
        if self.Input.ready():
            dtype = self.Input.meta.dtype
            if dtype not in self.supportedDtypes:
                msg = "{}: dtype '{}' not supported "\
                    "with method 'vigra'. Supported types: {}"
                msg = msg.format(self.name, dtype, self.supportedDtypes)
                raise ValueError(msg)

        # set cache chunk shape to the whole spatial volume
        shape = np.asarray(self.Input.meta.shape, dtype=np.int)
        shape[0] = 1
        shape[4] = 1
        self._cache.BlockShape.setValue(tuple(shape))

        # setup meta for Output
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = self.labelType

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.BypassModeEnabled:
            pass
        else:
            # a change in either input or background makes the whole
            # time-channel-slice dirty (CCL is a global operation)
            outroi = roi.copy()
            outroi.start[1:4] = (0, 0, 0)
            outroi.stop[1:4] = self.Input.meta.shape[1:4]
            self.Output.setDirty(outroi)
            self.CachedOutput.setDirty(outroi)

    def setInSlot(self, slot, subindex, roi, value):
        #    "Invalid slot for setInSlot(): {}".format( slot.name )
        # Nothing to do here.
        # Our Input slots are directly fed into the cache,
        #  so all calls to __setitem__ are forwarded automatically
        pass

    def execute(self, slot, subindex, roi, result):
        if slot == self.Output:
            # just label the ROI and write it to result
            self._label(roi, result)
        else:
            raise ValueError("Request to unknown slot {}".format(slot))

    def _label(self, roi, result):
        result = vigra.taggedView(result, axistags=self.Output.meta.axistags)
        # get the background values
        bg = self.Background[...].wait()
        bg = vigra.taggedView(bg, axistags=self.Background.meta.axistags)
        bg = bg.withAxes(*'ct')
        assert np.all(self.Background.meta.shape[0] ==
                      self.Input.meta.shape[0]),\
            "Shape of background values incompatible to shape of Input"
        assert np.all(self.Background.meta.shape[4] ==
                      self.Input.meta.shape[4]),\
            "Shape of background values incompatible to shape of Input"

        # do labeling in parallel over channels and time slices
        pool = RequestPool()

        start = np.asarray(roi.start, dtype=np.int)
        stop = np.asarray(roi.stop, dtype=np.int)
        for ti, t in enumerate(range(roi.start[0], roi.stop[0])):
            start[0], stop[0] = t, t+1
            for ci, c in enumerate(range(roi.start[4], roi.stop[4])):
                start[4], stop[4] = c, c+1
                newRoi = SubRegion(self.Output,
                                   start=tuple(start), stop=tuple(stop))
                resView = result[ti, ..., ci].withAxes(*'xyz')
                req = Request(partial(self._label3d, newRoi,
                                      bg[c, t], resView))
                pool.add(req)

        logger.debug(
            "{}: Computing connected components for ROI {} ...".format(
                self.name, roi))
        pool.wait()
        pool.clean()
        logger.debug("{}: Connected components computed.".format(
            self.name))

    ## compute the requested roi and put the results into result
    #
    # @param result the array to write into, 3d xyz
    @abstractmethod
    def _label3d(self, roi, bg, result):
        pass


## vigra connected components
class _OpLabelVigra(OpLabelingABC):
    name = "OpLabelVigra"
    supportedDtypes = [np.uint8, np.uint32, np.float32]

    def _label3d(self, roi, bg, result):
        source = vigra.taggedView(self.Input.get(roi).wait(),
                                  axistags='txyzc').withAxes(*'xyz')
        if source.shape[2] > 1:
            result[:] = vigra.analysis.labelVolumeWithBackground(
                source, background_value=int(bg))
        else:
            result[..., 0] = vigra.analysis.labelImageWithBackground(
                source[..., 0], background_value=int(bg))


# try to import the blockedarray module, fail only if neccessary
try:
    from blockedarray import OpBlockedConnectedComponents
    raise ImportError("blockedarray not supported")
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
# TODO this operator does not conform to OpLabelingABC
class _OpLabelBlocked(OpBlockedConnectedComponents):
    name = "OpLabelBlocked"

    def _updateSlice(self, c, t, bg):
        assert _blockedarray_module_available,\
            "Failed to import blockedarray. Message was: {}".format(_importMsg)

        blockShape = _findBlockShape(self.Input.meta.shape[:3]) + (1, 1)
        logger.debug("{}: Using blockshape {}".format(self.name, blockShape))
        self._cache.BlockShape.setValue(blockShape)
        super(_OpLabelBlocked, self)._updateSlice(c, t, bg)


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
