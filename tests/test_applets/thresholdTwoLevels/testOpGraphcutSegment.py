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
#		   http://ilastik.org/license.html
##############################################################################


import unittest
import numpy as np
import vigra

from numpy.testing.utils import assert_array_equal, assert_array_almost_equal, assert_array_less

from lazyflow.graph import Graph
from lazyflow.operators.opArrayPiper import OpArrayPiper

from ilastik.applets.thresholdTwoLevels.opGraphcutSegment import OpObjectsSegment, OpGraphCut

def getTestVolume():
    t, c = 3, 2
    shape = (t, 120, 100, 90, c)
    vol = np.zeros(shape, dtype=np.float32)
    labels = np.zeros(shape, dtype=np.uint32)

    # fill with noise
    vol += + np.random.rand(*shape)*.1

    # create some higher probability boxes
    vol[:, 20:40, 20:40, 20:40, :] = np.random.rand(t, 20, 20, 20, c)*.39 + .6
    vol[:, 60:80, 60:80, 60:80, :] = np.random.rand(t, 20, 20, 20, c)*.39 + .6
    labels[:, 20:40, 20:40, 20:40, :] = 1
    labels[:, 60:80, 60:80, 60:80, :] = 2

    # convert to the thresholding operators internal axes order
    fullVolume = vigra.taggedView(vol, axistags='tzyxc')
    fullLabels = vigra.taggedView(labels, axistags='tzyxc')
    
    return (fullVolume, fullLabels)


class TestOpGraphCut(unittest.TestCase):
 
    def setUp(self):
        self.fullVolume, self.labels = getTestVolume()
 
    def testComplete(self):
        graph = Graph()
        op = OpGraphCut(graph=graph)
        piper = OpArrayPiper(graph=graph)
        piper.Input.setValue(self.fullVolume)
        op.Prediction.connect(piper.Output)
 
        out = op.CachedOutput[...].wait()
        out = vigra.taggedView(out, axistags=op.Output.meta.axistags)
        assert_array_equal(out.shape, self.fullVolume.shape)
 
        # check whether no new blocks introduced
        mask = np.where(self.labels > 0, 0, 1)
        masked = out.view(np.ndarray) * mask
        assert_array_equal(masked, 0*masked)
 
        # check whether the interior was labeled 1
        assert np.all(out[:, 22:38, 22:38, 22:38, :] > 0)
        assert np.all(out[:, 62:78, 62:78, 62:78, :] > 0)
 
    #TODO test dirty propagation


class TestOpObjectsSegment(unittest.TestCase):
    
    def setUp(self):
        self.vol, self.labels = getTestVolume()

    def testBB(self):
        graph = Graph()
        op = OpObjectsSegment(graph=graph)
        piper = OpArrayPiper(graph=graph)
        piper.Input.setValue(self.vol)
        op.Prediction.connect(piper.Output)
        op.LabelImage.setValue(self.labels)
 
        bbox = op.BoundingBoxes[0, ..., 0].wait()
        assert isinstance(bbox, dict)

    def testComplete(self):
        graph = Graph()
        op = OpObjectsSegment(graph=graph)
        piper = OpArrayPiper(graph=graph)
        piper.Input.setValue(self.vol)
        op.Prediction.connect(piper.Output)
        piper = OpArrayPiper(graph=graph)
        piper.Input.setValue(self.labels)
        op.LabelImage.connect(piper.Output)

        # get whole volume
        out = op.CachedOutput[...].wait()
        out = vigra.taggedView(out, axistags=op.Output.meta.axistags)

        # check whether no new blocks introduced
        mask = np.where(self.labels > 0, 0, 1)
        masked = out.view(np.ndarray) * mask
        assert_array_equal(masked, 0*masked)

        # check whether the interior was labeled 1
        assert np.all(out[:, 22:38, 22:38, 22:38, :] > 0)
        assert np.all(out[:, 62:78, 62:78, 62:78, :] > 0)

    def testMargin(self):
        graph = Graph()
        vol = np.zeros((100, 110, 10), dtype=np.float32)
        # draw a big plus sign
        vol[50:70, :, :] = 1.0
        vol[:, 60:80, :] = 1.0
        vol = vigra.taggedView(vol, axistags='zyx').withAxes(*'tzyxc')
        labels = np.zeros((100, 110, 10), dtype=np.uint32)
        labels[45:75, 55:85, 3:4] = 1
        labels = vigra.taggedView(labels, axistags='zyx').withAxes(*'tzyxc')
 
        op = OpObjectsSegment(graph=graph)
        piper = OpArrayPiper(graph=graph)
        piper.Input.setValue(vol)
        op.Prediction.connect(piper.Output)
        op.LabelImage.setValue(labels)
 
        # without margin
        op.MarginZYX.setValue(np.asarray((0, 0, 0)))
        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags=op.Output.meta.axistags)
        out = out.withAxes(*'zyx')
        vol = vol.withAxes(*'zyx')
        assert_array_equal(out[50:70, 60:80, 3] > 0, vol[50:70, 60:80, 3] > .5)
        assert np.all(out[:45, ...] == 0)
 
        # with margin
        op.MarginZYX.setValue(np.asarray((5, 5, 0)))
        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags=op.Output.meta.axistags)
        out = out.withAxes(*'zyx')
        assert_array_equal(out[45:75, 55:85, 3] > 0, vol[45:75, 55:85, 3] > .5)
        assert np.all(out[:40, ...] == 0)
 
    def testFaulty(self):
        vec = vigra.taggedView(np.zeros((500,), dtype=np.float32),
                               axistags=vigra.defaultAxistags('x'))
        graph = Graph()
        op = OpObjectsSegment(graph=graph)
        piper = OpArrayPiper(graph=graph)
        piper.Input.setValue(vec)
 
        with self.assertRaises(AssertionError):
            op.Prediction.connect(piper.Output)
            op.LabelImage.connect(piper.Output)

    #TODO test dirty propagation
if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
