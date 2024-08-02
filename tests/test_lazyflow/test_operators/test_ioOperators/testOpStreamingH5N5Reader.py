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
import numpy
import pytest
import vigra

from lazyflow.operators.ioOperators import OpStreamingH5N5Reader


@pytest.fixture(params=["test.h5", "test.n5", "test.zarr"])
def h5n5_file(request, tmp_path):
    file = OpStreamingH5N5Reader.get_h5_n5_file(str(tmp_path / request.param))
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


@pytest.fixture(params=["v0.4", "v0.3", "v0.1/v0.2"])
def ome_zarr_file(request, tmp_path, data):
    file = OpStreamingH5N5Reader.get_h5_n5_file(str(tmp_path / "test.zarr"))
    # Not a fully OME-Zarr compliant spec; just the axes
    file.attrs["multiscales"] = [{"datasets": []}]
    axes = {
        "v0.4": [
            {"type": "time", "name": "t", "unit": "sec"},
            {"type": "channel", "name": "c"},
            {"type": "space", "name": "z", "unit": "pixel"},
            {"type": "space", "name": "y", "unit": "pixel"},
            {"type": "space", "name": "x", "unit": "pixel"},
        ],
        "v0.3": ["t", "c", "z", "y", "x"],
    }
    if request.param in axes:  # v0.1 and v0.2 did not allow axes metadata
        file.attrs["axes"] = axes[request.param]
    file.create_group("volume").create_dataset("ome_data", data=data)
    yield file
    file.close()


def test_reader_loads_ome_zarr_axes(graph, ome_zarr_file, data):
    op = OpStreamingH5N5Reader(graph=graph)
    op.H5N5File.setValue(ome_zarr_file)
    op.InternalPath.setValue("volume/ome_data")

    assert op.OutputImage.meta.shape == data.shape
    assert op.OutputImage.meta.axistags.keys() == ["t", "c", "z", "y", "x"]
    numpy.testing.assert_array_equal(op.OutputImage.value, data)
