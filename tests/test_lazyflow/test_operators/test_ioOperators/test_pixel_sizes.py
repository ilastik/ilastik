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
    "axes, shape, resolutions, units",
    [
        (["y", "x"], (65, 58), [6.000024000096, 13], ["μm", "mm"]),
        (["c", "y", "x"], (2, 65, 58), [0.0, 6.000024000096, 13], ["", "μm", "mm"]),
        (["z", "y", "x"], (2, 3, 5), [0.54321, 6.000024000096, 13], ["", "", ""]),  # tifffile doesn't work with x smaller 5
        (["z", "y", "x"], (2, 3, 5), [0.0, 0.0, 13], ["μm", "", "cm"]),
        (["z", "y", "x"], (2, 3, 5), [0.0, 0.0, 0.0], ["μm", "mm", "cm"]),
        (["z", "y", "x"], (23, 65, 58), [0.54321, 6.000024000096, 13], ["μm", "mm", "cm"]),
        (["z", "c", "y", "x"], (3, 2, 3, 5), [0.54321, 0.0, 6.000024000096, 13], ["", "", "", ""]),
        (["z", "c", "y", "x"], (3, 2, 3, 5), [0.54321, 42, 6.000024000096, 13], ["μm", "mistake", "mm", "micron"]),
        (["z", "c", "y", "x"], (3, 2, 3, 5), [0.0, 0.0, 0.0, 0.0], ["μm", "", "mm", "microns"]),
        (["z", "c", "y", "x"], (23, 2, 65, 58), [0.54321, 0.0, 6.000024000096, 13], ["μm", "", "mm", "cm"]),
        (["t", "z", "y", "x"], (15, 23, 65, 58), [120, 0.54321, 6.000024000096, 13], ["sec", "μm", "mm", "cm"]),
        (["t", "z", "c", "y", "x"], (6, 2, 3, 3, 5), [120, 0.54321, 0.0, 6.000024000096, 13], ["", "", "", "", ""]),
        (["t", "z", "c", "y", "x"], (2, 3, 6, 3, 5), [120, 0.54321, 42, 6.000024000096, 13], ["μm", "mm", "mistake", "sec", "micron"]),
        (["t", "z", "c", "y", "x"], (6, 2, 3, 3, 5), [0.0, 0.0, 0.0, 0.0, 0.0], ["sec", "μm", "", "mm", "microns"]),
        (["t", "z", "c", "y", "x"], (6, 2, 3, 3, 5), [-120, 0.54321, 0.0, 6.000024000096, 13], ["negative-sec", "μm", "", "mm", "microns"]),
        (["t", "z", "c", "y", "x"], (15, 23, 2, 65, 58), [120, 0.54321, 0.0, 6.000024000096, 13], ["ms", "μm", "", "mm", "cm"]),
    ],
)
def test_write_OpExportMultipageTiff(graph, tmp_path, axes, shape, resolutions, units):
    op_data = get_data_op_with_pixel_size_meta(graph, axes, shape, resolutions, units)
    out_path = str(tmp_path / "3d_export.tif")
    export = OpExportMultipageTiff(graph=graph)
    export.Input.connect(op_data.Output)
    export.Filepath.setValue(out_path)
    export.run_export()

    with tifffile.TiffFile(out_path) as f:
        written_data = f.asarray()
        np.testing.assert_array_equal(written_data, op_data.Output.value)
        if "t" in axes:
            pass  # todo
        else:
            pass  # todo
        # todo - see OpExport2DImage test for reference, need to parse ome-xml here to extract the written values


def test_write_OpH5N5WriterBigDataset():
    pass  # todo


@pytest.mark.parametrize(
    "image_path,expected_meta",
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
def test_read_OpTiffReader(image_path, expected_meta, inputdata_dir):
    file_path = inputdata_dir + image_path
    op = OpTiffReader(graph=Graph())
    op.Filepath.setValue(file_path)
    assert op.Output.ready()
    assert len(op.Output.meta.axistags) == len(expected_meta)
    for axis in expected_meta.keys():
        assert axis in op.Output.meta.axistags
        if axis == "c":
            assert op.Output.meta.axistags[axis].resolution == 0
            assert axis not in op.Output.meta.axis_units
            continue
        (resolution, unit) = expected_meta[axis]
        tag = op.Output.meta.axistags[axis]
        assert tag.resolution == resolution
        assert op.Output.meta.axis_units[axis] == unit


def test_read_OpStreamingH5N5Reader(graph, h5n5_file, data):
    axistags = vigra.defaultAxistags("xyzct")
    # TODO: resolution numbers
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


def test_write_read_roundtrip_tiff_OpExport2DImage(graph, tmp_path):
    op_data = get_data_op_with_pixel_size_meta(graph,
                                               ["c", "y", "x"], (2, 58, 67),
                                               [0.0, 6.000024000096, 13], ["", "μm", "mm"])
    out_path = str(tmp_path / "3d_export.tif")
    export = OpExport2DImage(graph=graph)
    export.Input.connect(op_data.Output)
    export.Filepath.setValue(out_path)
    export.run_export()

    # read written file
    reader = OpTiffReader(graph=graph)
    reader.Filepath.setValue(out_path)
    assert reader.Output.ready()

    expected_meta = {"y": (6.000024000096, "μm"), "x": (13, "mm")}
    assert len(reader.Output.meta.axistags) == 3
    for axis in reader.Output.meta.getAxisKeys():
        if axis == "c":
            assert op.Output.meta.axistags[axis].resolution == 0
            assert axis not in op.Output.meta.axis_units
            continue
        (resolution, unit) = expected_meta[axis]
        tag = reader.Output.meta.axistags[axis]
        # Resolution is represented in tifftags as a Rational.
        # Ironically, the way the numbers are stored is only precise to 8 decimal places.
        # Probably tifffile's fault, because the Rational is two 32-bit integers,
        # but tifffile just puts the uint32 max value into the denominator and basically rescales the numerator.
        assert np.isclose(tag.resolution, resolution, atol=1e-8)
        assert reader.Output.meta.axis_units[axis] == unit

def test_write_read_roundtrip_tiff_OpExportMultipageTiff():
    pass # todo

def test_write_read_roundtrip_h5():
    pass  # todo
