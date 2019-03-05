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

import contextlib
import pathlib
import tempfile
from typing import Any, Callable

import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operator import Operator
from lazyflow.operators.ioOperators import OpExportMultipageTiff
from lazyflow.operators.ioOperators.opTiffReader import OpTiffReader
from lazyflow.operators.opArrayPiper import OpArrayPiper
from lazyflow.operators.opReorderAxes import OpReorderAxes


class _Pipeline:
    def __init__(self, **op_init_kwargs):
        self._op_init_kwargs = op_init_kwargs
        self._ops = []

    def append(self, op_callable: Callable[..., Operator], **value_slots: Any) -> None:
        op = op_callable(**self._op_init_kwargs)
        for name, value in value_slots.items():
            if self and name == "Input":
                raise ValueError(
                    'Setting value of the input slot "Input" is allowed only for the first operator in the pipeline'
                )
            op.inputs[name].setValue(value)
        if self:
            op.Input.connect(self[-1].Output)
        self._ops.append(op)

    def __len__(self) -> int:
        return self._ops.__len__()

    def __getitem__(self, item: int) -> Operator:
        return self._ops.__getitem__(item)

    def close(self) -> None:
        for op in reversed(self._ops):
            op.cleanUp()


def test_OpExportMultipageTiff():
    shape = 3, 10, 64, 128, 2
    axes = "tzyxc"
    dtype = numpy.uint32
    data = numpy.arange(numpy.prod(shape), dtype=dtype).reshape(shape)
    expected = vigra.VigraArray(data, axistags=vigra.defaultAxistags(axes), order="C")

    with tempfile.TemporaryDirectory() as tempdir:
        filepath = str(pathlib.Path(tempdir, "multipage.tiff"))
        graph = Graph()

        write_tiff = _Pipeline(graph=graph)
        write_tiff.append(OpArrayPiper, Input=expected)
        write_tiff.append(OpExportMultipageTiff, Filepath=filepath)
        with contextlib.closing(write_tiff):
            write_tiff[-1].run_export()

        read_tiff = _Pipeline(graph=graph)
        read_tiff.append(OpTiffReader, Filepath=filepath)
        read_tiff.append(OpReorderAxes, AxisOrder=axes)
        with contextlib.closing(read_tiff):
            actual = read_tiff[-1].Output[:].wait().astype(dtype)

    numpy.testing.assert_array_equal(expected, actual)
