
from threading import Lock as ThreadLock
from functools import partial

import numpy as np
import vigra

from lazyflow.operator import Operator
from lazyflow.slot import InputSlot, OutputSlot
from lazyflow.rtype import SubRegion
from lazyflow.metaDict import MetaDict
from lazyflow.request import Request, RequestPool
from lazyflow.operators import OpCompressedCache, OpReorderAxes

# try to import the blockedarray module, fail only if neccessary
try:
    import blockedarray
except ImportError as e:
    _blockedarray_module_available = False
    _importMsg = str(e)
else:
    _blockedarray_module_available = True


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
    # Note: The output might be cached internally depending on the chosen CC
    # method, use the CachedOutput to avoid duplicate caches. (see inner
    # operator below for details)
    Output = OutputSlot()

    ## Cached label image
    # Access the internal cache. If you were planning to cache the labeled
    # volume, be sure to use this slot, since it makes use of the internal
    # cache that might be in use anyway.
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
        origOrder = "".join([s for s in self.Input.meta.getTaggedShape()])
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
    ## input with axes 'xyzct'
    Input = InputSlot()

    ## background with axes 'xyzct', spatial axes must be singletons
    Background = InputSlot()

    Output = OutputSlot()
    CachedOutput = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpLabelingABC, self).__init__(*args, **kwargs)
        self._cache = None
        self._metaProvider = _OpMetaProvider(parent=self)

    def setupOutputs(self):
        labelType = np.uint32

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

        s = self.Input.meta.getTaggedShape()
        shape = (s['c'], s['t'])
        self._cached = np.zeros(shape)

        # prepare locks for each channel and time slice
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
        #FIXME we don't care right now which slot is requested, just return cached CC
        # get the background values
        bg = self.Background[...].wait()
        bg = vigra.taggedView(bg, axistags=self.Background.meta.axistags)
        bg = bg.withAxes(*'ct')
        assert np.all(self.Background.meta.shape[3:] ==
                      self.Input.meta.shape[3:]),\
            "Shape of background values incompatible to shape of Input"

        # do labeling in parallel over channels and time slices
        pool = RequestPool()

        for t in range(roi.start[4], roi.stop[4]):
            for c in range(roi.start[3], roi.stop[3]):
                # only one thread may update the cache for this c and t, other requests
                # must wait until labeling is finished
                self._locks[c, t].acquire()
                if self._cached[c, t]:
                    # this slice is already computed
                    continue
                # update the whole slice
                req = Request(partial(self._updateSlice, c, t, bg[c, t]))
                pool.add(req)

        pool.wait()
        pool.clean()

        req = self._cache.Output.get(roi)
        req.writeInto(result)
        req.block()

        # release locks and set caching flags
        for t in range(roi.start[4], roi.stop[4]):
            for c in range(roi.start[3], roi.stop[3]):
                self._cached[c, t] = 1
                self._locks[c, t].release()

    ## compute the requested slice and put the results into self._cache
    #
    def _updateSlice(self, c, t, bg):
        raise NotImplementedError("This is an abstract method")


## vigra connected components
class _OpLabelVigra(OpLabelingABC):
    name = "OpLabelVigra"

    def setupOutputs(self):
        if self.Input.ready():
            supportedDtypes = [np.uint8, np.uint32, np.float32]
            dtype = self.Input.meta.dtype
            if dtype not in supportedDtypes:
                msg = "OpLabelVolume: dtype '{}' not supported "\
                    "with method 'vigra'. Supported types: {}"
                msg = msg.format(dtype, supportedDtypes)
                raise ValueError(msg)
        super(_OpLabelVigra, self).setupOutputs()

    def _updateSlice(self, c, t, bg):
        source = vigra.taggedView(self.Input[..., c, t].wait(),
                                  axistags='xyzct')
        source = source.withAxes(*'xyz')
        result = vigra.analysis.labelVolumeWithBackground(
            source, background_value=int(bg))
        result = result.withAxes(*'xyzct')

        stop = np.asarray(self.Input.meta.shape)
        start = 0*stop
        start[3:] = (c, t)
        stop[3:] = (c+1, t+1)
        roi = SubRegion(self._cache.Input, start=start, stop=stop)

        self._cache.setInSlot(self._cache.Input, (), roi, result)


## blockedarray connected components
class _OpLabelBlocked(OpLabelingABC):
    name = "OpLabelBlocked"

    def _updateSlice(self, c, t, bg):
        assert _blockedarray_module_available,\
            "Failed to import blockedarray: {}".format(_importMsg)
        assert bg == 0,\
            "Blocked Labeling not implemented for background value {}".format(bg)

        blockShape = _findBlockShape(self.Input.meta.shape[:3])

        source = _Source(self.Input, blockShape, c, t)
        sink = _Sink(self._cache, c, t)
        cc = blockedarray.dim3.ConnectedComponents(source, blockShape)
        cc.writeToSink(sink)


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


if _blockedarray_module_available:

    def fullRoiFromPQ(slot, p, q, c, t):
        fullp = np.zeros((5,), dtype=np.int)
        fullq = np.zeros((5,), dtype=np.int)
        fullp[:3] = p
        fullq[:3] = q
        fullp[3] = c
        fullp[4] = t
        fullq[3] = c+1
        fullq[4] = t+1
        return SubRegion(slot, start=fullp, stop=fullq)

    class _Source(blockedarray.adapters.SourceABC):
        def __init__(self, slot, blockShape, c, t):
            super(_Source, self).__init__()
            self._slot = slot
            self._blockShape = blockShape  # is passed to blockedarray!
            self._p = np.asarray(slot.meta.shape[:3], dtype=np.long)*0
            self._q = np.asarray(slot.meta.shape[:3], dtype=np.long)
            self._c = c
            self._t = t

        def pySetRoi(self, roi):
            assert len(roi) == 2
            self._p = np.asarray(roi[0], dtype=np.long)
            self._q = np.asarray(roi[1], dtype=np.long)

        def pyShape(self):
            return tuple(self._slot.meta.shape[:3])

        def pyReadBlock(self, roi, output):
            assert len(roi) == 2
            roiP = np.asarray(roi[0])
            roiQ = np.asarray(roi[1])
            p = self._p + roiP
            q = p + roiQ - roiP
            if np.any(q > self._q):
                raise IndexError("Requested roi is too large for selected "
                                 "roi (previous call to setRoi)")
            sub = fullRoiFromPQ(self._slot, p, q, self._c, self._t)
            req = self._slot.get(sub)
            req.writeInto(output[..., np.newaxis, np.newaxis])
            req.block()
            return True

    class _Sink(blockedarray.adapters.SinkABC):
        def __init__(self, op, c, t):
            super(_Sink, self).__init__()
            self._op = op
            self._c = c
            self._t = t

        def pyWriteBlock(self, roi, block):
            assert len(roi) == 2
            roiP = np.asarray(roi[0])
            roiQ = np.asarray(roi[1])
            sub = fullRoiFromPQ(self._op.Input, roiP, roiQ, self._c, self._t)
            self._op.setInSlot(self._op.Input, (), sub,
                               block[..., np.newaxis, np.newaxis])


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
