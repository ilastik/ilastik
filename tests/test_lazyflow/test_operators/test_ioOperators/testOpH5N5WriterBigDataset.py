from builtins import object

###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
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
import pytest

from lazyflow.operators.opArrayPiper import OpArrayPiper
from lazyflow.operators.ioOperators import OpH5N5WriterBigDataset
from shutil import rmtree
import numpy
import vigra
import h5py
import z5py
import os
import lazyflow.graph

import logging

logger = logging.getLogger("tests.testOpH5N5WriterBigDataset")
cacheLogger = logging.getLogger("lazyflow.operators.ioOperators.ioOperators.OpH5N5WriterBigDataset")
requesterLogger = logging.getLogger("lazyflow.utility.bigRequestStreamer")


class TestOpH5N5WriterBigDataset(object):
    @pytest.fixture
    def n5_path(self, tmp_path):
        dst = tmp_path / "bigH5TestData.n5"
        yield str(dst)
        rmtree(dst)

    @pytest.fixture
    def h5_path(self, tmp_path):
        dst = tmp_path / "bigH5TestData.h5"
        yield str(dst)
        dst.unlink()

    @pytest.fixture
    def dataShape(self):
        return (1, 10, 128, 128, 1)

    @pytest.fixture
    def testData(self, dataShape):
        testData = vigra.VigraArray(dataShape, axistags=vigra.defaultAxistags("txyzc"), order="C")
        testData[...] = numpy.indices(dataShape).sum(0)
        return testData

    @pytest.fixture
    def datasetInternalPath(self):
        return "volume/data"

    def test_Writer(self, graph, testData, dataShape, h5_path, n5_path, datasetInternalPath):
        # Create the h5 file

        hdf5File = h5py.File(h5_path)
        n5File = z5py.N5File(n5_path)

        opPiper = OpArrayPiper(graph=graph)
        opPiper.Input.setValue(testData)

        h5_opWriter = OpH5N5WriterBigDataset(graph=graph)
        n5_opWriter = OpH5N5WriterBigDataset(graph=graph)
        h5_opWriter.h5N5File.setValue(hdf5File)
        n5_opWriter.h5N5File.setValue(n5File)
        h5_opWriter.h5N5Path.setValue(datasetInternalPath)
        n5_opWriter.h5N5Path.setValue(datasetInternalPath)
        h5_opWriter.Image.connect(opPiper.Output)
        n5_opWriter.Image.connect(opPiper.Output)

        # Force the operator to execute by asking for the output (a bool)
        h5_success = h5_opWriter.WriteImage.value
        n5_success = n5_opWriter.WriteImage.value

        assert h5_success
        assert n5_success

        hdf5File.close()
        n5File.close()

        # Check the file.
        hdf5File = h5py.File(h5_path, "r")
        n5File = z5py.N5File(n5_path, "r")
        h5_dataset = hdf5File[datasetInternalPath]
        n5_dataset = n5File[datasetInternalPath]
        assert h5_dataset.shape == dataShape
        assert n5_dataset.shape == dataShape
        assert (numpy.all(h5_dataset[...] == testData.view(numpy.ndarray)[...])).all()
        assert (numpy.all(n5_dataset[...] == testData.view(numpy.ndarray)[...])).all()
        hdf5File.close()
        n5File.close()

    def test_Writer_2(self, graph, testData, dataShape, h5_path, n5_path, datasetInternalPath):
        # Create the h5 file
        hdf5File = h5py.File(h5_path)
        n5File = z5py.N5File(n5_path)

        opPiper = OpArrayPiper(graph=graph)
        opPiper.Input.setValue(testData)

        h5_opWriter = OpH5N5WriterBigDataset(graph=graph)
        n5_opWriter = OpH5N5WriterBigDataset(graph=graph)

        # This checks that you can give a preexisting group as the file
        h5_g = hdf5File.create_group("volume")
        n5_g = n5File.create_group("volume")
        h5_opWriter.h5N5File.setValue(h5_g)
        n5_opWriter.h5N5File.setValue(n5_g)
        h5_opWriter.h5N5Path.setValue("data")
        n5_opWriter.h5N5Path.setValue("data")
        h5_opWriter.Image.connect(opPiper.Output)
        n5_opWriter.Image.connect(opPiper.Output)

        # Force the operator to execute by asking for the output (a bool)
        h5_success = h5_opWriter.WriteImage.value
        n5_success = n5_opWriter.WriteImage.value
        assert h5_success
        assert n5_success

        hdf5File.close()
        n5File.close()

        # Check the file.
        hdf5File = h5py.File(h5_path, "r")
        n5File = z5py.N5File(n5_path, "r")
        h5_dataset = hdf5File[datasetInternalPath]
        n5_dataset = n5File[datasetInternalPath]
        assert h5_dataset.shape == dataShape
        assert n5_dataset.shape == dataShape
        assert (numpy.all(h5_dataset[...] == testData.view(numpy.ndarray)[...])).all()
        assert (numpy.all(n5_dataset[...] == testData.view(numpy.ndarray)[...])).all()
        hdf5File.close()
        n5File.close()

    def test_Writer_3(self, graph, testData, dataShape, h5_path, n5_path, datasetInternalPath):
        # Create the h5 file
        hdf5File = h5py.File(h5_path)
        n5File = z5py.N5File(n5_path)

        opPiper = OpArrayPiper(graph=graph)
        opPiper.Input.setValue(testData)

        # Force extra metadata onto the output
        opPiper.Output.meta.ideal_blockshape = (1, 1, 0, 0, 1)
        # Pretend the RAM usage will be really high to force lots of tiny blocks
        opPiper.Output.meta.ram_usage_per_requested_pixel = 1000000.0

        h5_opWriter = OpH5N5WriterBigDataset(graph=graph)
        n5_opWriter = OpH5N5WriterBigDataset(graph=graph)

        # This checks that you can give a preexisting group as the file
        h5_g = hdf5File.create_group("volume")
        n5_g = n5File.create_group("volume")
        h5_opWriter.h5N5File.setValue(h5_g)
        n5_opWriter.h5N5File.setValue(n5_g)
        h5_opWriter.h5N5Path.setValue("data")
        n5_opWriter.h5N5Path.setValue("data")
        h5_opWriter.Image.connect(opPiper.Output)
        n5_opWriter.Image.connect(opPiper.Output)

        # Force the operator to execute by asking for the output (a bool)
        h5_success = h5_opWriter.WriteImage.value
        n5_success = n5_opWriter.WriteImage.value
        assert h5_success
        assert n5_success

        hdf5File.close()
        n5File.close()

        # Check the file.
        hdf5File = h5py.File(h5_path, "r")
        n5File = z5py.File(n5_path, "r")
        h5_dataset = hdf5File[datasetInternalPath]
        n5_dataset = n5File[datasetInternalPath]
        assert h5_dataset.shape == dataShape
        assert n5_dataset.shape == dataShape
        assert (numpy.all(h5_dataset[...] == testData.view(numpy.ndarray)[...])).all()
        assert (numpy.all(n5_dataset[...] == testData.view(numpy.ndarray)[...])).all()
        hdf5File.close()
        n5File.close()
