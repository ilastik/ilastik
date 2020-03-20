from builtins import range
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
from lazyflow.operators.ioOperators import OpInputDataReader
import os
import numpy
import vigra
import lazyflow.graph
import tempfile
import shutil
import h5py
import pytest

from PIL import Image


class TestOpInputDataReader(object):
    def setup_method(self, method):
        self.graph = lazyflow.graph.Graph()
        tmpDir = tempfile.mkdtemp()
        self.testNpyDataFileName = tmpDir + "/test.npy"
        self.testNpzDataFileName = tmpDir + "/test.npz"
        self.testImageFileName = tmpDir + "/test.png"
        self.testmultiImageFileName = tmpDir + "/test-{index:02d}.png"
        self.testH5FileName = tmpDir + "/test.h5"
        self.testmultiH5FileName = tmpDir + "/test-{index:02d}.h5"
        self.testmultiTiffFileName = tmpDir + "/test-{index:02d}.tiff"
        self.tmpDir = tmpDir

    def teardown_method(self, method):
        # Clean up: Delete the test data files.
        shutil.rmtree(self.tmpDir)

    def test_npy(self):
        # Create Numpy test data
        a = numpy.zeros((10, 11))
        for x in range(0, 10):
            for y in range(0, 11):
                a[x, y] = x + y
        numpy.save(self.testNpyDataFileName, a)

        # Now read back our test data using an OpInputDataReader operator
        npyReader = OpInputDataReader(graph=self.graph)
        try:
            npyReader.FilePath.setValue(self.testNpyDataFileName)
            cwd = os.path.split(__file__)[0]
            npyReader.WorkingDirectory.setValue(cwd)

            # Read the entire NPY file and verify the contents
            npyData = npyReader.Output[:].wait()
            assert npyData.shape == (10, 11)
            for x in range(0, 10):
                for y in range(0, 11):
                    assert npyData[x, y] == x + y
        finally:
            npyReader.cleanUp()

    def test_npz(self):
        # Create two Numpy test arrays
        a = numpy.zeros((10, 11))
        for x in range(0, 10):
            for y in range(0, 11):
                a[x, y] = x + y

        b = numpy.arange((3 * 9)).reshape((3, 9))
        numpy.savez(self.testNpzDataFileName, a=a, b=b)

        # Now read back our test data using an OpInputDataReader operator
        npyReader = OpInputDataReader(graph=self.graph)

        try:
            for internalPath, referenceArray in zip(["a", "b"], [a, b]):
                npyReader.FilePath.setValue("{}/{}".format(self.testNpzDataFileName, internalPath))
                cwd = os.path.split(__file__)[0]
                npyReader.WorkingDirectory.setValue(cwd)

                npzData = npyReader.Output[:].wait()
                assert npzData.shape == referenceArray.shape
                numpy.testing.assert_array_equal(npzData, referenceArray)
        finally:
            npyReader.cleanUp()

    def test_png(self):
        # Create PNG test data
        a = numpy.zeros((100, 200))
        for x in range(a.shape[0]):
            for y in range(a.shape[1]):
                a[x, y] = (x + y) % 256
        vigra.impex.writeImage(a, self.testImageFileName)

        # Read the entire PNG file and verify the contents
        pngReader = OpInputDataReader(graph=self.graph)
        pngReader.FilePath.setValue(self.testImageFileName)
        cwd = os.path.split(__file__)[0]
        pngReader.WorkingDirectory.setValue(cwd)
        pngData = pngReader.Output[:].wait()
        for x in range(pngData.shape[0]):
            for y in range(pngData.shape[1]):
                assert pngData[x, y, 0] == (x + y) % 256

    @pytest.mark.parametrize("sequence_axis", ["t", "z", "c"])
    def test_multi_png(self, sequence_axis):

        # Create PNG test data
        data = numpy.random.randint(0, 255, size=(5, 100, 200)).astype(numpy.uint8)
        for idx, dat in enumerate(data):
            vigra.impex.writeImage(dat.T, self.testmultiImageFileName.format(index=idx))

        # Read the entire PNG file and verify the contents
        pngReader = OpInputDataReader(graph=self.graph)
        pngReader.SequenceAxis.setValue(sequence_axis)
        globString = self.testmultiImageFileName.replace("02d}", "s}").format(index="*")
        pngReader.FilePath.setValue(globString)
        cwd = os.path.split(__file__)[0]
        pngReader.WorkingDirectory.setValue(cwd)
        pngData = pngReader.Output[:].wait().squeeze()
        if sequence_axis == "c":
            data = data.T

        assert pngData.shape == data.shape, f"{pngData.shape}, {data.shape}"
        numpy.testing.assert_array_equal(pngData, data)

    def test_h5(self):
        # Create HDF5 test data
        with h5py.File(self.testH5FileName) as f:
            f.create_group("volume")
            shape = (1, 2, 3, 4, 5)
            f["volume"].create_dataset(
                "data", data=numpy.indices(shape).sum(0).astype(numpy.float32), chunks=True, compression="gzip"
            )

        # Read the entire HDF5 file and verify the contents
        h5Reader = OpInputDataReader(graph=self.graph)
        try:
            h5Reader.FilePath.setValue(self.testH5FileName + "/volume/data")  # Append internal path
            cwd = os.path.split(__file__)[0]
            h5Reader.WorkingDirectory.setValue(cwd)

            # Grab a section of the h5 data
            h5Data = h5Reader.Output[0, 0, :, :, :].wait()
            assert h5Data.shape == (1, 1, 3, 4, 5)
            # (Just check part of the data)
            for k in range(0, shape[2]):
                for l in range(0, shape[3]):
                    for m in range(0, shape[4]):
                        assert h5Data[0, 0, k, l, m] == k + l + m

        finally:
            # Call cleanUp() to close the file that this operator opened
            h5Reader.cleanUp()
            assert not h5Reader._file  # Whitebox assertion...

    @pytest.mark.parametrize("sequence_axis", ["t", "z", "c"])
    def test_h5_stack_single_file(self, sequence_axis):
        """Test stack/sequence reading in hdf5-files for given 'sequence_axis'"""
        shape = (4, 8, 16, 32, 3)  # assuming axis guess order is 'tzyxc'
        data = numpy.random.randint(0, 255, size=shape).astype(numpy.uint8)
        with h5py.File(self.testH5FileName) as f:
            data_group = f.create_group("volumes")
            for index, t_slice in enumerate(data):
                data_group.create_dataset("timepoint-{index:02d}".format(index=index), data=t_slice)

        if sequence_axis == "z":
            data = numpy.concatenate(data, axis=0)
        elif sequence_axis == "c":
            data = numpy.concatenate(data, axis=-1)

        h5SequenceReader = OpInputDataReader(graph=self.graph)
        h5SequenceReader.SequenceAxis.setValue(sequence_axis)
        filenamePlusGlob = "{}/volumes/timepoint-*".format(self.testH5FileName)
        try:
            h5SequenceReader.FilePath.setValue(filenamePlusGlob)

            h5data = h5SequenceReader.Output[:].wait()
            assert h5data.shape == data.shape, f"{h5data.shape}, {data.shape}"
            numpy.testing.assert_array_equal(h5data, data)
        finally:
            # Call cleanUp() to close the file that this operator opened
            h5SequenceReader.cleanUp()

    @pytest.mark.parametrize("sequence_axis", ["t", "z", "c"])
    def test_h5_stack_multi_file(self, sequence_axis):
        """Test stack/sequence reading in hdf5-files"""
        shape = (4, 8, 16, 32, 3)
        data = numpy.random.randint(0, 255, size=shape).astype(numpy.uint8)
        for index, t_slice in enumerate(data):
            fname = self.testmultiH5FileName.format(index=index)
            with h5py.File(fname) as f:
                data_group = f.create_group("volume")
                data_group.create_dataset("data", data=t_slice)

        if sequence_axis == "z":
            data = numpy.concatenate(data, axis=0)
        elif sequence_axis == "c":
            data = numpy.concatenate(data, axis=-1)

        h5SequenceReader = OpInputDataReader(graph=self.graph)
        h5SequenceReader.SequenceAxis.setValue(sequence_axis)
        globString = self.testmultiH5FileName.replace("02d}", "s}").format(index="*")
        filenamePlusGlob = "{}/volume/data".format(globString)
        try:
            h5SequenceReader.FilePath.setValue(filenamePlusGlob)
            h5data = h5SequenceReader.Output[:].wait()
            assert h5data.shape == data.shape
            numpy.testing.assert_array_equal(h5data, data)
        finally:
            # Call cleanUp() to close the file that this operator opened
            h5SequenceReader.cleanUp()

    @pytest.mark.parametrize("sequence_axis", ["t", "z", "c"])
    def test_tiff_stack_multi_file(self, sequence_axis):
        """Test stack/sequence reading in hdf5-files"""
        shape = (4, 8, 16, 3)
        data = numpy.random.randint(0, 255, size=shape).astype(numpy.uint8)
        for idx, data_slice in enumerate(data):
            im = Image.fromarray(data_slice, mode="RGB")
            im.save(self.testmultiTiffFileName.format(index=idx))

        if sequence_axis == "c":
            data = numpy.concatenate(data, axis=-1)

        reader = OpInputDataReader(graph=self.graph)
        reader.SequenceAxis.setValue(sequence_axis)
        globString = self.testmultiTiffFileName.replace("02d}", "s}").format(index="*")
        try:
            reader.FilePath.setValue(globString)
            tiffdata = reader.Output[:].wait()

            assert tiffdata.shape == data.shape, f"{tiffdata.shape}, {data.shape}"
            numpy.testing.assert_array_equal(tiffdata, data)
        finally:
            # Call cleanUp() to close the file that this operator opened
            reader.cleanUp()

    def test_npy_with_roi(self):
        a = numpy.indices((100, 100, 200)).astype(numpy.uint8).sum(0)
        assert a.shape == (100, 100, 200)
        numpy.save(self.testNpyDataFileName, a)
        opReader = OpInputDataReader(graph=lazyflow.graph.Graph())
        try:
            opReader.FilePath.setValue(self.testNpyDataFileName)
            opReader.SubVolumeRoi.setValue(((10, 20, 30), (50, 70, 90)))

            all_data = opReader.Output[:].wait()
            assert all_data.shape == (40, 50, 60)
            assert (all_data == a[10:50, 20:70, 30:90]).all()
        finally:
            opReader.cleanUp()


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
