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
#           http://ilastik.org/license.html
##############################################################################

# basic python modules
import functools
import logging
logger = logging.getLogger(__name__)  # noqa
logger.setLevel(logging.DEBUG)  # noqa
logger.addHandler(logging.NullHandler())  # noqa
# from threading import Lock as ThreadLock

# required numerical modules
import numpy as np
import vigra
import opengm

# basic lazyflow types
from lazyflow.operator import Operator
from lazyflow.slot import InputSlot, OutputSlot
from lazyflow.rtype import SubRegion
# from lazyflow.stype import Opaque
# from lazyflow.request import Request, RequestPool

# required lazyflow operators
from lazyflow.operators.opCompressedCache import OpCompressedCache
from lazyflow.operators.opReorderAxes import OpReorderAxes

from lazyflow.graph import Graph

from lazyflow.utility.reorderAxesDecorator import reorder, reorder_options


# This operator implements an interface to compute Graph Cut segmentations
# via the OpenGM library (http://hci.iwr.uni-heidelberg.de/opengm2/).
# Potts model is assumed, with a 4-neighborhood for 2D data and
# a 6-neighborhood for 3D data. The prediction maps in the input
# are used as unaries and are taken "as is", without an additional
# Log operation (TODO: make optional log).
#  - this operator assumes tzyxc axis order
#  - only ROIs with 1 channel, 1 time slice are valid for slot Output
#  - requests to slot CachedOutput are guaranteed to be consistent
@reorder
@reorder_options('tzyxc', ['Beta', 'Output', 'CachedOutput'])
class OpGraphCut(Operator):
    name = "OpGraphCut"

    # prediction maps
    Prediction = InputSlot()

    # graph cut parameter, usually called lambda
    Beta = InputSlot(value=.2)

    # labeled segmentation image
    #     i=0: background
    #     i>0: connected foreground object i
    Output = OutputSlot()
    CachedOutput = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpGraphCut, self).__init__(*args, **kwargs)
        # print('supertype', type(OpGraphCut))
        # print('superobj', self)
        self._cache = None

    def setupOutputs(self):
        # sanity checks
        shape = self.Prediction.meta.shape
        assert len(shape) == 5,\
            "Prediction maps must be a full 5d volume (tzyxc)"
        tags = self.Prediction.meta.getAxisKeys()
        tags = "".join(tags)
        assert tags == 'tzyxc',\
            "Prediction maps have wrong axes order" \
            "(expected: tzyxc, got: {})".format(tags)

        if self._cache is not None:
            self.CachedOutput.disconnect()
            self._cache.cleanUp()
            self._cache = None

        cache = OpCompressedCache(parent=self)
        cache.name = "{}._cache".format(self.name)
        cache.Input.connect(self.Output)
        self._cache = cache
        self.CachedOutput.connect(self._cache.Output)

        self.Output.meta.assignFrom(self.Prediction.meta)
        # output is a label image
        self.Output.meta.dtype = np.uint32

        # cache should hold entire c-t-slices in memory
        shape = list(self.Prediction.meta.shape)
        shape[0] = 1
        shape[4] = 1
        self._cache.BlockShape.setValue(tuple(shape))

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output, "Unknown slot requested: {}".format(slot)
        for i in (0, 4):
            assert roi.stop[i] - roi.start[i] == 1,\
                "Invalid roi for graph-cut: {}".format(str(roi))

        # request the prediction image
        pred = self.Prediction.get(roi).wait()
        pred = vigra.taggedView(pred, axistags=self.Prediction.meta.axistags)
        pred = pred.withAxes(*'zyx')

        # prepare result
        resView = vigra.taggedView(result, axistags=self.Output.meta.axistags)
        resView = resView.withAxes(*'zyx')

        logger.info("Executing graph cut ... (this might take a while)")
        threshold_binary = segmentGC(pred, self.Beta.value)
        threshold_binary = vigra.taggedView(threshold_binary, 'zyx')
        logger.info("Graph-cut done")

        # label the segmentation so that this operator is consistent with
        # the other thresholding operators
        vigra.analysis.labelVolumeWithBackground(
            threshold_binary.astype(np.uint8), out=resView)

    def propagateDirty(self, slot, subindex, roi):
        # all input slots affect the (global) graph cut computation

        if slot == self.Beta:
            # beta value affects the whole volume
            self.Output.setDirty(slice(None))
        elif slot == self.Prediction:
            # time-channel slices are pairwise independent

            # determine t, c from input volume
            t_ind = 0
            c_ind = 4
            t = (roi.start[t_ind], roi.stop[t_ind])
            c = (roi.start[c_ind], roi.stop[c_ind])

            # set output dirty
            start = t[0:1] + (0,) * 3 + c[0:1]
            stop = t[1:2] + self.Output.meta.shape[1:4] + c[1:2]
            roi = SubRegion(self.Output, start=start, stop=stop)
            self.Output.setDirty(roi)


def segmentGC(pred, beta):
    '''
       This function implements a call to the standard Graph Cut segmentation
       in the OpenGM library (http://hci.iwr.uni-heidelberg.de/opengm2/).
       Potts model is assumed, with a 4-neighborhood for 2D data and a 6-neighborhood
       for 3D data to define the pairwise terms.
       Parameters:
       -- pred - the unary terms, used directly (no Log applied, do it outside if needed)
          This input is assumed to be 3D!
       -- beta - the weight of the pairwise potentials, usually called lambda
       Return:
       -- binary volume, as produced by OpenGM

    '''
    nz, ny, nx = pred.shape

    numVar = pred.size
    numLabels = 2

    numberOfStates = np.ones(numVar, dtype=opengm.index_type) * numLabels
    gm = opengm.graphicalModel(numberOfStates, operator='adder')

    # Adding unary function and factors
    functions = np.zeros((numVar, 2))
    predflat = pred.reshape((numVar, 1))
    if (predflat.dtype == np.uint8):
        predflat = predflat.astype(np.float32)
        predflat = predflat / 256.

    functions[:, 0] = predflat[:, 0]
    functions[:, 1] = 1 - predflat[:, 0]

    unary_fids = gm.addFunctions(functions)
    gm.addFactors(unary_fids, np.arange(0, numVar))

    # add one binary function (potts fuction)
    potts = opengm.PottsFunction([2, 2], 0.0, beta)
    binary_fid = gm.addFunction(potts)

    # add binary factors
    indices = np.arange(numVar, dtype=np.uint32).reshape((nz, ny, nx))
    z_edges = np.concatenate([indices[:nz - 1, :, :], indices[1:, :, :]]
                             ).reshape((2, (nz - 1) * ny * nx)).transpose()
    y_edges = np.concatenate([indices[:, :ny - 1, :], indices[:, 1:, :]]
                             ).reshape((2, nz * (ny - 1) * nx)).transpose()
    x_edges = np.concatenate([indices[:, :, :nx - 1], indices[:, :, 1:]]
                             ).reshape((2, nz * ny * (nx - 1))).transpose()

    gm.addFactors(binary_fid, z_edges)
    gm.addFactors(binary_fid, y_edges)
    gm.addFactors(binary_fid, x_edges)

    grcut = opengm.inference.GraphCut(gm)
    grcut.infer()
    argmin = grcut.arg()

    res = argmin.reshape((nz, ny, nx))
    if hasattr(pred, 'axistags'):
        res = vigra.taggedView(res, pred.axistags)
    return res


if __name__ == '__main__':
    print('main')
    g = Graph()
    test = OpGraphCut(graph=g)
    print(test.Prediction)
    print('dict', test.__dict__)

    # test2 = ReorderedOperator(OpGraphCut, graph=g)
    # print(test2.Prediction)

    print(test.name)
    # print(test.__getitem__)
    # print(test.__iter__)
    # print(test._callbackInserted)
    # print(test._callbackPreRemove)
    # print(test._callbackPostRemoved)
    # print(test._callbackConnect)
    print(test.propagateDirty)
    # print(test._insertInnerOperator)
    # print(test.handleEarlyDisconnect)
    # print(test._removeInnerOperator)
    print(test._setupOutputs)
    print(test.execute)
    print(test.setInSlot)
