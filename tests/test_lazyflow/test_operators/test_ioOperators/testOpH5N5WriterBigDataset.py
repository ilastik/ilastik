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
    def setup_method(self, method):
        self.graph = lazyflow.graph.Graph()
        self.testDataH5FileName = "bigH5TestData.h5"
        self.testDataN5FileName = "bigN5TestData.n5"
        self.datasetInternalPath = "volume/data"

        # Generate some test data
        self.dataShape = (1, 10, 128, 128, 1)
        self.testData = vigra.VigraArray(self.dataShape, axistags=vigra.defaultAxistags("txyzc"), order="C")
        self.testData[...] = numpy.indices(self.dataShape).sum(0)

    def teardown_method(self, method):
        # Clean up: Delete the test file.
        try:
            os.remove(self.testDataH5FileName)
            rmtree(self.testDataN5FileName)
        except:
            pass

    def test_Writer(self):
        # Create the h5 file
        hdf5File = h5py.File(self.testDataH5FileName)
        n5File = z5py.N5File(self.testDataN5FileName)

        opPiper = OpArrayPiper(graph=self.graph)
        opPiper.Input.setValue(self.testData)

        h5_opWriter = OpH5N5WriterBigDataset(graph=self.graph)
        n5_opWriter = OpH5N5WriterBigDataset(graph=self.graph)
        h5_opWriter.h5N5File.setValue(hdf5File)
        n5_opWriter.h5N5File.setValue(n5File)
        h5_opWriter.h5N5Path.setValue(self.datasetInternalPath)
        n5_opWriter.h5N5Path.setValue(self.datasetInternalPath)
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
        hdf5File = h5py.File(self.testDataH5FileName, "r")
        n5File = z5py.N5File(self.testDataN5FileName, "r")
        h5_dataset = hdf5File[self.datasetInternalPath]
        n5_dataset = n5File[self.datasetInternalPath]
        assert h5_dataset.shape == self.dataShape
        assert n5_dataset.shape == self.dataShape
        assert (numpy.all(h5_dataset[...] == self.testData.view(numpy.ndarray)[...])).all()
        assert (numpy.all(n5_dataset[...] == self.testData.view(numpy.ndarray)[...])).all()
        hdf5File.close()
        n5File.close()


class TestOpH5N5WriterBigDataset_2(object):
    def setup_method(self, method):
        self.graph = lazyflow.graph.Graph()
        self.testDataH5FileName = "bigH5TestData.h5"
        self.testDataN5FileName = "bigH5TestData.n5"
        self.datasetInternalPath = "volume/data"

        # Generate some test data
        self.dataShape = (1, 10, 128, 128, 1)
        self.testData = vigra.VigraArray(
            self.dataShape, axistags=vigra.defaultAxistags("txyzc")
        )  # default vigra order this time...
        self.testData[...] = numpy.indices(self.dataShape).sum(0)

    def teardown_method(self, method):
        # Clean up: Delete the test file.
        try:
            os.remove(self.testDataH5FileName)
            rmtree(self.testDataN5FileName)
        except:
            pass

    def test_Writer(self):

        # Create the h5 file
        hdf5File = h5py.File(self.testDataH5FileName)
        n5File = z5py.N5File(self.testDataN5FileName)

        opPiper = OpArrayPiper(graph=self.graph)
        opPiper.Input.setValue(self.testData)

        h5_opWriter = OpH5N5WriterBigDataset(graph=self.graph)
        n5_opWriter = OpH5N5WriterBigDataset(graph=self.graph)

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
        hdf5File = h5py.File(self.testDataH5FileName, "r")
        n5File = h5py.File(self.testDataH5FileName, "r")
        h5_dataset = hdf5File[self.datasetInternalPath]
        n5_dataset = n5File[self.datasetInternalPath]
        assert h5_dataset.shape == self.dataShape
        assert n5_dataset.shape == self.dataShape
        assert (numpy.all(h5_dataset[...] == self.testData.view(numpy.ndarray)[...])).all()
        assert (numpy.all(n5_dataset[...] == self.testData.view(numpy.ndarray)[...])).all()
        hdf5File.close()
        n5File.close()


class TestOpH5N5WriterBigDataset_3(object):
    def setup_method(self, method):
        self.graph = lazyflow.graph.Graph()
        self.testDataH5FileName = "bigH5TestData.h5"
        self.testDataN5FileName = "bigH5TestData.n5"

        self.datasetInternalPath = "volume/data"

        # Generate some test data
        self.dataShape = (1, 10, 128, 128, 1)
        self.testData = vigra.VigraArray(
            self.dataShape, axistags=vigra.defaultAxistags("txyzc")
        )  # default vigra order this time...
        self.testData[...] = numpy.indices(self.dataShape).sum(0)

    def teardown_method(self, method):
        # Clean up: Delete the test file.
        try:
            os.remove(self.testDataH5FileName)
            rmtree(self.testDataN5FileName)
        except:
            pass

    def test_Writer(self):
        # Create the h5 file
        hdf5File = h5py.File(self.testDataH5FileName)
        n5File = z5py.N5File(self.testDataN5FileName)

        opPiper = OpArrayPiper(graph=self.graph)
        opPiper.Input.setValue(self.testData)

        # Force extra metadata onto the output
        opPiper.Output.meta.ideal_blockshape = (1, 1, 0, 0, 1)
        # Pretend the RAM usage will be really high to force lots of tiny blocks
        opPiper.Output.meta.ram_usage_per_requested_pixel = 1000000.0

        h5_opWriter = OpH5N5WriterBigDataset(graph=self.graph)
        n5_opWriter = OpH5N5WriterBigDataset(graph=self.graph)

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
        hdf5File = h5py.File(self.testDataH5FileName, "r")
        n5File = h5py.File(self.testDataH5FileName, "r")
        h5_dataset = hdf5File[self.datasetInternalPath]
        n5_dataset = n5File[self.datasetInternalPath]
        assert h5_dataset.shape == self.dataShape
        assert n5_dataset.shape == self.dataShape
        assert (numpy.all(h5_dataset[...] == self.testData.view(numpy.ndarray)[...])).all()
        assert (numpy.all(n5_dataset[...] == self.testData.view(numpy.ndarray)[...])).all()
        hdf5File.close()
        n5File.close()
