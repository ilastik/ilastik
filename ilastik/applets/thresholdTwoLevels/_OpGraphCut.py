# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers


# basic python modules
import functools
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
from threading import Lock as ThreadLock

# required numerical modules
import numpy as np
import vigra
import opengm

# basic lazyflow types
from lazyflow.operator import Operator
from lazyflow.slot import InputSlot, OutputSlot
from lazyflow.rtype import SubRegion
from lazyflow.stype import Opaque
from lazyflow.request import Request, RequestPool

# required lazyflow operators
from lazyflow.operators.opLabelVolume import OpLabelVolume
from lazyflow.operators.valueProviders import OpArrayCache
from lazyflow.operators.opCompressedCache import OpCompressedCache
from lazyflow.operators.opReorderAxes import OpReorderAxes


## TODO @akreshuk documentation
class OpGraphCut(Operator):
    name = "OpGraphCut"

    # prediction maps
    Prediction = InputSlot()

    # graph cut parameter
    Beta = InputSlot(value=.2)

    # segmentation image -> graph cut segmentation
    Output = OutputSlot()

    # for internal (reordered) use
    _Output = OutputSlot()
    _FakeSlot = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpGraphCut, self).__init__(*args, **kwargs)

        opReorder = OpReorderAxes(parent=self)
        opReorder.Input.connect(self.Prediction)
        opReorder.AxisOrder.setValue('xyztc')  # vigra order
        self._opReorderPred = opReorder

        cache = OpCompressedCache(parent=self)
        cache.Input.connect(self._FakeSlot)
        self._cache = cache

        opReorder = OpReorderAxes(parent=self)
        opReorder.Input.connect(self._Output)
        self._opReorderOutput = opReorder

        self.Output.connect(self._opReorderOutput.Output)

    def setupOutputs(self):
        self._opReorderOutput.AxisOrder.setValue(self.Prediction.meta.getAxisKeys())
        self._Output.meta.assignFrom(self._opReorderPred.Output.meta)
        # output is a binary image
        self._Output.meta.dtype = np.uint8

        # fake slot provides meta data for cache
        self._FakeSlot.meta.assignFrom(self._Output.meta)
        
        # cache should hold entire c-t-slices in memory
        shape = np.asarray(self._opReorderPred.Output.meta.shape)
        t = shape[3]
        c = shape[4]
        shape[3:5] = 1
        self._cache.BlockShape.setValue(tuple(shape))

        # set up multithreading environment
        self._need = np.ones((t, c), dtype=np.bool)
        self._lock = np.empty((t, c), dtype=np.object)
        for i in range(t):
            for j in range(c):
                self._lock[i, j] = ThreadLock()

    def execute(self, slot, subindex, roi, result):
        assert slot == self._Output, "Unknown slot requested: {}".format(slot)
        self._updateCache(roi)
        req = self._cache.Output.get(roi)
        req.writeInto(result)
        req.block()

    def _updateCache(self, roi):

        beta = self.Beta.value

        # closure to be handed to the request pool
        def processSingleVolume(t, c):
            self._lock[t, c].acquire()
            if not self._need[t, c]:
                return
            start = (0, 0, 0, t, c)
            stop = self._opReorderPred.Output.meta.shape[:3] + (t+1, c+1)
            predRoi = SubRegion(self._opReorderPred.Output,
                                start=start, stop=stop)
            cacheRoi = SubRegion(self._cache.Input, start=start, stop=stop)

            ## request the prediction image ##
            pred = self._opReorderPred.Output.get(predRoi).wait()
            pred = vigra.taggedView(
                pred, axistags=self._opReorderPred.Output.meta.axistags)
            pred = pred.withAxes(*'xyz')

            data = segmentGC_fast(pred, beta)
            data = vigra.taggedView(data, axistags='xyz')
            data = data.withAxes(*'xyztc')
            # process single volume, write result to cache
            self._cache.setInSlot(self._cache.Input, (), cacheRoi,
                                  data)
            self._need[t, c] = False
            self._lock[t, c].release()

        pool = RequestPool()

        for t in range(roi.start[3], roi.stop[3]):
            for c in range(roi.start[4], roi.stop[4]):
                pool.add(Request(functools.partial(processSingleVolume, t, c)))

        logger.info("Updating graph-cut cache")
        pool.wait()
        pool.clean()
        logger.info("Graph-cut done")

    def propagateDirty(self, slot, subindex, roi):
        # all input slots affect the (global) graph cut computation

        if slot == self.Beta:
            # beta value affects the whole volume
            self._Output.setDirty(slice(None))
        elif slot == self.Prediction:
            # time-channel slices are pairwise independent
            
            # determine t, c from input volume
            t_ind = self.Prediction.meta.axistags.index('t')
            if t_ind < len(self.Prediction.meta.shape):
                t = (roi.start[t_ind], roi.stop[t_ind])
            else:
                t = (0, 1)
            c_ind = self.Prediction.meta.axistags.index('t')
            if c_ind < len(self.Prediction.meta.shape):
                c = (roi.start[c_ind], roi.stop[c_ind])
            else:
                c = (0, 1)

            # schedule slices for recomputation
            #FIXME do we need a lock here?
            self._need[t[0]:t[1], c[0]:c[1]] = True

            # set output dirty
            start = (0,)*3 + t[0:1] + c[0:1]
            stop = (0,)*3 + t[1:2] + c[1:2]
            roi = SubRegion(self._Output, start=start, stop=stop)
            self._Output.setDirty(roi)


##TODO @akreshuk documetation needed
def segmentGC_fast(pred, beta):
    nx, ny, nz = pred.shape

    numVar = pred.size
    numLabels = 2

    numberOfStates = np.ones(numVar, dtype=opengm.index_type)*numLabels
    gm = opengm.graphicalModel(numberOfStates, operator='adder')

    #Adding unary function and factors
    functions = np.zeros((numVar, 2))
    predflat = pred.reshape((numVar, 1))
    if (predflat.dtype == np.uint8):
        predflat = predflat.astype(np.float32)
        predflat = predflat/256.

    functions[:, 0] = 2*predflat[:, 0]
    functions[:, 1] = 1-2*predflat[:, 0]

    fids = gm.addFunctions(functions)
    gm.addFactors(fids, np.arange(0, numVar))

    #add one binary function (potts fuction)
    potts = opengm.PottsFunction([2, 2], 0.0, beta)
    fid = gm.addFunction(potts)

    #add binary factors
    nyz = ny*nz
    indices = np.arange(numVar,
                        dtype=np.uint32).reshape((nx, ny, nz))
    arg1 = np.concatenate([indices[:nx - 1, :, :], indices[1:, :, :]]
                            ).reshape((2, numVar - nyz)).transpose()

    arg2 = np.concatenate([indices[:, :ny - 1, :], indices[:, 1:, :]]
                            ).reshape((2, numVar - nx*nz)).transpose()

    arg3 = np.concatenate([indices[:, :, :nz - 1], indices[:, :, 1:]]
                            ).reshape((2, numVar - nx*ny)).transpose()

    gm.addFactors(fid, arg1)
    gm.addFactors(fid, arg2)
    gm.addFactors(fid, arg3)

    grcut = opengm.inference.GraphCut(gm)
    grcut.infer()
    argmin = grcut.arg()

    res = argmin.reshape((nx, ny, nz))
    return res
