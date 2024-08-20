import math
from unittest import mock

import numpy
import pytest
import vigra
import zarr

from lazyflow.operators import OpArrayPiper
from lazyflow.utility import Timer
from lazyflow.utility.io_util.write_ome_zarr import write_ome_zarr


@pytest.fixture(params=["125MiB"])
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


def test_write_new_ome_zarr_on_disc(tmp_path, graph, data_array):
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
    m = store.attrs["multiscales"][0]
    assert all(key in m for key in ("datasets", "axes", "version"))
    assert m["version"] == "0.4"
    assert [a["name"] for a in m["axes"]] == list(expected_axiskeys)
    tagged_shape = dict(zip(data_array.axistags.keys(), data_array.shape))
    original_shape_reordered = [tagged_shape[a] if a in tagged_shape else 1 for a in expected_axiskeys]

    discovered_keys = []
    for i, dataset in enumerate(m["datasets"]):
        assert dataset["path"] in store
        discovered_keys.append(dataset["path"])
        written_array = store[dataset["path"]]
        assert "axistags" in written_array.attrs, f"no axistags for {dataset['path']}"
        assert vigra.AxisTags.fromJSON(written_array.attrs["axistags"]) == vigra.defaultAxistags(expected_axiskeys)
        reported_scaling = dataset["coordinateTransformations"][0]["scale"]
        expected_shape = tuple(numpy.array(original_shape_reordered) / numpy.array(reported_scaling))
        assert written_array.shape == expected_shape
        assert numpy.count_nonzero(written_array) > numpy.prod(expected_shape) / 2, "did not write actual data"
    assert all([key in discovered_keys for key in store.keys()]), "store contains undocumented subpaths"
