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
from lazyflow.utility.io_util import tiff_encoding
from ..test_ioOperators.testOpStreamingH5N5Reader import h5n5_file, data


def get_data_op_with_pixel_size_meta(graph, axes, shape, resolutions, units):
    data = np.random.default_rng(1337).integers(0, 255, shape).astype(np.uint16)
    tagged_data = vigra.taggedView(data, axes)
    for axis, res in zip(axes, resolutions):
        tagged_data.axistags.setResolution(axis, res)
    op = OpArrayPiper(graph=graph)
    op.Input.setValue(tagged_data)
    axis_units_dict = dict(zip(axes, units))
    if "c" in axis_units_dict:
        axis_units_dict.pop("c")
    op.Output.meta.axis_units = axis_units_dict
    return op


@pytest.mark.parametrize("axes, shape, resolutions, units", [
    (["y", "x"], (2, 3), [6.000024000096, 13], ["", ""]),
    (["y", "x"], (2, 3), [0.0, 13], ["μm", ""]),
    (["y", "x"], (2, 3), [0.0, 0.0], ["μm", "mm"]),
    (["y", "x"], (65, 58), [6.000024000096, 13], ["μm", "mm"]),
    (["y", "c", "x"], (2, 3, 3), [6.000024000096, 0.0, 13], ["", "", ""]),
    (["y", "c", "x"], (2, 3, 3), [6.000024000096, 10.0, 13], ["μm", "mistake", "mm"]),
    (["y", "c", "x"], (2, 3, 3), [0.0, 0.0, 13], ["μm", "", ""]),
    (["y", "c", "x"], (2, 3, 3), [0.0, 0.0, 0.0], ["μm", "", "mm"]),
    (["y", "c", "x"], (65, 2, 58), [6.000024000096, 0.0, 13], ["μm", "", "mm"]),
])
def test_write_OpExport2DImage(graph, tmp_path, axes, shape, resolutions, units):
    op_data = get_data_op_with_pixel_size_meta(graph, axes, shape, resolutions, units)
    target_path = str(tmp_path / "2d_export.tif")
    op_writer = OpExport2DImage(graph=graph)
    op_writer.Input.connect(op_data.Output)
    op_writer.Filepath.setValue(target_path)
    op_writer.run_export()

    with tifffile.TiffFile(target_path) as f:
        written_data = f.asarray()
        np.testing.assert_array_equal(written_data, op_data.Output.value)
        assert tiff_encoding.fromASCII(f.imagej_metadata["yunit"]) == units[axes.index("y")]
        assert tiff_encoding.fromASCII(f.imagej_metadata["unit"]) == units[axes.index("x")]
        page = f.series[0][0]
        assert page.axes == "YX"
        # page.resolution is in xy order
        assert np.isclose(page.resolution[0], 1 / resolutions[axes.index("x")], atol=1.0e-15)
        assert np.isclose(page.resolution[1], 1 / resolutions[axes.index("y")], atol=1.0e-15)
        assert f.imagej_metadata["spacing"] == 1  # z-resolution


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
