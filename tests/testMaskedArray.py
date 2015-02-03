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
__date__ = "$Feb 02, 2015 21:38:31 EST$"



import numpy

import vigra

from lazyflow.graph import Graph
from lazyflow.operator import Operator
from lazyflow.slot import InputSlot, OutputSlot


class OpMaskArrayIdentity(Operator):
    name = "OpMaskArrayIdentity"
    category = "Pointwise"


    Input = InputSlot()
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpMaskArrayIdentity, self ).__init__( *args, **kwargs )

    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.Input.meta )

    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()

        # Get data
        data = self.Input[key].wait()

        # Copy results
        if slot.name == 'Output':
            result[...] = data

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "Input":
            slicing = roi.toSlice()
            self.Output.setDirty(slicing)
        else:
            assert False, "Unknown dirty input slot"


class OpMaskArrayBorder(Operator):
    name = "OpMaskArrayBorder"
    category = "Pointwise"


    Input = InputSlot()

    Border = InputSlot(value=1, stype='int')

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpMaskArrayBorder, self ).__init__( *args, **kwargs )

    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.Input.meta )
        self.Output.meta.has_mask = True

    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()

        # Clean up key to follow certain rules.
        key = list(key)
        for i in xrange(len(key)):
            start = key[i].start
            stop = key[i].stop
            step = key[i].step

            if start is None:
                start = 0
            elif start < 0:
                start %= self.Input.meta.shape[i]

            if stop is None:
                stop = self.Input.meta.shape[i]
            elif stop < 0:
                stop %= self.Input.meta.shape[i]

            key[i] = slice(start, stop, step)

        key = tuple(key)

        # Get data
        data = self.Input[key].wait()
        border = abs(self.Border.value)

        # Make a masked array
        data = numpy.ma.masked_array(data, mask=numpy.zeros(data.shape, dtype=bool), shrink=False)

        # Using Input's shape, mask everything on the outside boundaries of Input (may not be on data).
        left_slicing = (len(self.Input.meta.shape) - 1) * (slice(None),) + (slice(None, border),)
        right_slicing = (len(self.Input.meta.shape) - 1) * (slice(None),) + (slice(-border, None),)
        for i in xrange(len(self.Input.meta.shape)):
            left_slicing = left_slicing[-1:] + left_slicing[:-1]
            right_slicing = right_slicing[-1:] + right_slicing[:-1]

            if key[i].start == 0:
                data[left_slicing] = numpy.ma.masked
            if key[i].stop == self.Input.meta.shape[i]:
                data[right_slicing] = numpy.ma.masked

        # Copy results
        if slot.name == 'Output':
            result[...] = data

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "Input":
            slicing = roi.toSlice()
            self.Output.setDirty(slicing)
        else:
            assert False, "Unknown dirty input slot"


class TestOpMaskArrayIdentity(object):
    def setUp(self):
        self.graph = Graph()

        self.operator_identity = OpMaskArrayIdentity(graph=self.graph)

        self.operator_identity.Input.meta.axistags = vigra.AxisTags("txyzc")
        self.operator_identity.Input.meta.has_mask = True

    def test1(self):
        # Generate a random dataset and see if it we get the right masking from the operator.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        expected_output = numpy.ma.masked_array(data.copy(),
                                                mask=numpy.zeros(data.shape, dtype=bool),
                                                shrink=False
                          )

        # Provide input read all output.
        self.operator_identity.Input.setValue(data)
        output = self.operator_identity.Output[None].wait()

        assert((expected_output == output).all())
        assert(expected_output.mask.shape == output.mask.shape)

    def test2(self):
        # Generate a dataset and grab chunks of it from the operator. The result should be the same as above.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        expected_output = numpy.ma.masked_array(data.copy(),
                                                mask=numpy.zeros(data.shape, dtype=bool),
                                                shrink=False
                          )

        # Create array to store results. Don't keep original data.
        output = expected_output.copy()
        output[:] = 0
        output[:] = numpy.ma.nomask

        # Provide input and grab chunks.
        self.operator_identity.Input.setValue(data)
        output[:2] = self.operator_identity.Output[:2].wait()
        output[2:] = self.operator_identity.Output[2:].wait()

        assert((expected_output == output).all())
        assert(expected_output.mask.shape == output.mask.shape)

    def tearDown(self):
        # Take down operators
        self.operator_identity.Input.disconnect()
        self.operator_identity.Output.disconnect()
        self.operator_identity.cleanUp()


class TestOpMaskArrayBorder(object):
    def setUp(self):
        self.graph = Graph()

        self.operator_border = OpMaskArrayBorder(graph=self.graph)
        self.operator_border.Input.meta.axistags = vigra.AxisTags("txyzc")

    def test1(self):
        # Generate a random dataset and see if it we get the right masking from the operator.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        expected_output = numpy.ma.masked_array(data.copy(),
                                                mask=numpy.zeros(data.shape, dtype=bool),
                                                shrink=False
                          )

        # Mask borders of the expected output.
        left_slicing = (expected_output.ndim - 1) * (slice(None),) + (slice(None, 1),)
        right_slicing = (expected_output.ndim - 1) * (slice(None),) + (slice(-1, None),)
        for i in xrange(expected_output.ndim):
            left_slicing = left_slicing[-1:] + left_slicing[:-1]
            right_slicing = right_slicing[-1:] + right_slicing[:-1]

            expected_output[left_slicing] = numpy.ma.masked
            expected_output[right_slicing] = numpy.ma.masked

        # Provide input read all output.
        self.operator_border.Input.setValue(data)
        output = self.operator_border.Output[None].wait()

        assert((expected_output == output).all())
        assert(expected_output.mask.shape == output.mask.shape)

    def test2(self):
        # Generate a dataset and grab chunks of it from the operator. The result should be the same as above.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        expected_output = numpy.ma.masked_array(data.copy(),
                                                mask=numpy.zeros(data.shape, dtype=bool),
                                                shrink=False
                          )

        # Mask borders of the expected output.
        left_slicing = (expected_output.ndim - 1) * (slice(None),) + (slice(None, 1),)
        right_slicing = (expected_output.ndim - 1) * (slice(None),) + (slice(-1, None),)
        for i in xrange(expected_output.ndim):
            left_slicing = left_slicing[-1:] + left_slicing[:-1]
            right_slicing = right_slicing[-1:] + right_slicing[:-1]

            expected_output[left_slicing] = numpy.ma.masked
            expected_output[right_slicing] = numpy.ma.masked


        # Create array to store results. Don't keep original data.
        output = expected_output.copy()
        output[:] = 0
        output[:] = numpy.ma.nomask

        # Provide input and grab chunks.
        self.operator_border.Input.setValue(data)
        output[:2] = self.operator_border.Output[:2].wait()
        output[2:] = self.operator_border.Output[2:].wait()

        assert((expected_output == output).all())
        assert(expected_output.mask.shape == output.mask.shape)

    def tearDown(self):
        # Take down operators
        self.operator_border.Input.disconnect()
        self.operator_border.Output.disconnect()
        self.operator_border.cleanUp()


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
