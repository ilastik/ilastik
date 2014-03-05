import unittest
import numpy as np
import vigra

try:
    import opengm
except ImportError:
    have_opengm = False
else:
    have_opengm = True

from numpy.testing.utils import assert_array_equal,\
    assert_array_almost_equal, assert_array_less
from nose import SkipTest

from lazyflow.graph import Graph
from lazyflow.operators.opArrayPiper import OpArrayPiper

if have_opengm:
    from ilastik.applets.graphCutSegmentation.opObjectsSegment import OpObjectsSegment


@unittest.skipIf(not have_opengm, "OpenGM not available")
class TestOpObjectsSegment(unittest.TestCase):
    def setUp(self):
        shape = (120, 100, 90)
        channel = 2
        vol = np.zeros(shape, dtype=np.float32)
        vol += + np.random.rand(*shape)*.1
        vol[20:40, 20:40, 20:40] = np.random.rand(20, 20, 20)*.39 + .6
        vol[60:80, 60:80, 60:80] = np.random.rand(20, 20, 20)*.39 + .6

        labels = np.zeros(shape, dtype=np.uint32)
        labels[20:40, 20:40, 20:40] = 13
        labels[60:80, 60:80, 60:80] = 37

        withChannels = np.zeros(shape + (4,), dtype=np.float32)
        withChannels[..., channel] = vol

        crazyAxes = np.zeros(shape, dtype=np.float32)
        crazyAxes[...] = vol

        self.withChannels = vigra.taggedView(withChannels, axistags='xyzc')
        self.crazyAxes = vigra.taggedView(crazyAxes, axistags='yzx')
        self.vol = vigra.taggedView(vol, axistags='xyz')
        self.labels = vigra.taggedView(labels.astype(np.uint8), axistags='xyz')
        self.channel = channel

    def testCC(self):
        graph = Graph()
        op = OpObjectsSegment(graph=graph)
        piper = OpArrayPiper(graph=graph)
        piper.Input.setValue(self.vol)
        op.Prediction.connect(piper.Output)
        piper = OpArrayPiper(graph=graph)
        piper.Input.setValue(self.labels)
        op.LabelImage.connect(piper.Output)

        out = op.ConnectedComponents[...].wait()

        # check whether no new blocks introduced
        assert np.all(out[0:20, ...] < 1)

        # check whether the interior was labeled 1
        assert np.all(out[22:38, 22:38, 22:38, ...] > 0)
        assert np.all(out[62:78, 62:78, 62:78, ...] > 0)

    def testBB(self):
        graph = Graph()
        op = OpObjectsSegment(graph=graph)
        piper = OpArrayPiper(graph=graph)
        piper.Input.setValue(self.vol)
        op.Prediction.connect(piper.Output)
        op.LabelImage.setValue(self.labels)

        bbox = op.BoundingBoxes[...].wait()
        assert isinstance(bbox, dict)

    def testComplete(self):
        graph = Graph()
        op = OpObjectsSegment(graph=graph)
        piper = OpArrayPiper(graph=graph)
        piper.Input.setValue(self.vol)
        op.Prediction.connect(piper.Output)
        op.LabelImage.setValue(self.labels)

        out = op.Output[...].wait()
        assert_array_equal(out.shape, self.vol.shape)

        # check whether no new blocks introduced
        # assert np.all(out[0:20, ...] < .5)

        # check whether the interior was labeled 1
        assert np.all(out[22:38, 22:38, 22:38, ...] > .5)
        assert np.all(out[62:78, 62:78, 62:78, ...] > .5)

    def testChannel(self):
        graph = Graph()
        op = OpObjectsSegment(graph=graph)
        piper = OpArrayPiper(graph=graph)
        piper.Input.setValue(self.withChannels)
        op.Prediction.connect(piper.Output)
        op.LabelImage.setValue(self.labels)
        op.Channel.setValue(self.channel)
        out = op.Output[...].wait()

        assert np.all(out[22:38, 22:38, 22:38, ...] > .5)
        assert np.all(out[62:78, 62:78, 62:78, ...] > .5)

    def testFaulty(self):
        vec = vigra.taggedView(np.zeros((500,), dtype=np.float32),
                               axistags=vigra.defaultAxistags('x'))
        graph = Graph()
        op = OpObjectsSegment(graph=graph)
        piper = OpArrayPiper(graph=graph)
        piper.Input.setValue(vec)

        with self.assertRaises(ValueError):
            op.Prediction.connect(piper.Output)
            op.LabelImage.connect(piper.Output)
