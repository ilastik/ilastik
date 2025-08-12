from collections import OrderedDict
from typing import List, Union, Iterable
from unittest import mock

import numpy
import pytest
import vigra
import zarr

from lazyflow.operators import OpArrayPiper
from lazyflow.utility.data_semantics import ImageTypes
from lazyflow.utility.io_util import multiscaleStore
from lazyflow.utility.io_util.OMEZarrStore import OMEZarrMultiscaleMeta
from lazyflow.utility.io_util.write_ome_zarr import (
    write_ome_zarr,
    generate_default_target_scales,
    _match_target_scales_to_input,
    match_target_scales_to_input_excluding_upscales,
)


def tagged_shape(axes: Union[str, List[str]], shape: Iterable[int]):
    return OrderedDict(zip(axes, shape))


@pytest.mark.parametrize(
    "shape, axes, target_scales",
    [
        ((1, 128, 127, 10, 1), "txyzc", None),  # ilastik default order
        ((1, 1, 3, 26, 25), "tczyx", None),  # OME-Zarr convention
        ((256, 255), "yx", None),
        ((10, 126, 125), "zyx", None),
        ((124, 123, 3), "yxc", None),
        (
            (21, 23, 3),
            "yxc",
            OrderedDict(
                [
                    ("raw", tagged_shape("tczyx", (1, 3, 1, 21, 23))),
                    ("scaled", tagged_shape("tczyx", (1, 3, 1, 10, 12))),
                ]
            ),
        ),
        (
            (21, 23, 3),
            "yxc",
            OrderedDict({"s0": tagged_shape("tczyx", (1, 3, 1, 10, 12))}),
        ),
    ],
)
def test_metadata_match_ome_zarr_spec(tmp_path, graph, shape, axes, target_scales):
    data_array = vigra.taggedView(numpy.random.randint(0, 255, shape, dtype="uint8"), axes)
    export_path = tmp_path / "test.zarr"
    source_op = OpArrayPiper(graph=graph)
    source_op.Input.setValue(data_array)
    progress = mock.Mock()

    write_ome_zarr(str(export_path), source_op.Output, progress, None, target_scales=target_scales)

    expected_axiskeys = "tczyx"
    assert export_path.exists()
    group = zarr.open(str(export_path))
    assert "multiscales" in group.attrs
    written_meta = group.attrs["multiscales"][0]
    required_keys = ("datasets", "axes", "version")  # version not required by spec but by us
    assert all([key in written_meta for key in required_keys])
    assert all(written_meta.values()), "Should not write empty values anywhere"
    assert written_meta["version"] == "0.4"
    assert [a["name"] for a in written_meta["axes"]] == list(expected_axiskeys)
    expected_len_datasets = 1 if target_scales is None else len(target_scales)
    assert len(written_meta["datasets"]) == expected_len_datasets, "not all specified scales written"

    discovered_keys = []
    for i, dataset in enumerate(written_meta["datasets"]):
        assert dataset["path"] in group
        if target_scales is not None:
            assert dataset["path"] == list(target_scales.keys())[i]
        discovered_keys.append(dataset["path"])
        written_array = group[dataset["path"]]
        assert written_array.fill_value is not None, "FIJI and z5py don't open zarrays without a fill_value"
        assert "axistags" in written_array.attrs, f"no axistags for {dataset['path']}"
        assert vigra.AxisTags.fromJSON(written_array.attrs["axistags"]) == vigra.defaultAxistags(expected_axiskeys)
        assert all([value is not None for value in written_array.attrs.values()])  # Should not write None anywhere
        reported_scalings = [
            transform for transform in dataset["coordinateTransformations"] if transform["type"] == "scale"
        ]
        assert len(reported_scalings) == 1
        if target_scales:
            assert dataset["path"] in target_scales, "unexpected scale key written"
            target_shape_reordered = tuple(target_scales[dataset["path"]].values())
        else:
            tagged_target_shape = dict(zip(data_array.axistags.keys(), data_array.shape))
            target_shape_reordered = tuple(
                tagged_target_shape[a] if a in tagged_target_shape else 1 for a in expected_axiskeys
            )
        tagged_original_shape = dict(zip(data_array.axistags.keys(), data_array.shape))
        original_shape_reordered = [
            tagged_original_shape[a] if a in tagged_original_shape else 1 for a in expected_axiskeys
        ]
        expected_shape_per_meta = tuple(
            round(shape / scale) for shape, scale in zip(original_shape_reordered, reported_scalings[0]["scale"])
        )
        assert written_array.shape == target_shape_reordered, "failed to scale dataset as specified"
        assert written_array.shape == expected_shape_per_meta, "scaling metadata does not match written shape"
        assert numpy.count_nonzero(written_array) > numpy.prod(expected_shape_per_meta) / 2, "did not write actual data"
    assert all([key in discovered_keys for key in group.keys()]), "store contains undocumented subpaths"


@pytest.fixture
def tiny_5d_vigra_array_piper(graph):
    data_array = vigra.VigraArray((2, 2, 5, 5, 5), axistags=vigra.defaultAxistags("tczyx"))
    data_array[...] = numpy.indices((2, 2, 5, 5, 5)).sum(0)
    op = OpArrayPiper(graph=graph)
    op.Input.setValue(data_array)
    return op


def test_do_not_overwrite(tmp_path, tiny_5d_vigra_array_piper):
    original_data_array = tiny_5d_vigra_array_piper.Output.value
    data_array2 = vigra.VigraArray((1, 1, 3, 3, 3), axistags=vigra.defaultAxistags("tczyx"))
    data_array2[...] = numpy.indices((1, 1, 3, 3, 3)).sum(0)
    export_path = tmp_path / "test.zarr"
    source_op = tiny_5d_vigra_array_piper
    progress = mock.Mock()
    write_ome_zarr(str(export_path), source_op.Output, progress, None)

    with pytest.raises(FileExistsError):
        write_ome_zarr(str(export_path), source_op.Output, progress, None)

    source_op.Input.setValue(data_array2)
    with pytest.raises(FileExistsError):
        write_ome_zarr(str(export_path), source_op.Output, progress, None)
    # should not overwrite existing array
    group = zarr.open(str(export_path))
    numpy.testing.assert_array_equal(group["s0"], original_data_array)


def test_match_input_scale_metadata_single_scale_export(tmp_path, tiny_5d_vigra_array_piper):
    """If the source slot has scale (but not OME-Zarr) metadata, single-scale export should match
    the scale name to the input. Scaling metadata should be relative to the input's raw data."""
    export_path = tmp_path / "test.zarr"
    source_op = tiny_5d_vigra_array_piper
    progress = mock.Mock()
    input_axes = ["t", "z", "y", "x"]
    multiscales: multiscaleStore.Multiscales = OrderedDict(
        [
            ("raw_scale", tagged_shape(input_axes, (2, 15, 15, 15))),
            ("matching_scale", tagged_shape(input_axes, (2, 5, 5, 5))),
            ("downscale", tagged_shape(input_axes, (2, 2, 2, 2))),
        ]
    )
    source_op.Output.meta.scales = multiscales
    source_op.Output.meta.active_scale = "matching_scale"
    # Scale metadata should be relative to raw scale, even if the export was not scaled
    # Exported array is 5d, so 5 scaling entries expected even though source multiscales to match are 4d
    expected_matching_scale_transform = [{"type": "scale", "scale": [1.0, 1.0, 3.0, 3.0, 3.0]}]

    write_ome_zarr(str(export_path), source_op.Output, progress, None)

    group = zarr.open(str(export_path))
    assert "multiscales" in group.attrs
    m = group.attrs["multiscales"][0]
    assert "datasets" in m and "path" in m["datasets"][0]
    assert len(m["datasets"]) == 1
    assert m["datasets"][0]["path"] == "matching_scale"
    assert m["datasets"][0]["coordinateTransformations"] == expected_matching_scale_transform


def test_port_ome_zarr_metadata_single_scale_export(tmp_path, tiny_5d_vigra_array_piper):
    """If the source slot has OME-Zarr metadata, single-scale export should match
    the input scale name, and higher-level coordinateTransformations should be carried over.
    The export scale's `scale` transformation should be copied from the input.
    If there is a CoordinateOffset (i.e. the user has restricted a ROI in the export settings),
    the export scale's `translation` transformation needs to be adjusted."""
    export_path = tmp_path / "test_multi_to_single.zarr"
    source_op = tiny_5d_vigra_array_piper
    progress = mock.Mock()
    multiscales: multiscaleStore.Multiscales = OrderedDict(
        [
            ("raw_scale", tagged_shape("tzyx", (2, 17, 17, 17))),
            ("matching_scale", tagged_shape("tzyx", (2, 9, 9, 9))),
            ("downscale", tagged_shape("tzyx", (2, 5, 5, 5))),
        ]
    )
    # The tiny_5d_array is 5x5x5; in this test it represents a subregion of source matching_scale after a 4/4/4 offset
    export_offset = (0, 0, 4, 4, 4)
    source_op.Output.meta.scales = multiscales
    source_op.Output.meta.active_scale = "matching_scale"
    expected_multiscale_transform = [{"type": "scale", "scale": [0.1, 1.0, 1.0, 1.0, 1.0]}]
    # When no actual scaling is done by ilastik, input scale should be carried over unmodified even if imprecise.
    expected_matching_scale_transform = [
        {"type": "scale", "scale": [1.0, 1.0, 2.0, 2.0, 2.0]},
        {"type": "translation", "translation": [0.1, 0.0, 11.2, 9.0, 9.0]},  # input translation + (offset*input scale)
    ]
    source_op.Output.meta.ome_zarr_meta = OMEZarrMultiscaleMeta.from_multiscale_spec(
        {
            "name": "wonderful_pyramid",
            "axes": [
                {"name": "t", "type": "time", "unit": "second"},
                {"name": "z", "type": "space", "unit": "micrometer"},
                {"name": "y", "type": "space", "unit": "micrometer"},
                {"name": "x", "type": "space", "unit": "micrometer"},
            ],  # Input metadata tzyx, but e.g. Probabilities output would be tczyx
            "coordinateTransformations": [{"type": "scale", "scale": [0.1, 1.0, 1.0, 1.0]}],
            "datasets": [
                {
                    "path": "raw_scale",
                    "coordinateTransformations": [
                        {"type": "scale", "scale": [1.0, 1.0, 1.0, 1.0]},
                        {"type": "translation", "translation": [0.1, 5.0, 2.0, 1.0]},
                    ],
                },
                {
                    "path": "matching_scale",
                    "coordinateTransformations": [
                        {"type": "scale", "scale": [1.0, 2.0, 2.0, 2.0]},
                        {"type": "translation", "translation": [0.1, 3.2, 1.0, 1.0]},
                    ],
                },
                {
                    "path": "downscale",
                    "coordinateTransformations": [
                        {"type": "scale", "scale": [1.0, 4.0, 4.0, 4.0]},
                        {"type": "translation", "translation": [5.1, 3.5, 5.4, 1.0]},
                    ],
                },
            ],
        }
    )

    write_ome_zarr(str(export_path), source_op.Output, progress, export_offset)

    group = zarr.open(str(export_path))
    assert "multiscales" in group.attrs
    m = group.attrs["multiscales"][0]
    assert "datasets" in m and "path" in m["datasets"][0]
    assert len(m["datasets"]) == 1
    assert "name" not in m  # Input name should not be carried over - presumably it names the raw data
    assert m["axes"] == [
        {"name": "t", "type": "time", "unit": "second"},
        {"name": "c", "type": "channel"},
        {"name": "z", "type": "space", "unit": "micrometer"},
        {"name": "y", "type": "space", "unit": "micrometer"},
        {"name": "x", "type": "space", "unit": "micrometer"},
    ]  # Axis units should be carried over
    assert m["coordinateTransformations"] == expected_multiscale_transform
    assert m["datasets"][0]["path"] == "matching_scale"
    assert m["datasets"][0]["coordinateTransformations"] == expected_matching_scale_transform


def test_scale_resized_export_relative_base(tmp_path, tiny_5d_vigra_array_piper):
    """If the source slot has scale metadata, but the export is a single resized scale,
    the scale key should be as specified as target; factors should be relative to raw input."""
    export_path = tmp_path / "test.zarr"
    source_op = tiny_5d_vigra_array_piper
    progress = mock.Mock()
    input_axes = ["c", "z", "y", "x"]  # Neuroglancer Precomputed axes for a change
    input_scales: multiscaleStore.Multiscales = OrderedDict(
        [
            ("raw_scale", tagged_shape(input_axes, (2, 15, 15, 15))),
            ("downscale", tagged_shape(input_axes, (2, 5, 5, 5))),
        ]
    )
    target_scales: multiscaleStore.Multiscales = OrderedDict(
        [
            ("resized_scale", tagged_shape("tczyx", (2, 2, 10, 10, 10))),
        ]
    )
    source_op.Output.meta.scales = input_scales
    source_op.Output.meta.active_scale = "downscale"
    expected_output_transform = [{"type": "scale", "scale": [1.0, 1.0, 1.5, 1.5, 1.5]}]

    write_ome_zarr(str(export_path), source_op.Output, progress, None, target_scales)

    group = zarr.open(str(export_path))
    assert "multiscales" in group.attrs
    m = group.attrs["multiscales"][0]
    assert "coordinateTransformations" not in m
    assert "datasets" in m and "path" in m["datasets"][0]
    assert len(m["datasets"]) == 1
    assert m["datasets"][0]["path"] == "resized_scale"
    assert m["datasets"][0]["coordinateTransformations"] == expected_output_transform


def test_match_raw_input_scale_metadata_multi_scale_export(tmp_path, tiny_5d_vigra_array_piper):
    """When the input is multiscale but not OME-Zarr, multiscale export should report
    scaling factors precisely, relative to the input's base scale. The translation
    of scales should correspond to export_offset * scale factor of the input scale (export source)."""
    export_path = tmp_path / "test_multi_to_multi.zarr"
    source_op = tiny_5d_vigra_array_piper
    progress = mock.Mock()
    # The tiny_5d_array is 5x5x5; in this test it represents a subregion of source_scale after a 3/3/3 offset
    export_offset = (0, 0, 3, 3, 3)
    multiscales: multiscaleStore.Multiscales = OrderedDict(
        [  # Include c to make sure export metadata ignores it as it should
            ("upscale", tagged_shape("tzyxc", (2, 34, 34, 34, 3))),
            ("raw_scale", tagged_shape("tzyxc", (2, 17, 17, 17, 3))),
            ("source_scale", tagged_shape("tzyxc", (2, 8, 8, 8, 3))),
            ("downscale", tagged_shape("tzyxc", (2, 4, 4, 4, 3))),
        ]
    )
    source_op.Output.meta.scales = multiscales
    source_op.Output.meta.active_scale = "source_scale"
    # Boundary conditions: Do not export source scale, but export downscale and a new upscale.
    # The export image is (2,2,5,5,5), (simulating a 0,_,3,3,3 crop of source_scale),
    # so downscale and upscale shapes here need to be relative to that shape.
    # Also make up-scaling factors anisotropic and non-integer for good measure.
    target_scales: multiscaleStore.Multiscales = OrderedDict(
        [
            ("weird_upscale", tagged_shape("tczyx", (2, 2, 13, 12, 12))),
            ("downscale", tagged_shape("tczyx", (2, 2, 2, 2, 2))),
        ]
    )
    # Expected output scaling: source scale * target scaling relative to source
    s = 34 / 8  # source scale = base shape / uncropped source shape
    expected_upscale = [1.0, 1.0, s * 5 / 13, s * 5 / 12, s * 5 / 12]  # cropped source shape / target shape
    # 2px would be the result of scaling 5px by 2.0.
    # The scaling implementation in OpResize is precise though, so metadata should not be rounded.
    expected_downscale = [1.0, 1.0, s * 5 / 2, s * 5 / 2, s * 5 / 2]
    expected_translation = [0.0, 0.0, s * 3, s * 3, s * 3]  # offset in pixels * source scaling

    write_ome_zarr(str(export_path), source_op.Output, progress, export_offset, target_scales)

    group = zarr.open(str(export_path))
    assert "multiscales" in group.attrs
    m = group.attrs["multiscales"][0]
    assert "datasets" in m and "path" in m["datasets"][0]
    assert len(m["datasets"]) == 2
    assert m["datasets"][0]["path"] == "weird_upscale"
    # The factor calculations come out unequal at 1e-16
    upscale_transforms = m["datasets"][0]["coordinateTransformations"]
    numpy.testing.assert_allclose(upscale_transforms[0]["scale"], expected_upscale, atol=1e-15)
    numpy.testing.assert_allclose(upscale_transforms[1]["translation"], expected_translation, atol=1e-15)
    assert m["datasets"][1]["path"] == "downscale"
    downscale_transforms = m["datasets"][1]["coordinateTransformations"]
    numpy.testing.assert_allclose(downscale_transforms[0]["scale"], expected_downscale, atol=1e-15)
    numpy.testing.assert_allclose(downscale_transforms[1]["translation"], expected_translation, atol=1e-15)


def test_port_ome_zarr_metadata_multi_scale_export(tmp_path, tiny_5d_vigra_array_piper):
    """
    See test above, but with OME-Zarr metadata present:
    * Additional metadata should be carried over (axis units, multiscale transformations)
    * Offset should be computed based on the source scale's translation and scale
    """
    export_path = tmp_path / "test_multi_to_multi.zarr"
    source_op = tiny_5d_vigra_array_piper
    progress = mock.Mock()
    # The tiny_5d_array is 5x5x5; in this test it represents a subregion of source_scale after a 3/3/3 offset
    export_offset = (0, 0, 3, 3, 3)
    multiscales: multiscaleStore.Multiscales = OrderedDict(
        [  # Include c to make sure export metadata ignores it as it should
            ("upscale", tagged_shape("tzyxc", (2, 34, 34, 34, 3))),
            ("raw_scale", tagged_shape("tzyxc", (2, 17, 17, 17, 3))),
            ("source_scale", tagged_shape("tzyxc", (2, 8, 8, 8, 3))),
            ("downscale", tagged_shape("tzyxc", (2, 4, 4, 4, 3))),
        ]
    )
    source_op.Output.meta.scales = multiscales
    source_op.Output.meta.active_scale = "source_scale"
    source_op.Output.meta.ome_zarr_meta = OMEZarrMultiscaleMeta.from_multiscale_spec(
        {
            "name": "wonderful_pyramid",
            "axes": [
                {"name": "t", "type": "time", "unit": "second"},
                {"name": "z", "type": "space", "unit": "micrometer"},
                {"name": "y", "type": "space", "unit": "micrometer"},
                {"name": "x", "type": "space", "unit": "micrometer"},
            ],  # Input metadata tzyx, but e.g. Probabilities output would be tczyx
            "coordinateTransformations": [{"type": "scale", "scale": [0.1, 1.0, 1.0, 1.0]}],
            "datasets": [
                {
                    "path": "upscale",  # The first scale is usually the raw data, but not necessarily
                    "coordinateTransformations": [
                        {"type": "scale", "scale": [1.0, 0.5, 0.5, 0.5]},
                    ],
                },
                {
                    "path": "raw_scale",
                    "coordinateTransformations": [
                        {"type": "scale", "scale": [1.0, 1.0, 1.0, 1.0]},
                        {"type": "translation", "translation": [0.1, 5.0, 2.0, 1.0]},
                    ],
                },
                {
                    "path": "source_scale",
                    "coordinateTransformations": [
                        {"type": "scale", "scale": [1.0, 2.0, 2.0, 2.0]},
                        {"type": "translation", "translation": [3.1, 3.2, 2.1, 1.0]},
                    ],
                },
                {
                    "path": "downscale",
                    "coordinateTransformations": [
                        {"type": "scale", "scale": [1.0, 4.0, 4.0, 4.0]},
                        {"type": "translation", "translation": [5.1, 3.5, 5.4, 1.0]},
                    ],
                },
            ],
        }
    )
    target_scales: multiscaleStore.Multiscales = OrderedDict(
        [
            ("weird_upscale", tagged_shape("tczyx", (2, 2, 13, 12, 12))),
            ("downscale", tagged_shape("tczyx", (2, 2, 2, 2, 2))),
        ]
    )
    expected_multiscale_transform = [{"type": "scale", "scale": [0.1, 1.0, 1.0, 1.0, 1.0]}]
    s_abs = 2.0  # Even if OpResize scales precisely, output should be computed based on the input's metadata.
    upscale = [1.0, 1.0, s_abs * 5 / 13, s_abs * 5 / 12, s_abs * 5 / 12]
    downscale = [1.0, 1.0, s_abs * 5 / 2, s_abs * 5 / 2, s_abs * 5 / 2]
    translation = [3.1, 0.0, s_abs * 3 + 3.2, s_abs * 3 + 2.1, s_abs * 3 + 1.0]
    expected_upscale_transform = [
        {"type": "scale", "scale": upscale},
        {"type": "translation", "translation": translation},
    ]
    expected_downscale_transform = [
        {"type": "scale", "scale": downscale},
        {"type": "translation", "translation": translation},
    ]

    write_ome_zarr(str(export_path), source_op.Output, progress, export_offset, target_scales)

    group = zarr.open(str(export_path))
    assert "multiscales" in group.attrs
    m = group.attrs["multiscales"][0]
    assert "datasets" in m and "path" in m["datasets"][0]
    assert len(m["datasets"]) == 2
    assert "name" not in m  # Input name should not be carried over - presumably it names the raw data
    assert m["axes"] == [
        {"name": "t", "type": "time", "unit": "second"},
        {"name": "c", "type": "channel"},
        {"name": "z", "type": "space", "unit": "micrometer"},
        {"name": "y", "type": "space", "unit": "micrometer"},
        {"name": "x", "type": "space", "unit": "micrometer"},
    ]  # Axis units should be carried over
    assert m["coordinateTransformations"] == expected_multiscale_transform
    assert m["datasets"][0]["path"] == "weird_upscale"
    assert m["datasets"][0]["coordinateTransformations"] == expected_upscale_transform
    assert m["datasets"][1]["path"] == "downscale"
    assert m["datasets"][1]["coordinateTransformations"] == expected_downscale_transform


def test_respects_interpolation_order(tmp_path, tiny_5d_vigra_array_piper):
    """
    Image source slots may specify `data_semantics` of the image data they produce.
    This affects how the image should be interpolated when downsampling
    E.g. order 0 (nearest-neighbor) is appropriate for labels, binary or segmentation images.
    Default is order 1 (linear interpolation), appropriate for raw data or probabilities.
    """
    export_path = tmp_path
    source_op = tiny_5d_vigra_array_piper
    progress = mock.Mock()
    target_scales: multiscaleStore.Multiscales = OrderedDict(
        [
            ("0", tagged_shape("tczyx", (2, 2, 5, 5, 5))),
            ("1", tagged_shape("tczyx", (2, 2, 2, 2, 2))),
        ]
    )
    # Data expected for channel 0 with the example dataset and nearest-neighbor interpolation
    expected_downscale_c0 = numpy.array(
        [[[[3.0, 5.0], [5.0, 7.0]], [[5.0, 7.0], [7.0, 9.0]]], [[[4.0, 6.0], [6.0, 8.0]], [[6.0, 8.0], [8.0, 10.0]]]]
    )

    write_ome_zarr(str(export_path / "test_default_interp.zarr"), source_op.Output, progress, None, target_scales)

    source_op.Output.meta.data_semantics = ImageTypes.Labels

    write_ome_zarr(str(export_path / "test_interp_0.zarr"), source_op.Output, progress, None, target_scales)

    group_default = zarr.open(str(export_path / "test_default_interp.zarr"))
    group_order0 = zarr.open(str(export_path / "test_interp_0.zarr"))
    data_default_unscaled = group_default["0"][:]
    data_order0_unscaled = group_order0["0"][:]
    numpy.testing.assert_array_equal(data_default_unscaled, data_order0_unscaled), "unscaled data should be identical"
    data_default_scaled = group_default["1"][:]
    data_order0_scaled = group_order0["1"][:]
    numpy.testing.assert_array_equal(data_order0_scaled[0, :], expected_downscale_c0)
    diff = numpy.abs(data_default_scaled - data_order0_scaled)
    assert numpy.all(diff > 0), "all data points in NN-interpolation should be different from linear interpolation"
    assert numpy.all(diff < 1), "all data points in NN-interpolation should be within 1 of linear interpolation"


@pytest.mark.parametrize(
    "shape,expected_shapes",
    [
        (  # Edge case
            tagged_shape("yx", (1, 1)),
            OrderedDict([("s0", tagged_shape("tczyx", (1, 1, 1, 1, 1)))]),
        ),
        (  # 2d below scaling threshold (chunk size defaults to 506x505 for 2d square 32bit)
            tagged_shape("yx", (500, 500)),
            OrderedDict([("s0", tagged_shape("tczyx", (1, 1, 1, 500, 500)))]),
        ),
        (  # 3d above scaling threshold (chunk size defaults to 63x65x63 for 3d cube 32bit)
            tagged_shape("zyx", (65, 65, 65)),
            OrderedDict(
                [
                    ("s0", tagged_shape("tczyx", (1, 1, 65, 65, 65))),
                    ("s1", tagged_shape("tczyx", (1, 1, 32, 32, 32))),
                ]
            ),
        ),
        (  # Multiple scales 2d
            tagged_shape("yx", (4000, 4000)),
            OrderedDict(
                [
                    ("s0", tagged_shape("tczyx", (1, 1, 1, 4000, 4000))),
                    ("s1", tagged_shape("tczyx", (1, 1, 1, 2000, 2000))),
                    ("s2", tagged_shape("tczyx", (1, 1, 1, 1000, 1000))),
                    ("s3", tagged_shape("tczyx", (1, 1, 1, 500, 500))),
                ]
            ),
        ),
        (  # 2d + c + t in odd order
            tagged_shape("cytx", (3, 700, 10, 700)),
            OrderedDict(
                [
                    ("s0", tagged_shape("tczyx", (10, 3, 1, 700, 700))),
                    ("s1", tagged_shape("tczyx", (10, 3, 1, 350, 350))),
                ]
            ),
        ),
    ],
)
def test_generate_default_target_scales(shape, expected_shapes):
    generated_shapes = generate_default_target_scales(shape, numpy.float32)
    assert generated_shapes == expected_shapes


@pytest.mark.parametrize(
    "shape, input_scales, expected_shapes",
    [
        (  # Simple: match input scales in OME-Zarr order
            tagged_shape("yx", (1, 1)),
            OrderedDict([("s0", tagged_shape("yx", (2, 2))), ("source_scale", tagged_shape("yx", (1, 1)))]),
            OrderedDict(
                [
                    ("s0", tagged_shape("tczyx", (1, 1, 1, 2, 2))),
                    ("source_scale", tagged_shape("tczyx", (1, 1, 1, 1, 1))),
                ]
            ),
        ),
        (  # Input no channels + default scaling would create different scales than input has
            tagged_shape("yxc", (500, 500, 3)),
            OrderedDict([("s0", tagged_shape("yx", (1100, 1100))), ("source_scale", tagged_shape("yx", (500, 500)))]),
            OrderedDict(
                [
                    ("s0", tagged_shape("tczyx", (1, 3, 1, 1100, 1100))),
                    ("source_scale", tagged_shape("tczyx", (1, 3, 1, 500, 500))),
                ]
            ),
        ),
        (  # Different number of channels in in put and export; input downscale was ceil-rounded (i.e. not like ilastik does)
            tagged_shape("yxc", (500, 500, 3)),
            OrderedDict(
                [("s0", tagged_shape("cyx", (2, 999, 999))), ("source_scale", tagged_shape("cyx", (2, 500, 500)))]
            ),
            OrderedDict(
                [
                    ("s0", tagged_shape("tczyx", (1, 3, 1, 999, 999))),
                    ("source_scale", tagged_shape("tczyx", (1, 3, 1, 500, 500))),
                ]
            ),
        ),
        (  # Default scaling would not scale the input + export is cropped + source is middle scale
            tagged_shape("zyxc", (16, 16, 16, 3)),
            OrderedDict(
                [
                    ("0", tagged_shape("czyx", (2, 75, 75, 75))),
                    ("source_scale", tagged_shape("czyx", (2, 25, 25, 25))),
                    ("2", tagged_shape("czyx", (2, 8, 8, 8))),
                ]
            ),
            OrderedDict(
                [
                    ("0", tagged_shape("tczyx", (1, 3, 48, 48, 48))),
                    ("source_scale", tagged_shape("tczyx", (1, 3, 16, 16, 16))),
                    ("2", tagged_shape("tczyx", (1, 3, 5, 5, 5))),
                ]
            ),
        ),
    ],
)
def test_match_target_scales_to_input(shape, input_scales, expected_shapes):
    generated_shapes = _match_target_scales_to_input(shape, input_scales, "source_scale")
    assert generated_shapes == expected_shapes


@pytest.mark.parametrize(
    "shape, input_scales, expected_shapes",
    [
        (  # Simple: match input scales in original order, even if ilastik default would not downscale
            tagged_shape("yx", (4, 4)),
            OrderedDict(
                [
                    ("source_scale", tagged_shape("yx", (4, 4))),
                    ("s2", tagged_shape("yx", (2, 2))),
                    ("s3", tagged_shape("yx", (1, 1))),
                ]
            ),
            OrderedDict(
                [
                    ("source_scale", tagged_shape("tczyx", (1, 1, 1, 4, 4))),
                    ("s2", tagged_shape("tczyx", (1, 1, 1, 2, 2))),
                    ("s3", tagged_shape("tczyx", (1, 1, 1, 1, 1))),
                ]
            ),
        ),
        (  # Input had no channels + ilastik default _would_ downscale
            tagged_shape("yxc", (1000, 1000, 3)),
            OrderedDict([("source_scale", tagged_shape("yx", (1000, 1000)))]),
            OrderedDict([("source_scale", tagged_shape("tczyx", (1, 3, 1, 1000, 1000)))]),
        ),
        (  # Different number of channels in input and export; input downscale was ceil-rounded (i.e. not like ilastik does)
            tagged_shape("yxc", (531, 531, 3)),
            OrderedDict(
                [("source_scale", tagged_shape("cyx", (2, 531, 531))), ("s2", tagged_shape("cyx", (2, 266, 266)))]
            ),
            OrderedDict(
                [
                    ("source_scale", tagged_shape("tczyx", (1, 3, 1, 531, 531))),
                    ("s2", tagged_shape("tczyx", (1, 3, 1, 266, 266))),
                ]
            ),
        ),
        (  # Export is cropped + source is middle scale (upscales should be excluded)
            tagged_shape("zyxc", (16, 16, 16, 3)),
            OrderedDict(
                [
                    ("0", tagged_shape("czyx", (2, 225, 225, 225))),
                    ("1", tagged_shape("czyx", (2, 75, 75, 75))),
                    ("source_scale", tagged_shape("czyx", (2, 25, 25, 25))),
                    ("4", tagged_shape("czyx", (2, 8, 8, 8))),
                ]
            ),
            OrderedDict(
                [
                    ("source_scale", tagged_shape("tczyx", (1, 3, 16, 16, 16))),
                    ("4", tagged_shape("tczyx", (1, 3, 5, 5, 5))),
                ]
            ),
        ),
        (  # Export is cropped + input has no channels
            tagged_shape("zyxc", (16, 16, 16, 3)),
            OrderedDict(
                [
                    ("source_scale", tagged_shape("zyx", (25, 25, 25))),
                    ("4", tagged_shape("zyx", (8, 8, 8))),
                ]
            ),
            OrderedDict(
                [
                    ("source_scale", tagged_shape("tczyx", (1, 3, 16, 16, 16))),
                    ("4", tagged_shape("tczyx", (1, 3, 5, 5, 5))),
                ]
            ),
        ),
    ],
)
def test_match_target_scales_to_input_excluding_upscales(shape, input_scales, expected_shapes):
    generated_shapes = match_target_scales_to_input_excluding_upscales(shape, input_scales, "source_scale")
    assert generated_shapes == expected_shapes
