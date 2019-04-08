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
from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators import OpArrayPiper, OpMultiInputConcatenater


class TestMultiInputConcatenater(object):
    def test(self):
        g = Graph()

        array1 = numpy.zeros((1, 1), dtype=float)
        array2 = numpy.ones((2, 2), dtype=float)
        array3 = numpy.zeros((3, 3), dtype=float)

        array4 = numpy.zeros((4, 4), dtype=float)
        array5 = numpy.zeros((5, 5), dtype=float)
        array6 = numpy.zeros((6, 6), dtype=float)

        array2[0, 0] = 0.123
        array6[0, 0] = 0.456

        opIn0Provider = OperatorWrapper(OpArrayPiper, graph=g)

        # We will provide 2 lists to concatenate
        # The first is provided by a separate operator which we set up in advance
        opIn0Provider.Input.resize(3)
        opIn0Provider.Input[0].setValue(array1)
        opIn0Provider.Input[1].setValue(array2)
        opIn0Provider.Input[2].setValue(array3)

        op = OpMultiInputConcatenater(graph=g)
        op.Inputs.resize(2)  # Two lists to concatenate

        # Connect the first list
        op.Inputs[0].connect(opIn0Provider.Output)

        # Set up the second list directly via setValue() (no external operator)
        op.Inputs[1].resize(3)
        op.Inputs[1][0].setValue(array4)
        op.Inputs[1][1].setValue(array5)
        op.Inputs[1][2].setValue(array6)

        # print op.Inputs[0][0].meta
        # print op.Inputs[0][1].meta
        # print op.Inputs[0][2].meta
        # print op.Output[0].meta
        # print op.Output[1].meta
        # print op.Output[2].meta

        assert len(op.Output) == 6
        assert op.Output[0].meta.shape == array1.shape
        assert op.Output[5].meta.shape == array6.shape

        assert numpy.all(op.Output[1][...].wait() == array2[...])
        assert numpy.all(op.Output[5][...].wait() == array6[...])

        op.Inputs[0].removeSlot(1, 2)

        # print len(op.Output)
        assert len(op.Output) == 5
        assert op.Output[0].meta.shape == array1.shape
        assert op.Output[4].meta.shape == array6.shape

        assert numpy.all(op.Output[1][...].wait() == array3[...])
        assert numpy.all(op.Output[4][...].wait() == array6[...])


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
