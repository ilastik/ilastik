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
from lazyflow.operators.ioOperators.opTiffReader import OpTiffReader
from lazyflow.operators.opArrayPiper import OpArrayPiper
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.utility import Pipeline
from lazyflow.operators.ioOperators import OpExportMultipageTiff, OpExport2DImage

import os

import pytest

import numpy as np
import tifffile
import vigra
import pathlib


def test_OpExportMultipageTiff(tmp_path):
    shape = 3, 10, 64, 128, 2
    axes = "tzyxc"
    dtype = numpy.uint32
    data = numpy.arange(numpy.prod(shape), dtype=dtype).reshape(shape)
    expected = vigra.VigraArray(data, axistags=vigra.defaultAxistags(axes), order="C")

    filepath = str(tmp_path / "multipage.tiff")
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


@pytest.mark.parametrize(
    "image_path,checktags",
    [
        (f"3d_c.tif", {"x": (2, "μm"), "y": (11, "nm"), "z": (13, "cm"), "c": (0,)}),
        (f"3d.tif", {"x": (11, "cm"), "y": (6, "mm"), "z": (2, "pm")}),
        (f"2d_t.tif", {"x": (50, "μm"), "y": (3, "pm"), "t": (3, "sec")}),
        (f"3d_t.tif", {"x": (3, "mm"), "y": (5, "mm"), "z": (7, "mm"), "t": (3, "sec")}),
        (f"5d.tif", {"x": (17, "cm"), "y": (13, "pm"), "z": (8, "mm"), "c": (0,), "t": (3, "sec")}),
    ],
)
def test_write_units(image_path, checktags, inputdata_dir):
    in_path = inputdata_dir + f"/pix_res/" + image_path
    out_path = inputdata_dir + f"/pix_res/output/"
    if not os.path.isdir(out_path):
        os.mkdir(out_path)
    out_path += image_path

    graph = Graph()
    with tifffile.TiffFile(in_path) as tif:
        olddata = tif.asarray()
        data = olddata.squeeze()

        axes = tif.series[0].axes.lower()
        if "c" not in axes:
            axes += "c"
            data = data[..., np.newaxis]
        axis_infos = []
        axis_units = {}

        op_data = OpArrayPiper(graph=Graph())
        op_data.Input.setValue(data.astype(np.uint8))

        for axis in axes:
            axis_infos.append(
                vigra.AxisInfo(
                    key=axis,
                    resolution=checktags[axis][0] if axis in checktags else 0,
                    typeFlags=(
                        vigra.AxisType.Time
                        if axis == "t"
                        else vigra.AxisType.Channels if axis == "c" else vigra.AxisType.Space
                    ),
                )
            )
            if axis != "c" and axis in checktags:
                axis_units[axis] = checktags[axis][1]
        axistags = vigra.AxisTags(axis_infos)

        out_slot = op_data.Output
        out_slot.meta.axis_units = axis_units
        out_slot.meta.axistags = axistags
        out_slot.setDirty()

        export = OpExportMultipageTiff(graph=graph)
        export.Input.connect(op_data.Output)
        export.Filepath.setValue(out_path)
        export.run_export()

    # read written file
    op = OpTiffReader(graph=Graph())
    op.Filepath.setValue(out_path)
    assert op.Output.ready()
    assert len(op.Output.meta.axistags) == len(checktags)
    for axis in op.Output.meta.getAxisKeys():
        if axis == "c":
            continue
        resolution = checktags[axis][0]
        unit = checktags[axis][1]
        tag = op.Output.meta.axistags[axis]
        assert tag.resolution == resolution
        assert op.Output.meta.axis_units[axis] == unit
