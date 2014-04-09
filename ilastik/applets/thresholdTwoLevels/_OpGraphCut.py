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


## TODO documentation
class OpGraphCut(Operator):
    name = "OpGraphCut"

    # prediction maps
    Prediction = InputSlot()

    # graph cut parameter
    Beta = InputSlot(value=.2)

    ## intermediate results ##

    # segmentation image -> graph cut segmentation
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpGraphCut, self).__init__(*args, **kwargs)

        opReorder = OpReorderAxes(parent=self)
        opReorder.Input.connect(self.Prediction)
        opReorder.AxisOrder.setValue('xyztc')  # vigra order
        self._opReorderPred = opReorder

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Prediction.meta)
        self.Output.meta.dtype = np.uint8
        self.Output.meta.shape = self._opReorderPred.Output.meta.shape[:3]
        self.Output.meta.axistags = vigra.defaultAxistags('xyz')

    def execute(self, slot, subindex, roi, result):
        self._execute_graphcut(roi, result)

    def _execute_graphcut(self, roi, result):

        beta = self.Beta.value

        ## request the prediction image ##
        # add time and channel to roi (we reordered to full 'xyztc'!)
        #FIXME support time slices
        predRoi = roi.copy()
        predRoi.insertDim(3, 0, 1)  # t
        predRoi.insertDim(4, 0, 1)  # c

        pred = self._opReorderPred.Output.get(predRoi).wait()
        pred = vigra.taggedView(pred,
                                axistags=self._opReorderPred.Output.meta.axistags)
        pred = pred.withAxes(*'xyz')

        logger.info("Running global graph-cut")
        result[:] = segmentGC_fast(pred, beta)
        logger.info("Graph-cut done")

        return result

    def propagateDirty(self, slot, subindex, roi):
        # all input slots affect the (global) graph cut computation
        #FIXME time slices?
        self.Output.setDirty(slice(None))

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
