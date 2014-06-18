#!/usr/bin/env python
# coding: utf-8
# author: Markus Döring

import numpy as np
import vigra

from lazyflow.operators.opLabelVolume import OpLabelVolume, OpLabelingABC
from lazyflow.operators import OperatorWrapper, OpMultiArraySlicer
from lazyflow.rtype import SubRegion

from lazycc import OpLazyCC


class OpLabelVolumeChild(OpLabelVolume):
    def __init__(self, *args, **kwargs):
        super(OpLabelVolumeChild, self).__init__(*args, **kwargs)
        self._labelOps['lazy'] = _OpLazyCCWrapper


class _OpLazyCCWrapper(OpLabelingABC):
    name = "OpLazyConnectedComponents"
    supportedDtypes = [np.uint8, np.uint32, np.float32]

    def __init__(self, *args, **kwargs):
        super(_OpLazyCCWrapper, self).__init__(*args, **kwargs)

        opTimeSlicer = OpMultiArraySlicer(parent=self)
        opTimeSlicer.AxisFlag.setValue('t')
        opChannelSlicer = OperatorWrapper(OpMultiArraySlicer, parent=self,
                                          broadcastingSlotNames=['AxisFlag'])
        opChannelSlicer.AxisFlag.setValue('c')

        opTimeSlicer.Input.connect(self.Input)
        opChannelSlicer.Input.connect(opTimeSlicer.Slices)
        assert opChannelSlicer.Slices.level == 2

        self._opTimeSlicer = opTimeSlicer
        self._opChannelSlicer = opChannelSlicer
        self._ops = np.empty((1,), dtype=np.object)

        self._defaultChunkShape = (64, 64, 64)

    def setupOutputs(self):
        super(_OpLazyCCWrapper, self).setupOutputs()
        # clear old labeling operators
        for op in self._ops.flat:
            if op is not None:
                op.Input.disconnect()
        del self._ops

        # overwrite the default cache block shape
        shape = self._defaultChunkShape + (1, 1)
        self._cache.BlockShape.setValue(shape)

        # create new labeling operators
        c, t = self.Input.meta.shape[3:]
        ops = np.empty((c, t), dtype=np.object)
        for i in range(c):
            for j in range(t):
                op = OpLazyCC(parent=self)
                # reverse order because the outermost [] corresponds to the
                # index that was sliced last, i.e. c
                op.Input.connect(self._opChannelSlicer.Slices[j][i])
                op.ChunkShape.setValue(self._defaultChunkShape)
                # set background values
                #TODO
                ops[i, j] = op
        self._ops = ops

    def _label3d(self, roi, _, result):
        currOp = self._ops[roi.start[3], roi.start[4]]
        newRoi = SubRegion(currOp.Output,
                           start=roi.start[:3], stop=roi.stop[:3])
        req = currOp.Output.get(newRoi)
        req.writeInto(result)
        req.block()


if __name__ == "__main__":
    from lazyflow.graph import Graph
    g = Graph()
    op = OpLabelVolumeChild(graph=g)

    vol = np.zeros((200, 150, 100, 5, 2), dtype=np.uint8)
    vol = vigra.taggedView(vol, axistags='xyzct')
    op.Input.setValue(vol)
    op.Method.setValue('lazy')

    out = op.CachedOutput[...].wait()

