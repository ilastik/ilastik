import math
from collections import OrderedDict
from unittest import mock

import numpy
import pytest
import vigra
import zarr

from lazyflow.operators import OpArrayPiper
from lazyflow.roi import roiToSlice
from lazyflow.utility.io_util import multiscaleStore
from lazyflow.utility.io_util.OMEZarrStore import OMEZarrMultiscaleMeta
from lazyflow.utility.io_util.write_ome_zarr import write_ome_zarr
from lazyflow.utility.resolution import unitTags


@pytest.mark.parametrize(
    "shape, axes",
    [
        ((1, 128, 127, 10, 1), "txyzc"),  # ilastik default order
        ((1, 1, 3, 26, 25), "tczyx"),  # OME-Zarr convention
        ((256, 255), "yx"),
        ((10, 126, 125), "zyx"),
        ((124, 123, 3), "yxc"),
    ],
)
def test_metadata_integrity(tmp_path, graph, shape, axes):
    data_array = vigra.VigraArray(shape, axistags=vigra.defaultAxistags(axes))
    data_array[...] = numpy.indices(shape).sum(0)
    export_path = tmp_path / "test.zarr"
    source_op = OpArrayPiper(graph=graph)
    source_op.Input.setValue(data_array)
    progress = mock.Mock()

    write_ome_zarr(str(export_path), source_op.Output, None, progress)

    expected_axiskeys = "tczyx"
    assert export_path.exists()
    group = zarr.open(str(export_path))
    assert "multiscales" in group.attrs
    written_meta = group.attrs["multiscales"][0]
    assert all([key in written_meta for key in ("datasets", "axes", "version")])  # Keys required by spec
    assert all([value is not None for value in written_meta.values()])  # Should not write None anywhere
    assert written_meta["version"] == "0.4"
    assert [a["name"] for a in written_meta["axes"]] == list(expected_axiskeys)
    tagged_shape = dict(zip(data_array.axistags.keys(), data_array.shape))
    original_shape_reordered = [tagged_shape[a] if a in tagged_shape else 1 for a in expected_axiskeys]

    discovered_keys = []
    for dataset in written_meta["datasets"]:
        assert dataset["path"] in group
        discovered_keys.append(dataset["path"])
        written_array = group[dataset["path"]]
        assert written_array.fill_value is not None, "FIJI and z5py don't open zarrays without a fill_value"
        assert "axistags" in written_array.attrs, f"no axistags for {dataset['path']}"
        assert unitTags.fromJSON(written_array.attrs["axistags"]) == unitTags(vigra.defaultAxistags(expected_axiskeys))
        assert all([value is not None for value in written_array.attrs.values()])  # Should not write None anywhere
        reported_scalings = [
            transform for transform in dataset["coordinateTransformations"] if transform["type"] == "scale"
        ]
        assert len(reported_scalings) == 1
        expected_shape = tuple(
            math.ceil(orig / reported)
            for orig, reported in zip(original_shape_reordered, reported_scalings[0]["scale"])
        )
        assert written_array.shape == expected_shape
        assert numpy.count_nonzero(written_array) > numpy.prod(expected_shape) / 2, "did not write actual data"
    assert all([key in discovered_keys for key in group.keys()]), "store contains undocumented subpaths"


@pytest.mark.skip("To be implemented after releasing single-scale export")
@pytest.mark.parametrize(
    "data_shape,scaling_on",
    [
        # Criterion: 4 x chunk size, i.e.: 4 * math.prod(4, 179, 178) -- times 8 for scaling by 2 in 3D
        ((1, 1, 4, 1008, 1010), True),  # Just under criterion to be scaled
        ((1, 1, 1, 30, 30), True),  # Tiny
        ((1, 1, 2, 1432, 1432), True),  # No reduction to singleton or anisotropic scaling
        ((3, 3, 67, 79, 97), True),  # Big enough to scale when taking c and t into account (which we shouldn't)
        ((1, 1, 4, 1432, 1432), False),  # Big enough but switched off
    ],
)
def test_writes_with_no_scaling(tmp_path, graph, data_shape, scaling_on):
    data = vigra.VigraArray(data_shape, axistags=vigra.defaultAxistags("tczyx"))
    data[...] = numpy.indices(data_shape).sum(0)
    export_path = tmp_path / "test.zarr"
    source_op = OpArrayPiper(graph=graph)
    source_op.Input.setValue(data)
    progress = mock.Mock()

    write_ome_zarr(str(export_path), source_op.Output, progress, compute_downscales=scaling_on)

    group = zarr.open(str(export_path))
    meta = group.attrs["multiscales"][0]
    assert len(meta["datasets"]) == 1
    dataset = meta["datasets"][0]
    numpy.testing.assert_array_equal(group[dataset["path"]], data)
    scale_transforms = [transform for transform in dataset["coordinateTransformations"] if transform["type"] == "scale"]
    assert scale_transforms[0]["scale"] == [1.0, 1.0, 1.0, 1.0, 1.0]


@pytest.mark.skip("To be implemented after releasing single-scale export")
@pytest.mark.parametrize(
    "data_shape, computation_block_shape, expected_scalings",
    [
        # Criterion: 4 x chunk size = 4 * math.prod(50, 51, 50) -- times 8 for scaling by 2 in 3D
        ((1, 1, 66, 250, 250), None, [[1.0, 1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 2.0, 2.0, 2.0]]),
        # 2D scaling: complements the (1, 1, 2, 1432, 1432) case in test_writes_with_no_scaling.
        # Ensures that the xy dimensions are sufficient to be scaled (but z=2 suppresses it).
        ((1, 1, 1, 1432, 1432), None, [[1.0, 1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 2.0, 2.0]]),
        (  # Provoke rounding difficulties due to blockwise scaling at 4x
            (1, 1, 310, 361, 371),  # 371/4 = 92.75, so expected scaled shape in x is 93. 371/91 = 4 blocks + 7 pixels.
            (1, 1, 310, 361, 91),  # 91/4 = 22.75, so 23 per block. Plus 7/4 = 1.75, so 2. Total of 94px blockwise.
            [[1.0, 1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 2.0, 2.0, 2.0], [1.0, 1.0, 4.0, 4.0, 4.0]],
        ),
    ],
)
def test_downscaling(tmp_path, graph, data_shape, computation_block_shape, expected_scalings):
    data = vigra.VigraArray(data_shape, axistags=vigra.defaultAxistags("tczyx"))
    data[...] = numpy.indices(data_shape).sum(0)
    export_path = tmp_path / "test.zarr"
    source_op = OpArrayPiper(graph=graph)
    source_op.Input.setValue(data)
    # max_blockshape should not affect chunk size on disc or scaling decision,
    # but computations and scaling are broken up into blocks.
    source_op.Output.meta.max_blockshape = computation_block_shape
    progress = mock.Mock()

    write_ome_zarr(str(export_path), source_op.Output, progress, compute_downscales=True)

    group = zarr.open(str(export_path))
    meta = group.attrs["multiscales"][0]
    assert len(meta["datasets"]) == len(expected_scalings)
    numpy.testing.assert_array_equal(group[meta["datasets"][0]["path"]], data)

    for i, scaling in enumerate(expected_scalings):
        dataset = meta["datasets"][i]
        scale_transforms = [
            transform for transform in dataset["coordinateTransformations"] if transform["type"] == "scale"
        ]
        assert scale_transforms[0]["scale"] == scaling
        # Makes sure that the blockwise-scaled image is identical to downscaling the data at once
        if scaling == [1.0, 1.0, 4.0, 4.0, 4.0]:
            downscaled_data = data[:, :, ::4, ::4, ::4]
            numpy.testing.assert_array_equal(group[dataset["path"]], downscaled_data)
        elif scaling == [1.0, 1.0, 2.0, 2.0, 2.0]:
            downscaled_data = data[:, :, ::2, ::2, ::2]
            numpy.testing.assert_array_equal(group[dataset["path"]], downscaled_data)
        elif scaling == [1.0, 1.0, 1.0, 2.0, 2.0]:
            downscaled_data = data[:, :, :, ::2, ::2]
            numpy.testing.assert_array_equal(group[dataset["path"]], downscaled_data)


@pytest.mark.skip("To be implemented after releasing single-scale export")
def test_downscaling_raises():
    # Testing at the implementation level instead of top-level write_ome_zarr for simplicity.
    # Would need to set up a data array with an insane shape without actually allocating RAM for it.
    scaling_factor = 2
    sanity_limit = 20
    minimum_chunks_per_scale = 8
    chunk_length = 100
    insane_length = chunk_length * (scaling_factor**sanity_limit) * minimum_chunks_per_scale
    insane_data_shape = OrderedDict({"t": 1, "c": 1, "z": 1, "y": 1, "x": insane_length})
    with pytest.raises(ValueError, match="Too many scales"):
        _compute_new_scaling_factors(insane_data_shape, (1, 1, 1, 1, chunk_length), compute_downscales=True)


@pytest.mark.skip("To be implemented after releasing single-scale export")
def test_blockwise_downsampling_edge_cases():
    """Ensures that downsampling can handle blocks smaller than scaling step size,
    and starts that are not a multiple of block size (both of which can occur in the last block
    along an axis).
    Also ensures that the correct pixels are sampled when starting in the middle of a step (here x),
    exactly at the start of a step (here y), and when no step start is within block (0 sampled along z)."""
    # Tested at implementation level because passing odd scaling and data shapes is easier this way.
    data_shape = (1, 1, 15, 15, 25)
    step_size = 11
    data = vigra.VigraArray(data_shape, axistags=vigra.defaultAxistags("tczyx"))
    data[...] = numpy.indices(data_shape).sum(0)
    roi = ([0, 0, 6, step_size, 24], [1, 1, 15, 15, 25])
    block = data[roiToSlice(*roi)]
    expected_scaled_roi = ([0, 0, 1, 1, 3], [1, 1, 2, 2, 3])
    expected_scaled_block = data[:, :, ::step_size, ::step_size, ::step_size][roiToSlice(*expected_scaled_roi)]
    scaling = OrderedDict([("t", 1), ("c", 1), ("z", step_size), ("y", step_size), ("x", step_size)])

    scaled_block, scaled_roi = _apply_scaling_method(block, roi, scaling)

    assert scaled_block.shape == expected_scaled_block.shape
    numpy.testing.assert_array_equal(scaled_block, expected_scaled_block)
    assert scaled_roi == expected_scaled_roi


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
    write_ome_zarr(str(export_path), source_op.Output, None, progress)

    with pytest.raises(FileExistsError):
        write_ome_zarr(str(export_path), source_op.Output, None, progress)

    source_op.Input.setValue(data_array2)
    with pytest.raises(FileExistsError):
        write_ome_zarr(str(export_path), source_op.Output, None, progress)
    # should not overwrite existing array
    group = zarr.open(str(export_path))
    numpy.testing.assert_array_equal(group["s0"], original_data_array)


def test_match_input_scale_key_and_factors(tmp_path, tiny_5d_vigra_array_piper):
    """If the source slot has scale metadata, the export should match the scale name to the input.
    Scaling metadata should be relative to the input's raw data."""
    export_path = tmp_path / "test.zarr"
    source_op = tiny_5d_vigra_array_piper
    progress = mock.Mock()
    input_axes = ["t", "z", "y", "x"]
    multiscales: multiscaleStore.Multiscales = OrderedDict(
        [
            ("raw_scale", OrderedDict(zip(input_axes, (2, 15, 15, 15)))),
            ("matching_scale", OrderedDict(zip(input_axes, (2, 5, 5, 5)))),
            ("downscale", OrderedDict(zip(input_axes, (2, 2, 2, 2)))),
        ]
    )
    source_op.Output.meta.scales = multiscales
    source_op.Output.meta.active_scale = "matching_scale"
    # Scale metadata should be relative to raw scale, even if the export was not scaled
    # Exported array is 5d, so 5 scaling entries expected even though source multiscales to match are 4d
    expected_matching_scale_transform = [{"type": "scale", "scale": [1.0, 1.0, 3.0, 3.0, 3.0]}]

    write_ome_zarr(str(export_path), source_op.Output, None, progress)

    group = zarr.open(str(export_path))
    assert "multiscales" in group.attrs
    m = group.attrs["multiscales"][0]
    assert "datasets" in m and "path" in m["datasets"][0]
    assert len(m["datasets"]) == 1
    assert m["datasets"][0]["path"] == "matching_scale"
    assert m["datasets"][0]["coordinateTransformations"] == expected_matching_scale_transform


def test_port_ome_zarr_metadata_from_input(tmp_path, tiny_5d_vigra_array_piper):
    """If the source slot has scale metadata, the export should match the scale name to the input.
    If there is OME-Zarr specific additional metadata (even unused in ilastik),
    the export should write metadata that describe the pyramid as a whole, and those that
    describe the written scale.
    If there is a CoordinateOffset (i.e. the user has restricted a ROI in the export settings),
    this should be written to the multiscale's coordinateTransformations - and correctly combined
    with the input's coordinateTransformations (multiplied by scale to convert pixel offset to physical units,
    and added to the input's translation)."""
    export_path = tmp_path / "test.zarr"
    source_op = tiny_5d_vigra_array_piper
    progress = mock.Mock()
    multiscales: multiscaleStore.Multiscales = OrderedDict(
        [
            ("raw_scale", OrderedDict([("t", 2), ("z", 17), ("y", 17), ("x", 17)])),
            ("matching_scale", OrderedDict([("t", 2), ("z", 9), ("y", 9), ("x", 9)])),
            ("downscale", OrderedDict([("t", 2), ("z", 5), ("y", 5), ("x", 5)])),
        ]
    )
    # The tiny_5d_array is 5x5x5; in this test it represents a subregion of source matching_scale after a 4/4/4 offset
    export_offset = (0, 0, 4, 4, 4)
    source_op.Output.meta.scales = multiscales
    source_op.Output.meta.active_scale = "matching_scale"
    expected_multiscale_transform = [{"type": "scale", "scale": [0.1, 1.0, 1.0, 1.0, 1.0]}]
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

    write_ome_zarr(str(export_path), source_op.Output, export_offset, progress)

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
