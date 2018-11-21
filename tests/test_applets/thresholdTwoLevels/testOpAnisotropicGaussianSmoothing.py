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
###############################################################################
import numpy
from numpy.testing import assert_array_equal
import vigra
np = numpy

from lazyflow.graph import Graph
from lazyflow.operators import OpReorderAxes

from ilastik.applets.thresholdTwoLevels.thresholdingTools import OpAnisotropicGaussianSmoothing5d

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()
import unittest


class TestOpAnisotropicGaussianSmoothing5d(unittest.TestCase):

    def setUp(self):
        g = Graph()
        r1 = OpReorderAxes(graph=g)
        r1.AxisOrder.setValue('tzyxc')
        op = OpAnisotropicGaussianSmoothing5d(graph=g)
        op.Input.connect(r1.Output)
        self.r1 = r1
        self.op = op

    def test2d(self):
        vol = np.random.rand(50, 50)
        vol = vigra.taggedView(vol, axistags='yx')
        self.r1.Input.setValue(vol)
        out = self.op.Output[...].wait()

    def test3d(self):
        vol = np.random.rand(50, 50, 50)
        vol = vigra.taggedView(vol, axistags='zyx')
        self.r1.Input.setValue(vol)
        out = self.op.Output[...].wait()

    def test4d(self):
        vol = np.random.rand(50, 50, 50, 5)
        vol = vigra.taggedView(vol, axistags='zyxc')
        self.r1.Input.setValue(vol)
        out = self.op.Output[...].wait()

    def test5d(self):
        vol = np.random.rand(50, 50, 50, 5, 2)
        vol = vigra.taggedView(vol, axistags='zyxct')
        self.r1.Input.setValue(vol)
        out = self.op.Output[...].wait()

    def testExtend(self):
        vol = np.random.rand(50, 50)
        vol = vigra.taggedView(vol, axistags='yx')
        self.r1.Input.setValue(vol)
        out = self.op.Output[0, 0, :10, :10, 0].wait().squeeze()
        out2 = self.op.Output[...].wait()

        assert_array_equal(out, out2[0, 0, :10, :10, 0].squeeze())

    def testSmoothing(self):
        op = self.op
        vol = np.random.rand(50, 50).astype(np.float32)
        vol = vigra.taggedView(vol, axistags='yx')
        self.r1.Input.setValue(vol)
        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags=op.Output.meta.axistags).squeeze()
        out2 = vigra.filters.gaussianSmoothing(vol, 1.0, window_size=2.0)

        assert_array_equal(out, out2)

    def testReqFromMid(self):
        vol = np.random.rand(3, 50, 50, 1, 1)
        vol = vigra.taggedView(vol, axistags='tzyxc')
        self.r1.Input.setValue(vol)
        out = self.op.Output[2, 10:20, 10:20, 0, 0].wait()
