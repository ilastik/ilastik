###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2024, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
# 		   http://ilastik.org/license/
###############################################################################
from typing import List

import numpy
import pytest
import vigra
import z5py

from lazyflow.operators.ioOperators import OpStreamingH5N5Reader


@pytest.fixture(params=["test.h5", "test.n5", "test.zarr"])
def h5n5_file(request, tmp_path):
    file = OpStreamingH5N5Reader.get_h5_n5_file(str(tmp_path / request.param))
    if request.param == "test.zarr":
        file.attrs["multiscales"] = [{"datasets": [{"path": "volume/data"}]}]
    yield file
    file.close()


@pytest.fixture
def data() -> numpy.ndarray:
    # Create a test dataset
    datashape = (1, 2, 3, 4, 5)
    return numpy.indices(datashape).sum(0).astype(numpy.float32)


def test_reader_loads_data(graph, h5n5_file, data):
    h5n5_file.create_group("volume").create_dataset("data", data=data)
    op = OpStreamingH5N5Reader(graph=graph)
    op.H5N5File.setValue(h5n5_file)
    op.InternalPath.setValue("volume/data")

    assert op.OutputImage.meta.shape == data.shape
    numpy.testing.assert_array_equal(op.OutputImage.value, data)


def test_reader_loads_data_with_axistags(graph, h5n5_file, data):
    axistags = vigra.AxisTags(
        vigra.AxisInfo("x", vigra.AxisType.Space),
        vigra.AxisInfo("y", vigra.AxisType.Space),
        vigra.AxisInfo("z", vigra.AxisType.Space),
        vigra.AxisInfo("c", vigra.AxisType.Channels),
        vigra.AxisInfo("t", vigra.AxisType.Time),
    )
    h5n5_file.create_group("volume").create_dataset("tagged_data", data=data)
    h5n5_file["volume/tagged_data"].attrs["axistags"] = axistags.toJSON()
    op = OpStreamingH5N5Reader(graph=graph)
    op.H5N5File.setValue(h5n5_file)
    op.InternalPath.setValue("volume/tagged_data")

    assert op.OutputImage.meta.shape == data.shape
    assert op.OutputImage.meta.axistags == axistags
    numpy.testing.assert_array_equal(op.OutputImage.value, data)


@pytest.fixture(
    ids=["v0.4", "v0.4 custom", "v0.3", "v0.3 multiple datasets", "v0.1/v0.2"],
    params=[
        (  # Tuple[OME-Zarr_multiscale_spec, expected_axiskeys]
            [  # Not fully OME-Zarr compliant spec; just the axes
                {
                    "datasets": [{"path": "volume/ome_data"}],
                    "axes": [  # Conventional order
                        {"type": "time", "name": "t", "unit": "sec"},
                        {"type": "channel", "name": "c"},
                        {"type": "space", "name": "z", "unit": "pixel"},
                        {"type": "space", "name": "y", "unit": "pixel"},
                        {"type": "space", "name": "x", "unit": "pixel"},
                    ],
                }
            ],
            ["t", "c", "z", "y", "x"],
        ),
        (
            [
                {
                    "datasets": [{"path": "volume/ome_data"}],
                    "axes": [  # v0.4 requires leading t and c, but xyz may be arbitrarily ordered
                        {"type": "time", "name": "t", "unit": "sec"},
                        {"type": "channel", "name": "c"},
                        {"type": "space", "name": "x", "unit": "pixel"},
                        {"type": "space", "name": "y", "unit": "pixel"},
                        {"type": "space", "name": "z", "unit": "pixel"},
                    ],
                }
            ],
            ["t", "c", "x", "y", "z"],
        ),
        ([{"datasets": [{"path": "volume/ome_data"}], "axes": ["t", "c", "z", "y", "x"]}], ["t", "c", "z", "y", "x"]),
        (
            [  # Multiple multiscales tested on v0.3 because it's more compact :)
                {"datasets": [{"path": "somewhere/else"}], "axes": ["t", "c", "z", "y", "x"]},
                {"datasets": [{"path": "volume/ome_data"}], "axes": ["t", "c", "y", "x", "z"]},
            ],
            ["t", "c", "y", "x", "z"],
        ),
        ([{"datasets": [{"path": "volume/ome_data"}]}], ["t", "c", "z", "y", "x"]),
    ],
)
def ome_zarr_params(request, tmp_path, data) -> (z5py.ZarrFile, List[str]):
    """Sets up a Zarr-file with relevant OME-Zarr metadata, returns file handle and expected axis keys"""
    spec, expected_axiskeys = request.param
    file = OpStreamingH5N5Reader.get_h5_n5_file(str(tmp_path / "test.zarr"))
    file.attrs["multiscales"] = spec
    file.create_group("volume").create_dataset("ome_data", data=data)
    yield file, expected_axiskeys
    file.close()


def test_reader_loads_ome_zarr_axes(graph, ome_zarr_params, data):
    ome_zarr_file, expected_axes = ome_zarr_params
    op = OpStreamingH5N5Reader(graph=graph)
    op.H5N5File.setValue(ome_zarr_file)
    op.InternalPath.setValue("volume/ome_data")

    assert op.OutputImage.meta.shape == data.shape
    assert op.OutputImage.meta.axistags.keys() == expected_axes
    numpy.testing.assert_array_equal(op.OutputImage.value, data)


@pytest.mark.parametrize(
    "attrs",
    [
        {},
        {"axes": "xyz"},
        {"multiscales": [{"datasets": []}]},  # Empty datasets
        {"multiscales": [{"datasets": [{"path": "s0"}]}]},  # Valid OME-Zarr but no meta for this dataset
    ],
)
def test_reader_raises_on_invalid_meta(tmp_path, graph, data, attrs):
    file = OpStreamingH5N5Reader.get_h5_n5_file(str(tmp_path / "test.zarr"))
    for k, v in attrs.items():
        file.attrs[k] = v
    file.create_group("volume").create_dataset("ome_data", data=data)

    op = OpStreamingH5N5Reader(graph=graph)
    op.H5N5File.setValue(file)
    with pytest.raises(ValueError, match="Could not find axis information"):
        op.InternalPath.setValue("volume/ome_data")
