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

import unittest

import numpy as np
import vigra

from lazyflow.graph import Graph
from lazyflow.rtype import SubRegion
from lazyflow.operators import OpCacheFixer

from lazyflow.utility.testing import OpArrayPiperWithAccessCount
from lazyflow.utility.testing import OpCallWhenDirty
from numpy.testing import assert_array_equal


class TestOpCacheFixer(unittest.TestCase):
    def setup_method(self, method):
        g = Graph()

        vol = np.random.random(size=(100, 110, 120))
        self.vol = vigra.taggedView(vol, axistags="xyz")

        vol5d = np.random.random(size=(3, 100, 110, 120, 7))
        self.vol5d = vigra.taggedView(vol5d, axistags="cxyzt")

        piper = OpArrayPiperWithAccessCount(graph=g)
        op = OpCacheFixer(graph=g)
        op.Input.connect(piper.Output)
        call = OpCallWhenDirty(graph=g)
        call.Input.connect(op.Output)

        self.piper = piper
        self.op = op
        self.call = call

    def testPassThroughAndFixed(self):
        self.op.fixAtCurrent.setValue(False)
        # we want the last operator to throw an exception when its
        # propagateDirty is called, so we can catch it below
        def foo():
            raise PropagateDirtyCalled()

        self.call.function = foo

        with self.assertRaises(PropagateDirtyCalled):
            self.piper.Input.setValue(self.vol)

        roi = self.call.roi
        assert_array_equal(roi.start, (0, 0, 0))
        assert_array_equal(roi.stop, self.vol.shape)

        with self.assertRaises(PropagateDirtyCalled):
            self.piper.Input.setDirty(slice(None))

        roi = self.call.roi
        assert_array_equal(roi.start, (0, 0, 0))
        assert_array_equal(roi.stop, self.vol.shape)

        self.op.fixAtCurrent.setValue(True)

        try:
            roi1 = SubRegion(self.piper.Input, (0, 10, 20), (15, 15, 35))
            self.piper.Input.setDirty(roi1)
            roi2 = SubRegion(self.piper.Input, (15, 9, 1), (20, 14, 20))
            self.piper.Input.setDirty(roi2)
        except PropagateDirtyCalled:
            raise AssertionError("dirtyness is not fixed")

        with self.assertRaises(PropagateDirtyCalled):
            self.op.fixAtCurrent.setValue(False)

        roi = self.call.roi
        assert_array_equal(roi.start, (0, 9, 1))
        assert_array_equal(roi.stop, (20, 15, 35))


class PropagateDirtyCalled(Exception):
    pass
