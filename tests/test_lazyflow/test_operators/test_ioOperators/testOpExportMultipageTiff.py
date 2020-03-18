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

import pathlib
import tempfile

import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpExportMultipageTiff
from lazyflow.operators.ioOperators.opTiffReader import OpTiffReader
from lazyflow.operators.opArrayPiper import OpArrayPiper
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.utility import Pipeline


def test_OpExportMultipageTiff():
    shape = 3, 10, 64, 128, 2
    axes = "tzyxc"
    dtype = numpy.uint32
    data = numpy.arange(numpy.prod(shape), dtype=dtype).reshape(shape)
    expected = vigra.VigraArray(data, axistags=vigra.defaultAxistags(axes), order="C")

    with tempfile.TemporaryDirectory() as tempdir:
        filepath = str(pathlib.Path(tempdir, "multipage.tiff"))
        graph = Graph()

        with Pipeline(graph=graph) as write_tiff:
            write_tiff.add(OpArrayPiper, Input=expected)
            write_tiff.add(OpExportMultipageTiff, Filepath=filepath)
            write_tiff[-1].run_export()

        with Pipeline(graph=graph) as read_tiff:
            read_tiff.add(OpTiffReader, Filepath=filepath)
            read_tiff.add(OpReorderAxes, AxisOrder=axes)
            actual = read_tiff[-1].Output[:].wait().astype(dtype)

    numpy.testing.assert_array_equal(expected, actual)
