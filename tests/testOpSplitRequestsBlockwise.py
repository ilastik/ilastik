from __future__ import print_function

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
from lazyflow.operators.opSplitRequestsBlockwise import OpSplitRequestsBlockwise

from lazyflow.utility.testing import OpArrayPiperWithAccessCount
from lazyflow.utility.testing import OpCallWhenDirty
from numpy.testing import assert_array_equal


class TestOpSplitRequestsBlockwise(unittest.TestCase):
    def setup_method(self, method):
        g = Graph()

        vol = np.random.random(size=(100, 110, 120))
        self.vol = vigra.taggedView(vol, axistags="xyz")

        vol5d = np.random.random(size=(3, 100, 110, 120, 7))
        self.vol5d = vigra.taggedView(vol5d, axistags="cxyzt")

        piper = OpArrayPiperWithAccessCount(graph=g)
        piper.Input.setValue(self.vol)

        self.g = g
        self.piper = piper

    def testFullBlocks(self):
        op = OpSplitRequestsBlockwise(True, graph=self.g)
        op.Input.connect(self.piper.Output)
        op.BlockShape.setValue((10, 15, 20))

        op.Output[0:20, 30:45, 10:30].wait()
        slot = self.piper.Output
        expected = [
            SubRegion(slot, (0, 30, 0), (10, 45, 20)),
            SubRegion(slot, (0, 30, 20), (10, 45, 40)),
            SubRegion(slot, (10, 30, 0), (20, 45, 20)),
            SubRegion(slot, (10, 30, 20), (20, 45, 40)),
        ]

        for roi in expected:
            filtered = [x for x in self.piper.requests if x == roi]
            assert len(filtered) == 1, "missing roi {}".format(roi)

        self.piper.requests = []

        op.Output[5:14, 32:44, 17:21].wait()
        for roi in expected:
            filtered = [x for x in self.piper.requests if x == roi]
            assert len(filtered) == 1, "missing roi {}".format(roi)

    def testNoFullBlocks(self):
        op = OpSplitRequestsBlockwise(False, graph=self.g)
        op.Input.connect(self.piper.Output)
        op.BlockShape.setValue((10, 15, 20))

        op.Output[0:20, 30:45, 10:30].wait()
        slot = self.piper.Output
        expected = [
            SubRegion(slot, (0, 30, 10), (10, 45, 20)),
            SubRegion(slot, (0, 30, 20), (10, 45, 30)),
            SubRegion(slot, (10, 30, 10), (20, 45, 20)),
            SubRegion(slot, (10, 30, 20), (20, 45, 30)),
        ]

        for req in self.piper.requests:
            print(req)

        for roi in expected:
            filtered = [x for x in self.piper.requests if x == roi]
            assert len(filtered) == 1, "missing roi {}".format(roi)

        self.piper.requests = []

        op.Output[5:14, 32:44, 17:21].wait()
        expected = [
            SubRegion(slot, (5, 32, 17), (10, 44, 20)),
            SubRegion(slot, (5, 32, 20), (10, 44, 21)),
            SubRegion(slot, (10, 32, 17), (14, 44, 20)),
            SubRegion(slot, (10, 32, 20), (14, 44, 21)),
        ]
        for roi in expected:
            filtered = [x for x in self.piper.requests if x == roi]
            assert len(filtered) == 1, "missing roi {}".format(roi)

    def testCorrectData(self):
        op = OpSplitRequestsBlockwise(False, graph=self.g)
        op.Input.connect(self.piper.Output)
        op.BlockShape.setValue((10, 15, 20))

        data = op.Output[0:20, 30:45, 10:30].wait()
        assert_array_equal(data, self.vol[:20, 30:45, 10:30].view(np.ndarray))

        data = op.Output[5:14, 32:44, 17:21].wait()
        assert_array_equal(data, self.vol[5:14, 32:44, 17:21].view(np.ndarray))

        op = OpSplitRequestsBlockwise(True, graph=self.g)
        op.Input.connect(self.piper.Output)
        op.BlockShape.setValue((10, 15, 20))

        data = op.Output[0:20, 30:45, 10:30].wait()
        assert_array_equal(data, self.vol[:20, 30:45, 10:30].view(np.ndarray))

        data = op.Output[5:14, 32:44, 17:21].wait()
        assert_array_equal(data, self.vol[5:14, 32:44, 17:21].view(np.ndarray))


if __name__ == "__main__":
    import sys
    import nose
    import logging

    handler = logging.StreamHandler(sys.stdout)
    logging.getLogger().addHandler(handler)

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
