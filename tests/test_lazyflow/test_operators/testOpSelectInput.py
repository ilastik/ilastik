###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2022, the ilastik developers
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
from lazyflow.operators import OpArrayPiper, OpSelectInput
import pytest


def array_piper(data, graph):
    op = OpArrayPiper(graph=graph)
    op.Input.setValue(data)
    return op


def test_value(graph):
    data1 = numpy.zeros(1) + 42
    data2 = numpy.zeros(1) + 123

    opdata1 = array_piper(data1, graph)
    opdata2 = array_piper(data2, graph)

    op = OpSelectInput(graph=graph)

    op.UseSecondInput.setValue(False)
    op.Input1.connect(opdata1.Output)
    op.Input2.connect(opdata2.Output)

    assert op.Output.value == data1

    op.UseSecondInput.setValue(True)

    assert op.Output.value == data2


@pytest.mark.parametrize(
    "shape1,shape2",
    [
        (999, 1000),
        ((10, 12, 13), (10, 12, 12)),
    ],
)
def test_raises_shape(shape1, shape2, graph):
    opdata1 = array_piper(numpy.random.random(shape1), graph)
    opdata2 = array_piper(numpy.random.random(shape2), graph)

    op = OpSelectInput(graph=graph)

    op.Input1.connect(opdata1.Output)

    with pytest.raises(ValueError):
        op.Input2.connect(opdata2.Output)


@pytest.mark.parametrize(
    "dtype1,dtype2",
    [
        ("float32", "float64"),
        ("float64", "int32"),
    ],
)
def test_raises_dtype(dtype1, dtype2, graph):
    opdata1 = array_piper(numpy.random.random(42).astype(dtype1), graph)
    opdata2 = array_piper(numpy.random.random(42).astype(dtype2), graph)

    op = OpSelectInput(graph=graph)

    op.Input1.connect(opdata1.Output)

    with pytest.raises(ValueError):
        op.Input2.connect(opdata2.Output)


def test_dirty_selected(graph):
    data1 = numpy.zeros(1) + 42
    data2 = numpy.zeros(1) + 123

    opdata1 = array_piper(data1, graph)
    opdata2 = array_piper(data2, graph)

    op = OpSelectInput(graph=graph)
    op.UseSecondInput.setValue(False)
    op.Input1.connect(opdata1.Output)
    op.Input2.connect(opdata2.Output)

    dirty = False

    def _dirty(*args, **kwargs):
        nonlocal dirty
        dirty = True

    op.Output.notifyDirty(_dirty)

    opdata1.Input.setValue(data1 + 42)

    assert dirty


def test_suppress_dirty_nonselected(graph):
    data1 = numpy.zeros(1) + 42
    data2 = numpy.zeros(1) + 123

    opdata1 = array_piper(data1, graph)
    opdata2 = array_piper(data2, graph)

    op = OpSelectInput(graph=graph)
    op.UseSecondInput.setValue(False)
    op.Input1.connect(opdata1.Output)
    op.Input2.connect(opdata2.Output)

    dirty = False

    def _dirty(*args, **kwargs):
        nonlocal dirty
        dirty = True

    op.Output.notifyDirty(_dirty)

    opdata2.Input.setValue(data2 + 42)

    assert not dirty
