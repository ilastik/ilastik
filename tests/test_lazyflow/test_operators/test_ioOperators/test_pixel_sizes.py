import os

import pytest
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpTiffReader
import numpy as np
import tifffile
import vigra
import pathlib

from lazyflow.operators import OpArrayPiper
from lazyflow.operators.ioOperators import OpExportMultipageTiff, OpExport2DImage


@pytest.mark.parametrize(
    "image_path,checktags",
    [
        (f"/pix_res/2d.tif", {"x": (2, "cm"), "y": (7, "nm")}),
        (f"/pix_res/3d.tif", {"x": (11, "cm"), "y": (6, "mm"), "z": (2, "pm")}),
        (f"/pix_res/2d_t.tif", {"x": (50, "μm"), "y": (3, "pm"), "t": (3, "min")}),
        (f"/pix_res/3d_t.tif", {"x": (3, "mm"), "y": (5, ""), "z": (7, ""), "t": (3, "")}),
        (f"/pix_res/3d_c.tif", {"x": (2, "μm"), "y": (11, "nm"), "z": (13, "cm"), "c": ()}),
        (f"/pix_res/5d.tif", {"x": (17, "cm"), "y": (13, "pm"), "z": (8, "nm"), "c": (), "t": (3, "hr")}),
    ],
)
def test_read(image_path, checktags, inputdata_dir):  # checks
    actual_path = inputdata_dir + image_path
    op = OpTiffReader(graph=Graph())
    op.Filepath.setValue(actual_path)
    assert op.Output.ready()
    assert len(op.Output.meta.axistags) == len(checktags)
    for axis in checktags.keys():
        if axis == "c":
            continue
        (resolution, unit) = checktags[axis]
        tag = op.Output.meta.axistags[axis]
        assert tag.resolution == resolution
        assert tag.unit == unit


@pytest.mark.parametrize(
    "image_path,checktags, hyperstack",
    [
        (f"2d.tif", {"x": (2, "cm"), "y": (7, "nm")}, False),
        (f"3d_c.tif", {"x": (2, "μm"), "y": (11, "nm"), "z": (13, "cm"), "c": (0,)}, True),
        (f"3d.tif", {"x": (11, "cm"), "y": (6, "mm"), "z": (2, "pm")}, True),
        (f"2d_t.tif", {"x": (50, "μm"), "y": (3, "pm"), "t": (3, "sec")}, True),
        (f"3d_t.tif", {"x": (3, "mm"), "y": (5, "mm"), "z": (7, "mm"), "t": (3, "sec")}, True),
        (f"5d.tif", {"x": (17, "cm"), "y": (13, "pm"), "z": (8, "mm"), "c": (0,), "t": (3, "sec")}, True),
    ],
)
def test_write(image_path, checktags, hyperstack, inputdata_dir):
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
                    unit=(checktags[axis][1] if (axis in checktags and axis != "c") else ""),
                )
            )
        axistags = vigra.AxisTags(axis_infos)

        out_slot = op_data.Output
        out_slot.meta.axistags = axistags
        out_slot.setDirty()

        export = OpExportMultipageTiff(graph=graph) if hyperstack else OpExport2DImage(graph=graph)
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
        assert tag.unit == unit
