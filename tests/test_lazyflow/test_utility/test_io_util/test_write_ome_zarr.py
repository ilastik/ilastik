import math
from collections import OrderedDict
from unittest import mock

import numpy
import pytest
import vigra
import zarr

from lazyflow.operators import OpArrayPiper
from lazyflow.utility import Timer
from lazyflow.utility.io_util.write_ome_zarr import write_ome_zarr, _get_scalings


@pytest.fixture(params=["ilastik default order", "2d", "3d", "2dc", "125MiB"])
def data_array(request) -> vigra.VigraArray:
    shapes = {
        "ilastik default order": (1, 128, 127, 10, 1),
        "2d": (256, 255),
        "3d": (10, 126, 125),
        "2dc": (124, 123, 3),
        "125MiB": (30, 1024, 1024),  # 4 bytes per pixel
        "500MiB": (125, 1024, 1024),  # 4 bytes per pixel
        "1GiB": (256, 1024, 1024),
        "3GiB": (768, 1024, 1024),
        "6GiB": (768, 2048, 1024),
    }
    axis_order = {
        "ilastik default order": "txyzc",
        "2d": "yx",
        "3d": "zyx",
        "2dc": "yxc",
        "125MiB": "zyx",
        "500MiB": "zyx",
        "1GiB": "zyx",
        "3GiB": "zyx",
        "6GiB": "zyx",
    }
    shape = shapes[request.param]
    data = vigra.VigraArray(shape, axistags=vigra.defaultAxistags(axis_order[request.param]))
    data[...] = numpy.indices(shape).sum(0)
    return data


def test_metadata_integrity(tmp_path, graph, data_array):
    export_path = tmp_path / "test.zarr"
    source_op = OpArrayPiper(graph=graph)
    source_op.Input.setValue(data_array)
    progress = mock.Mock()
    with Timer() as timer:
        write_ome_zarr(str(export_path), source_op.Output, progress)
        duration = timer.seconds()

    # Manual benchmarking
    raw_size = math.prod(data_array.shape) * data_array.dtype.type().nbytes
    print(";" f"{data_array.shape};" f"{data_array.dtype};" f"{raw_size};" f"{duration};" f"{duration / raw_size};")

    expected_axiskeys = "tczyx"
    assert export_path.exists()
    store = zarr.open(str(export_path))
    assert "multiscales" in store.attrs
    written_meta = store.attrs["multiscales"][0]
    assert all([key in written_meta for key in ("datasets", "axes", "version")])  # Keys required by spec
    assert all([value is not None for value in written_meta.values()])  # Should not write None anywhere
    assert written_meta["version"] == "0.4"
    assert [a["name"] for a in written_meta["axes"]] == list(expected_axiskeys)
    tagged_shape = dict(zip(data_array.axistags.keys(), data_array.shape))
    original_shape_reordered = [tagged_shape[a] if a in tagged_shape else 1 for a in expected_axiskeys]

    discovered_keys = []
    for dataset in written_meta["datasets"]:
        assert dataset["path"] in store
        discovered_keys.append(dataset["path"])
        written_array = store[dataset["path"]]
        assert "axistags" in written_array.attrs, f"no axistags for {dataset['path']}"
        assert vigra.AxisTags.fromJSON(written_array.attrs["axistags"]) == vigra.defaultAxistags(expected_axiskeys)
        assert all([value is not None for value in written_array.attrs.values()])  # Should not write None anywhere
        reported_scalings = [
            transform for transform in dataset["coordinateTransformations"] if transform["type"] == "scale"
        ]
        assert len(reported_scalings) == 1
        expected_shape = tuple(numpy.array(original_shape_reordered) // numpy.array(reported_scalings[0]["scale"]))
        assert written_array.shape == expected_shape
        assert numpy.count_nonzero(written_array) > numpy.prod(expected_shape) / 2, "did not write actual data"
    assert all([key in discovered_keys for key in store.keys()]), "store contains undocumented subpaths"


@pytest.mark.parametrize(
    "data_shape, expected_scalings",
    [
        # Criterion: 4 x chunk size, i.e.: 4 * math.prod(4, 179, 178) -- times 8 for scaling by 2 in 3D
        ((1, 1, 4, 1009, 1010), [[1.0, 1.0, 1.0, 1.0, 1.0]]),  # Just under criterion to be scaled
        ((1, 1, 4, 1011, 1010), [[1.0, 1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 2.0, 2.0]]),  # Just over criterion
        ((1, 1, 1, 30, 30), [[1.0, 1.0, 1.0, 1.0, 1.0]]),  # Too small
        ((1, 1, 2, 4040, 4040), [[1.0, 1.0, 1.0, 1.0, 1.0]]),  # No reduction to singleton or anisotropic scaling
        ((1, 1, 1, 1430, 1430), [[1.0, 1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 2.0, 2.0]]),  # 2D scaling is fine
    ],
)
def test_downscaling(tmp_path, graph, data_shape, expected_scalings):
    data = vigra.VigraArray(data_shape, axistags=vigra.defaultAxistags("tczyx"))
    data[...] = numpy.indices(data_shape).sum(0)
    export_path = tmp_path / "test.zarr"
    source_op = OpArrayPiper(graph=graph)
    source_op.Input.setValue(data)
    progress = mock.Mock()
    with Timer() as timer:
        write_ome_zarr(str(export_path), source_op.Output, progress)
        duration = timer.seconds()

    # Manual benchmarking
    raw_size = math.prod(data.shape) * data.dtype.type().nbytes
    print(";" f"{data.shape};" f"{data.dtype};" f"{raw_size};" f"{duration};" f"{duration / raw_size};")

    store = zarr.open(str(export_path))
    meta = store.attrs["multiscales"][0]
    assert len(meta["datasets"]) == len(expected_scalings)

    for i, scaling in enumerate(expected_scalings):
        dataset = meta["datasets"][i]
        scale_transforms = [
            transform for transform in dataset["coordinateTransformations"] if transform["type"] == "scale"
        ]
        assert scale_transforms[0]["scale"] == scaling


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
        _get_scalings(insane_data_shape, (1, 1, 1, 1, chunk_length), None)
