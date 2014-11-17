import unittest

from ilastik.workflows.mriVolumetry.opSmoothing import OpCostVolumeFilter
from ilastik.workflows.mriVolumetry.opSmoothing import getMaxSigma
from ilastik.workflows.mriVolumetry.opMriVolFilter import OpMriBinarizeImage
from ilastik.workflows.mriVolumetry.opMriVolFilter import OpMriRevertBinarize
from ilastik.workflows.mriVolumetry.opMriVolFilter import OpMriVolFilter
from ilastik.workflows.mriVolumetry.opImplementationChoice import OpImplementationChoice
from ilastik.workflows.mriVolumetry.opOpenGMFilter import OpOpenGMFilter

from lazyflow.graph import Graph
from lazyflow.operator import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpMaxChannelIndicatorOperator
from lazyflow.operators import OpArrayPiper
from lazyflow.operators import OpPixelOperator
from lazyflow.operators import OpSingleChannelSelector

import numpy as np
from numpy.testing import assert_array_equal

import vigra


class TestOpCostVolumeFilter(unittest.TestCase):
    def setUp(self):
        self.vol = np.random.rand(120, 130, 110)
        # necessary for meta information, convert to vigra array
        self.vol = vigra.taggedView(self.vol, axistags='xyz')
        self.vol = self.vol.withAxes(*'txyzc')
        self.sig = 1.2

    def testUsage(self):
        g = Graph()
        op = OpCostVolumeFilter(graph=g)
        op.Input.setValue(self.vol)
        op.Configuration.setValue({'sigma': self.sig})
        out = op.Output[0:1, ...].wait()
        assert out.shape == self.vol.shape, \
            'In and output data differs in shape'


class TestOpMriBinarizeImage(unittest.TestCase):
    def setUp(self):
        self.num_channels = 4
        self.vol = np.random.randint(1, self.num_channels, size=(120,130,110))
        # necessary for meta information, convert to vigra array 
        self.vol = vigra.taggedView(self.vol, axistags='xyz')
        self.BackgroundChannel = 2
        self.ActiveChannels = [2, 0, 0, 2]

    def testUsage(self):
        g = Graph()
        op = OpMriBinarizeImage(graph=g)
        op.Input.setValue(self.vol)
        op.ActiveChannels.setValue(self.ActiveChannels)

        out = op.Output[...].wait()
        assert out.shape == self.vol.shape, \
            'In and output data differs in shape'
        assert np.all(np.unique(out) == [0, 1]), \
            'Not a binary image (0,1)'

    def testSingleChannel(self):
        vol = np.ones_like(self.vol)
        vol = vigra.taggedView(vol, axistags='xyz')
        g = Graph()
        op = OpMriBinarizeImage(graph=g)
        op.Input.setValue(vol)

        op.ActiveChannels.setValue(np.zeros((1,), dtype=int))
        out = op.Output[...].wait()

        op.ActiveChannels.setValue(np.array([1], dtype=int))
        out = op.Output[...].wait()


class TestOpMriRevertBinarize(unittest.TestCase):
    def setUp(self):
        pass

    def testBasics(self):
        argmax = np.asarray([[1, 1, 1, 1],
                             [1, 2, 1, 3],
                             [1, 2, 1, 1],
                             [1, 1, 1, 1]], dtype=np.uint32)
        cc = np.asarray([[0, 0, 0, 0],
                         [0, 1, 0, 0],
                         [0, 1, 0, 0],
                         [0, 0, 0, 0]], dtype=np.uint32)

        expected = np.asarray([[0, 0, 0, 0],
                               [0, 2, 0, 0],
                               [0, 2, 0, 0],
                               [0, 0, 0, 0]], dtype=np.uint32)

        op = OpMriRevertBinarize(graph=Graph())
        op.ArgmaxInput.setValue(argmax)
        op.CCInput.setValue(cc)
        out = op.Output[...].wait()
        assert_array_equal(out, expected)


class TestOpImplementationChoice(unittest.TestCase):

    class Base(Operator):
        Input = InputSlot()
        Output = OutputSlot()

        def setupOutputs(self):
            self.Output.meta.assignFrom(self.Input.meta)

        def execute(self, slot, subidnex, roi, result):
            req = self.Input.get(roi)
            req.writeInto(result)
            req.block()

        def propagateDirty(self, slot, subindex, roi):
            self.Output.setDirty(roi)

    class ABC(Base):
        # needed by OpPixelOperator
        Function = InputSlot(optional=True)
        # needed by OpSingleChannelSelector
        Index = InputSlot(optional=True)

    class Ex1(Base):
        AltOutput1 = OutputSlot()

        def setupOutputs(self):
            self.Output.meta.assignFrom(self.Input.meta)
            self.AltOutput1.meta.assignFrom(self.Input.meta)

        def propagateDirty(self, slot, subindex, roi):
            self.Output.setDirty(roi)
            self.AltOutput1.setDirty(roi)

    class Ex2(Base):
        AltOutput2 = OutputSlot()

        def setupOutputs(self):
            self.Output.meta.assignFrom(self.Input.meta)
            self.AltOutput2.meta.assignFrom(self.Input.meta)

        def propagateDirty(self, slot, subindex, roi):
            self.Output.setDirty(roi)
            self.AltOutput2.setDirty(roi)

    class ABC2(Operator):
        Input = InputSlot()
        AltOutput1 = OutputSlot()
        AltOutput2 = OutputSlot()
        Output = OutputSlot()

    def setUp(self):
        pass

    def TestUsage(self):
        choices = {'pipe': OpArrayPiper,
                   'chan': OpMaxChannelIndicatorOperator}

        wrap = OpImplementationChoice(self.Base, graph=Graph())
        wrap.implementations = choices

        wrap.Implementation.setValue('pipe')
        vol = np.zeros((2, 10, 15, 20, 3))
        vol = vigra.taggedView(vol, axistags='txyzc')
        wrap.Input.setValue(vol)
        # check if connection is done properly
        assert vol.shape == wrap.Output.meta.shape, "inner op not connected"
        # check if piping works
        out = wrap.Output[...].wait()

        vol2 = np.zeros((5, 6, 7))
        vol2 = vigra.taggedView(vol2, axistags='xyz')
        wrap.Input.setValue(vol2)
        # check if setupOutputs still works
        assert vol2.shape == wrap.Output.meta.shape, "setupOutputs not called"

        wrap.Implementation.setValue('chan')
        vol = np.zeros((2, 10, 15, 20, 3))
        vol = vigra.taggedView(vol, axistags='txyzc')
        wrap.Input.setValue(vol)
        # check if operator is switched
        assert wrap.Output.meta.dtype == np.uint8, "op not switched"

    def TestAdvancedUsage(self):
        choices = {'pixop': OpPixelOperator,
                   'chan': OpSingleChannelSelector}

        wrap = OpImplementationChoice(self.ABC, graph=Graph())
        wrap.implementations = choices

        wrap.Implementation.setValue('pixop')
        vol = np.zeros((2, 10, 15, 20, 3), dtype=np.int)
        vol = vigra.taggedView(vol, axistags='txyzc')
        wrap.Input.setValue(vol)
        wrap.Function.setValue(lambda x: x+1)
        # check if connection is done properly
        assert vol.shape == wrap.Output.meta.shape, "inner op not connected"
        # check if piping works
        out = wrap.Output[...].wait()
        # check if correct operator in use
        assert np.all(out == 1)

        wrap.Implementation.setValue('chan')
        wrap.Index.setValue(0)
        # check if operator is switched
        out = wrap.Output[...].wait()
        ts = wrap.Output.meta.getTaggedShape()
        if 'c' in ts:
            assert ts['c'] == 1, "op not switched"

    def testVaryingOutputSlots(self):
        choices = {'1': self.Ex1, '2': self.Ex2}

        wrap = OpImplementationChoice(self.ABC2, graph=Graph())
        wrap.implementations = choices

        vol = np.zeros((2, 10, 15, 20, 3), dtype=np.int)
        vol = vigra.taggedView(vol, axistags='txyzc')
        wrap.Input.setValue(vol)

        wrap.Implementation.setValue('1')
        assert wrap.Output.ready()
        assert wrap.AltOutput1.ready()
        assert not wrap.AltOutput2.ready(), str(wrap.AltOutput2)

        wrap.Implementation.setValue('2')
        assert wrap.Output.ready()
        assert not wrap.AltOutput1.ready(), str(wrap.AltOutput1)
        assert wrap.AltOutput2.ready()


class TestOpMriVolFilter(unittest.TestCase):
    def setUp(self):
        shape = (4, 100, 150, 200)
        vol = np.random.randint(0, 255, size=shape)
        vol = vigra.taggedView(vol, axistags='txyz')
        self.vol = vol
        pred = np.zeros(shape + (2,))
        pred = vigra.taggedView(pred, axistags='txyzc')
        pred[..., 1] = vol/255.0
        pred[..., 0] = 1 - pred[..., 1]
        self.pred = pred

    def testGaussian(self):
        g = Graph()
        op = OpMriVolFilter(graph=g)
        op.Method.setValue('gaussian')
        op.RawInput.setValue(self.vol)
        op.Input.setValue(self.pred)
        op.Configuration.setValue({'sigma': 0.2})
        op.Threshold.setValue(0)

        op.ActiveChannels.setValue(np.ones((2,), dtype=np.int))
        op.LabelNames.setValue(np.asarray(["black", "white"]))

        out = op.ArgmaxOutput[...].wait()

    def testGuided(self):
        g = Graph()
        op = OpMriVolFilter(graph=g)
        op.Method.setValue('guided')
        op.RawInput.setValue(self.vol)
        op.Input.setValue(self.pred)
        d = {'sigma': 0.2, 'eps': 0.2, 'guided': False}
        op.Configuration.setValue(d)
        op.Threshold.setValue(0)

        op.ActiveChannels.setValue(np.ones((2,), dtype=np.int))
        op.LabelNames.setValue(np.asarray(["black", "white"]))

        out = op.ArgmaxOutput[...].wait()

    # TODO implement test for opengm

    def testObjectAssignment(self):
        m = 255
        v = [[0, 0, 0, 0, 0, 0, 0],
             [0, m, m, 0, 0, m, 0],
             [0, m, m, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0, 0]]
        vol = np.asarray(v, dtype=np.uint8)
        vol = vigra.taggedView(vol, axistags='xy')
        vol = vol.withAxes(*'txyzc')

        # make 3 channel prediction image, last channel unused
        pred = np.zeros((1, 4, 7, 1, 4), dtype=np.float32)
        pred = vigra.taggedView(pred, axistags='txyzc')
        pred[..., 0:1] = vol == 0
        pred[0, 1:3, 1, 0, 1] = 1.0
        pred[0, 1:3, 2, 0, 2] = 1.0
        pred[0, 1, 5, 0, 2] = 1.0
        assert pred.sum() == vol.size

        g = Graph()
        op = OpMriVolFilter(graph=g)
        op.Method.setValue('gaussian')
        op.Input.setValue(pred)
        op.RawInput.setValue(vol)
        op.Configuration.setValue({'sigma': 0})
        # filter single pixel object
        op.Threshold.setValue(2)

        # ignore background of 0's
        op.ActiveChannels.setValue(np.asarray([0, 1, 1, 1], dtype=np.int))
        op.LabelNames.setValue(np.asarray(
            ["black", "white", "?"], dtype=np.object))

        # trigger computation
        result = op.CachedOutput[...].wait()
        tags = op.CachedOutput.meta.axistags
        result = vigra.taggedView(result, axistags=tags)
        expected = vol.copy().astype(np.uint32)
        expected[:] = 0
        expected[0, 1:3, 1, 0, 0] = 2
        expected[0, 1:3, 2, 0, 0] = 3
        assert_array_equal(result.squeeze(), expected.squeeze())

        class DirtyException(Exception):
            pass

        def dirtyHandler(self, roi):
            exp_start = [0, 1, 1, 0, 0]
            exp_stop = [1, 3, 2, 1, 1]
            assert_array_equal(exp_start, roi.start)
            assert_array_equal(exp_stop, roi.stop)
            raise DirtyException()

        op.CachedOutput.notifyDirty(dirtyHandler)

        with self.assertRaises(DirtyException):
            op.AssignChannelForObject[0:1, 1:2, 1:2, 0:1, 0:1] = 4

        # check that class was assigned
        result = op.CachedOutput[0, 1:3, 1:2, 0, 0].wait().squeeze()
        assert np.all(result == 4)

        # check that the rest was not assigned
        result = op.CachedOutput[0, 1:3, 2:3, 0, 0].wait().squeeze()
        assert np.all(result == 3)


class TestOpOpenGMFilter(unittest.TestCase):
    def setUp(self):
        pred = np.ones((2, 10, 15, 20, 2), dtype=np.float32) * .1
        pred = vigra.taggedView(pred, axistags='txyzc')
        pred[:, 3:6, 4:8, 5:10, 0] = .9
        pred[..., 1] = 1 - pred[..., 0]
        self.pred = pred
        vol = 255*(pred[..., 0] > .5)
        vol = vol.astype(np.uint8).withAxes(*'txyzc')
        self.vol = vol
        self.g = Graph()

    def testSimple(self):
        op = OpOpenGMFilter(graph=self.g)
        op.Input.setValue(self.pred)
        op.RawInput.setValue(self.vol)
        op.Configuration.setValue({'sigma': 0.2, 'unaries': 0.1})
        s = op.Output.meta.shape
        assert_array_equal(self.pred.shape[:4], s[:4])
        assert s[4] == 1

        out = op.Output[...].wait()
        print(out[0, ...].sum())


class TestVariousSmallComponents(unittest.TestCase):
    def setUp(self):
        pass

    def deFactoVigraMaxSigma(self, minShape):
        return minShape/3.0

    def testGetMaxSigma(self):
        # http://ukoethe.github.io/vigra/doc/vigra/classvigra_1_1Gaussian
        for s in np.arange(10, 1000, 10):
            np.testing.assert_array_less(getMaxSigma((s,)),
                                         self.deFactoVigraMaxSigma(s))


if __name__ == "__main__": 
    unittest.main()


