import unittest
import tempfile
import os

import h5py
import z5py
import numpy

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpStreamingH5N5SequenceReaderM
import vigra


class TestOpStreamingH5N5SequenceReaderM(unittest.TestCase):
    def setup_method(self, method):
        self.graph = Graph()

    def test_2d_vigra_along_z(self):
        """Test if 2d files generated through vigra are recognized correctly"""
        # Prepare some data set for this case
        data = numpy.random.randint(0, 255, (20, 100, 200, 3)).astype(numpy.uint8)
        axistags = vigra.defaultAxistags("yxc")
        expected_axistags = vigra.defaultAxistags("zyxc")

        h5_op = OpStreamingH5N5SequenceReaderM(graph=self.graph)
        n5_op = OpStreamingH5N5SequenceReaderM(graph=self.graph)

        tempdir = tempfile.TemporaryDirectory()
        try:
            for sliceIndex, zSlice in enumerate(data):
                testDataH5FileName = f"{tempdir.name}/test-{sliceIndex:02d}.h5"
                testDataN5FileName = f"{tempdir.name}/test-{sliceIndex:02d}.n5"
                # Write the dataset to an hdf5 and a n5 file
                # (Note: Don't use vigra to do this, which may reorder the axes)
                h5File = h5py.File(testDataH5FileName)
                n5File = z5py.N5File(testDataN5FileName)
                try:
                    h5File.create_group("volume")
                    n5File.create_group("volume")

                    h5File["volume"].create_dataset("subvolume", data=zSlice)
                    n5File["volume"].create_dataset("subvolume", data=zSlice)
                    # Write the axistags attribute
                    current_path = "volume/subvolume"
                    h5File[current_path].attrs["axistags"] = axistags.toJSON()
                    n5File[current_path].attrs["axistags"] = axistags.toJSON()
                finally:
                    h5File.close()
                    n5File.close()

            # Read the data with an operator
            hdf5GlobString = f"{tempdir.name}/test-*.h5/volume/subvolume"
            n5GlobString = f"{tempdir.name}/test-*.n5/volume/subvolume"
            h5_op.SequenceAxis.setValue("z")
            n5_op.SequenceAxis.setValue("z")
            h5_op.GlobString.setValue(hdf5GlobString)
            n5_op.GlobString.setValue(n5GlobString)

            assert h5_op.OutputImage.ready()
            assert n5_op.OutputImage.ready()
            assert h5_op.OutputImage.meta.axistags == expected_axistags
            assert n5_op.OutputImage.meta.axistags == expected_axistags
            numpy.testing.assert_array_equal(
                h5_op.OutputImage.value[5:10, 50:100, 100:150], data[5:10, 50:100, 100:150]
            )
            numpy.testing.assert_array_equal(
                n5_op.OutputImage.value[5:10, 50:100, 100:150], data[5:10, 50:100, 100:150]
            )
        finally:
            h5_op.cleanUp()
            n5_op.cleanUp()

    def test_2d_vigra_along_t(self):
        """Test if 2d files generated through vigra are recognized correctly"""
        # Prepare some data set for this case
        data = numpy.random.randint(0, 255, (20, 100, 200, 3)).astype(numpy.uint8)
        axistags = vigra.defaultAxistags("yxc")
        expected_axistags = vigra.defaultAxistags("tyxc")

        h5_op = OpStreamingH5N5SequenceReaderM(graph=self.graph)
        n5_op = OpStreamingH5N5SequenceReaderM(graph=self.graph)

        tempdir = tempfile.TemporaryDirectory()
        try:
            for sliceIndex, tSlice in enumerate(data):
                testDataH5FileName = f"{tempdir.name}/test-{sliceIndex:02d}.h5"
                testDataN5FileName = f"{tempdir.name}/test-{sliceIndex:02d}.n5"
                # Write the dataset to an hdf5 and a n5 file
                # (Note: Don't use vigra to do this, which may reorder the axes)
                h5File = h5py.File(testDataH5FileName)
                n5File = z5py.N5File(testDataN5FileName)
                try:
                    h5File.create_group("volume")
                    n5File.create_group("volume")

                    h5File["volume"].create_dataset("subvolume", data=tSlice)
                    n5File["volume"].create_dataset("subvolume", data=tSlice)
                    # Write the axistags attribute
                    current_path = "volume/subvolume"
                    h5File[current_path].attrs["axistags"] = axistags.toJSON()
                    n5File[current_path].attrs["axistags"] = axistags.toJSON()
                finally:
                    h5File.close()
                    n5File.close()

            # Read the data with an operator
            hdf5GlobString = f"{tempdir.name}/test-*.h5/volume/subvolume"
            n5GlobString = f"{tempdir.name}/test-*.n5/volume/subvolume"
            h5_op.SequenceAxis.setValue("t")
            n5_op.SequenceAxis.setValue("t")
            h5_op.GlobString.setValue(hdf5GlobString)
            n5_op.GlobString.setValue(n5GlobString)

            assert h5_op.OutputImage.ready()
            assert n5_op.OutputImage.ready()
            assert h5_op.OutputImage.meta.axistags == expected_axistags
            assert n5_op.OutputImage.meta.axistags == expected_axistags
            numpy.testing.assert_array_equal(h5_op.OutputImage.value, data)
            numpy.testing.assert_array_equal(n5_op.OutputImage.value, data)
        finally:
            h5_op.cleanUp()
            n5_op.cleanUp()

    def test_3d_vigra_along_t(self):
        """Test if 3d volumes generated through vigra are recognized correctly"""
        # Prepare some data set for this case
        data = numpy.random.randint(0, 255, (10, 15, 50, 100, 3)).astype(numpy.uint8)

        axistags = vigra.defaultAxistags("zyxc")
        expected_axistags = vigra.defaultAxistags("tzyxc")

        h5_op = OpStreamingH5N5SequenceReaderM(graph=self.graph)
        n5_op = OpStreamingH5N5SequenceReaderM(graph=self.graph)

        tempdir = tempfile.TemporaryDirectory()
        try:
            for sliceIndex, tSlice in enumerate(data):
                testDataH5FileName = f"{tempdir.name}/test-{sliceIndex:02d}.h5"
                testDataN5FileName = f"{tempdir.name}/test-{sliceIndex:02d}.n5"
                # Write the dataset to an hdf5 file
                # (Note: Don't use vigra to do this, which may reorder the axes)
                h5File = h5py.File(testDataH5FileName)
                n5File = z5py.N5File(testDataN5FileName)
                try:
                    h5File.create_group("volume")
                    n5File.create_group("volume")

                    h5File["volume"].create_dataset("subvolume", data=tSlice)
                    n5File["volume"].create_dataset("subvolume", data=tSlice)
                    # Write the axistags attribute
                    current_path = "volume/subvolume"
                    h5File[current_path].attrs["axistags"] = axistags.toJSON()
                    n5File[current_path].attrs["axistags"] = axistags.toJSON()
                finally:
                    h5File.close()
                    n5File.close()

            # Read the data with an operator
            hdf5GlobString = f"{tempdir.name}/test-*.h5/volume/subvolume"
            n5GlobString = f"{tempdir.name}/test-*.n5/volume/subvolume"
            h5_op.SequenceAxis.setValue("t")
            n5_op.SequenceAxis.setValue("t")
            h5_op.GlobString.setValue(hdf5GlobString)
            n5_op.GlobString.setValue(n5GlobString)

            assert h5_op.OutputImage.ready()
            assert n5_op.OutputImage.ready()
            assert h5_op.OutputImage.meta.axistags == expected_axistags
            assert n5_op.OutputImage.meta.axistags == expected_axistags
            numpy.testing.assert_array_equal(h5_op.OutputImage.value, data)
            numpy.testing.assert_array_equal(n5_op.OutputImage.value, data)
        finally:
            h5_op.cleanUp()
            n5_op.cleanUp()

    def test_globStringValidity(self):
        """Check whether globStrings are correctly verified"""
        testGlobString = "/tmp/test.h5/somedata"
        with self.assertRaises(OpStreamingH5N5SequenceReaderM.NoExternalPlaceholderError):
            OpStreamingH5N5SequenceReaderM.checkGlobString(testGlobString)

        testGlobString = "/tmp/test.n5/somedata"
        with self.assertRaises(OpStreamingH5N5SequenceReaderM.NoExternalPlaceholderError):
            OpStreamingH5N5SequenceReaderM.checkGlobString(testGlobString)

        testGlobString = "/tmp/test.jpg/*"
        with self.assertRaises(OpStreamingH5N5SequenceReaderM.WrongFileTypeError):
            OpStreamingH5N5SequenceReaderM.checkGlobString(testGlobString)

        testGlobString = "/tmp/test.h5/data" + os.pathsep + "/tmp/test.h5/data2"
        with self.assertRaises(OpStreamingH5N5SequenceReaderM.SameFileError):
            OpStreamingH5N5SequenceReaderM.checkGlobString(testGlobString)

        testGlobString = "/tmp/test.n5/data" + os.pathsep + "/tmp/test.n5/data2"
        with self.assertRaises(OpStreamingH5N5SequenceReaderM.SameFileError):
            OpStreamingH5N5SequenceReaderM.checkGlobString(testGlobString)

        testGlobString = "/tmp/test-*.h5/data*"
        with self.assertRaises(OpStreamingH5N5SequenceReaderM.InternalPlaceholderError):
            OpStreamingH5N5SequenceReaderM.checkGlobString(testGlobString)

        testGlobString = "/tmp/test-*.n5/data*"
        with self.assertRaises(OpStreamingH5N5SequenceReaderM.InternalPlaceholderError):
            OpStreamingH5N5SequenceReaderM.checkGlobString(testGlobString)

        testGlobString = "/tmp/test-0.h5/data" + os.pathsep + "/tmp/test-1.h5/data*"
        with self.assertRaises(OpStreamingH5N5SequenceReaderM.InternalPlaceholderError):
            OpStreamingH5N5SequenceReaderM.checkGlobString(testGlobString)

        testGlobString = "/tmp/test-0.n5/data" + os.pathsep + "/tmp/test-1.n5/data*"
        with self.assertRaises(OpStreamingH5N5SequenceReaderM.InternalPlaceholderError):
            OpStreamingH5N5SequenceReaderM.checkGlobString(testGlobString)

        validGlobStrings = [
            "/tmp/test-*.h5/data",
            "/tmp/test-1.h5/data1" + os.pathsep + "/tmp/test-2.h5/data1",
            "/tmp/test-*.n5/data",
            "/tmp/test-1.n5/data1" + os.pathsep + "/tmp/test-2.n5/data1",
        ]

        for testGlobString in validGlobStrings:
            OpStreamingH5N5SequenceReaderM.checkGlobString(testGlobString)
        # Implicit test for validity; test fails if an exception is raised
        self.assertTrue(True)
