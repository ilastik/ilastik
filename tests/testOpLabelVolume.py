from __future__ import print_function
from builtins import range
import numpy as np
import vigra

import unittest
import weakref
import gc

from lazyflow.graph import Graph
from lazyflow.operators import OpLabelVolume, OpArrayPiper
from lazyflow.operator import Operator
from lazyflow.slot import InputSlot, OutputSlot
from lazyflow.rtype import SubRegion
from lazyflow.utility.testing import assertEquivalentLabeling
from lazyflow.operators.cacheMemoryManager import CacheMemoryManager

from numpy.testing import assert_array_equal

from lazyflow.operators.opLabelVolume import haveBlocked


class TestVigra(unittest.TestCase):
    def setup_method(self, method):
        self.method = np.asarray(["vigra"], dtype=np.object)

    def testSimpleUsage(self):
        vol = np.random.randint(255, size=(100, 30, 4))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags="xyz")

        op = OpLabelVolume(graph=Graph())
        op.Method.setValue(self.method)
        op.Input.setValue(vol)

        out = op.Output[...].wait()

        assert_array_equal(vol.shape, out.shape)

    def testCorrectLabeling(self):
        vol = np.zeros((1000, 100, 10))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags="xyz")

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
        vol = vigra.taggedView(vol, axistags="xyzct")

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

    def testSingletonZ(self):
        vol = np.zeros((82, 70, 1, 5, 5), dtype=np.uint8)
        vol = vigra.taggedView(vol, axistags="xyzct")

        blocks = np.zeros(vol.shape, dtype=np.uint8)
        blocks[30:50, 40:60, :, 2:4, 3:5] = 1
        blocks[30:50, 40:60, :, 2:4, 0:2] = 2
        blocks[60:70, 30:40, :, :, :] = 3

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
        vol = vigra.taggedView(vol, axistags="xyz")
        vol[:200, ...] = 1
        vol[800:, ...] = 1

        op = OpLabelVolume(graph=Graph())
        op.Method.setValue(self.method)
        op.Input.setValue(vol)

        out1 = op.CachedOutput[:500, ...].wait()
        out2 = op.CachedOutput[500:, ...].wait()
        assert out1[0, 0, 0] != out2[499, 0, 0]

    def testNoRecomputation(self):
        g = Graph()

        vol = np.zeros((1000, 100, 10))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags="xyz")
        vol[:200, ...] = 1
        vol[800:, ...] = 1

        opCount = CountExecutes(graph=g)
        opCount.Input.setValue(vol)

        op = OpLabelVolume(graph=g)
        op.Method.setValue(self.method)
        op.Input.connect(opCount.Output)

        out1 = op.CachedOutput[:500, ...].wait()
        out2 = op.CachedOutput[500:, ...].wait()

        assert opCount.numExecutes == 1

    def testCorrectBlocking(self):
        g = Graph()
        c, t = 2, 3
        vol = np.zeros((1000, 100, 10, 2, 3))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags="xyzct")
        vol[:200, ...] = 1
        vol[800:, ...] = 1

        opCount = CountExecutes(graph=g)
        opCount.Input.setValue(vol)

        op = OpLabelVolume(graph=g)
        op.Method.setValue(self.method)
        op.Input.connect(opCount.Output)

        out1 = op.CachedOutput[:500, ...].wait()
        out2 = op.CachedOutput[500:, ...].wait()

        assert opCount.numExecutes == c * t

    def testThreadSafety(self):
        g = Graph()

        vol = np.zeros((1000, 100, 10))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags="xyz")
        vol[:200, ...] = 1
        vol[800:, ...] = 1

        opCount = CountExecutes(graph=g)
        opCount.Input.setValue(vol)

        op = OpLabelVolume(graph=g)
        op.Method.setValue(self.method)
        op.Input.connect(opCount.Output)

        reqs = [op.CachedOutput[...] for i in range(4)]
        [r.submit() for r in reqs]
        [r.block() for r in reqs]
        assert opCount.numExecutes == 1, "Parallel requests to CachedOutput resulted in recomputation " "({}/4)".format(
            opCount.numExecutes
        )

        # reset numCounts
        opCount.numExecutes = 0

        reqs = [op.Output[250 * i : 250 * (i + 1), ...] for i in range(4)]
        [r.submit() for r in reqs]
        [r.block() for r in reqs]
        assert opCount.numExecutes == 4, "Not all requests to Output were computed on demand " "({}/4)".format(
            opCount.numExecutes
        )

    def testSetDirty(self):
        g = Graph()
        vol = np.zeros((5, 2, 200, 100, 10))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags="tcxyz")
        vol[:200, ...] = 1
        vol[800:, ...] = 1

        op = OpLabelVolume(graph=g)
        op.Method.setValue(self.method)
        op.Input.setValue(vol)

        opCheck = DirtyAssert(graph=g)
        opCheck.Input.connect(op.Output)
        opCheck.willBeDirty(1, 1)

        roi = SubRegion(op.Input, start=(1, 1, 0, 0, 0), stop=(2, 2, 200, 100, 10))
        with self.assertRaises(PropagateDirtyCalled):
            op.Input.setDirty(roi)

        opCheck.Input.disconnect()
        opCheck.Input.connect(op.CachedOutput)
        opCheck.willBeDirty(1, 1)

        out = op.Output[...].wait()

        roi = SubRegion(op.Input, start=(1, 1, 0, 0, 0), stop=(2, 2, 200, 100, 10))
        with self.assertRaises(PropagateDirtyCalled):
            op.Input.setDirty(roi)

    def testUnsupported(self):
        g = Graph()
        vol = np.zeros((50, 50))
        vol = vol.astype(np.int16)
        vol = vigra.taggedView(vol, axistags="xy")
        vol[:200, ...] = 1
        vol[800:, ...] = 1

        op = OpLabelVolume(graph=g)
        op.Method.setValue(self.method)
        with self.assertRaises(ValueError):
            op.Input.setValue(vol)

    def testBackground(self):
        vol = np.zeros((1000, 100, 10))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags="xyz")

        vol[20:40, 10:30, 2:4] = 1

        op = OpLabelVolume(graph=Graph())
        op.Method.setValue(self.method)
        op.Background.setValue(1)
        op.Input.setValue(vol)

        out = op.Output[...].wait()
        tags = op.Output.meta.getTaggedShape()
        out = vigra.taggedView(out, axistags="".join([s for s in tags]))

        assert np.all(out[20:40, 10:30, 2:4] == 0)
        assertEquivalentLabeling(1 - vol, out)

        vol = vol.withAxes(*"xyzct")
        vol = np.concatenate(3 * (vol,), axis=3)
        vol = np.concatenate(4 * (vol,), axis=4)
        vol = vigra.taggedView(vol, axistags="xyzct")
        assert len(vol.shape) == 5
        assert vol.shape[3] == 3
        assert vol.shape[4] == 4
        # op = OpLabelVolume(graph=Graph())
        op.Method.setValue(self.method)
        bg = np.asarray([[1, 0, 1, 0], [0, 1, 0, 1], [1, 0, 0, 1]], dtype=np.uint8)
        bg = vigra.taggedView(bg, axistags="ct")
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
                    assertEquivalentLabeling(1 - vol[..., c, t], out.squeeze())
                else:
                    assertEquivalentLabeling(vol[..., c, t], out.squeeze())

    def testCleanup(self):
        try:
            CacheMemoryManager().disable()

            sampleData = np.random.randint(0, 256, size=(50, 30, 10))
            sampleData = sampleData.astype(np.uint8)
            sampleData = vigra.taggedView(sampleData, axistags="xyz")

            graph = Graph()
            opData = OpArrayPiper(graph=graph)
            opData.Input.setValue(sampleData)

            op = OpLabelVolume(graph=graph)
            op.Input.connect(opData.Output)
            x = op.Output[...].wait()
            op.Input.disconnect()
            op.cleanUp()

            r = weakref.ref(op)
            del op
            gc.collect()
            ref = r()
            if ref is not None:
                for i, o in enumerate(gc.get_referrers(ref)):
                    print("Object", i, ":", type(o), ":", o)

            assert r() is None, "OpBlockedArrayCache was not cleaned up correctly"
        finally:
            CacheMemoryManager().enable()


if haveBlocked():

    class TestBlocked(TestVigra):
        def setup_method(self, method):
            self.method = np.asarray(["blocked"], dtype=np.object)

        # @unittest.skip("Not implemented yet")
        # def testUnsupported(self):
        # pass

        # background value is unsupported for blocked labeling
        @unittest.expectedFailure
        def testBackground(self):
            super(TestBlocked, self).testBackground()


class TestLazy(TestVigra):
    def setup_method(self, method):
        self.method = np.asarray(["lazy"], dtype=np.object)

    @unittest.skip("This test does not make sense with lazy connected components")
    def testCorrectBlocking(self):
        pass

    @unittest.skip("This test does not make sense with lazy connected components")
    def testNoRecomputation(self):
        pass

    # setting particular regions dirty is currently not supported by lazy
    # connected components
    @unittest.expectedFailure
    def testSetDirty(self):
        super(TestLazy, self).testSetDirty()

    def testThreadSafety(self):
        g = Graph()

        vol = np.zeros((1000, 100, 10))
        vol = vol.astype(np.uint8)
        vol = vigra.taggedView(vol, axistags="xyz")
        vol[:200, ...] = 1
        vol[800:, ...] = 1

        opCount = CountExecutes(graph=g)
        opCount.Input.setValue(vol)
        opCount.Output.meta["ideal_blockshape"] = vol.shape

        op = OpLabelVolume(graph=g)
        op.Method.setValue(self.method)
        op.Input.connect(opCount.Output)

        reqs = [op.CachedOutput[...] for i in range(4)]
        [r.submit() for r in reqs]
        [r.block() for r in reqs]
        assert opCount.numExecutes == 1, "Parallel requests to CachedOutput resulted in recomputation " "({}/4)".format(
            opCount.numExecutes
        )


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
        raise PropagateDirtyCalled()


class CountExecutes(Operator):
    Input = InputSlot()
    Output = OutputSlot()

    numExecutes = 0

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(roi)

    def execute(self, slot, sunbindex, roi, result):
        self.numExecutes += 1
        req = self.Input.get(roi)
        req.writeInto(result)
        req.block()


class PropagateDirtyCalled(Exception):
    pass


if __name__ == "__main__":
    method = np.asarray(["lazy"], dtype=np.object)
    vol = np.random.randint(255, size=(10, 10, 10))
    vol = vol.astype(np.uint8)
    vol = vigra.taggedView(vol, axistags="xyz")

    op = OpLabelVolume(graph=Graph())
    op.Method.setValue(method)
    op.Input.setValue(vol)

    out = op.Output[...].wait()

    assert_array_equal(vol.shape, out.shape)

    import nose

    ret = nose.run(defaultTest=__file__)
