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
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpStreamingH5N5Reader
import numpy
import vigra
import tempfile


class TestOpStreamingH5N5Reader(object):
    def setup_method(self, method):
        self.graph = Graph()
        self.testFileDir = tempfile.TemporaryDirectory()
        self.testDataH5FileName = self.testFileDir.name + "test.h5"
        self.testDataN5FileName = self.testFileDir.name + "test.n5"
        self.h5_op = OpStreamingH5N5Reader(graph=self.graph)
        self.n5_op = OpStreamingH5N5Reader(graph=self.graph)

        self.h5File = OpStreamingH5N5Reader.get_h5_n5_file(self.testDataH5FileName)
        self.n5File = OpStreamingH5N5Reader.get_h5_n5_file(self.testDataN5FileName)
        self.h5File.create_group("volume")
        self.n5File.create_group("volume")

        # Create a test dataset
        datashape = (1, 2, 3, 4, 5)
        self.data = numpy.indices(datashape).sum(0).astype(numpy.float32)

    def teardown_method(self, method):
        self.h5File.close()
        self.n5File.close()
        self.testFileDir.cleanup()

    def test_plain(self):
        # Write the dataset to an hdf5 file
        self.h5File["volume"].create_dataset("data", data=self.data)
        self.n5File["volume"].create_dataset("data", data=self.data)

        # Read the data with an operator
        self.h5_op.H5N5File.setValue(self.h5File)
        self.n5_op.H5N5File.setValue(self.n5File)
        self.h5_op.InternalPath.setValue("volume/data")
        self.n5_op.InternalPath.setValue("volume/data")

        assert self.h5_op.OutputImage.meta.shape == self.data.shape
        assert self.n5_op.OutputImage.meta.shape == self.data.shape
        numpy.testing.assert_array_equal(self.h5_op.OutputImage.value, self.data)
        numpy.testing.assert_array_equal(self.n5_op.OutputImage.value, self.data)

    def test_withAxisTags(self):
        # Write it again, this time with weird axistags
        axistags = vigra.AxisTags(
            vigra.AxisInfo("x", vigra.AxisType.Space),
            vigra.AxisInfo("y", vigra.AxisType.Space),
            vigra.AxisInfo("z", vigra.AxisType.Space),
            vigra.AxisInfo("c", vigra.AxisType.Channels),
            vigra.AxisInfo("t", vigra.AxisType.Time),
        )

        # Write the dataset to an hdf5 file
        # (Note: Don't use vigra to do this, which may reorder the axes)
        self.h5File["volume"].create_dataset("tagged_data", data=self.data)
        self.n5File["volume"].create_dataset("tagged_data", data=self.data)
        # Write the axistags attribute
        self.h5File["volume/tagged_data"].attrs["axistags"] = axistags.toJSON()
        self.n5File["volume/tagged_data"].attrs["axistags"] = axistags.toJSON()

        # Read the data with an operator
        self.h5_op.H5N5File.setValue(self.h5File)
        self.n5_op.H5N5File.setValue(self.n5File)
        self.h5_op.InternalPath.setValue("volume/tagged_data")
        self.n5_op.InternalPath.setValue("volume/tagged_data")

        assert self.h5_op.OutputImage.meta.shape == self.data.shape
        assert self.n5_op.OutputImage.meta.shape == self.data.shape
        numpy.testing.assert_array_equal(self.h5_op.OutputImage.value, self.data)
        numpy.testing.assert_array_equal(self.n5_op.OutputImage.value, self.data)
