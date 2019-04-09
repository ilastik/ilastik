from builtins import object

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
# 		   http://ilastik.org/license/
###############################################################################
import numpy
import vigra
from lazyflow.graph import Graph
from lazyflow.operators import OpVigraWatershed
from lazyflow.utility.slicingtools import sl, slicing2shape


class TestOpVigraWatershed(object):
    def setup_method(self, method):
        graph = Graph()

        inputData = numpy.random.random((1, 10, 100, 100, 1))
        inputData *= 256
        inputData = inputData.astype("float32")
        inputData = inputData.view(vigra.VigraArray)
        inputData.axistags = vigra.defaultAxistags("txyzc")
        self.inputData = inputData

        self.op = OpVigraWatershed(graph=graph)
        self.op.InputImage.setValue(inputData)
        self.op.PaddingWidth.setValue(10)

    def testOutputCrash(self):
        """
        Bare-minimum test: Just make sure we can request the output without crashing.
        """
        slicing = sl[0:1, 0:5, 6:20, 30:40, 0:1]
        result = self.op.Output[slicing].wait()
        assert result.shape == slicing2shape(slicing)

    def testWithSeeds(self):
        """
        Bare-minimum test: Just make sure we can request the output without crashing.
        """
        seeds = numpy.zeros(self.inputData.shape, dtype=numpy.uint32)
        self.op.SeedImage.setValue(seeds)

        slicing = sl[0:1, 0:5, 6:20, 30:40, 0:1]
        result = self.op.Output[slicing].wait()

        assert result.shape == slicing2shape(slicing)

    def testWithFullSeeds(self):
        """
        If every pixel is seeded, there's nothing for the watershed to do.
        Output should be a copy of the seeds
        """
        # Random seed data
        seeds = 4 * numpy.random.random(self.inputData.shape)
        seeds = seeds.astype(numpy.uint32)
        seeds += 1

        self.op.SeedImage.setValue(seeds)

        slicing = sl[0:1, 0:5, 6:20, 30:40, 0:1]
        result = self.op.Output[slicing].wait()

        assert result.shape == slicing2shape(slicing)
        assert (result == seeds[slicing]).all()

    def testDirtyInput(self):
        """
        Mark the input dirty and check to see that the output slot was notified of the right roi
        """
        dirtyRois = []

        def handleDirty(slot, roi):
            dirtyRois.append(roi)

        self.op.Output.notifyDirty(handleDirty)
        self.op.InputImage.setDirty(sl[0:1, 5:6, 45:55, 5:15, 0:1])

        assert len(dirtyRois) == 1, "Didn't get dirty notification"

        # Dirty region should include the padding (10 pixels)
        dirtySlice = dirtyRois[0].toSlice()
        assert dirtySlice == sl[0:1, 0:10, 35:65, 0:25, 0:1]

    def testDirtySeeds(self):
        """
        Mark the seed input dirty and check to see that the output slot was notified of the right roi
        """
        seeds = numpy.zeros(self.inputData.shape, dtype=numpy.uint32)
        self.op.SeedImage.setValue(seeds)

        dirtyRois = []

        def handleDirty(slot, roi):
            dirtyRois.append(roi)

        self.op.Output.notifyDirty(handleDirty)
        self.op.SeedImage.setDirty(sl[0:1, 5:6, 45:55, 5:15, 0:1])

        assert len(dirtyRois) == 1, "Didn't get dirty notification"

        # Dirty region should include the padding (10 pixels)
        dirtySlice = dirtyRois[0].toSlice()
        assert dirtySlice == sl[0:1, 0:10, 35:65, 0:25, 0:1]


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
