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
#		   http://ilastik.org/license/
###############################################################################

__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Feb 26, 2015 12:02:29 EST$"



import numpy

import vigra

from lazyflow.graph import Graph
from lazyflow.operators.opArrayPiper import OpArrayPiper
from lazyflow.operators.opFillMaskArray import OpFillMaskArray


class TestOpFillMaskArray(object):
    def setUp(self):
        self.graph = Graph()

        self.operator_fill = OpFillMaskArray(graph=self.graph)
        self.operator_fill.InputArray.meta.axistags = vigra.AxisTags("txyzc")

    def test1(self):
        # Generate a random dataset and see if it we get the right masking from the operator.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        mask = numpy.zeros(data.shape, dtype=bool)

        # Mask borders of the expected output.
        left_slicing = (mask.ndim - 1) * (slice(None),) + (slice(None, 1),)
        right_slicing = (mask.ndim - 1) * (slice(None),) + (slice(-1, None),)
        for i in xrange(mask.ndim):
            left_slicing = left_slicing[-1:] + left_slicing[:-1]
            right_slicing = right_slicing[-1:] + right_slicing[:-1]

            mask[left_slicing] = True
            mask[right_slicing] = True

        data = numpy.ma.masked_array(
            data,
            mask=mask,
            shrink=False
        )

        expected_output = data.filled(numpy.nan)

        # Provide input read all output.
        self.operator_fill.InputArray.setValue(data)
        self.operator_fill.InputFillValue.setValue(numpy.nan)
        output = self.operator_fill.Output[None].wait()

        assert not isinstance(expected_output, numpy.ma.masked_array)
        assert (
            (expected_output == output) |
            (numpy.isnan(expected_output) & numpy.isnan(output))
        ).all()

    def test2(self):
        # Generate a dataset and grab chunks of it from the operator. The result should be the same as above.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        mask = numpy.zeros(data.shape, dtype=bool)

        # Mask borders of the expected output.
        left_slicing = (mask.ndim - 1) * (slice(None),) + (slice(None, 1),)
        right_slicing = (mask.ndim - 1) * (slice(None),) + (slice(-1, None),)
        for i in xrange(mask.ndim):
            left_slicing = left_slicing[-1:] + left_slicing[:-1]
            right_slicing = right_slicing[-1:] + right_slicing[:-1]

            mask[left_slicing] = True
            mask[right_slicing] = True

        data = numpy.ma.masked_array(
            data,
            mask=mask,
            shrink=False
        )

        expected_output = data.filled(numpy.nan)

        # Create array to store results. Don't keep original data.
        output = expected_output.copy()
        output[:] = 0
        output[:] = numpy.ma.nomask

        # Provide input and grab chunks.
        self.operator_fill.InputArray.setValue(data)
        self.operator_fill.InputFillValue.setValue(numpy.nan)
        output[:2] = self.operator_fill.Output[:2].wait()
        output[2:] = self.operator_fill.Output[2:].wait()

        assert not isinstance(expected_output, numpy.ma.masked_array)
        assert (
            (expected_output == output) |
            (numpy.isnan(expected_output) & numpy.isnan(output))
        ).all()

    def tearDown(self):
        # Take down operators
        self.operator_fill.InputArray.disconnect()
        self.operator_fill.Output.disconnect()
        self.operator_fill.cleanUp()


class TestOpFillMaskArray2(object):
    def setUp(self):
        self.graph = Graph()

        self.operator_fill = OpFillMaskArray(graph=self.graph)
        self.operator_identity = OpArrayPiper(graph=self.graph)

        self.operator_fill.InputArray.meta.axistags = vigra.AxisTags("txyzc")

        self.operator_identity.Input.connect(self.operator_fill.Output)

    def test1(self):
        # Generate a random dataset and see if it we get the right masking from the operator.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        mask = numpy.zeros(data.shape, dtype=bool)

        # Mask borders of the expected output.
        left_slicing = (mask.ndim - 1) * (slice(None),) + (slice(None, 1),)
        right_slicing = (mask.ndim - 1) * (slice(None),) + (slice(-1, None),)
        for i in xrange(mask.ndim):
            left_slicing = left_slicing[-1:] + left_slicing[:-1]
            right_slicing = right_slicing[-1:] + right_slicing[:-1]

            mask[left_slicing] = True
            mask[right_slicing] = True

        data = numpy.ma.masked_array(data,
                                     mask=mask,
                                     shrink=False
        )

        expected_output = data.filled(numpy.nan)

        # Provide input read all output.
        self.operator_fill.InputArray.setValue(data)
        self.operator_fill.InputFillValue.setValue(numpy.nan)
        output = self.operator_identity.Output[None].wait()

        assert not isinstance(expected_output, numpy.ma.masked_array)
        assert (
            (expected_output == output) |
            (numpy.isnan(expected_output) & numpy.isnan(output))
        ).all()

    def test2(self):
        # Generate a dataset and grab chunks of it from the operator. The result should be the same as above.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        mask = numpy.zeros(data.shape, dtype=bool)

        # Mask borders of the expected output.
        left_slicing = (mask.ndim - 1) * (slice(None),) + (slice(None, 1),)
        right_slicing = (mask.ndim - 1) * (slice(None),) + (slice(-1, None),)
        for i in xrange(mask.ndim):
            left_slicing = left_slicing[-1:] + left_slicing[:-1]
            right_slicing = right_slicing[-1:] + right_slicing[:-1]

            mask[left_slicing] = True
            mask[right_slicing] = True

        data = numpy.ma.masked_array(data,
                                     mask=mask,
                                     shrink=False
        )

        expected_output = data.filled(numpy.nan)

        # Create array to store results. Don't keep original data.
        output = expected_output.copy()
        output[:] = 0
        output[:] = numpy.ma.nomask

        # Provide input and grab chunks.
        self.operator_fill.InputArray.setValue(data)
        self.operator_fill.InputFillValue.setValue(numpy.nan)
        output[:2] = self.operator_identity.Output[:2].wait()
        output[2:] = self.operator_identity.Output[2:].wait()

        assert not isinstance(expected_output, numpy.ma.masked_array)
        assert (
            (expected_output == output) |
            (numpy.isnan(expected_output) & numpy.isnan(output))
        ).all()

    def tearDown(self):
        # Take down operators
        self.operator_identity.Input.disconnect()
        self.operator_identity.Output.disconnect()
        self.operator_identity.cleanUp()


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
