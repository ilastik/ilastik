import unittest
import tempfile
import os
import pathlib

import h5py
import z5py
import numpy

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpStreamingH5N5SequenceReaderS
from ilastik.utility.data_url import Dataset
import vigra


class TestOpStreamingH5N5SequenceReaderS(unittest.TestCase):
    def setup_method(self, method):
        self.graph = Graph()
        self.tempdir = tempfile.TemporaryDirectory()
        # necessary to ensure forward-slashes on windows, which are assumed in our code
        self.tempdir_normalized_name = pathlib.Path(self.tempdir.name).as_posix()

    def test_2d_vigra_along_z(self):
        """Test if 2d files generated through vigra are recognized correctly"""
        # Prepare some data set for this case
        data = numpy.random.randint(0, 255, (20, 100, 200, 3)).astype(numpy.uint8)
        axistags = vigra.defaultAxistags("yxc")
        expected_axistags = vigra.defaultAxistags("zyxc")

        h5_op = OpStreamingH5N5SequenceReaderS(graph=self.graph)
        n5_op = OpStreamingH5N5SequenceReaderS(graph=self.graph)

        try:
            testDataH5FileName = f"{self.tempdir_normalized_name}/test.h5"
            testDataN5FileName = f"{self.tempdir_normalized_name}/test.n5"
            # Write the dataset to an hdf5 and a n5 file
            # (Note: Don't use vigra to do this, which may reorder the axes)
            h5File = h5py.File(testDataH5FileName, "w")
            n5File = z5py.N5File(testDataN5FileName, "w")
            try:
                h5File.create_group("volumes")
                n5File.create_group("volumes")

                internalPathString = "subvolume-{sliceIndex:02d}"
                for sliceIndex, zSlice in enumerate(data):
                    subpath = internalPathString.format(sliceIndex=sliceIndex)
                    h5File["volumes"].create_dataset(subpath, data=zSlice)
                    n5File["volumes"].create_dataset(subpath, data=zSlice)
                    # Write the axistags attribute
                    current_path = "volumes/{}".format(subpath)
                    h5File[current_path].attrs["axistags"] = axistags.toJSON()
                    n5File[current_path].attrs["axistags"] = axistags.toJSON()
            finally:
                h5File.close()
                n5File.close()

            # Read the data with an operator
            hdf5GlobString = f"{testDataH5FileName}/volumes/subvolume-*"
            n5GlobString = f"{testDataN5FileName}/volumes/subvolume-*"
            h5_op.SequenceAxis.setValue("z")
            n5_op.SequenceAxis.setValue("z")
            h5_op.ArchiveDataPaths.setValue(Dataset.from_string(hdf5GlobString, deglob=True).data_paths)
            n5_op.ArchiveDataPaths.setValue(Dataset.from_string(n5GlobString, deglob=True).data_paths)

            assert h5_op.OutputImage.ready()
            assert n5_op.OutputImage.ready()
            assert h5_op.OutputImage.meta.axistags == expected_axistags
            assert n5_op.OutputImage.meta.axistags == expected_axistags
            numpy.testing.assert_array_equal(h5_op.OutputImage.value, data)
            numpy.testing.assert_array_equal(n5_op.OutputImage.value, data)
        finally:
            h5_op.cleanUp()
            n5_op.cleanUp()

    def test_2d_vigra_along_t(self):
        """Test if 2d files generated through vigra are recognized correctly"""
        # Prepare some data set for this case
        data = numpy.random.randint(0, 255, (20, 100, 200, 3)).astype(numpy.uint8)
        axistags = vigra.defaultAxistags("yxc")

        expected_axistags = vigra.defaultAxistags("tyxc")

        h5_op = OpStreamingH5N5SequenceReaderS(graph=self.graph)
        n5_op = OpStreamingH5N5SequenceReaderS(graph=self.graph)

        try:
            testDataH5FileName = f"{self.tempdir_normalized_name}/test.h5"
            testDataN5FileName = f"{self.tempdir_normalized_name}/test.n5"
            # Write the dataset to an hdf5 and a n5 file
            # (Note: Don't use vigra to do this, which may reorder the axes)
            h5File = h5py.File(testDataH5FileName, "w")
            n5File = z5py.N5File(testDataN5FileName, "w")
            try:
                h5File.create_group("volumes")
                n5File.create_group("volumes")

                internalPathString = "subvolume-{sliceIndex:02d}"
                for sliceIndex, zSlice in enumerate(data):
                    subpath = internalPathString.format(sliceIndex=sliceIndex)
                    h5File["volumes"].create_dataset(subpath, data=zSlice)
                    n5File["volumes"].create_dataset(subpath, data=zSlice)
                    # Write the axistags attribute
                    current_path = "volumes/{}".format(subpath)
                    h5File[current_path].attrs["axistags"] = axistags.toJSON()
                    n5File[current_path].attrs["axistags"] = axistags.toJSON()
            finally:
                h5File.close()
                n5File.close()

            # Read the data with an operator
            hdf5GlobString = f"{testDataH5FileName}/volumes/subvolume-*"
            n5GlobString = f"{testDataN5FileName}/volumes/subvolume-*"
            h5_op.SequenceAxis.setValue("t")
            n5_op.SequenceAxis.setValue("t")
            h5_op.ArchiveDataPaths.setValue(Dataset.from_string(hdf5GlobString, deglob=True).data_paths)
            n5_op.ArchiveDataPaths.setValue(Dataset.from_string(n5GlobString, deglob=True).data_paths)

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

        h5_op = OpStreamingH5N5SequenceReaderS(graph=self.graph)
        n5_op = OpStreamingH5N5SequenceReaderS(graph=self.graph)

        try:
            testDataH5FileName = f"{self.tempdir_normalized_name}/test.h5"
            testDataN5FileName = f"{self.tempdir_normalized_name}/test.n5"
            # Write the dataset to an hdf5 file
            # (Note: Don't use vigra to do this, which may reorder the axes)
            h5File = h5py.File(testDataH5FileName, "w")
            n5File = z5py.N5File(testDataN5FileName, "w")

            try:
                h5File.create_group("volumes")
                n5File.create_group("volumes")

                internalPathString = "subvolume-{sliceIndex:02d}"
                for sliceIndex, tSlice in enumerate(data):
                    subpath = internalPathString.format(sliceIndex=sliceIndex)
                    h5File["volumes"].create_dataset(subpath, data=tSlice)
                    n5File["volumes"].create_dataset(subpath, data=tSlice)
                    # Write the axistags attribute
                    current_path = "volumes/{}".format(subpath)
                    h5File[current_path].attrs["axistags"] = axistags.toJSON()
                    n5File[current_path].attrs["axistags"] = axistags.toJSON()
            finally:
                h5File.close()
                n5File.close()

            # Read the data with an operator
            hdf5GlobString = f"{testDataH5FileName}/volumes/subvolume-*"
            n5GlobString = f"{testDataN5FileName}/volumes/subvolume-*"
            h5_op.SequenceAxis.setValue("t")
            n5_op.SequenceAxis.setValue("t")
            h5_op.ArchiveDataPaths.setValue(Dataset.from_string(hdf5GlobString, deglob=True).data_paths)
            n5_op.ArchiveDataPaths.setValue(Dataset.from_string(n5GlobString, deglob=True).data_paths)

            assert h5_op.OutputImage.ready()
            assert n5_op.OutputImage.ready()
            assert h5_op.OutputImage.meta.axistags == expected_axistags
            assert n5_op.OutputImage.meta.axistags == expected_axistags
            numpy.testing.assert_array_equal(h5_op.OutputImage.value, data)
            numpy.testing.assert_array_equal(n5_op.OutputImage.value, data)
        finally:
            h5_op.cleanUp()
            n5_op.cleanUp()
