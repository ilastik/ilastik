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
from typing import Union

import h5py
import numpy
import pytest
import vigra
import z5py

import lazyflow.graph
from lazyflow.operators.ioOperators import OpH5N5WriterBigDataset
from lazyflow.operators.opArrayPiper import OpArrayPiper


def setup_writer(
    graph: lazyflow.graph.Graph,
    file: Union[h5py.File, z5py.N5File, h5py.Group, z5py.Group],
    internal_path: str,
    source_slot: lazyflow.slot.OutputSlot,
) -> OpH5N5WriterBigDataset:
    opWriter = OpH5N5WriterBigDataset(graph=graph)
    opWriter.h5N5File.setValue(file)
    opWriter.h5N5Path.setValue(internal_path)
    opWriter.Image.connect(source_slot)
    return opWriter


@pytest.fixture
def test_data_order_c():
    dataShape = (1, 10, 128, 128, 1)
    testData = vigra.VigraArray(dataShape, axistags=vigra.defaultAxistags("txyzc"), order="C")
    testData[...] = numpy.indices(dataShape).sum(0)
    return testData


@pytest.mark.parametrize(
    "file_ext, file_class",
    [
        ("h5", h5py.File),
        ("n5", z5py.N5File),
    ],
)
def test_write_nested_internal_path_with_order_c(tmp_path, graph, test_data_order_c, file_ext, file_class):
    file_path = tmp_path / f"test.{file_ext}"

    opPiper = OpArrayPiper(graph=graph)
    opPiper.Input.setValue(test_data_order_c)
    file = file_class(file_path, "w")
    internal_path = "volume/data"
    opWriter = setup_writer(graph, file, internal_path, opPiper.Output)

    try:
        assert opWriter.WriteImage.value  # Trigger write
    finally:
        file.close()
    del file

    file = file_class(file_path, "r")
    dataset = file[internal_path]

    try:
        assert dataset.shape == test_data_order_c.shape
        numpy.testing.assert_array_equal(dataset[...], test_data_order_c.view(numpy.ndarray)[...])
    finally:
        file.close()


@pytest.fixture
def test_data_default_order():
    dataShape = (1, 10, 128, 128, 1)
    testData = vigra.VigraArray(dataShape, axistags=vigra.defaultAxistags("txyzc"))  # default vigra order this time...
    testData[...] = numpy.indices(dataShape).sum(0)
    return testData


@pytest.mark.parametrize(
    "file_ext, file_class",
    [
        ("h5", h5py.File),
        ("n5", z5py.N5File),
    ],
)
def test_write_to_group_default_order(tmp_path, graph, test_data_default_order, file_ext, file_class):
    opPiper = OpArrayPiper(graph=graph)
    opPiper.Input.setValue(test_data_default_order)

    file_path = tmp_path / f"test.{file_ext}"
    file = file_class(file_path, "w")
    g = file.create_group("volume")
    opWriter = setup_writer(graph, g, "data", opPiper.Output)

    try:
        assert opWriter.WriteImage.value  # Trigger write
    finally:
        file.close()
    del file

    file = file_class(file_path, "r")
    dataset = file["volume/data"]

    try:
        assert dataset.shape == test_data_default_order.shape
        numpy.testing.assert_array_equal(dataset[...], test_data_default_order.view(numpy.ndarray)[...])
    finally:
        file.close()


@pytest.mark.parametrize(
    "file_ext, file_class",
    [
        ("h5", h5py.File),
        ("n5", z5py.N5File),
    ],
)
def test_write_to_group_with_extra_meta(tmp_path, graph, test_data_default_order, file_ext, file_class):
    opPiper = OpArrayPiper(graph=graph)
    opPiper.Input.setValue(test_data_default_order)

    # Force extra metadata onto the output
    opPiper.Output.meta.ideal_blockshape = (1, 1, 0, 0, 1)
    # Pretend the RAM usage will be really high to force lots of tiny blocks
    opPiper.Output.meta.ram_usage_per_requested_pixel = 1000000.0

    file_path = tmp_path / f"test.{file_ext}"
    file = file_class(file_path, "w")
    g = file.create_group("volume")
    opWriter = setup_writer(graph, g, "data", opPiper.Output)

    try:
        assert opWriter.WriteImage.value  # Trigger write
    finally:
        file.close()
    del file

    file = file_class(file_path, "r")
    dataset = file["volume/data"]

    try:
        assert dataset.shape == test_data_default_order.shape
        numpy.testing.assert_array_equal(dataset[...], test_data_default_order.view(numpy.ndarray)[...])
    finally:
        file.close()
