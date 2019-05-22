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
import sys
import logging

import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators import OpDummyData
from lazyflow.operators.opCachedLabelImage import _OpCachedLabelImage as OpCachedLabelImage

logger = logging.getLogger("tests.testOpCachedLabelImage")
labelerLogger = logging.getLogger("lazyflow.operators.opCachedLabelImage")


class TestOpCachedLabelImage(object):
    def testBasic(self):
        graph = Graph()
        # OpDummyData needs an input array to decide what shape/dtype/axes to make the output
        a = numpy.ndarray(shape=(2, 100, 100, 100, 3), dtype=numpy.uint32)
        v = a.view(vigra.VigraArray)
        v.axistags = vigra.defaultAxistags("txyzc")

        # OpDummyData provides a simple binary image with a bunch of thick diagonal planes.
        opData = OpDummyData(graph=graph)
        opData.Input.setValue(v)
        assert opData.Output.ready()
        assert opData.Output.meta.axistags is not None

        data = opData.Output[:].wait()
        # logger.debug( "data:\n{}".format( str(data[0,:80:5,:80:5,0,0])) )

        # Each diagonal plane should get it's own label...
        op = OpCachedLabelImage(graph=graph)
        op.Input.connect(opData.Output)
        assert op.Output.ready()

        labels = op.Output[:].wait()
        # logger.debug( "labels:\n{}".format( str(labels[0,:80:5,:80:5,0,0])) )

    def testWithCustomBackground(self):
        graph = Graph()
        # OpDummyData needs an input array to decide what shape/dtype/axes to make the output
        a = numpy.ndarray(shape=(2, 100, 100, 100, 3), dtype=numpy.uint32)
        v = a.view(vigra.VigraArray)
        v.axistags = vigra.defaultAxistags("txyzc")

        # OpDummyData provides a simple binary image with a bunch of thick diagonal planes.
        opData = OpDummyData(graph=graph)
        opData.Input.setValue(v)
        assert opData.Output.ready()
        assert opData.Output.meta.axistags is not None

        # Each diagonal plane should get it's own label...
        op = OpCachedLabelImage(graph=graph)
        op.Input.connect(opData.Output)
        op.BackgroundLabels.setValue([0, 1, 0])  # Use inverted background for the second channel
        assert op.Output.ready()

        data = opData.Output[:].wait()
        labels = op.Output[:].wait()
        channel = 0
        # logger.debug( "data-c0:\n{}".format( str(data[0,:80:5,:80:5,0,channel])) )
        # logger.debug( "labels-c0:\n{}".format( str(labels[0,:80:5,:80:5,0,channel])) )

        channel = 1
        # logger.debug( "data-c1:\n{}".format( str(data[0,:80:5,:80:5,0,channel])) )
        # logger.debug( "labels-c1:\n{}".format( str(labels[0,:80:5,:80:5,0,channel])) )

        assert labels[0, 0, 0, 0, 0] == 1
        assert labels[0, 0, 0, 0, 1] == 0, "Expected inverted background for the second channel"


if __name__ == "__main__":
    # Set up logging for debug
    logger.setLevel(logging.DEBUG)
    labelerLogger.setLevel(logging.DEBUG)

    # Run nose
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)

    if not ret:
        sys.exit(1)
