import json
import os

import pytest
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpTiffReader
import numpy as np
import tifffile
import vigra

from lazyflow.operators import OpArrayPiper
from lazyflow.operators.ioOperators import OpExportMultipageTiff, OpExport2DImage, OpStreamingH5N5Reader
from ..test_ioOperators.testOpStreamingH5N5Reader import h5n5_file, data

@pytest.mark.parametrize(
    "image_path,checktags",
    [
        ("/pix_res/2d.tif", {"x": (2, "cm"), "y": (7, "nm")}),
        ("/pix_res/3d.tif", {"x": (11.000011000011, "cm"), "y": (6.000024000096, "mm"), "z": (2, "pm")}),
        ("/pix_res/2d_t.tif", {"x": (50, "μm"), "y": (3, "pm"), "t": (3, "min")}),
        ("/pix_res/3d_t.tif", {"x": (3, "mm"), "y": (5, ""), "z": (7, ""), "t": (3, "")}),
        ("/pix_res/3d_c.tif", {"x": (2, "μm"), "y": (11.000011000011, "nm"), "z": (13, "cm"), "c": ()}),
        (
            "/pix_res/5d.tif",
            {"x": (17.00015300137701, "cm"), "y": (13.000013000013, "pm"), "z": (8, "nm"), "c": (), "t": (3, "hr")},
        ),
    ],
)
def test_read_OpTiffReader(image_path, checktags, inputdata_dir):  # checks
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
        assert op.Output.meta.axis_units[axis] == unit


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
def test_write_OpExportMultipageTiff_read_OpTiffReader(image_path, checktags, inputdata_dir):
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


@pytest.mark.parametrize(
    "image_path,checktags, hyperstack",
    [
        ("2d.tif", {"x": (2, "cm"), "y": (7, "nm")}, False),
        ("3d_c.tif", {"x": (2, "μm"), "y": (11, "nm"), "z": (13, "cm"), "c": (0,)}, True),
        ("3d.tif", {"x": (11, "cm"), "y": (6, "mm"), "z": (2, "pm")}, True),
        ("2d_t.tif", {"x": (50, "μm"), "y": (3, "pm"), "t": (3, "sec")}, True),
        ("3d_t.tif", {"x": (3, "mm"), "y": (5, "mm"), "z": (7, "mm"), "t": (3, "sec")}, True),
        ("5d.tif", {"x": (17, "cm"), "y": (13, "pm"), "z": (8, "mm"), "c": (0,), "t": (3, "sec")}, True),
    ],
)
def test_write_OpExportMultipageTiff_OpExport2DImage_read_OpTiffReader(image_path, checktags, hyperstack, inputdata_dir):
    in_path = inputdata_dir + "/pix_res/" + image_path
    out_path = inputdata_dir + "/pix_res/output/"
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
        assert op.Output.meta.axis_units[axis] == unit


def test_read_OpStreamingH5N5Reader(graph, h5n5_file, data):
    axistags = vigra.defaultAxistags("xyzct")
    axis_units = {"x": "cm", "y": "μm", "z": "m", "t": "sec"}
    h5n5_file.create_group("volume").create_dataset("data", data=data)
    h5n5_file["volume/data"].attrs["axistags"] = axistags.toJSON()
    h5n5_file["volume/data"].attrs["axis_units"] = json.dumps(axis_units)
    op = OpStreamingH5N5Reader(graph=graph)
    op.H5N5File.setValue(h5n5_file)
    op.InternalPath.setValue("volume/data")

    assert op.OutputImage.meta.shape == data.shape
    assert op.OutputImage.meta.axistags == axistags
    assert op.OutputImage.meta.axis_units == axis_units
    np.testing.assert_array_equal(op.OutputImage.value, data)
