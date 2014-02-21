import numpy as np
import vigra

import unittest

from lazyflow.graph import Graph
from lazyflow.operators import OpLabelVolume
from lazyflow.operator import Operator
from lazyflow.slot import InputSlot, OutputSlot
from lazyflow.rtype import SubRegion

from numpy.testing import assert_array_equal, assert_array_almost_equal

try:
    import blockedarray
except ImportError:
    have_blocked = False
else:
    have_blocked = True


class TestVigra(unittest.TestCase):

    def setUp(self):
        self.method = np.asarray(['vigra'], dtype=np.object)

    def testSimpleUsage(self):
        vol = np.random.randint(255, size=(1000, 100, 10))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags='xyz')

        op = OpLabelVolume(graph=Graph())
        op.Method.setValue(self.method)
        op.Input.setValue(vol)

        out = op.Output[...].wait()

        assert_array_equal(vol.shape, out.shape)

    def testCorrectLabeling(self):
        vol = np.zeros((1000, 100, 10))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags='xyz')

        vol[20:40, 10:30, 2:4] = 1

        op = OpLabelVolume(graph=Graph())
        op.Method.setValue(self.method)
        op.Input.setValue(vol)

        out = op.Output[...].wait()
        tags = op.Output.meta.getTaggedShape()
        out = vigra.taggedView(out, axistags="".join([s for s in tags]))

        assertEquivalentLabeling(vol, out)

    def testMultiDim(self):
        vol = np.zeros((82, 70, 75, 5, 5), dtype=np.uint8)
        vol = vigra.taggedView(vol, axistags='xyzct')

        blocks = np.zeros(vol.shape, dtype=np.uint8)
        blocks[30:50, 40:60, 50:70, 2:4, 3:5] = 1
        blocks[30:50, 40:60, 50:70, 2:4, 0:2] = 2
        blocks[60:70, 30:40, 10:33, :, :] = 3

        vol[blocks == 1] = 255
        vol[blocks == 2] = 255
        vol[blocks == 3] = 255

        op = OpLabelVolume(graph=Graph())
        op.Method.setValue(self.method)
        op.Input.setValue(vol)

        out = op.Output[...].wait()
        tags = op.Output.meta.getTaggedShape()
        print(tags)
        out = vigra.taggedView(out, axistags="".join([s for s in tags]))

        for c in range(out.shape[3]):
            for t in range(out.shape[4]):
                print("t={}, c={}".format(t, c))
                assertEquivalentLabeling(blocks[..., c, t], out[..., c, t])

    def testConsistency(self):
        vol = np.zeros((1000, 100, 10))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags='xyz')
        vol[:200, ...] = 1
        vol[800:, ...] = 1

        op = OpLabelVolume(graph=Graph())
        op.Method.setValue(self.method)
        op.Input.setValue(vol)

        out1 = op.Output[:500, ...].wait()
        out2 = op.Output[500:, ...].wait()
        assert out1[0, 0, 0] != out2[499, 0, 0]

    def testSetDirty(self):
        g = Graph()
        vol = np.zeros((5, 2, 200, 100, 10))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags='tcxyz')
        vol[:200, ...] = 1
        vol[800:, ...] = 1

        op = OpLabelVolume(graph=g)
        op.Method.setValue(self.method)
        op.Input.setValue(vol)

        opCheck = DirtyAssert(graph=g)
        opCheck.Input.connect(op.Output)
        opCheck.willBeDirty(1, 1)

        out = op.Output[...].wait()

        roi = SubRegion(op.Input,
                        start=(1, 1, 0, 0, 0),
                        stop=(2, 2, 200, 100, 10))
        with self.assertRaises(PropagateDirtyCalled):
            op.Input.setDirty(roi)

        opCheck.Input.disconnect()
        opCheck.Input.connect(op.CachedOutput)
        opCheck.willBeDirty(1, 1)

        out = op.Output[...].wait()

        roi = SubRegion(op.Input,
                        start=(1, 1, 0, 0, 0),
                        stop=(2, 2, 200, 100, 10))
        with self.assertRaises(PropagateDirtyCalled):
            op.Input.setDirty(roi)

    def testUnsupported(self):
        g = Graph()
        vol = np.zeros((50, 50))
        vol = vol.astype(np.int16)
        vol = vigra.taggedView(vol, axistags='xy')
        vol[:200, ...] = 1
        vol[800:, ...] = 1

        op = OpLabelVolume(graph=g)
        op.Method.setValue(self.method)
        with self.assertRaises(ValueError):
            op.Input.setValue(vol)

    def testBackground(self):
        vol = np.zeros((1000, 100, 10))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags='xyz')

        vol[20:40, 10:30, 2:4] = 1

        op = OpLabelVolume(graph=Graph())
        op.Method.setValue(self.method)
        op.Background.setValue(1)
        op.Input.setValue(vol)

        out = op.Output[...].wait()
        tags = op.Output.meta.getTaggedShape()
        out = vigra.taggedView(out, axistags="".join([s for s in tags]))

        assertEquivalentLabeling(1-vol, out)

        vol = vol.withAxes(*'xyzct')
        vol = np.concatenate(3*(vol,), axis=3)
        vol = np.concatenate(4*(vol,), axis=4)
        vol = vigra.taggedView(vol, axistags='xyzct')
        assert len(vol.shape) == 5
        assert vol.shape[3] == 3
        assert vol.shape[4] == 4
        #op = OpLabelVolume(graph=Graph())
        op.Method.setValue(self.method)
        bg = np.asarray([[1, 0, 1, 0],
                         [0, 1, 0, 1],
                         [1, 0, 0, 1]], dtype=np.uint8)
        bg = vigra.taggedView(bg, axistags='ct')
        assert len(bg.shape) == 2
        assert bg.shape[0] == 3
        assert bg.shape[1] == 4
        op.Background.setValue(bg)
        op.Input.setValue(vol)

        for c in range(bg.shape[0]):
            for t in range(bg.shape[1]):
                out = op.Output[..., c, t].wait()
                out = vigra.taggedView(out, axistags=op.Output.meta.axistags)
                if bg[c, t]:
                    assertEquivalentLabeling(1-vol[..., c, t], out.squeeze())
                else:
                    assertEquivalentLabeling(vol[..., c, t], out.squeeze())


@unittest.skipIf(not have_blocked, "Cannot test blockedarray because you don't have the module")
class TestBlocked(TestVigra):

    def setUp(self):
        self.method = np.asarray(['blocked'], dtype=np.object)

    @unittest.skip("Not implemented yet")
    def testUnsupported(self):
        pass

    @unittest.skip("Not implemented yet")
    def testBackground(self):
        pass


def assertEquivalentLabeling(x, y):
    assert np.all(x.shape == y.shape),\
        "Shapes do not agree ({} vs {})".format(x.shape, y.shape)

    # identify labels used in x
    labels = set(x.flat)
    for label in labels:
        if label == 0:
            continue
        idx = np.where(x == label)
        block = y[idx]
        # check that labels are the same
        an_index = [a[0] for a in idx]
        print("Inspecting block of shape {} at".format(block.shape))
        print(an_index)
        assert np.all(block == block[0]),\
            "Block at {} has multiple labels".format(an_index)
        # check that nothing else is labeled with this label
        m = block.size
        n = len(np.where(y == block[0])[0])
        assert m == n, "Label {} is used somewhere else.".format(label)


class DirtyAssert(Operator):
    Input = InputSlot()

    def willBeDirty(self, t, c):
        self._t = t
        self._c = c

    def propagateDirty(self, slot, subindex, roi):
        t_ind = self.Input.meta.axistags.index('t')
        c_ind = self.Input.meta.axistags.index('c')
        assert roi.start[t_ind] == self._t
        assert roi.start[c_ind] == self._c
        assert roi.stop[t_ind] == self._t+1
        assert roi.stop[c_ind] == self._c+1
        raise PropagateDirtyCalled()


class PropagateDirtyCalled(Exception):
    pass
