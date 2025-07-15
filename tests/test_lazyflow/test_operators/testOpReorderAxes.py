from builtins import range

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
import unittest
import random
import vigra
import numpy

import pytest
from vigra import AxisType

from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
from lazyflow.request.request import RequestError
from lazyflow.roi import TinyVector
from lazyflow.roi import roiToSlice

from lazyflow.operators.opReorderAxes import OpReorderAxes

# Use logging instead of print statements ...
import logging

from lazyflow.utility.resolution import UnitAxisTags, UnitAxisInfo

logger = logging.getLogger(__name__)


class OpArrayProvider(Operator):

    Input = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)

    def execute(self, slot, subindex, out_roi, result):
        assert not isinstance(
            result, vigra.VigraArray
        ), "The 'write into' view passed to upstream operators must not be a VigraArray."
        self.Input(out_roi.start, out_roi.stop).writeInto(result).wait()
        return result

    def propagateDirty(self, inputSlot, subindex, in_roi):
        pass


class TestOpReorderAxes(unittest.TestCase):
    def setup_method(self, method):
        self.array = None
        self.axis = list("tzyxc")
        self.tests = 20
        self.graph = Graph()
        self.operator = OpReorderAxes(graph=self.graph)

    def prepareVolnOp(self, possible_axes="tzyxc", num=5, AxisOrder=None, config_via_init=False):
        tagStr = "".join(random.sample(possible_axes, random.randint(2, num)))
        axisTags = vigra.defaultAxistags(tagStr)

        self.shape = [random.randint(20, 30) for tag in axisTags]

        self.array = numpy.random.rand(*self.shape) * 255
        self.array = (float(250) / 255 * self.array + 5).astype(int)
        self.inArray = vigra.VigraArray(self.array, axistags=axisTags)

        opProvider = OpArrayProvider(graph=self.graph)
        opProvider.Input.setValue(self.inArray)

        if config_via_init:
            self.operator = OpReorderAxes(graph=self.graph, Input=opProvider.Output, AxisOrder=AxisOrder)
        else:
            self.operator.Input.connect(opProvider.Output)
            if AxisOrder is not None:
                self.operator.AxisOrder.setValue(AxisOrder)

    def test_Full(self):
        for i in range(self.tests):
            self.prepareVolnOp()
            result = self.operator.Output().wait()
            logger.debug("------------------------------------------------------")
            logger.debug("self.array.shape = " + str(self.array.shape))
            logger.debug("type(input) == " + str(type(self.operator.Input.value)))
            logger.debug("input.shape == " + str(self.operator.Input.meta.shape))
            logger.debug("Input Tags:")
            logger.debug(str(self.operator.Input.meta.axistags))
            logger.debug("Output Tags:")
            logger.debug(str(self.operator.Output.meta.axistags))
            logger.debug("type(result) == " + str(type(result)))
            logger.debug("result.shape == " + str(result.shape))
            logger.debug("------------------------------------------------------")

            # Check the shape
            assert len(result.shape) == 5

            assert not isinstance(
                result, vigra.VigraArray
            ), "For compatibility with generic code, output should be provided as a plain numpy array."

            # Ensure the result came out in default order
            assert self.operator.Output.meta.axistags == vigra.defaultAxistags("tzyxc")

            # Check the data
            vresult = result.view(vigra.VigraArray)
            vresult.axistags = self.operator.Output.meta.axistags
            reorderedInput = self.inArray.withAxes(*[tag.key for tag in vresult.axistags])
            assert numpy.all(vresult == reorderedInput)

    def test_Roi_default_order(self):
        for i in range(self.tests):
            self.prepareVolnOp()
            shape = self.operator.Output.meta.shape
            roi = [None, None]
            roi[1] = [numpy.random.randint(2, s) if s != 1 else 1 for s in shape]
            roi[0] = [numpy.random.randint(0, roi[1][i]) if s != 1 else 0 for i, s in enumerate(shape)]
            roi[0] = TinyVector(roi[0])
            roi[1] = TinyVector(roi[1])
            result = self.operator.Output(roi[0], roi[1]).wait()
            logger.debug("------------------------------------------------------")
            logger.debug("self.array.shape = " + str(self.array.shape))
            logger.debug("type(input) == " + str(type(self.operator.Input.value)))
            logger.debug("input.shape == " + str(self.operator.Input.meta.shape))
            logger.debug("Input Tags:")
            logger.debug(str(self.operator.Input.meta.axistags))
            logger.debug("Output Tags:")
            logger.debug(str(self.operator.Output.meta.axistags))
            logger.debug("roi= " + str(roi))
            logger.debug("type(result) == " + str(type(result)))
            logger.debug("result.shape == " + str(result.shape))
            logger.debug("------------------------------------------------------")

            # Check the shape
            assert len(result.shape) == 5
            assert not isinstance(
                result, vigra.VigraArray
            ), "For compatibility with generic code, output should be provided as a plain numpy array."

            # Ensure the result came out in volumina order
            assert self.operator.Output.meta.axistags == vigra.defaultAxistags("tzyxc")

            # Check the data
            vresult = result.view(vigra.VigraArray)
            vresult.axistags = self.operator.Output.meta.axistags
            reorderedInput = self.inArray.withAxes(*[tag.key for tag in self.operator.Output.meta.axistags])
            assert numpy.all(vresult == reorderedInput[roiToSlice(roi[0], roi[1])])

    def test_Roi_custom_order(self):
        self._impl_roi_custom_order("cztxy")
        self._impl_roi_custom_order("xyz")

    def _impl_roi_custom_order(self, axisorder):
        for i in range(self.tests):
            config_via_init = bool(i % 2)
            # Specify a strange order for the output axis tags
            self.prepareVolnOp(axisorder, len(axisorder) - 1, AxisOrder=axisorder, config_via_init=config_via_init)

            shape = self.operator.Output.meta.shape

            roi = [None, None]
            roi[1] = [numpy.random.randint(2, s) if s != 1 else 1 for s in shape]
            roi[0] = [numpy.random.randint(0, roi[1][i]) if s != 1 else 0 for i, s in enumerate(shape)]
            roi[0] = TinyVector(roi[0])
            roi[1] = TinyVector(roi[1])
            result = self.operator.Output(roi[0], roi[1]).wait()
            logger.debug("------------------------------------------------------")
            logger.debug("self.array.shape = " + str(self.array.shape))
            logger.debug("type(input) == " + str(type(self.operator.Input.value)))
            logger.debug("input.shape == " + str(self.operator.Input.meta.shape))
            logger.debug("Input Tags:")
            logger.debug(str(self.operator.Input.meta.axistags))
            logger.debug("Output Tags:")
            logger.debug(str(self.operator.Output.meta.axistags))
            logger.debug("roi= " + str(roi))
            logger.debug("type(result) == " + str(type(result)))
            logger.debug("result.shape == " + str(result.shape))
            logger.debug("------------------------------------------------------")

            # Check the shape
            assert len(result.shape) == len(axisorder)

            assert not isinstance(
                result, vigra.VigraArray
            ), "For compatibility with generic code, output should be provided as a plain numpy array."

            # Ensure the result came out in the same strange order we asked for.
            assert self.operator.Output.meta.axistags == vigra.defaultAxistags(axisorder)

            # Check the data
            vresult = result.view(vigra.VigraArray)
            vresult.axistags = self.operator.Output.meta.axistags
            reorderedInput = self.inArray.withAxes(*[tag.key for tag in self.operator.Output.meta.axistags])
            assert numpy.all(vresult == reorderedInput[roiToSlice(roi[0], roi[1])])

    def test_insert_singleton_axis(self):
        for i in range(self.tests):
            self.prepareVolnOp("xyzc", 4)

            # Specify a strange order for the output axis tags
            self.operator.AxisOrder.setValue("yxtzc")
            shape = self.operator.Output.meta.shape

            roi = [None, None]
            roi[1] = [numpy.random.randint(2, s) if s != 1 else 1 for s in shape]
            roi[0] = [numpy.random.randint(0, roi[1][i]) if s != 1 else 0 for i, s in enumerate(shape)]
            roi[0] = TinyVector(roi[0])
            roi[1] = TinyVector(roi[1])
            result = self.operator.Output(roi[0], roi[1]).wait()
            logger.debug("------------------------------------------------------")
            logger.debug("self.array.shape = " + str(self.array.shape))
            logger.debug("type(input) == " + str(type(self.operator.Input.value)))
            logger.debug("input.shape == " + str(self.operator.Input.meta.shape))
            logger.debug("Input Tags:")
            logger.debug(str(self.operator.Input.meta.axistags))
            logger.debug("Output Tags:")
            logger.debug(str(self.operator.Output.meta.axistags))
            logger.debug("roi= " + str(roi))
            logger.debug("type(result) == " + str(type(result)))
            logger.debug("result.shape == " + str(result.shape))
            logger.debug("------------------------------------------------------")

            # Check the shape
            assert len(result.shape) == 5

            assert not isinstance(
                result, vigra.VigraArray
            ), "For compatibility with generic code, output should be provided as a plain numpy array."

            # Ensure the result came out in the same strange order we asked for.
            assert self.operator.Output.meta.axistags == vigra.defaultAxistags("yxtzc")

            # Check the data
            vresult = result.view(vigra.VigraArray)
            vresult.axistags = self.operator.Output.meta.axistags
            reorderedInput = self.inArray.withAxes(*[tag.key for tag in self.operator.Output.meta.axistags])
            assert numpy.all(vresult == reorderedInput[roiToSlice(roi[0], roi[1])])

    def test_attempt_drop_nonsingleton_axis(self):
        """
        Attempt to configure the operator with invalid settings by trying to drop a non-singleton axis.
        The execute method should assert in that case.
        """
        data = numpy.zeros((100, 100, 100), dtype=numpy.uint8)
        data = vigra.taggedView(data, vigra.defaultAxistags("xyz"))

        # Attempt to drop some axes that can't be dropped.
        op = OpReorderAxes(graph=Graph(), Input=data, AxisOrder="txc")

        # Make sure this results in an error.
        req = op.Output[:]

        with pytest.raises(RequestError):
            req.wait()

    def test_preserve_unit_axistags(self):
        source_op = OpArrayProvider(graph=self.graph)
        data = numpy.random.randint(0, 255, (100, 100))
        data = vigra.taggedView(data, vigra.defaultAxistags("yx"))
        source_op.Input.setValue(data)
        axes = [
            UnitAxisInfo(key="x", typeFlags=AxisType.Space, resolution=13.0, unit="nm"),
            UnitAxisInfo(key="y", typeFlags=AxisType.Space, resolution=5.0, unit="pizzas"),
        ]
        source_op.Output.meta.axistags = UnitAxisTags(axes)
        self.operator.Input.connect(source_op.Output)
        assert isinstance(self.operator.Output.meta.axistags, UnitAxisTags)
        assert (
            self.operator.Output.meta.axistags["x"] == axes[0]
        )  # we can't use "is" because reordered axis is a new object
        assert self.operator.Output.meta.axistags["y"] == axes[1]
        assert self.operator.Output.meta.axistags["x"].unit == "nm"
        assert self.operator.Output.meta.axistags["y"].unit == "pizzas"
        assert self.operator.Output.meta.axistags["x"].resolution == 13.0
        assert self.operator.Output.meta.axistags["y"].resolution == 5.0
