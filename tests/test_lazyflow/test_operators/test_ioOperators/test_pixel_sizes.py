from lazyflow.graph import Graph
from lazyflow.operators import OpArrayPiper
from lazyflow.operators.ioOperators import OpTiffReader, OpExportMultipageTiff
import pytest
import xml.etree.ElementTree as ET
import numpy as np
import vigra
import tifffile


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
    "image_path,expected_meta",
    [
        ("/pix_res/2d.tif", {"x": (2, "cm"), "y": (7.000007000007, "nm")}),
        ("/pix_res/2d_zero_division.tif", {"x": (0, "cm"), "y": (0, "mm")}),
        ("/pix_res/2d_stringified_tuple.tif", {"x": (5, "cm"), "y": (6.000024000096, "nm")}),
        ("/pix_res/3d.tif", {"x": (11.000011000011, "cm"), "y": (6.000024000096, "mm"), "z": (2, "pm")}),
        ("/pix_res/2d_t.tif", {"x": (50, "μm"), "y": (3.000003000003, "pm"), "t": (3, "min")}),
        ("/pix_res/3d_t.tif", {"x": (3.000003000003, "mm"), "y": (5, ""), "z": (7, ""), "t": (3, "")}),
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
            continue
        (resolution, unit) = expected_meta[axis]
        tag = op.Output.meta.axistags[axis]
        assert tag.resolution == resolution
        assert op.Output.meta.axis_units[axis] == unit


@pytest.mark.parametrize(
    "axes, shape, resolutions, units",
    [
        (["y", "x"], (65, 58), [6.000024000096, 13], ["µm", "mm"]),
        (["c", "y", "x"], (2, 65, 58), [0.0, 6.000024000096, 13], ["", "µm", "mm"]),
        (
            ["z", "y", "x"],
            (2, 3, 5),
            [0.54321, 6.000024000096, 13],
            ["pixel", "pixel", "pixel"],
        ),  # tifffile doesn't work with x smaller 5
        (["z", "y", "x"], (2, 3, 5), [0.0, 0.0, 13], ["µm", "pixel", "cm"]),
        (["z", "y", "x"], (2, 3, 5), [0.0, 0.0, 0.0], ["µm", "mm", "cm"]),
        (["z", "y", "x"], (23, 65, 58), [0.54321, 6.000024000096, 13], ["µm", "mm", "cm"]),
        (["z", "c", "y", "x"], (3, 2, 3, 5), [0.54321, 0.0, 6.000024000096, 13], ["pixel", "", "pixel", "pixel"]),
        (["z", "c", "y", "x"], (3, 2, 3, 5), [0.54321, 42, 6.000024000096, 13], ["µm", "", "mm", "µm"]),
        (["z", "c", "y", "x"], (3, 2, 3, 5), [0.0, 0.0, 0.0, 0.0], ["µm", "", "mm", "nm"]),
        (["z", "c", "y", "x"], (23, 2, 65, 58), [0.54321, 0.0, 6.000024000096, 13], ["µm", "", "mm", "cm"]),
        (["t", "z", "y", "x"], (15, 23, 65, 58), [120, 0.54321, 6.000024000096, 13], ["s", "µm", "mm", "cm"]),
        (
            ["t", "z", "c", "y", "x"],
            (6, 2, 3, 3, 5),
            [120, 0.54321, 0.0, 6.000024000096, 13],
            ["pixel", "pixel", "", "pixel", "pixel"],
        ),
        (
            ["t", "z", "c", "y", "x"],
            (2, 3, 6, 3, 5),
            [120, 0.54321, 42, 6.000024000096, 13],
            ["µm", "mm", "", "ms", "µm"],
        ),
        (["t", "z", "c", "y", "x"], (6, 2, 3, 3, 5), [0.0, 0.0, 0.0, 0.0, 0.0], ["s", "µm", "", "mm", "µm"]),
        (
            ["t", "z", "c", "y", "x"],
            (6, 2, 3, 3, 5),
            [-120, 0.54321, 0.0, 6.000024000096, 13],
            ["s", "µm", "", "mm", "µm"],
        ),
        (
            ["t", "z", "c", "y", "x"],
            (15, 23, 2, 65, 58),
            [120, 0.54321, 0.0, 6.000024000096, 13],
            ["ms", "µm", "", "mm", "cm"],
        ),
    ],
)
def test_write_OpExportMultipageTiff(graph, tmp_path, axes, shape, resolutions, units):
    op_data = get_data_op_with_pixel_size_meta(graph, axes, shape, resolutions, units)
    out_path = str(tmp_path / "multipage_export.tif")
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
            assert pixels.attrib.get(sizes[axis][1], "") == units[axes.index(axis)]
            assert float(pixels.attrib.get(sizes[axis][0], 0)) == resolutions[axes.index(axis)]


def test_write_read_roundtrip_tiff_OpExportMultipageTiff(graph, tmp_path):
    op_data = get_data_op_with_pixel_size_meta(
        graph,
        ["t", "z", "c", "y", "x"],
        (5, 45, 2, 58, 67),
        [5.0, 7.0, 0.0, 6.000024000096, 13],
        ["seconds", "cm", "", "µm", "mm"],
    )
    out_path = str(tmp_path / "multipage_export.tif")
    export = OpExportMultipageTiff(graph=graph)
    export.Input.connect(op_data.Output)
    export.Filepath.setValue(out_path)
    export.run_export()

    # read written file
    reader = OpTiffReader(graph=graph)
    reader.Filepath.setValue(out_path)
    assert reader.Output.ready()

    expected_meta = {"t": (5.0, "s"), "z": (7.0, "cm"), "y": (6.000024000096, "µm"), "x": (13, "mm")}
    assert len(reader.Output.meta.axistags) == 5
    for axis in reader.Output.meta.getAxisKeys():
        if axis == "c":
            assert reader.Output.meta.axistags[axis].resolution == 0
            continue
        (resolution, unit) = expected_meta[axis]
        tag = reader.Output.meta.axistags[axis]
        # Rounding is not necessary here as ome stores resolution as floats
        assert tag.resolution == resolution
        assert reader.Output.meta.axis_units[axis] == unit
