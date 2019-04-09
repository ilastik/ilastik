from __future__ import print_function
from builtins import range

###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#          http://ilastik.org/license/
###############################################################################

import numpy as np
import vigra
import h5py
import unittest

from numpy.testing import assert_array_equal, assert_array_almost_equal

from lazyflow.utility.testing import assertEquivalentLabeling
from lazyflow.operators.opLazyConnectedComponents import OpLazyConnectedComponents as OpLazyCC

from lazyflow.graph import Graph
from lazyflow.operator import Operator
from lazyflow.slot import InputSlot, OutputSlot
from lazyflow.rtype import SubRegion

from lazyflow.operators import OpArrayPiper, OpCompressedCache


class DirtyAssert(Operator):
    Input = InputSlot()

    def willBeDirty(self, t, c):
        self._t = t
        self._c = c

    def propagateDirty(self, slot, subindex, roi):
        t_ind = self.Input.meta.axistags.index("t")
        c_ind = self.Input.meta.axistags.index("c")
        assert roi.start[t_ind] == self._t
        assert roi.start[c_ind] == self._c
        assert roi.stop[t_ind] == self._t + 1
        assert roi.stop[c_ind] == self._c + 1
        raise self.PropagateDirtyCalled()

    class PropagateDirtyCalled(Exception):
        pass


class TestOpLazyCC(unittest.TestCase):
    def setup_method(self, method):
        pass

    def testCorrectLabeling(self):
        vol = np.zeros((1000, 100, 10))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags="zyx")

        vol[20:40, 10:30, 2:4] = 1

        op = OpLazyCC(graph=Graph())
        op.Input.setValue(vol)
        op.ChunkShape.setValue((100, 10, 10))

        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags=op.Output.meta.axistags)

        assertEquivalentLabeling(vol, out)

    def testSingletonZ(self):
        vol = np.zeros((1, 70, 82), dtype=np.uint8)
        vol = vigra.taggedView(vol, axistags="zyx")

        blocks = np.zeros(vol.shape, dtype=np.uint8)
        blocks[:, 30:50, 40:60] = 1
        blocks[:, 60:70, 30:40] = 3
        blocks = vigra.taggedView(blocks, axistags="zyx")

        vol[blocks > 0] = 255

        op = OpLazyCC(graph=Graph())
        op.ChunkShape.setValue((1, 25, 30))
        op.Input.setValue(vol)

        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags=op.Output.meta.axistags)
        np.set_printoptions(threshold=np.nan, linewidth=200)
        assertEquivalentLabeling(blocks, out)

    def testLazyness(self):
        g = Graph()
        vol = np.asarray(
            [
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
            ],
            dtype=np.uint8,
        )
        vol = vigra.taggedView(vol, axistags="yx").withAxes(*"zyx")
        chunkShape = (1, 3, 3)

        opCount = OpExecuteCounter(graph=g)
        opCount.Input.setValue(vol)

        opCache = OpCompressedCache(graph=g)
        opCache.Input.connect(opCount.Output)
        opCache.BlockShape.setValue(chunkShape)

        op = OpLazyCC(graph=g)
        op.Input.connect(opCache.Output)
        op.ChunkShape.setValue(chunkShape)

        out = op.Output[:, :3, :3].wait()
        n = 3
        assert opCount.numCalls <= n, "Executed {} times (allowed: {})".format(opCount.numCalls, n)

    def testContiguousLabels(self):
        g = Graph()
        vol = np.asarray(
            [
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, 1, 1, 0, 0, 0, 0],
                [0, 1, 0, 1, 0, 0, 0, 0, 0],
                [0, 1, 0, 1, 0, 0, 0, 0, 0],
                [0, 1, 1, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
            ],
            dtype=np.uint8,
        )
        vol = vigra.taggedView(vol, axistags="yx").withAxes(*"zyx")
        chunkShape = (1, 3, 3)

        op = OpLazyCC(graph=g)
        op.Input.setValue(vol)
        op.ChunkShape.setValue(chunkShape)

        out1 = op.Output[:, :3, :3].wait()
        out2 = op.Output[:, 7:, 7:].wait()
        assert max(out1.max(), out2.max()) == 2

    def testConsistency(self):
        vol = np.zeros((1000, 100, 10))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags="zyx")
        vol[:200, ...] = 1
        vol[800:, ...] = 1

        op = OpLazyCC(graph=Graph())
        op.Input.setValue(vol)
        op.ChunkShape.setValue((100, 10, 10))

        out1 = op.Output[:500, ...].wait()
        out2 = op.Output[500:, ...].wait()
        assert out1[0, 0, 0] != out2[499, 0, 0]

    def testCircular(self):
        g = Graph()

        op = OpLazyCC(graph=g)
        op.ChunkShape.setValue((3, 3, 1))

        vol = np.asarray(
            [
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 1, 1, 0, 1, 1, 1, 0],
                [0, 1, 0, 0, 0, 0, 0, 1, 0],
                [0, 1, 0, 0, 0, 0, 0, 1, 0],
                [0, 1, 0, 0, 0, 0, 0, 1, 0],
                [0, 1, 0, 0, 0, 0, 0, 1, 0],
                [0, 1, 0, 0, 0, 0, 0, 1, 0],
                [0, 1, 1, 1, 1, 1, 1, 1, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
            ],
            dtype=np.uint8,
        )
        vol1 = vigra.taggedView(vol, axistags="yx")
        vol2 = vigra.taggedView(vol, axistags="xy")
        vol3 = vigra.taggedView(np.flipud(vol), axistags="yx")
        vol4 = vigra.taggedView(np.flipud(vol), axistags="xy")

        for v in (vol1, vol2, vol3, vol4):
            op.Input.setValue(v)
            for x in [0, 3, 6]:
                for y in [0, 3, 6]:
                    if x == 3 and y == 3:
                        continue
                    op.Input.setDirty(slice(None))
                    out = op.Output[x : x + 3, y : y + 3].wait()
                    print(out.squeeze())
                    assert out.max() == 1

    def testParallelConsistency(self):
        vol = np.zeros((1000, 100, 10))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags="zyx")
        vol[:200, ...] = 1
        vol[800:, ...] = 1

        op = OpLazyCC(graph=Graph())
        op.Input.setValue(vol)
        op.ChunkShape.setValue((100, 10, 10))

        req1 = op.Output[:50, :10, :]
        req2 = op.Output[950:, 90:, :]
        req1.submit()
        req2.submit()

        out1 = req1.wait()
        out2 = req2.wait()

        assert np.all(out1 != out2)

    def testSetDirty(self):
        g = Graph()
        vol = np.zeros((200, 100, 10))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags="zyx")
        vol[:200, ...] = 1
        vol[800:, ...] = 1

        op = OpLazyCC(graph=g)
        op.ChunkShape.setValue((100, 20, 5))
        op.Input.setValue(vol)

        opCheck = DirtyAssert(graph=g)
        opCheck.Input.connect(op.Output)

        out = op.Output[:100, :20, :5].wait()

        roi = SubRegion(op.Input, start=(0, 0, 0), stop=(200, 100, 10))
        with self.assertRaises(PropagateDirtyCalled):
            op.Input.setDirty(roi)

    def testDirtyPropagation(self):
        g = Graph()
        vol = np.asarray([[0, 0, 0, 0], [0, 0, 1, 1], [0, 1, 0, 1], [0, 1, 0, 1]], dtype=np.uint8)
        vol = vigra.taggedView(vol, axistags="yx").withAxes(*"zyx")

        chunkShape = (1, 2, 2)

        opCache = OpCompressedCache(graph=g)
        opCache.Input.setValue(vol)
        opCache.BlockShape.setValue(chunkShape)

        op = OpLazyCC(graph=g)
        op.Input.connect(opCache.Output)
        op.ChunkShape.setValue(chunkShape)

        out1 = op.Output[:, :2, :2].wait()
        assert np.all(out1 == 0)

        opCache.Input[0:1, 0:1, 0:1] = np.asarray([[[1]]], dtype=np.uint8)

        out2 = op.Output[:, :1, :1].wait()
        assert np.all(out2 > 0)

    @unittest.skip("too costly")
    def testFromDataset(self):
        shape = (500, 500, 500)

        vol = np.zeros(shape, dtype=np.uint8)
        vol = vigra.taggedView(vol, axistags="zxy")

        centers = [(45, 15), (45, 350), (360, 50)]
        extent = (10, 10)
        shift = (1, 1)
        zrange = np.arange(0, 20)
        zsteps = np.arange(5, 455, 50)

        for x, y in centers:
            for z in zsteps:
                for t in zrange:
                    sx = x + t * shift[0]
                    sy = y + t * shift[1]
                    vol[zsteps + t, sx - extent[0] : sx + extent[0], sy - extent[0] : sy + extent[0]] = 255

        vol = vol.withAxes(*"zyx")

        # all at once
        op = OpLazyCC(graph=Graph())
        op.Input.setValue(vol)
        op.ChunkShape.setValue((64, 64, 64))
        out1 = op.Output[...].wait()
        out2 = vigra.analysis.labelVolumeWithBackground(vol)
        assertEquivalentLabeling(out1.view(np.ndarray), out2.view(np.ndarray))

    @unittest.skip("too costly")
    def testFromDataset2(self):
        shape = (500, 500, 500)

        vol = np.zeros(shape, dtype=np.uint8)
        vol = vigra.taggedView(vol, axistags="zxy")

        centers = [(45, 15), (45, 350), (360, 50)]
        extent = (10, 10)
        shift = (1, 1)
        zrange = np.arange(0, 20)
        zsteps = np.arange(5, 455, 50)

        for x, y in centers:
            for z in zsteps:
                for t in zrange:
                    sx = x + t * shift[0]
                    sy = y + t * shift[1]
                    vol[zsteps + t, sx - extent[0] : sx + extent[0], sy - extent[0] : sy + extent[0]] = 255

        vol = vol.withAxes(*"zyx")

        # step by step
        op = OpLazyCC(graph=Graph())
        op.Input.setValue(vol)
        op.ChunkShape.setValue((64, 64, 64))
        out1 = np.zeros(op.Output.meta.shape, dtype=op.Output.meta.dtype)
        for z in reversed(list(range(500))):
            out1[..., z : z + 1] = op.Output[..., z : z + 1].wait()
        vigra.writeHDF5(out1, "/tmp/data.h5", "data")
        out2 = vigra.analysis.labelVolumeWithBackground(vol)
        assertEquivalentLabeling(out1.view(np.ndarray), out2.view(np.ndarray))

    @unittest.skip("temporarily disabled")
    def testParallel(self):
        shape = (100, 100, 100)

        vol = np.ones(shape, dtype=np.uint8)
        vol = vigra.taggedView(vol, axistags="zyx")

        op = OpLazyCC(graph=Graph())
        op.Input.setValue(vol)
        op.ChunkShape.setValue((50, 50, 1))

        reqs = [
            op.Output[..., 0],
            op.Output[..., 0],
            op.Output[..., 99],
            op.Output[..., 99],
            op.Output[0, ...],
            op.Output[0, ...],
            op.Output[99, ...],
            op.Output[99, ...],
            op.Output[:, 0, ...],
            op.Output[:, 0, ...],
            op.Output[:, 99, ...],
            op.Output[:, 99, ...],
        ]

        [r.submit() for r in reqs]

        out = [r.wait() for r in reqs]
        for i in range(len(out) - 1):
            try:
                assert_array_equal(out[i].squeeze(), out[i + 1].squeeze())
            except AssertionError:
                raise

    def testMultiDimSame(self):
        vol = np.zeros((2, 10, 10, 1, 3))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags="tzyxc")

        vol[:, 3:7, 3:7, :] = 1

        op = OpLazyCC(graph=Graph())
        op.Input.setValue(vol)
        op.ChunkShape.setValue((5, 5, 1))

        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags=op.Output.meta.axistags)
        assert_array_equal(out[0, ...], out[1, ...])

    def testMultiDimDiff(self):
        vol = np.zeros((2, 10, 10, 1, 3))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags="tzyxc")

        vol[0, 3:7, 3:7, :] = 1
        vol[1, 7:, 7:, :] = 1

        op = OpLazyCC(graph=Graph())
        op.Input.setValue(vol)
        op.ChunkShape.setValue((5, 5, 1))

        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags=op.Output.meta.axistags)
        assert np.all(out[1, :7, :7, ...] == 0)

    def testStrangeDim(self):
        vol = np.zeros((2, 10, 10, 1, 3))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags="tzyxc")

        vol[:, 3:7, 3:7, :] = 1

        strangeVol = vol.withAxes(*"ytxcz")

        op = OpLazyCC(graph=Graph())
        op.Input.setValue(strangeVol)
        op.ChunkShape.setValue((5, 5, 1))

        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags=op.Output.meta.axistags)
        out = out.withAxes(*"tzyxc")
        assert np.all(out[1, 3:7, 3:7, ...] > 0)

    def testHDF5(self):
        vol = np.zeros((1000, 100, 10))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags="xyz")
        vol[:200, ...] = 1
        vol[800:, ...] = 1

        op = OpLazyCC(graph=Graph())
        op.Input.setValue(vol)
        op.ChunkShape.setValue((100, 10, 10))

        blocks = op.CleanBlocks[0].wait()[0]
        assert len(blocks) == 0

        out1 = op.Output[:200, ...].wait()
        blocks = op.CleanBlocks[0].wait()[0]
        assert len(blocks) == 20

        # prepare hdf5 file
        f = h5py.File("temp.h5", driver="core", backing_store=False)

        for block in blocks:
            req = op.OutputHdf5(start=block[0], stop=block[1])
            req.writeInto(f)
            req.block()

        # fill whole cache
        op.Output[...].wait()

        f.create_dataset("TEST", shape=(1, 1000, 100, 10, 1), dtype=np.uint32)
        ds = f["TEST"]
        ds[0, ..., 0] = 23

        op.InputHdf5[0:1, 0:1000, 0:100, 0:10, 0:1] = ds
        blocks = op.CleanBlocks[0].wait()[0]
        assert len(blocks) == 100, "Got {} clean blocks (expected {}".format(len(blocks), 100)


class OpExecuteCounter(OpArrayPiper):
    def __init__(self, *args, **kwargs):
        self.numCalls = 0
        super(OpExecuteCounter, self).__init__(*args, **kwargs)

    def execute(self, slot, subindex, roi, result):
        self.numCalls += 1
        super(OpExecuteCounter, self).execute(slot, subindex, roi, result)


class DirtyAssert(Operator):
    Input = InputSlot()

    def propagateDirty(self, slot, subindex, roi):
        assert np.all(roi.start == 0)
        assert np.all(roi.stop == self.Input.meta.shape)
        raise PropagateDirtyCalled()


class PropagateDirtyCalled(Exception):
    pass


if __name__ == "__main__":
    # make the program quit on Ctrl+C
    import signal

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)

#     vol = np.zeros((1000, 100, 10))
#     vol[300:600, 40:70, 2:5] = 255
#     vol = vol.astype(np.uint8)
#     vol = vigra.taggedView(vol, axistags='zyx')
#
#     op = OpLazyCC(graph=Graph())
#     op.Input.setValue(vol)
#     op.ChunkShape.setValue((100, 10, 10))
#
#     out = op.Output[...].wait()
