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


import unittest
import numpy as np
import vigra

from ilastik.applets.thresholdTwoLevels.opGraphcutSegment import haveGraphCut
have_opengm = haveGraphCut()

from numpy.testing.utils import assert_array_equal,\
    assert_array_almost_equal, assert_array_less
from nose import SkipTest

from lazyflow.graph import Graph
from lazyflow.operators.opArrayPiper import OpArrayPiper

if have_opengm:
    from ilastik.applets.thresholdTwoLevels.opGraphcutSegment\
        import OpObjectsSegment, OpGraphCut


@unittest.skipIf(not have_opengm, "OpenGM not available")
class TestOpGraphCut(unittest.TestCase):
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

    def testComplete(self):
        graph = Graph()
        op = OpGraphCut(graph=graph)
        piper = OpArrayPiper(graph=graph)
        piper.Input.setValue(self.vol)
        op.Prediction.connect(piper.Output)

        out = op.Output[...].wait()
        assert_array_equal(out.shape, self.vol.shape)

        # check whether no new blocks introduced
        # assert np.all(out[0:20, ...] < .5)

        # check whether the interior was labeled 1
        assert np.all(out[22:38, 22:38, 22:38, ...] > .5)
        assert np.all(out[62:78, 62:78, 62:78, ...] > .5)


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

    def testMargin(self):
        graph = Graph()
        vol = np.zeros((100, 110, 10), dtype=np.float32)
        # draw a big plus sign
        vol[50:70, :, :] = 1.0
        vol[:, 60:80, :] = 1.0
        vol = vigra.taggedView(vol, axistags='xyz')
        labels = np.zeros((100, 110, 10), dtype=np.uint8)
        labels[45:75, 55:85, 3:4] = 1
        labels = vigra.taggedView(labels, axistags='xyz')

        op = OpObjectsSegment(graph=graph)
        piper = OpArrayPiper(graph=graph)
        piper.Input.setValue(vol)
        op.Prediction.connect(piper.Output)
        op.LabelImage.setValue(labels)

        # without margin
        op.Margin.setValue(np.asarray((0, 0, 0)))
        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags=op.Output.meta.axistags)
        out = out.withAxes(*'xyz')
        assert_array_equal(out[50:70, 60:80, 3] > 0, vol[50:70, 60:80, 3] > .5)
        assert np.all(out[:45, ...] == 0)

        # with margin
        op.Margin.setValue(np.asarray((5, 5, 0)))
        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags=op.Output.meta.axistags)
        out = out.withAxes(*'xyz')
        assert_array_equal(out[45:75, 55:85, 3] > 0, vol[45:75, 55:85, 3] > .5)
        assert np.all(out[:40, ...] == 0)

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
