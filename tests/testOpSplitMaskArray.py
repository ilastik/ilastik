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
__date__ = "$Feb 27, 2015 10:31:24 EST$"



import numpy

import vigra

from lazyflow.graph import Graph
from lazyflow.operators.opSplitMaskArray import OpSplitMaskArray


class TestOpSplitMaskArray(object):
    def setUp(self):
        self.graph = Graph()

        self.operator_split = OpSplitMaskArray(graph=self.graph)
        self.operator_split.Input.meta.axistags = vigra.AxisTags("txyzc")

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
            fill_value=data.dtype.type(numpy.nan),
            shrink=False
        )

        # Provide input read all output.
        self.operator_split.Input.setValue(data)
        output_array = self.operator_split.OutputArray[None].wait()
        output_mask = self.operator_split.OutputMask[None].wait()
        output_fill_value = self.operator_split.OutputFillValue[None].wait()

        assert not isinstance(output_array, numpy.ma.masked_array)
        assert not isinstance(output_mask, numpy.ma.masked_array)
        assert not isinstance(output_fill_value, numpy.ma.masked_array)
        assert output_array.dtype.type == data.dtype.type
        assert output_mask.dtype.type == data.mask.dtype
        assert output_fill_value.dtype.type == data.dtype.type
        assert (
            (data.data == output_array) |
            (numpy.isnan(data.data) & numpy.isnan(output_array))
        ).all()
        assert (data.mask == output_mask).all()
        assert (
            (data.fill_value[()] == output_fill_value) |
            (numpy.isnan(data.fill_value[()]) & numpy.isnan(output_fill_value))
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
            fill_value=data.dtype.type(numpy.nan),
            shrink=False
        )

        # Create array to store results. Don't keep original data.
        output_array = data.data.copy()
        output_array[:] = 0
        output_mask = data.mask.copy()
        output_mask[:] = False

        # Provide input and grab chunks.
        self.operator_split.Input.setValue(data)
        output_array[:2] = self.operator_split.OutputArray[:2].wait()
        output_mask[:2] = self.operator_split.OutputMask[:2].wait()
        output_array[2:] = self.operator_split.OutputArray[2:].wait()
        output_mask[2:] = self.operator_split.OutputMask[2:].wait()
        output_fill_value = self.operator_split.OutputFillValue[None].wait()

        assert not isinstance(output_array, numpy.ma.masked_array)
        assert not isinstance(output_mask, numpy.ma.masked_array)
        assert not isinstance(output_fill_value, numpy.ma.masked_array)
        assert output_array.dtype.type == data.dtype.type
        assert output_mask.dtype.type == data.mask.dtype
        assert output_fill_value.dtype.type == data.dtype.type
        assert (
            (data.data == output_array) |
            (numpy.isnan(data.data) & numpy.isnan(output_array))
        ).all()
        assert (data.mask == output_mask).all()
        assert (
            (data.fill_value[()] == output_fill_value) |
            (numpy.isnan(data.fill_value[()]) & numpy.isnan(output_fill_value))
        ).all()

    def tearDown(self):
        # Take down operators
        self.operator_split.Input.disconnect()
        self.operator_split.OutputArray.disconnect()
        self.operator_split.OutputMask.disconnect()
        self.operator_split.OutputFillValue.disconnect()
        self.operator_split.cleanUp()


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
