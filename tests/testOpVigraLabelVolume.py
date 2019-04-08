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
from lazyflow.operators.opVigraLabelVolume import _OpVigraLabelVolume as OpVigraLabelVolume
from lazyflow.utility.slicingtools import sl, slicing2shape


class TestOpVigraLabelVolume(object):
    def setup_method(self, method):
        graph = Graph()

        inputData = numpy.random.random((1, 10, 100, 100, 1))
        inputData = (inputData < 0.1).astype(numpy.uint8)
        inputData = inputData.view(vigra.VigraArray)
        inputData.axistags = vigra.defaultAxistags("txyzc")
        self.inputData = inputData

        self.op = OpVigraLabelVolume(graph=graph)
        self.op.Input.setValue(inputData)

    def testBasic(self):
        labeled = self.op.Output[...].wait()
        assert labeled.shape == self.inputData.shape

    def testBasicWithBackground(self):
        self.op.BackgroundValue.setValue(0)
        labeled = self.op.Output[...].wait()
        assert labeled.shape == self.inputData.shape


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
