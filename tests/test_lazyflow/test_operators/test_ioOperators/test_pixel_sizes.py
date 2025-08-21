import json
import h5py
import pytest
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpTiffReader, OpH5N5WriterBigDataset
import xml.etree.ElementTree as ET
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
    op.Output.meta.axis_units = axis_units_dict
    return op


@pytest.mark.parametrize(
    "axes, shape, resolutions, units",
    [
        (["y", "x"], (2, 3), [6.000024000096, 13], ["", ""]),
        (["y", "x"], (2, 3), [0.0, 13], ["μm", ""]),
        (["y", "x"], (2, 3), [0.0, 0.0], ["μm", "mm"]),
        (["y", "x"], (65, 58), [6.000024000096, 13], ["μm", "mm"]),
        (["y", "c", "x"], (2, 3, 3), [6.000024000096, 0.0, 13], ["", "", ""]),
        (["y", "c", "x"], (2, 3, 3), [6.000024000096, 10.0, 13], ["μm", "mistake", "mm"]),
        (["y", "c", "x"], (2, 3, 3), [0.0, 0.0, 13], ["μm", "", ""]),
        (["y", "c", "x"], (2, 3, 3), [0.0, 0.0, 0.0], ["μm", "", "mm"]),
        (["y", "c", "x"], (65, 2, 58), [6.000024000096, 0.0, 13], ["μm", "", "mm"]),
    ],
)
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
        assert np.isclose(
            page.resolution[0],
            0 if resolutions[axes.index("x")] == 0 else (1 / resolutions[axes.index("x")]),
            atol=1.0e-15,
        )
        assert np.isclose(
            page.resolution[1],
            0 if resolutions[axes.index("y")] == 0 else (1 / resolutions[axes.index("y")]),
            atol=1.0e-15,
        )
        assert f.imagej_metadata["spacing"] == 1  # z-resolution


@pytest.mark.parametrize(
    "axes, shape, resolutions, units",
    [
        (["y", "x"], (65, 58), [6.000024000096, 13], ["μm", "mm"]),
        (["c", "y", "x"], (2, 65, 58), [0.0, 6.000024000096, 13], ["", "μm", "mm"]),
        (
            ["z", "y", "x"],
            (2, 3, 5),
            [0.54321, 6.000024000096, 13],
            ["", "", ""],
        ),  # tifffile doesn't work with x smaller 5
        (["z", "y", "x"], (2, 3, 5), [0.0, 0.0, 13], ["μm", "", "cm"]),
        (["z", "y", "x"], (2, 3, 5), [0.0, 0.0, 0.0], ["μm", "mm", "cm"]),
        (["z", "y", "x"], (23, 65, 58), [0.54321, 6.000024000096, 13], ["μm", "mm", "cm"]),
        (["z", "c", "y", "x"], (3, 2, 3, 5), [0.54321, 0.0, 6.000024000096, 13], ["", "", "", ""]),
        (["z", "c", "y", "x"], (3, 2, 3, 5), [0.54321, 42, 6.000024000096, 13], ["μm", "mistake", "mm", "micron"]),
        (["z", "c", "y", "x"], (3, 2, 3, 5), [0.0, 0.0, 0.0, 0.0], ["μm", "", "mm", "microns"]),
        (["z", "c", "y", "x"], (23, 2, 65, 58), [0.54321, 0.0, 6.000024000096, 13], ["μm", "", "mm", "cm"]),
        (["t", "z", "y", "x"], (15, 23, 65, 58), [120, 0.54321, 6.000024000096, 13], ["sec", "μm", "mm", "cm"]),
        (["t", "z", "c", "y", "x"], (6, 2, 3, 3, 5), [120, 0.54321, 0.0, 6.000024000096, 13], ["", "", "", "", ""]),
        (
            ["t", "z", "c", "y", "x"],
            (2, 3, 6, 3, 5),
            [120, 0.54321, 42, 6.000024000096, 13],
            ["μm", "mm", "mistake", "sec", "micron"],
        ),
        (["t", "z", "c", "y", "x"], (6, 2, 3, 3, 5), [0.0, 0.0, 0.0, 0.0, 0.0], ["sec", "μm", "", "mm", "microns"]),
        (
            ["t", "z", "c", "y", "x"],
            (6, 2, 3, 3, 5),
            [-120, 0.54321, 0.0, 6.000024000096, 13],
            ["negative-sec", "μm", "", "mm", "microns"],
        ),
        (
            ["t", "z", "c", "y", "x"],
            (15, 23, 2, 65, 58),
            [120, 0.54321, 0.0, 6.000024000096, 13],
            ["ms", "μm", "", "mm", "cm"],
        ),
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

        xml = ET.fromstring(f.ome_metadata)
        ns = {"ome": "http://www.openmicroscopy.org/Schemas/OME/2016-06"}
        image = xml.find("ome:Image", ns)
        pixels = image.find("ome:Pixels", ns)
        assert image and pixels
        sizes = {
            "x": ("PhysicalSizeX", "PhysicalSizeXUnit"),
            "y": ("PhysicalSizeY", "PhysicalSizeYUnit"),
            "z": ("PhysicalSizeZ", "PhysicalSizeZUnit"),
            "t": ("TimeIncrement", "TimeIncrementUnit"),
        }

        comp_axes = "".join(axes).upper()
        assert comp_axes == f.series[0].axes

        for axis in axes:
            if axis.lower() == "c":
                assert "c" not in sizes.keys()  # Channel sizes are not written to TIFF
                continue
            assert tiff_encoding.fromASCII(pixels.attrib.get(sizes[axis][1], "")) == units[axes.index(axis)]
            assert float(pixels.attrib.get(sizes[axis][0], 0)) == resolutions[axes.index(axis)]


@pytest.mark.parametrize(
    "axes, shape, resolutions, units",
    [
        (["y", "x"], (65, 58), [6.000024000096, 13], ["μm", "mm"]),
        (["c", "y", "x"], (2, 65, 58), [0.0, 6.000024000096, 13], ["", "μm", "mm"]),
        (
            ["z", "y", "x"],
            (2, 3, 5),
            [0.54321, 6.000024000096, 13],
            ["", "", ""],
        ),  # tifffile doesn't work with x smaller 5
        (["z", "y", "x"], (2, 3, 5), [0.0, 0.0, 13], ["μm", "", "cm"]),
        (["z", "y", "x"], (2, 3, 5), [0.0, 0.0, 0.0], ["μm", "mm", "cm"]),
        (["z", "y", "x"], (23, 65, 58), [0.54321, 6.000024000096, 13], ["μm", "mm", "cm"]),
        (["z", "c", "y", "x"], (3, 2, 3, 5), [0.54321, 0.0, 6.000024000096, 13], ["", "", "", ""]),
        (["z", "c", "y", "x"], (3, 2, 3, 5), [0.54321, 42, 6.000024000096, 13], ["μm", "mistake", "mm", "micron"]),
        (["z", "c", "y", "x"], (3, 2, 3, 5), [0.0, 0.0, 0.0, 0.0], ["μm", "", "mm", "microns"]),
        (["z", "c", "y", "x"], (23, 2, 65, 58), [0.54321, 0.0, 6.000024000096, 13], ["μm", "", "mm", "cm"]),
        (["t", "z", "y", "x"], (15, 23, 65, 58), [120, 0.54321, 6.000024000096, 13], ["sec", "μm", "mm", "cm"]),
        (["t", "z", "c", "y", "x"], (6, 2, 3, 3, 5), [120, 0.54321, 0.0, 6.000024000096, 13], ["", "", "", "", ""]),
        (
            ["t", "z", "c", "y", "x"],
            (2, 3, 6, 3, 5),
            [120, 0.54321, 42, 6.000024000096, 13],
            ["μm", "mm", "mistake", "sec", "micron"],
        ),
        (["t", "z", "c", "y", "x"], (6, 2, 3, 3, 5), [0.0, 0.0, 0.0, 0.0, 0.0], ["sec", "μm", "", "mm", "microns"]),
        (
            ["t", "z", "c", "y", "x"],
            (6, 2, 3, 3, 5),
            [-120, 0.54321, 0.0, 6.000024000096, 13],
            ["negative-sec", "μm", "", "mm", "microns"],
        ),
        (
            ["t", "z", "c", "y", "x"],
            (15, 23, 2, 65, 58),
            [120, 0.54321, 0.0, 6.000024000096, 13],
            ["ms", "μm", "", "mm", "cm"],
        ),
    ],
)
def test_write_OpH5N5WriterBigDataset(graph, tmp_path, axes, shape, resolutions, units):

    op_data = get_data_op_with_pixel_size_meta(graph, axes, shape, resolutions, units)
    file_path = tmp_path / f"3d_image.h5"
    file = h5py.File(file_path, "w")
    group = file.create_group("volume")
    opWriter = OpH5N5WriterBigDataset(graph=graph)
    opWriter.h5N5File.setValue(group)
    opWriter.h5N5Path.setValue("data")
    opWriter.Image.connect(op_data.Output)

    try:
        assert opWriter.WriteImage.value  # Trigger write
    finally:
        file.close()
    del file

    file = h5py.File(file_path, "r")
    dataset = file["volume/data"]
    assert dataset.attrs["axistags"]
    assert dataset.attrs["axis_units"]
    axistags = vigra.AxisTags.fromJSON(dataset.attrs["axistags"])
    axis_units = json.loads(dataset.attrs["axis_units"])
    assert axes == axistags.keys()
    for axis in axes:
        assert axis_units[axis] == units[axes.index(axis)]
        assert float(axistags[axis].resolution) == resolutions[axes.index(axis)]


@pytest.mark.parametrize(
    "image_path,expected_meta",
    [
        ("/pix_res/2d.tif", {"x": (2, "cm"), "y": (7, "nm")}),
        ("/pix_res/2d_zero_division.tif", {"x": (0, "cm"), "y": (0, "mm")}),
        ("/pix_res/2d_stringified_tuple.tif", {"x": (5, "cm"), "y": (6.000024000096, "nm")}),
        ("/pix_res/3d.tif", {"x": (11.000011000011, "cm"), "y": (6.000024000096, "mm"), "z": (2, "pm")}),
        ("/pix_res/2d_t.tif", {"x": (50, "μm"), "y": (3, "pm"), "t": (3, "min")}),
        ("/pix_res/3d_t.tif", {"x": (3, "mm"), "y": (5, ""), "z": (7, ""), "t": (3, "")}),
        ("/pix_res/3d_c.tif", {"x": (2, "μm"), "y": (11.000011000011, "nm"), "z": (13, "cm"), "c": (0.0, "")}),
        (
            "/pix_res/5d.tif",
            {
                "x": (17.00015300137701, "cm"),
                "y": (13.000013000013, "pm"),
                "z": (8, "nm"),
                "c": (0.0, ""),
                "t": (3, "hr"),
            },
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
        if axis == "c":  # Channel sizes are not written to TIFF
            assert op.Output.meta.axistags[axis].resolution == 0
            assert axis not in op.Output.meta.axis_units.keys()
            continue
        (resolution, unit) = expected_meta[axis]
        tag = op.Output.meta.axistags[axis]
        assert tag.resolution == resolution
        assert op.Output.meta.axis_units[axis] == unit


def test_read_OpStreamingH5N5Reader(graph, h5n5_file, data):
    axistags = vigra.defaultAxistags("xyzct")
    resolutions = [1.0, 2.0, 3.0, 4.0, 5.0]
    for axis, res in zip(axistags, resolutions):
        axistags.setResolution(axis.key, res)
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
    op_data = get_data_op_with_pixel_size_meta(
        graph, ["c", "y", "x"], (2, 58, 67), [0.0, 6.000024000096, 13], ["", "μm", "mm"]
    )
    out_path = str(tmp_path / "2d_export.tif")
    export = OpExport2DImage(graph=graph)
    export.Input.connect(op_data.Output)
    export.Filepath.setValue(out_path)
    export.run_export()

    # read written file
    reader = OpTiffReader(graph=graph)
    reader.Filepath.setValue(out_path)
    assert reader.Output.ready()

    expected_meta = {"c": (0.0, ""), "y": (6.000024000096, "μm"), "x": (13, "mm")}
    assert len(reader.Output.meta.axistags) == 3
    for axis in reader.Output.meta.getAxisKeys():
        if axis == "c":
            assert reader.Output.meta.axistags[axis].resolution == 0
            assert axis not in reader.Output.meta.axis_units
            continue
        (resolution, unit) = expected_meta[axis]
        tag = reader.Output.meta.axistags[axis]
        # Resolution is represented in tifftags as a Rational.
        # Ironically, the way the numbers are stored is only precise to 8 decimal places.
        # Probably tifffile's fault, because the Rational is two 32-bit integers,
        # but tifffile just puts the uint32 max value into the denominator and basically rescales the numerator.
        assert np.isclose(tag.resolution, resolution, atol=1e-8)
        assert reader.Output.meta.axis_units[axis] == unit


def test_write_read_roundtrip_tiff_OpExportMultipageTiff(graph, tmp_path):
    op_data = get_data_op_with_pixel_size_meta(
        graph,
        ["t", "z", "c", "y", "x"],
        (5, 45, 2, 58, 67),
        [5.0, 7.0, 0.0, 6.000024000096, 13],
        ["sec", "cm", "", "μm", "mm"],
    )
    out_path = str(tmp_path / "3d_export.tif")
    export = OpExportMultipageTiff(graph=graph)
    export.Input.connect(op_data.Output)
    export.Filepath.setValue(out_path)
    export.run_export()

    # read written file
    reader = OpTiffReader(graph=graph)
    reader.Filepath.setValue(out_path)
    assert reader.Output.ready()

    expected_meta = {"t": (5.0, "sec"), "z": (7.0, "cm"), "y": (6.000024000096, "μm"), "x": (13, "mm")}
    assert len(reader.Output.meta.axistags) == 5
    for axis in reader.Output.meta.getAxisKeys():
        if axis == "c":
            assert reader.Output.meta.axistags[axis].resolution == 0
            assert axis not in reader.Output.meta.axis_units
            continue
        (resolution, unit) = expected_meta[axis]
        tag = reader.Output.meta.axistags[axis]
        # Rounding is not necessary here as ome stores resolution as floats
        assert tag.resolution == resolution
        assert reader.Output.meta.axis_units[axis] == unit


def test_write_read_roundtrip_h5(
    graph,
    tmp_path,
    axes=["c", "y", "x"],
    shape=(2, 58, 67),
    resolutions=[0.0, 6.000024000096, 13],
    units=["", "μm", "mm"],
):

    op_data = get_data_op_with_pixel_size_meta(graph, axes, shape, resolutions, units)

    file_path = tmp_path / f"3d_image.h5"
    file = h5py.File(file_path, "w")
    group = file.create_group("volume")

    opWriter = OpH5N5WriterBigDataset(graph=graph)
    opWriter.h5N5File.setValue(group)
    opWriter.h5N5Path.setValue("data")
    opWriter.Image.connect(op_data.Output)
    try:
        assert opWriter.WriteImage.value
    finally:
        file.close()
    del file

    reader = OpStreamingH5N5Reader(graph=graph)
    reader.H5N5File.setValue(OpStreamingH5N5Reader.get_h5_n5_file(file_path))
    reader.InternalPath.setValue("volume/data")
    meta = reader.OutputImage.meta

    assert meta.getAxisKeys() == axes
    for axis in axes:
        assert meta.axistags[axis].resolution == resolutions[axes.index(axis)]
        assert meta.axis_units[axis] == units[axes.index(axis)]
