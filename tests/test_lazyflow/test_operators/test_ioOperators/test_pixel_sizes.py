import json
import os
import xml.etree.ElementTree as ET
from collections import OrderedDict
from contextlib import contextmanager
from typing import Dict, List, Tuple, Union
from unittest import mock
from unittest.mock import ANY

import h5py
import numpy as np
import pytest
import tifffile
import vigra
import zarr

from ilastik.applets.dataSelection import DataSelectionApplet, OpDataSelectionGroup, FilesystemDatasetInfo
from lazyflow.graph import Graph
from lazyflow.operator import Operator
from lazyflow.operators import OpArrayPiper
from lazyflow.operators.ioOperators import (
    OpTiffReader,
    OpExportMultipageTiff,
    OpH5N5WriterBigDataset,
    OpOMEZarrMultiscaleReader,
    OpRESTfulPrecomputedChunkedVolumeReader,
    OpStreamingH5N5Reader,
)
from lazyflow.slot import Slot
from lazyflow.utility.io_util.write_ome_zarr import write_ome_zarr, ShapesByScaleKey
from ..test_ioOperators.testOpStreamingH5N5Reader import h5n5_file, data


def get_data_op_with_pixel_size_meta(
    graph, axes: str, shape: Tuple[int, ...], resolutions: List[float], units: Union[Dict[str, str], List[str]]
):
    data = np.random.default_rng(1337).integers(0, 255, shape).astype(np.uint16)
    tagged_data = vigra.taggedView(data, axes)
    for axis, res in zip(axes, resolutions):
        tagged_data.axistags.setResolution(axis, res)
    op = OpArrayPiper(graph=graph)
    op.Input.setValue(tagged_data)
    axis_units_dict = units if isinstance(units, dict) else dict(zip(axes, units))
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
        (
            # x, y and z unit are the same.
            # ImageJ convention is not to store y and z unit in this case, so reader should transfer.
            "/pix_res/3d_t.tif",  # The file doesn't actually contain "mm" for y and z
            {"x": (3.000003000003, "mm"), "y": (5, "mm"), "z": (7, "mm"), "t": (3, "")},
        ),
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
            ["", "pixel", "", "pixel", "pixel"],
        ),
        (
            ["t", "z", "c", "y", "x"],
            (2, 3, 6, 3, 5),
            [120, 0.54321, 42, 6.000024000096, 13],
            ["min", "mm", "", "mm", "µm"],
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

        expected_axes = "".join(axes).upper()
        assert expected_axes == f.series[0].axes

        for axis in axes:
            if axis.lower() == "c":
                assert "c" not in sizes.keys()  # Channel sizes are not written to TIFF
                continue
            expected_resolution = resolutions[axes.index(axis)]
            expected_unit = units[axes.index(axis)]
            if not expected_resolution:
                assert sizes[axis][0] not in pixels
            else:
                assert np.isclose(float(pixels.attrib[sizes[axis][0]]), expected_resolution, atol=1e-15)
            if not expected_unit:
                assert sizes[axis][1] not in pixels
            else:
                assert pixels.attrib[sizes[axis][1]] == expected_unit


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


@pytest.mark.parametrize(
    "axes, shape, resolutions, units, converted_units",
    [
        (["y", "x"], (65, 58), [6.000024000096, 13], ["µm", "millimeter"], ["µm", "mm"]),
        (
            ["c", "y", "x"],
            (2, 65, 58),
            [0.0, 6.000024000096, 13],
            ["", "microns", "millimeters"],
            ["pixel", "µm", "mm"],
        ),
        (
            ["z", "y", "x"],
            (2, 3, 5),
            [0.54321, 6.000024000096, 13],
            ["", "", ""],
            ["pixel", "pixel", "pixel"],
        ),  # tifffile doesn't work with x smaller 5
        (["z", "y", "x"], (2, 3, 5), [0.0, 0.0, 13], ["km", "", "centimetre"], ["km", "pixel", "cm"]),
        (["z", "y", "x"], (2, 3, 5), [0.0, 0.0, 0.0], ["um", "MILLIMETER", "cENtIMETEr"], ["µm", "mm", "cm"]),
        (
            ["z", "c", "y", "x"],
            (3, 2, 3, 5),
            [0.54321, 0.0, 6.000024000096, 13],
            ["", "", "", ""],
            ["pixel", "pixel", "pixel", "pixel"],
        ),
        (
            ["z", "c", "y", "x"],
            (3, 2, 3, 5),
            [0.54321, 42, 6.000024000096, 13],
            ["µm", "mistake", "mm", "micron"],
            ["µm", "pixel", "mm", "µm"],
        ),
        (
            ["z", "c", "y", "x"],
            (3, 2, 3, 5),
            [0.0, 0.0, 0.0, 0.0],
            ["µm", "", "mm", "microns"],
            ["µm", "pixel", "mm", "µm"],
        ),
        (
            ["z", "c", "y", "x"],
            (23, 2, 65, 58),
            [0.54321, 0.0, 6.000024000096, 13],
            ["µm", "", "mm", "cm"],
            ["µm", "pixel", "mm", "cm"],
        ),
        (
            ["t", "z", "y", "x"],
            (15, 23, 65, 58),
            [120, 0.54321, 6.000024000096, 13],
            ["sec", "µm", "mm", "cm"],
            ["s", "µm", "mm", "cm"],
        ),
        (
            ["t", "z", "c", "y", "x"],
            (6, 2, 3, 3, 5),
            [120, 0.54321, 0.0, 6.000024000096, 13],
            ["", "", "", "", ""],
            ["", "pixel", "pixel", "pixel", "pixel"],
        ),
    ],
)
def test_unit_conversion_OpExportMultipageTiff(graph, tmp_path, axes, shape, resolutions, units, converted_units):
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

        expected_axes = "".join(axes).upper()
        assert expected_axes == f.series[0].axes

        for axis in axes:
            if axis.lower() == "c":
                assert "c" not in sizes.keys()  # Channel sizes are not written to TIFF
                continue
            expected_resolution = resolutions[axes.index(axis)]
            expected_unit = converted_units[axes.index(axis)]
            if not expected_resolution:
                assert sizes[axis][0] not in pixels
            else:
                assert np.isclose(float(pixels.attrib[sizes[axis][0]]), expected_resolution, atol=1e-15)
            if not expected_unit:
                assert sizes[axis][1] not in pixels
            else:
                assert pixels.attrib[sizes[axis][1]] == expected_unit


@pytest.mark.parametrize(
    "axes, shape, resolutions, units",
    [
        (["y", "x"], (65, 58), [6.000024000096, 13], ["µm", "mm"]),
        (["c", "y", "x"], (2, 65, 58), [0.0, 6.000024000096, 13], ["", "µm", "mm"]),
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


def setup_op_data_lane(dataset_infos: List[FilesystemDatasetInfo], graph):
    roles = ["Raw Data", "Secondary", "Tertiary"]
    assert len(roles) == len(dataset_infos), "bad setup"
    op_data = OpDataSelectionGroup(graph=graph)
    op_data.WorkingDirectory.setValue(os.getcwd())
    op_data.DatasetRoles.setValue(roles)
    op_data.DatasetGroup.setValues(dataset_infos)
    return op_data


def assert_eq_spatial_pixel_size(actual_slot: Slot, expect_tags: vigra.AxisTags, expect_units: Dict[str, str]):
    for actual_tag in actual_slot.meta.axistags:
        if actual_tag.key == "c":
            continue
        assert actual_tag in expect_tags, f"axis {actual_tag.key} was not expected"
        assert np.isclose(
            actual_tag.resolution, expect_tags[actual_tag.key].resolution, atol=1e-15
        ), "slot axis resolution: actual != expected"
    assert actual_slot.meta.axis_units == expect_units, "actual slot axis units != expected"


@pytest.fixture
def dataset_with_pixel_size(inputdata_dir) -> FilesystemDatasetInfo:
    return FilesystemDatasetInfo(filePath=inputdata_dir + "/pix_res/3d_t.tif")


@pytest.fixture
def dataset_no_pixel_size(inputdata_dir) -> FilesystemDatasetInfo:
    info = FilesystemDatasetInfo(filePath=inputdata_dir + "/pix_res/3d_t.tif", axistags=vigra.defaultAxistags("tzyx"))
    info.axis_units = None
    return info


@pytest.fixture
def dataset_other_pixel_size(inputdata_dir) -> FilesystemDatasetInfo:
    info = FilesystemDatasetInfo(filePath=inputdata_dir + "/pix_res/3d_t.tif")
    for tag in info.axistags:
        info.axistags.setResolution(tag.key, 3.1415)
    info.axis_units = {"t": "sec", "x": "nm", "y": "cm", "z": "micron"}
    return info


def test_DataSelection_roles_copies_from_raw_data(graph, dataset_with_pixel_size, dataset_no_pixel_size):
    dataset_infos = [dataset_with_pixel_size, dataset_no_pixel_size, None]
    op_data = setup_op_data_lane(dataset_infos, graph)

    for i in range(2):
        assert_eq_spatial_pixel_size(
            op_data.ImageGroup[i], dataset_with_pixel_size.axistags, dataset_with_pixel_size.axis_units
        )
    assert OpDataSelectionGroup.META_COPY_KEY not in op_data.ImageGroup[0].meta
    assert OpDataSelectionGroup.META_COPY_KEY in op_data.ImageGroup[1].meta
    assert op_data.ImageGroup[1].meta[OpDataSelectionGroup.META_COPY_KEY] == "Raw Data"
    assert "axistags" not in op_data.ImageGroup[2].meta
    assert "axis_units" not in op_data.ImageGroup[2].meta
    assert OpDataSelectionGroup.META_COPY_KEY not in op_data.ImageGroup[2].meta


def test_DataSelection_roles_copies_from_raw_data_to_tertiary(graph, dataset_with_pixel_size, dataset_no_pixel_size):
    dataset_infos = [dataset_with_pixel_size, dataset_no_pixel_size, dataset_no_pixel_size]
    op_data = setup_op_data_lane(dataset_infos, graph)

    for i in range(3):
        assert_eq_spatial_pixel_size(
            op_data.ImageGroup[i], dataset_with_pixel_size.axistags, dataset_with_pixel_size.axis_units
        )
    assert OpDataSelectionGroup.META_COPY_KEY not in op_data.ImageGroup[0].meta
    assert OpDataSelectionGroup.META_COPY_KEY in op_data.ImageGroup[1].meta
    assert op_data.ImageGroup[1].meta[OpDataSelectionGroup.META_COPY_KEY] == "Raw Data"
    assert OpDataSelectionGroup.META_COPY_KEY in op_data.ImageGroup[2].meta
    assert op_data.ImageGroup[2].meta[OpDataSelectionGroup.META_COPY_KEY] == "Raw Data"


def test_DataSelection_roles_copies_from_secondary(graph, dataset_with_pixel_size, dataset_no_pixel_size):
    dataset_infos = [dataset_no_pixel_size, dataset_with_pixel_size, dataset_no_pixel_size]
    op_data = setup_op_data_lane(dataset_infos, graph)

    for i in range(3):
        assert_eq_spatial_pixel_size(
            op_data.ImageGroup[i], dataset_with_pixel_size.axistags, dataset_with_pixel_size.axis_units
        )
    assert OpDataSelectionGroup.META_COPY_KEY in op_data.ImageGroup[0].meta
    assert op_data.ImageGroup[0].meta[OpDataSelectionGroup.META_COPY_KEY] == "Secondary"
    assert OpDataSelectionGroup.META_COPY_KEY not in op_data.ImageGroup[1].meta
    assert OpDataSelectionGroup.META_COPY_KEY in op_data.ImageGroup[2].meta
    assert op_data.ImageGroup[2].meta[OpDataSelectionGroup.META_COPY_KEY] == "Secondary"


def test_DataSelection_roles_detects_conflict(
    graph, dataset_with_pixel_size, dataset_no_pixel_size, dataset_other_pixel_size
):
    dataset_infos = [dataset_with_pixel_size, dataset_other_pixel_size, dataset_no_pixel_size]
    op_data = setup_op_data_lane(dataset_infos, graph)

    for i in range(3):
        assert (
            OpDataSelectionGroup.META_COPY_KEY not in op_data.ImageGroup[i].meta
        ), "should not have carried over pixel size"
        assert_eq_spatial_pixel_size(op_data.ImageGroup[i], dataset_infos[i].axistags, dataset_infos[i].axis_units)


def test_DataSelection_roles_gui_warns_on_conflict(
    graph, dataset_with_pixel_size, dataset_no_pixel_size, dataset_other_pixel_size
):
    workflow = Operator(graph=graph)
    workflow.handleNewLanesAdded = mock.Mock()
    workflow.shell = mock.Mock()
    applet = DataSelectionApplet(workflow, "Input Data", "Input Data")
    applet.topLevelOperator.WorkingDirectory.setValue(dataset_with_pixel_size.base_dir)
    applet.topLevelOperator.DatasetRoles.setValue(["Raw Data", "Secondary", "Tertiary"])
    gui = applet.getMultiLaneGui()

    warn_mock = mock.Mock()
    with mock.patch("qtpy.QtWidgets.QMessageBox.warning", warn_mock):
        gui.addLanes([dataset_with_pixel_size], 0, None)
    warn_mock.assert_not_called()

    with mock.patch("qtpy.QtWidgets.QMessageBox.warning", warn_mock):
        gui.addLanes([dataset_no_pixel_size], 1, 0)
    warn_mock.assert_not_called()

    with mock.patch("qtpy.QtWidgets.QMessageBox.warning", warn_mock):
        gui.addLanes([dataset_other_pixel_size], 2, 0)
    warn_mock.assert_called_once_with(gui, "Pixel size mismatch", ANY)


def test_DataSelection_roles_rolls_back(
    graph, dataset_with_pixel_size, dataset_no_pixel_size, dataset_other_pixel_size
):
    """
    The first dataset has no pixel size.
    When the second dataset is added, its pixel size is transferred to the first.
    When the third dataset is added, it conflicts with the other two.
    At this point, the meta carried from secondary to raw data needs to be rolled back.
    """
    dataset_infos = [dataset_no_pixel_size, dataset_with_pixel_size, dataset_other_pixel_size]
    op_data = setup_op_data_lane(dataset_infos, graph)
    for i in range(3):
        assert (
            OpDataSelectionGroup.META_COPY_KEY not in op_data.ImageGroup[i].meta
        ), "should not have carried over pixel size"
        assert_eq_spatial_pixel_size(op_data.ImageGroup[i], dataset_infos[i].axistags, dataset_infos[i].axis_units)


@pytest.mark.parametrize(
    "shape1, res1, units1, shape2, res2, units2",
    [
        ((3, 4), [0.2, 3.0], {"x": "cm", "y": "nm"}, (5, 6), [0.2, 3.0], {"x": "cm", "y": "nm"}),
        ((3, 1), [0.2, 7.0], {"x": "cm", "y": "nm"}, (5, 6), [0.2, 3.0], {"x": "cm", "y": "nm"}),
        ((3, 1), [0.2, 3.0], {"x": "cm", "y": "px"}, (5, 6), [0.2, 3.0], {"x": "cm", "y": "nm"}),
        ((3, 1), [0.2, 7.0], {"x": "cm", "y": "px"}, (5, 6), [0.2, 3.0], {"x": "cm", "y": "nm"}),
        ((3, 4), [0.2, 3.0], {"x": "cm", "y": "nm"}, (1, 6), [0.8, 3.0], {"x": "px", "y": "nm"}),
        (
            (3, 4, 7, 8, 9),
            [0.2, 3.0, 0.4, 0.0, 2.0],
            {"x": "cm", "y": "nm", "z": "mm", "c": "", "t": "m"},
            (5, 6, 2, 3, 2),
            [0.2, 3.0, 0.4, 0.0, 2.0],
            {"x": "cm", "y": "nm", "z": "mm", "c": "", "t": "m"},
        ),
        (
            (3, 1, 7, 8, 1),
            [0.2, 3.0, 0.4, 0.0, 2.0],
            {"x": "cm", "y": "px", "z": "mm", "c": "", "t": "sec"},
            (5, 1, 1, 3, 2),
            [0.2, 7.0, 8.0, 0.0, 5.0],
            {"x": "cm", "y": "nm", "z": "px", "c": "", "t": "m"},
        ),
        (
            (3, 4, 7, 8, 9),
            [0.2, 7.0, 0.4, 0.0, 5.0],
            {"x": "cm", "y": "nm", "z": "mm", "c": "", "t": "m"},
            (5, 6, 2, 3, 2),
            [0.2, 7.0, 0.4, 2.0, 5.0],
            {"x": "cm", "y": "nm", "z": "mm", "c": "radians", "t": "m"},
        ),
    ],
)
def test_eq_pixel_size_ignores_singletons_and_channel(graph, shape1, res1, units1, shape2, res2, units2):
    default_axes = "xyzct"
    axes1 = default_axes[: len(shape1)]
    axes2 = default_axes[: len(shape2)]
    op_data1 = get_data_op_with_pixel_size_meta(graph, axes1, shape1, res1, units1 or [])
    op_data2 = get_data_op_with_pixel_size_meta(graph, axes2, shape2, res2, units2 or [])

    assert OpDataSelectionGroup.eq_resolution_and_units_xyzt(op_data1.Output, op_data2.Output)


@pytest.mark.parametrize(
    "shape1, res1, units1, shape2, res2, units2",
    [
        ((3, 4), [0.2, 7.0], {"x": "cm", "y": "nm"}, (5, 6), [0.2, 3.0], {"x": "cm", "y": "nm"}),
        ((3, 4), [0.2, 3.0], {"x": "cm", "y": "px"}, (5, 6), [0.2, 3.0], {"x": "cm", "y": "nm"}),
        ((3, 4), [0.2, 7.0], {"x": "cm", "y": "px"}, (5, 6), [0.2, 3.0], {"x": "cm", "y": "nm"}),
        ((3, 4), [0.2, 3.0], {"x": "cm", "y": "nm"}, (5, 6), [0.8, 3.0], {"x": "px", "y": "nm"}),
        (
            (3, 4, 7, 8, 9),
            [0.2, 3.0, 0.4, 0.0, 2.0],
            {"x": "cm", "y": "px", "z": "mm", "c": "", "t": "sec"},
            (5, 6, 2, 3, 2),
            [0.2, 7.0, 8.0, 0.0, 5.0],
            {"x": "cm", "y": "nm", "z": "px", "c": "", "t": "m"},
        ),
    ],
)
def test_eq_pixel_size_true_negatives(graph, shape1, res1, units1, shape2, res2, units2):
    default_axes = "xyzct"
    axes1 = default_axes[: len(shape1)]
    axes2 = default_axes[: len(shape2)]
    op_data1 = get_data_op_with_pixel_size_meta(graph, axes1, shape1, res1, units1 or [])
    op_data2 = get_data_op_with_pixel_size_meta(graph, axes2, shape2, res2, units2 or [])

    assert not OpDataSelectionGroup.eq_resolution_and_units_xyzt(op_data1.Output, op_data2.Output)


@pytest.mark.parametrize(
    "expect_eq, res1, units1, res2, units2",
    [
        (True, [0.0, 0.0], None, [0.0, 0.0], None),
        (True, [0.0, 3.0], {"y": "nm"}, [0.0, 3.0], {"y": "nm"}),
        (True, [0.0, 3.0], {"y": "nm"}, [0.0, 3.0], {"x": "", "y": "nm"}),
        (True, [0.0, 3.0], {"x": "nm"}, [0.0, 3.0], {"x": "nm"}),
        (True, [0.0, 0.0], None, [0.0, 0.0, 0.0, 0.0, 0.0], {"t": ""}),
        (True, [0.0, 0.0, 0.0, 0.0, 0.0], None, [0.0, 0.0], None),
        (False, [0.0, 3.0], {"y": "nm"}, [0.0, 0.0], None),
        (False, [0.0, 0.0, 0.0, 0.0, 1.0], None, [0.0, 0.0], None),
        (False, [0.0, 0.0], None, [0.0, 0.0, 0.0, 0.0, 0.0], {"t": "cm"}),
    ],
)
def test_eq_pixel_size_empty(graph, expect_eq, res1, units1, res2, units2):
    default_axes = "xyzct"
    default_shape = (2, 3, 4, 5, 6)
    axes1 = default_axes[: len(res1)]
    shape1 = default_shape[: len(res1)]
    axes2 = default_axes[: len(res2)]
    shape2 = default_shape[: len(res2)]
    op_data1 = get_data_op_with_pixel_size_meta(graph, axes1, shape1, res1, units1 or [])
    op_data2 = get_data_op_with_pixel_size_meta(graph, axes2, shape2, res2, units2 or [])

    assert OpDataSelectionGroup.eq_resolution_and_units_xyzt(op_data1.Output, op_data2.Output) == expect_eq


@contextmanager
def patch_ome_zarr(ome_spec: Dict, uri: str, array: np.ndarray):
    with (
        mock.patch(
            "lazyflow.utility.io_util.OMEZarrStore._introspect_for_multiscales_root",
            lambda _uri: (ome_spec, uri, None),
        ),
        mock.patch("lazyflow.utility.io_util.OMEZarrStore.ZarrArray", lambda **_: array),
    ):
        yield


def test_read_ome_zarr_v0_3(graph):
    """No pixel size metadata possible in OME-Zarr v0.3 or earlier"""
    axes = ["t", "c", "z", "y", "x"]
    ome_spec_v0_3 = {"multiscales": [{"datasets": [{"path": "boop"}], "axes": axes}]}
    array_mock = mock.Mock()
    array_mock.shape = (3, 2, 11, 10, 9)

    reader = OpOMEZarrMultiscaleReader(graph=graph)
    with patch_ome_zarr(ome_spec_v0_3, "file:///noop", array_mock):
        reader.Uri.setValue("file:///noop")

    assert reader.Output.ready()
    assert "axis_units" not in reader.Output.meta
    assert reader.Output.meta.getAxisKeys() == axes
    for tag in reader.Output.meta.axistags:
        assert tag.resolution == 0.0


def test_read_ome_zarr_v0_4(graph):
    pyramid_scale = {"t": 0.1, "c": 0, "z": 1, "y": 1, "x": 1}
    dataset_scale = {"t": 1.0, "c": 0, "z": 2.0, "y": 0.3, "x": 4.0}
    units = {"t": "sec", "c": "", "z": "mm", "y": "beep", "x": "metres"}
    ome_spec_v0_4 = {
        "multiscales": [
            {
                "datasets": [
                    {
                        "path": "boop",
                        "coordinateTransformations": [
                            {"scale": list(dataset_scale.values()), "type": "scale"},
                        ],
                    }
                ],
                "axes": [
                    {"name": "t", "type": "time", "unit": units["t"]},
                    {"name": "c", "type": "channel"},
                    {"name": "z", "type": "space", "unit": units["z"]},
                    {"name": "y", "type": "space", "unit": units["y"]},
                    {"name": "x", "type": "space", "unit": units["x"]},
                ],
                "coordinateTransformations": [
                    {"scale": list(pyramid_scale.values()), "type": "scale"},
                ],
            }
        ]
    }
    array_mock = mock.Mock()
    array_mock.shape = (3, 2, 11, 10, 9)

    reader = OpOMEZarrMultiscaleReader(graph=graph)
    with patch_ome_zarr(ome_spec_v0_4, "file:///noop", array_mock):
        reader.Uri.setValue("file:///noop")

    assert reader.Output.ready()
    assert "axis_units" in reader.Output.meta
    assert reader.Output.meta.axis_units == units
    assert reader.Output.meta.getAxisKeys() == list(dataset_scale.keys())
    for tag in reader.Output.meta.axistags:
        expected_resolution = pyramid_scale[tag.key] * dataset_scale[tag.key]
        assert tag.resolution == expected_resolution


def test_read_ome_zarr_v0_4_no_units(graph):
    dataset_scale = {"t": 1.0, "c": 0, "z": 2.0, "y": 0.3, "x": 4.0}
    ome_spec_v0_4 = {
        "multiscales": [
            {
                "axes": [{"name": "t"}, {"name": "c"}, {"name": "z"}, {"name": "y"}, {"name": "x"}],
                "datasets": [
                    {
                        "path": "boop",
                        "coordinateTransformations": [
                            {"scale": list(dataset_scale.values()), "type": "scale"},
                        ],
                    }
                ],
            }
        ]
    }
    array_mock = mock.Mock()
    array_mock.shape = (3, 2, 11, 10, 9)

    reader = OpOMEZarrMultiscaleReader(graph=graph)
    with patch_ome_zarr(ome_spec_v0_4, "file:///noop", array_mock):
        reader.Uri.setValue("file:///noop")

    assert reader.Output.ready()
    # GUI uses presence of axis_units as indicator that pixel size exists
    assert "axis_units" in reader.Output.meta
    assert reader.Output.meta.axis_units == {a: "" for a in dataset_scale}
    assert reader.Output.meta.getAxisKeys() == list(dataset_scale.keys())
    for tag in reader.Output.meta.axistags:
        assert tag.resolution == dataset_scale[tag.key]


def test_write_ome_zarr_single_scale(graph, tmp_path):
    """
    Smoke test of the simplest case.
    Combinatorics of single/multiscale input to single/multiscale export are tested in test_write_ome_zarr.
    """
    op_data = get_data_op_with_pixel_size_meta(
        graph,
        ["t", "z", "y", "x", "c"],
        (6, 5, 4, 3, 2),
        [0.4, 5.0, 0.3, 6.4, 8.99991],
        ["sec", "um", "nm", "mm", "noodles"],
    )
    export_path = tmp_path / "test.zarr"
    progress = mock.Mock()
    expected_axes = [  # Expect copied strings. TODO: Normalize https://ngff.openmicroscopy.org/0.4/#axes-md
        {"name": "t", "type": "time", "unit": "sec"},
        {"name": "c", "type": "channel", "unit": "noodles"},  # obviously non-standard, but allowed
        {"name": "z", "type": "space", "unit": "um"},
        {"name": "y", "type": "space", "unit": "nm"},
        {"name": "x", "type": "space", "unit": "mm"},
    ]
    # Dataset scale is mandatory, but should be noop here. In single-scale export from a single-scale source,
    # pixel size should be written on multiscale-level. This isn't a spec requirement, but a generalisation of the
    # convention of writing scale for the t-axis into the multiscale-level transforms.
    expected_multiscale_transform = [{"type": "scale", "scale": [0.4, 8.99991, 5.0, 0.3, 6.4]}]  # tczyx
    expected_dataset_transform = [{"type": "scale", "scale": [1.0, 1.0, 1.0, 1.0, 1.0]}]

    write_ome_zarr(str(export_path), op_data.Output, progress, None)

    group = zarr.open(str(export_path))
    assert "multiscales" in group.attrs
    m = group.attrs["multiscales"][0]
    assert "axes" in m
    assert m["axes"] == expected_axes
    assert "coordinateTransformations" in m
    assert m["coordinateTransformations"] == expected_multiscale_transform
    assert "datasets" in m and "path" in m["datasets"][0]
    assert len(m["datasets"]) == 1
    assert m["datasets"][0]["coordinateTransformations"] == expected_dataset_transform


def test_write_read_roundtrip_ome_zarr(graph, tmp_path):
    axes = ["t", "z", "y", "x", "c"]
    source_shape = OrderedDict(zip(axes, (6, 5, 4, 3, 2)))
    resolutions = OrderedDict(zip(axes, [0.4, 5.0, 0.3, 6.4, 8.99991]))
    units = ["sec", "um", "nm", "mm", "noodles"]
    op_data = get_data_op_with_pixel_size_meta(graph, axes, tuple(source_shape.values()), resolutions.values(), units)
    export_path = tmp_path / "test_pixel_size.zarr"
    progress = mock.Mock()
    target_shape_up = OrderedDict(zip("tczyx", (6, 2, 16, 15, 13)))  # ome-zarr standard
    target_shape_down = OrderedDict(zip("tczyx", (6, 2, 3, 2, 3)))
    target_scales: ShapesByScaleKey = OrderedDict([("upscale", target_shape_up), ("downscale", target_shape_down)])

    write_ome_zarr(str(export_path), op_data.Output, progress, None, target_scales)

    reader = OpOMEZarrMultiscaleReader(graph=graph, Uri=export_path.as_uri(), Scale="downscale")

    assert reader.Output.ready()
    assert "axis_units" in reader.Output.meta
    assert reader.Output.meta.axis_units == dict(zip(axes, units))
    assert reader.Output.meta.getAxisKeys() == list("tczyx")
    assert reader.Output.meta.scales == target_scales
    for tag in reader.Output.meta.axistags:
        scaling = source_shape[tag.key] / target_shape_down[tag.key]
        expected_resolution = scaling * resolutions[tag.key]
        assert tag.resolution == expected_resolution

    reader = OpOMEZarrMultiscaleReader(graph=graph, Uri=export_path.as_uri(), Scale="upscale")

    assert reader.Output.ready()
    for tag in reader.Output.meta.axistags:
        scaling = source_shape[tag.key] / target_shape_up[tag.key]
        expected_resolution = scaling * resolutions[tag.key]
        assert tag.resolution == expected_resolution


def test_read_precomputed(graph):
    resolution = [801, 802, 70]
    tagged_resolution = {"c": 0, "z": 70, "y": 802, "x": 801}
    precomputed_info = {
        "@type": "neuroglancer_multiscale_volume",
        "type": "image",
        "data_type": "uint16",
        "num_channels": 1,
        "scales": [
            {
                "key": "some_key",
                "size": [4, 5, 6],
                "resolution": resolution,
                "chunk_sizes": [[4, 5, 6]],
            },
        ],
    }
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.content = json.dumps(precomputed_info)

    reader = OpRESTfulPrecomputedChunkedVolumeReader(graph=graph)
    with mock.patch("requests.get", lambda _url: mock_response):
        reader.BaseUrl.setValue("precomputed://https://noop")

    assert reader.Output.ready()
    assert "axis_units" in reader.Output.meta
    assert reader.Output.meta.axis_units == {"c": "", "z": "nm", "y": "nm", "x": "nm"}
    assert reader.Output.meta.getAxisKeys() == ["c", "z", "y", "x"]
    for tag in reader.Output.meta.axistags:
        assert tag.resolution == tagged_resolution[tag.key]
