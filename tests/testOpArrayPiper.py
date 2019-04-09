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

__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Feb 06, 2015 12:28:04 EST$"


import nose

import numpy

import vigra

from lazyflow.graph import Graph
from lazyflow.operators.opArrayPiper import OpArrayPiper
from lazyflow.roi import roiFromShape, roiToSlice


class AllowMaskException(Exception):
    pass


class TestOpArrayPiper(object):
    def setup_method(self, method):
        self.graph = Graph()

        self.operator_identity = OpArrayPiper(graph=self.graph)

        self.operator_identity.Input.meta.axistags = vigra.AxisTags("txyzc")

    def test1(self):
        # Generate a random dataset and see if it we get the right masking from the operator.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)

        # Provide input read all output.
        self.operator_identity.Input.setValue(data)
        output = self.operator_identity.Output[None].wait()

        assert (data == output).all()

    def test2(self):
        # Generate a dataset and grab chunks of it from the operator. The result should be the same as above.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)

        # Create array to store results. Don't keep original data.
        output = data.copy()
        output[:] = 0

        # Provide input and grab chunks.
        self.operator_identity.Input.setValue(data)
        output[:2] = self.operator_identity.Output[:2].wait()
        output[2:] = self.operator_identity.Output[2:].wait()

        assert (data == output).all()

    def test3(self):
        # Generate a random dataset and see if it we get the right masking from the operator.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)

        # Provide input read all output.
        self.operator_identity.Input.setValue(numpy.zeros_like(data))
        output = self.operator_identity.Output[None].wait()

        assert (output == 0).all()

        # Try setInSlot
        data_shape_roi = roiFromShape(data.shape)
        data_shape_slice = roiToSlice(*data_shape_roi)
        self.operator_identity.Input[data_shape_slice] = data
        output = self.operator_identity.Output[None].wait()

        assert (data == output).all()

    def teardown_method(self, method):
        # Take down operators
        self.operator_identity.Input.disconnect()
        self.operator_identity.Output.disconnect()
        self.operator_identity.cleanUp()


class TestOpArrayPiper2(object):
    def setup_method(self, method):
        self.graph = Graph()

        self.operator_identity = OpArrayPiper(graph=self.graph)

        self.operator_identity.Input.meta.axistags = vigra.AxisTags("txyzc")
        self.operator_identity.Input.meta.has_mask = True

    def test1(self):
        # Generate a random dataset and see if it we get the right masking from the operator.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        data = numpy.ma.masked_array(data, mask=numpy.zeros(data.shape, dtype=bool), shrink=False)

        # Provide input read all output.
        self.operator_identity.Input.setValue(data)
        output = self.operator_identity.Output[None].wait()

        assert (data == output).all()
        assert data.mask.shape == output.mask.shape
        assert (data.mask == output.mask).all()

    def test2(self):
        # Generate a dataset and grab chunks of it from the operator. The result should be the same as above.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        data = numpy.ma.masked_array(data, mask=numpy.zeros(data.shape, dtype=bool), shrink=False)

        # Create array to store results. Don't keep original data.
        output = data.copy()
        output[:] = 0
        output[:] = numpy.ma.nomask

        # Provide input and grab chunks.
        self.operator_identity.Input.setValue(data)
        output[:2] = self.operator_identity.Output[:2].wait()
        output[2:] = self.operator_identity.Output[2:].wait()

        assert (data == output).all()
        assert data.mask.shape == output.mask.shape
        assert (data.mask == output.mask).all()

    def test3(self):
        # Generate a random dataset and see if it we get the right masking from the operator.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        data = numpy.ma.masked_array(data, mask=numpy.zeros(data.shape, dtype=bool), shrink=False)

        # Provide input read all output.
        self.operator_identity.Input.setValue(numpy.zeros_like(data))
        output = self.operator_identity.Output[None].wait()

        assert (output == 0).all()
        assert data.mask.shape == output.mask.shape
        assert (output.mask == False).all()

        # Try setInSlot
        data_shape_roi = roiFromShape(data.shape)
        data_shape_slice = roiToSlice(*data_shape_roi)
        self.operator_identity.Input[data_shape_slice] = data
        output = self.operator_identity.Output[None].wait()

        assert (data == output).all()
        assert data.mask.shape == output.mask.shape
        assert (data.mask == output.mask).all()

    def teardown_method(self, method):
        # Take down operators
        self.operator_identity.Input.disconnect()
        self.operator_identity.Output.disconnect()
        self.operator_identity.cleanUp()


class TestOpArrayPiper3(object):
    def setup_method(self, method):
        self.graph = Graph()

        self.operator_identity = OpArrayPiper(graph=self.graph)

        self.operator_identity.Input.meta.axistags = vigra.AxisTags("txyzc")

    def test1(self):
        # Generate a random dataset and see if it we get the right masking from the operator.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        data = numpy.ma.masked_array(data, mask=numpy.zeros(data.shape, dtype=bool), shrink=False)

        # Provide input read all output.
        self.operator_identity.Input.setValue(data)
        assert self.operator_identity.Input.meta.has_mask
        assert self.operator_identity.Output.meta.has_mask
        output = self.operator_identity.Output[None].wait()

        assert (data == output).all()
        assert data.mask.shape == output.mask.shape
        assert (data.mask == output.mask).all()

    def test2(self):
        # Generate a dataset and grab chunks of it from the operator. The result should be the same as above.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        data = numpy.ma.masked_array(data, mask=numpy.zeros(data.shape, dtype=bool), shrink=False)

        # Create array to store results. Don't keep original data.
        output = data.copy()
        output[:] = 0
        output[:] = numpy.ma.nomask

        # Provide input and grab chunks.
        self.operator_identity.Input.setValue(data)
        assert self.operator_identity.Input.meta.has_mask
        assert self.operator_identity.Output.meta.has_mask
        output[:2] = self.operator_identity.Output[:2].wait()
        output[2:] = self.operator_identity.Output[2:].wait()

        assert (data == output).all()
        assert data.mask.shape == output.mask.shape
        assert (data.mask == output.mask).all()

    def test3(self):
        # Generate a random dataset and see if it we get the right masking from the operator.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        data = numpy.ma.masked_array(data, mask=numpy.zeros(data.shape, dtype=bool), shrink=False)

        # Provide input read all output.
        self.operator_identity.Input.setValue(numpy.zeros_like(data))
        assert self.operator_identity.Input.meta.has_mask
        assert self.operator_identity.Output.meta.has_mask
        output = self.operator_identity.Output[None].wait()

        assert (output == 0).all()
        assert data.mask.shape == output.mask.shape
        assert (output.mask == False).all()

        # Try setInSlot
        data_shape_roi = roiFromShape(data.shape)
        data_shape_slice = roiToSlice(*data_shape_roi)
        self.operator_identity.Input[data_shape_slice] = data
        output = self.operator_identity.Output[None].wait()

        assert (data == output).all()
        assert data.mask.shape == output.mask.shape
        assert (data.mask == output.mask).all()

    def teardown_method(self, method):
        # Take down operators
        self.operator_identity.Input.disconnect()
        self.operator_identity.Output.disconnect()
        self.operator_identity.cleanUp()


class TestOpArrayPiper4(object):
    def setup_method(self, method):
        self.graph = Graph()

        self.operator_identity = OpArrayPiper(graph=self.graph)
        self.operator_identity.Input.allow_mask = False
        self.operator_identity.Output.allow_mask = False
        self.operator_identity.Input.meta.has_mask = False
        self.operator_identity.Output.meta.has_mask = False

        self.operator_identity.Input.meta.axistags = vigra.AxisTags("txyzc")

    @nose.tools.raises(AllowMaskException)
    def test1(self):
        # Generate a random dataset and see if it we get the right masking from the operator.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        data = numpy.ma.masked_array(data, mask=numpy.zeros(data.shape, dtype=bool), shrink=False)

        # Provide input read all output.
        try:
            self.operator_identity.Input.setValue(data)
        except AssertionError as e:
            raise AllowMaskException(str(e))

    @nose.tools.raises(AllowMaskException)
    def test2(self):
        # Generate a dataset and grab chunks of it from the operator. The result should be the same as above.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        data = numpy.ma.masked_array(data, mask=numpy.zeros(data.shape, dtype=bool), shrink=False)

        # Create array to store results. Don't keep original data.
        output = data.copy()
        output[:] = 0
        output[:] = numpy.ma.nomask

        # Provide input and grab chunks.
        try:
            self.operator_identity.Input.setValue(data)
        except AssertionError as e:
            raise AllowMaskException(str(e))

    @nose.tools.raises(AllowMaskException)
    def test3(self):
        # Generate a random dataset and see if it we get the right masking from the operator.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        data = numpy.ma.masked_array(data, mask=numpy.zeros(data.shape, dtype=bool), shrink=False)

        # Provide input read all output.
        try:
            self.operator_identity.Input.setValue(numpy.zeros_like(data))
        except AssertionError as e:
            raise AllowMaskException(str(e))

    def teardown_method(self, method):
        # Take down operators
        self.operator_identity.Input.disconnect()
        self.operator_identity.Output.disconnect()
        self.operator_identity.cleanUp()


class TestOpArrayPiper5(object):
    def setup_method(self, method):
        self.graph = Graph()

        self.operator_identity = OpArrayPiper(graph=self.graph)
        self.operator_identity.Input.allow_mask = False
        self.operator_identity.Output.allow_mask = False

        self.operator_identity.Input.meta.axistags = vigra.AxisTags("txyzc")

    @nose.tools.raises(AllowMaskException)
    def test1(self):
        # Generate a random dataset and see if it we get the right masking from the operator.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        data = numpy.ma.masked_array(data, mask=numpy.zeros(data.shape, dtype=bool), shrink=False)

        # Provide input read all output.
        try:
            self.operator_identity.Input.setValue(data)
        except AssertionError as e:
            raise AllowMaskException(str(e))

    @nose.tools.raises(AllowMaskException)
    def test2(self):
        # Generate a dataset and grab chunks of it from the operator. The result should be the same as above.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        data = numpy.ma.masked_array(data, mask=numpy.zeros(data.shape, dtype=bool), shrink=False)

        # Create array to store results. Don't keep original data.
        output = data.copy()
        output[:] = 0
        output[:] = numpy.ma.nomask

        # Provide input and grab chunks.
        try:
            self.operator_identity.Input.setValue(data)
        except AssertionError as e:
            raise AllowMaskException(str(e))

    @nose.tools.raises(AllowMaskException)
    def test3(self):
        # Generate a random dataset and see if it we get the right masking from the operator.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        data = numpy.ma.masked_array(data, mask=numpy.zeros(data.shape, dtype=bool), shrink=False)

        # Provide input read all output.
        try:
            self.operator_identity.Input.setValue(numpy.zeros_like(data))
        except AssertionError as e:
            raise AllowMaskException(str(e))

    def teardown_method(self, method):
        # Take down operators
        self.operator_identity.Input.disconnect()
        self.operator_identity.Output.disconnect()
        self.operator_identity.cleanUp()


class TestOpArrayPiper6(object):
    def setup_method(self, method):
        self.graph = Graph()

        self.operator_identity_1 = OpArrayPiper(graph=self.graph)
        self.operator_identity_2 = OpArrayPiper(graph=self.graph)
        self.operator_identity_2.Input.allow_mask = False
        self.operator_identity_2.Output.allow_mask = False

        self.operator_identity_1.Input.meta.axistags = vigra.AxisTags("txyzc")
        self.operator_identity_2.Input.meta.axistags = vigra.AxisTags("txyzc")

    @nose.tools.raises(AllowMaskException)
    def test1(self):
        # Explicitly set has_mask for the input
        self.operator_identity_1.Input.meta.has_mask = True
        self.operator_identity_1.Output.meta.has_mask = True

        # Try to connect the incompatible operators.
        try:
            self.operator_identity_2.Input.connect(self.operator_identity_1.Output)
        except AssertionError as e:
            raise AllowMaskException(str(e))

    @nose.tools.raises(AllowMaskException)
    def test2(self):
        # Generate a dataset and grab chunks of it from the operator. The result should be the same as above.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        data = numpy.ma.masked_array(data, mask=numpy.zeros(data.shape, dtype=bool), shrink=False)

        # Implicitly set has_mask for the input by setting the value.
        self.operator_identity_1.Input.setValue(data)

        # Try to connect the incompatible operators.
        try:
            self.operator_identity_2.Input.connect(self.operator_identity_1.Output)
        except AssertionError as e:
            raise AllowMaskException(str(e))

    def teardown_method(self, method):
        # Take down operators
        self.operator_identity_2.Input.disconnect()
        self.operator_identity_2.Output.disconnect()
        self.operator_identity_2.cleanUp()
        self.operator_identity_1.Input.disconnect()
        self.operator_identity_1.Output.disconnect()
        self.operator_identity_1.cleanUp()


class TestOpArrayPiper7(object):
    def setup_method(self, method):
        self.graph = Graph()

        self.operator_identity_1 = OpArrayPiper(graph=self.graph)
        self.operator_identity_2 = OpArrayPiper(graph=self.graph)

        self.operator_identity_1.Input.meta.axistags = vigra.AxisTags("txyzc")
        self.operator_identity_2.Input.meta.axistags = vigra.AxisTags("txyzc")

    def test1(self):
        # Explicitly set has_mask for the input
        self.operator_identity_1.Input.meta.has_mask = True
        self.operator_identity_1.Output.meta.has_mask = True

        # Generate a dataset and grab chunks of it from the operator. The result should be the same as above.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        data = numpy.ma.masked_array(data, mask=numpy.zeros(data.shape, dtype=bool), shrink=False)

        # Try to connect the compatible operators.
        self.operator_identity_2.Input.connect(self.operator_identity_1.Output)
        self.operator_identity_1.Input.setValue(data)
        output = self.operator_identity_2.Output[None].wait()

        assert (data == output).all()
        assert data.mask.shape == output.mask.shape
        assert (data.mask == output.mask).all()

    def test2(self):
        # Generate a dataset and grab chunks of it from the operator. The result should be the same as above.
        data = numpy.random.random((4, 5, 6, 7, 3)).astype(numpy.float32)
        data = numpy.ma.masked_array(data, mask=numpy.zeros(data.shape, dtype=bool), shrink=False)

        # Try to connect the compatible operators.
        self.operator_identity_1.Input.setValue(data)
        self.operator_identity_2.Input.connect(self.operator_identity_1.Output)
        output = self.operator_identity_2.Output[None].wait()

        assert (data == output).all()
        assert data.mask.shape == output.mask.shape
        assert (data.mask == output.mask).all()

    def teardown_method(self, method):
        # Take down operators
        self.operator_identity_2.Input.disconnect()
        self.operator_identity_2.Output.disconnect()
        self.operator_identity_2.cleanUp()
        self.operator_identity_1.Input.disconnect()
        self.operator_identity_1.Output.disconnect()
        self.operator_identity_1.cleanUp()
