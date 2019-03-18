import unittest
import contextlib
import tempfile
import shutil
import os

import h5py
import numpy

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpStreamingHdf5SequenceReaderM
import vigra


@contextlib.contextmanager
def tempdir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


class TestOpStreamingHdf5SequenceReader(unittest.TestCase):

    def setup_method(self, method):
        self.graph = Graph()

    def test_2d_vigra_along_z(self):
        """Test if 2d files generated through vigra are recognized correctly"""
        # Prepare some data set for this case
        data = numpy.random.randint(0, 255, (20, 100, 200, 3)).astype(numpy.uint8)
        axistags = vigra.defaultAxistags('yxc')
        expected_axistags = vigra.defaultAxistags('zyxc')

        op = OpStreamingHdf5SequenceReaderM(graph=self.graph)

        with tempdir() as d:
            try:
                for sliceIndex, zSlice in enumerate(data):
                    testDataFileName = '{path}/test-{index:02d}.h5'.format(path=d, index=sliceIndex)
                    # Write the dataset to an hdf5 file
                    # (Note: Don't use vigra to do this, which may reorder the axes)
                    h5File = h5py.File(testDataFileName)
                    try:
                        h5File.create_group('volume')

                        h5File['volume'].create_dataset("subvolume", data=zSlice)
                        # Write the axistags attribute
                        current_path = 'volume/subvolume'
                        h5File[current_path].attrs['axistags'] = axistags.toJSON()
                    finally:
                        h5File.close()

                # Read the data with an operator
                hdf5GlobString = "{path}/test-*.h5/volume/subvolume".format(path=d)
                op.SequenceAxis.setValue('z')
                op.GlobString.setValue(hdf5GlobString)

                assert op.OutputImage.ready()
                assert op.OutputImage.meta.axistags == expected_axistags
                numpy.testing.assert_array_equal(
                    op.OutputImage[5:10, 50:100, 100:150].wait(), data[5:10, 50:100, 100:150]
                )
            finally:
                op.cleanUp()

    def test_2d_vigra_along_t(self):
        """Test if 2d files generated through vigra are recognized correctly"""
        # Prepare some data set for this case
        data = numpy.random.randint(0, 255, (20, 100, 200, 3)).astype(numpy.uint8)
        axistags = vigra.defaultAxistags('yxc')
        expected_axistags = vigra.defaultAxistags('tyxc')

        op = OpStreamingHdf5SequenceReaderM(graph=self.graph)

        with tempdir() as d:
            try:
                for sliceIndex, tSlice in enumerate(data):
                    testDataFileName = '{path}/test-{index:02d}.h5'.format(path=d, index=sliceIndex)
                    # Write the dataset to an hdf5 file
                    # (Note: Don't use vigra to do this, which may reorder the axes)
                    h5File = h5py.File(testDataFileName)
                    try:
                        h5File.create_group('volume')

                        h5File['volume'].create_dataset("subvolume", data=tSlice)
                        # Write the axistags attribute
                        current_path = 'volume/subvolume'
                        h5File[current_path].attrs['axistags'] = axistags.toJSON()
                    finally:
                        h5File.close()

                # Read the data with an operator
                hdf5GlobString = "{path}/test-*.h5/volume/subvolume".format(path=d)
                op.SequenceAxis.setValue('t')
                op.GlobString.setValue(hdf5GlobString)

                assert op.OutputImage.ready()
                assert op.OutputImage.meta.axistags == expected_axistags
                numpy.testing.assert_array_equal(
                    op.OutputImage[5:10, 50:100, 100:150].wait(), data[5:10, 50:100, 100:150]
                )
            finally:
                op.cleanUp()

    def test_3d_vigra_along_t(self):
        """Test if 3d volumes generated through vigra are recognized correctly"""
        # Prepare some data set for this case
        data = numpy.random.randint(0, 255, (10, 15, 50, 100, 3)).astype(numpy.uint8)

        axistags = vigra.defaultAxistags('zyxc')
        expected_axistags = vigra.defaultAxistags('tzyxc')

        op = OpStreamingHdf5SequenceReaderM(graph=self.graph)

        with tempdir() as d:
            try:
                for sliceIndex, tSlice in enumerate(data):
                    testDataFileName = '{path}/test-{index:02d}.h5'.format(path=d, index=sliceIndex)
                    # Write the dataset to an hdf5 file
                    # (Note: Don't use vigra to do this, which may reorder the axes)
                    h5File = h5py.File(testDataFileName)
                    try:
                        h5File.create_group('volume')

                        h5File['volume'].create_dataset("subvolume", data=tSlice)
                        # Write the axistags attribute
                        current_path = 'volume/subvolume'
                        h5File[current_path].attrs['axistags'] = axistags.toJSON()
                    finally:
                        h5File.close()

                # Read the data with an operator
                hdf5GlobString = "{path}/test-*.h5/volume/subvolume".format(path=d)
                op.SequenceAxis.setValue('t')
                op.GlobString.setValue(hdf5GlobString)

                assert op.OutputImage.ready()
                assert op.OutputImage.meta.axistags == expected_axistags
                numpy.testing.assert_array_equal(
                    op.OutputImage[0:2, 5:10, 20:50, 40:70].wait(), data[0:2, 5:10, 20:50, 40:70]
                )
            finally:
                op.cleanUp()

    def test_globStringValidity(self):
        """Check whether globStrings are correctly verified"""
        testGlobString = '/tmp/test.h5/somedata'
        with self.assertRaises(OpStreamingHdf5SequenceReaderM.NoExternalPlaceholderError):
            OpStreamingHdf5SequenceReaderM.checkGlobString(testGlobString)

        testGlobString = '/tmp/test.jpg/*'
        with self.assertRaises(OpStreamingHdf5SequenceReaderM.WrongFileTypeError):
            OpStreamingHdf5SequenceReaderM.checkGlobString(testGlobString)

        testGlobString = '/tmp/test.h5/data'+os.pathsep+'/tmp/test.h5/data2'
        with self.assertRaises(OpStreamingHdf5SequenceReaderM.SameFileError):
            OpStreamingHdf5SequenceReaderM.checkGlobString(testGlobString)

        testGlobString = '/tmp/test-*.h5/data*'
        with self.assertRaises(OpStreamingHdf5SequenceReaderM.InternalPlaceholderError):
            OpStreamingHdf5SequenceReaderM.checkGlobString(testGlobString)

        testGlobString = '/tmp/test-0.h5/data'+os.pathsep+'/tmp/test-1.h5/data*'
        with self.assertRaises(OpStreamingHdf5SequenceReaderM.InternalPlaceholderError):
            OpStreamingHdf5SequenceReaderM.checkGlobString(testGlobString)

        validGlobStrings = [
            '/tmp/test-*.h5/data',
            '/tmp/test-1.h5/data1'+os.pathsep+'/tmp/test-2.h5/data1',
        ]

        for testGlobString in validGlobStrings:
             OpStreamingHdf5SequenceReaderM.checkGlobString(testGlobString)
        # Implicit test for validity; test fails if an exception is raised
        self.assertTrue(True)


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
