from unittest import mock

import numpy
import pytest
import vigra
import zarr

from lazyflow.operators import OpArrayPiper
from lazyflow.utility.io_util.write_ome_zarr import write_ome_zarr


@pytest.fixture(params=["ilastik default order", "2d", "3d", "2dc"])
def data_array(request) -> vigra.VigraArray:
    shapes = {
        "ilastik default order": (1, 128, 128, 10, 1),
        "2d": (128, 128),
        "3d": (10, 128, 128),
        "2dc": (128, 128, 3),
    }
    axis_order = {
        "ilastik default order": "txyzc",
        "2d": "yx",
        "3d": "zyx",
        "2dc": "yxc",
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
    write_ome_zarr(str(export_path), source_op.Output, progress)

    assert export_path.exists()
    store = zarr.open(str(export_path))
    assert "multiscales" in store.attrs
    m = store.attrs["multiscales"][0]
    assert all(key in m for key in ("datasets", "axes", "version"))
    assert m["version"] == "0.4"
    assert [a["name"] for a in m["axes"]] == ["t", "c", "z", "y", "x"]
    assert all(dataset["path"] in store for dataset in m["datasets"])
