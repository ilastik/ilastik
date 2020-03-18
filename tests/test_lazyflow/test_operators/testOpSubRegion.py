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
from lazyflow.graph import Graph
from lazyflow.operators.opArrayPiper import OpArrayPiper
from lazyflow.operators.generic import OpSubRegion


class TestOpSubRegion(object):
    def testOutput(self):
        graph = Graph()
        data = numpy.random.random((1, 100, 100, 10, 1))
        opProvider = OpArrayPiper(graph=graph)
        opProvider.Input.setValue(data)

        opSubRegion = OpSubRegion(graph=graph)
        opSubRegion.Input.connect(opProvider.Output)

        opSubRegion.Roi.setValue(((0, 20, 30, 5, 0), (1, 30, 50, 8, 1)))

        subData = opSubRegion.Output(start=(0, 5, 10, 1, 0), stop=(1, 10, 20, 3, 1)).wait()
        assert (subData == data[0:1, 25:30, 40:50, 6:8, 0:1]).all()

    def testDirtyPropagation(self):
        graph = Graph()
        data = numpy.random.random((1, 100, 100, 10, 1))
        opProvider = OpArrayPiper(graph=graph)
        opProvider.Input.setValue(data)

        opSubRegion = OpSubRegion(graph=graph)
        opSubRegion.Input.connect(opProvider.Output)

        opSubRegion.Roi.setValue(((0, 20, 30, 5, 0), (1, 30, 50, 8, 1)))

        gotDirtyRois = []

        def handleDirty(slot, roi):
            gotDirtyRois.append(roi)

        opSubRegion.Output.notifyDirty(handleDirty)

        # Set an input dirty region that overlaps with the subregion
        key = numpy.s_[0:1, 15:35, 32:33, 0:10, 0:1]
        opProvider.Input.setDirty(key)

        assert len(gotDirtyRois) == 1
        assert gotDirtyRois[0].start == [0, 0, 2, 0, 0]
        assert gotDirtyRois[0].stop == [1, 10, 3, 3, 1]

        # Now mark a region that DOESN'T overlap with the subregion
        key = numpy.s_[0:1, 70:80, 32:33, 0:10, 0:1]
        opProvider.Input.setDirty(key)

        # Should have gotten no extra dirty notifications
        assert len(gotDirtyRois) == 1

    def testOutput_masked(self):
        graph = Graph()
        data = numpy.random.random((1, 100, 100, 10, 1))
        data = numpy.ma.masked_array(
            data, mask=numpy.ma.getmaskarray(data), fill_value=data.dtype.type(numpy.nan), shrink=False
        )
        data[:, 25] = numpy.ma.masked
        opProvider = OpArrayPiper(graph=graph)
        opProvider.Input.setValue(data)

        opSubRegion = OpSubRegion(graph=graph)
        opSubRegion.Input.connect(opProvider.Output)

        opSubRegion.Roi.setValue(((0, 20, 30, 5, 0), (1, 30, 50, 8, 1)))

        subData = opSubRegion.Output(start=(0, 5, 10, 1, 0), stop=(1, 10, 20, 3, 1)).wait()
        assert (subData == data[0:1, 25:30, 40:50, 6:8, 0:1]).all()
        assert (subData.mask == data.mask[0:1, 25:30, 40:50, 6:8, 0:1]).all()
        assert (
            (subData.fill_value == data.fill_value) | (numpy.isnan(subData.fill_value) & numpy.isnan(data.fill_value))
        ).all()

    def testDirtyPropagation_masked(self):
        graph = Graph()
        data = numpy.random.random((1, 100, 100, 10, 1))
        data = numpy.ma.masked_array(
            data, mask=numpy.ma.getmaskarray(data), fill_value=data.dtype.type(numpy.nan), shrink=False
        )
        data[:, 25] = numpy.ma.masked
        opProvider = OpArrayPiper(graph=graph)
        opProvider.Input.setValue(data)

        opSubRegion = OpSubRegion(graph=graph)
        opSubRegion.Input.connect(opProvider.Output)

        opSubRegion.Roi.setValue(((0, 20, 30, 5, 0), (1, 30, 50, 8, 1)))

        gotDirtyRois = []

        def handleDirty(slot, roi):
            gotDirtyRois.append(roi)

        opSubRegion.Output.notifyDirty(handleDirty)

        # Set an input dirty region that overlaps with the subregion
        key = numpy.s_[0:1, 15:35, 32:33, 0:10, 0:1]
        opProvider.Input.setDirty(key)

        assert len(gotDirtyRois) == 1
        assert gotDirtyRois[0].start == [0, 0, 2, 0, 0]
        assert gotDirtyRois[0].stop == [1, 10, 3, 3, 1]

        # Now mark a region that DOESN'T overlap with the subregion
        key = numpy.s_[0:1, 70:80, 32:33, 0:10, 0:1]
        opProvider.Input.setDirty(key)

        # Should have gotten no extra dirty notifications
        assert len(gotDirtyRois) == 1


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
