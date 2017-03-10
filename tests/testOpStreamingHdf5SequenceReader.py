import contextlib
import tempfile
import shutil

import h5py
import numpy

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpStreamingHdf5SequenceReader
import vigra


@contextlib.contextmanager
def tempdir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


class TestOpStreamingHdf5SequenceReader(object):

    def setUp(self):
        self.graph = Graph()

    def test_2d_vigra_along_z(self):
        """Test if 2d files generated through vigra are recognized correctly"""
        # Prepare some data set for this case
        data = numpy.random.randint(0, 255, (20, 100, 200, 3)).astype(numpy.uint8)
        axistags = vigra.AxisTags([
            vigra.AxisInfo("y", typeFlags=vigra.AxisType.Space),
            vigra.AxisInfo("x", typeFlags=vigra.AxisType.Space),
            vigra.AxisInfo("c", typeFlags=vigra.AxisType.Channels)])

        expected_axistags = vigra.AxisTags([
            vigra.AxisInfo("z", typeFlags=vigra.AxisType.Space),
            vigra.AxisInfo("y", typeFlags=vigra.AxisType.Space),
            vigra.AxisInfo("x", typeFlags=vigra.AxisType.Space),
            vigra.AxisInfo("c", typeFlags=vigra.AxisType.Channels)])

        op = OpStreamingHdf5SequenceReader(graph=self.graph)

        with tempdir() as d:
            testDataFileName = '{}/test.h5'.format(d)
            # Write the dataset to an hdf5 file
            # (Note: Don't use vigra to do this, which may reorder the axes)
            h5File = h5py.File(testDataFileName)
            h5File.create_group('volumes')

            internalPathString = "subvolume-{sliceIndex:02d}"
            for sliceIndex, zSlice in enumerate(data):
                subpath = internalPathString.format(sliceIndex=sliceIndex)
                h5File['volumes'].create_dataset(subpath, data=zSlice)
                # Write the axistags attribute
                current_path = 'volumes/{}'.format(subpath)
                h5File[current_path].attrs['axistags'] = axistags.toJSON()

            h5File.close()

            h5File = h5py.File(testDataFileName, mode='r')
            # Read the data with an operator
            hdf5GlobString = "{}/volumes/subvolume-*".format(testDataFileName)
            op.SequenceAxis.setValue('z')
            op.GlobString.setValue(hdf5GlobString)
            op.Hdf5File.setValue(h5File)

            assert op.OutputImage.ready()
            assert op.OutputImage.meta.axistags == expected_axistags
            assert (op.OutputImage[5:10, 50:100, 100:150].wait() == data[5:10, 50:100, 100:150]).all()

    def test_2d_vigra_along_t(self):
        """Test if 2d files generated through vigra are recognized correctly"""
        # Prepare some data set for this case
        data = numpy.random.randint(0, 255, (20, 100, 200, 3)).astype(numpy.uint8)
        axistags = vigra.AxisTags([
            vigra.AxisInfo("y", typeFlags=vigra.AxisType.Space),
            vigra.AxisInfo("x", typeFlags=vigra.AxisType.Space),
            vigra.AxisInfo("c", typeFlags=vigra.AxisType.Channels)])

        expected_axistags = vigra.AxisTags([
            vigra.AxisInfo("t", typeFlags=vigra.AxisType.Time),
            vigra.AxisInfo("y", typeFlags=vigra.AxisType.Space),
            vigra.AxisInfo("x", typeFlags=vigra.AxisType.Space),
            vigra.AxisInfo("c", typeFlags=vigra.AxisType.Channels)])

        op = OpStreamingHdf5SequenceReader(graph=self.graph)

        with tempdir() as d:
            testDataFileName = '{}/test.h5'.format(d)
            # Write the dataset to an hdf5 file
            # (Note: Don't use vigra to do this, which may reorder the axes)
            h5File = h5py.File(testDataFileName)
            h5File.create_group('volumes')

            internalPathString = "subvolume-{sliceIndex:02d}"
            for sliceIndex, zSlice in enumerate(data):
                subpath = internalPathString.format(sliceIndex=sliceIndex)
                h5File['volumes'].create_dataset(subpath, data=zSlice)
                # Write the axistags attribute
                current_path = 'volumes/{}'.format(subpath)
                h5File[current_path].attrs['axistags'] = axistags.toJSON()

            # Read the data with an operator
            hdf5GlobString = "{}/volumes/subvolume-*".format(testDataFileName)
            op.SequenceAxis.setValue('t')
            op.GlobString.setValue(hdf5GlobString)
            op.Hdf5File.setValue(h5File)

            assert op.OutputImage.ready()
            assert op.OutputImage.meta.axistags == expected_axistags
            assert (op.OutputImage[5:10, 50:100, 100:150].wait() == data[5:10, 50:100, 100:150]).all()

    def test_3d_vigra_along_t(self):
        """Test if 3d volumes generated through vigra are recognized correctly"""
        # Prepare some data set for this case
        data = numpy.random.randint(0, 255, (10, 15, 50, 100, 3)).astype(numpy.uint8)

        axistags = vigra.AxisTags([
            vigra.AxisInfo("z", typeFlags=vigra.AxisType.Space),
            vigra.AxisInfo("y", typeFlags=vigra.AxisType.Space),
            vigra.AxisInfo("x", typeFlags=vigra.AxisType.Space),
            vigra.AxisInfo("c", typeFlags=vigra.AxisType.Channels)])

        expected_axistags = vigra.AxisTags([
            vigra.AxisInfo("t", typeFlags=vigra.AxisType.Time),
            vigra.AxisInfo("z", typeFlags=vigra.AxisType.Space),
            vigra.AxisInfo("y", typeFlags=vigra.AxisType.Space),
            vigra.AxisInfo("x", typeFlags=vigra.AxisType.Space),
            vigra.AxisInfo("c", typeFlags=vigra.AxisType.Channels)])

        op = OpStreamingHdf5SequenceReader(graph=self.graph)

        with tempdir() as d:
            testDataFileName = '{}/test.h5'.format(d)
            # Write the dataset to an hdf5 file
            # (Note: Don't use vigra to do this, which may reorder the axes)
            h5File = h5py.File(testDataFileName)
            h5File.create_group('volumes')

            internalPathString = "subvolume-{sliceIndex:02d}"
            for sliceIndex, tSlice in enumerate(data):
                subpath = internalPathString.format(sliceIndex=sliceIndex)
                h5File['volumes'].create_dataset(subpath, data=tSlice)
                # Write the axistags attribute
                current_path = 'volumes/{}'.format(subpath)
                h5File[current_path].attrs['axistags'] = axistags.toJSON()

            # Read the data with an operator
            hdf5GlobString = "{}/volumes/subvolume-*".format(testDataFileName)
            op.SequenceAxis.setValue('t')
            op.GlobString.setValue(hdf5GlobString)
            op.Hdf5File.setValue(h5File)

            assert op.OutputImage.ready()
            assert op.OutputImage.meta.axistags == expected_axistags
            assert (op.OutputImage[0:2, 5:10, 20:50, 40:70].wait() == 
                    data[0:2, 5:10, 20:50, 40:70]).all()


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
