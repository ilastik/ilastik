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

            internal_path_string = "subvolume-{slice_index:02d}"
            for slice_index, z_slice in enumerate(data):
                subpath = internal_path_string.format(slice_index=slice_index)
                h5File['volumes'].create_dataset(subpath, data=data)
                # Write the axistags attribute
                current_path = 'volumes/{}'.format(subpath)
                h5File[current_path].attrs['axistags'] = axistags.toJSON()

            # Read the data with an operator
            hdf5_glob_string = "volumes/subvolume-*"
            op.SequenceAxis.setValue('z')
            op.GlobString.setValue(hdf5_glob_string)
            op = OpStreamingHdf5SequenceReader(graph=Graph())

            assert op.Output.ready()
            assert op.Output.meta.axistags == expected_axistags
            assert (op.Output[5:10, 50:100, 100:150].wait() == data[5:10, 50:100, 100:150]).all()

    def test_2d_vigra_along_t(self):
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

            internal_path_string = "subvolume-{slice_index:02d}"
            for slice_index, z_slice in enumerate(data):
                subpath = internal_path_string.format(slice_index=slice_index)
                h5File['volumes'].create_dataset(subpath, data=data)
                # Write the axistags attribute
                current_path = 'volumes/{}'.format(subpath)
                h5File[current_path].attrs['axistags'] = axistags.toJSON()

            # Read the data with an operator
            hdf5_glob_string = "volumes/subvolume-*"
            op.SequenceAxis.setValue('t')
            op.GlobString.setValue(hdf5_glob_string)
            op = OpStreamingHdf5SequenceReader(graph=Graph())

            assert op.Output.ready()
            assert op.Output.meta.axistags == expected_axistags
            assert (op.Output[5:10, 50:100, 100:150].wait() == data[5:10, 50:100, 100:150]).all()

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

            internal_path_string = "subvolume-{slice_index:02d}"
            for slice_index, z_slice in enumerate(data):
                subpath = internal_path_string.format(slice_index=slice_index)
                h5File['volumes'].create_dataset(subpath, data=data)
                # Write the axistags attribute
                current_path = 'volumes/{}'.format(subpath)
                h5File[current_path].attrs['axistags'] = axistags.toJSON()

            # Read the data with an operator
            hdf5_glob_string = "volumes/subvolume-*"
            op.SequenceAxis.setValue('t')
            op.GlobString.setValue(hdf5_glob_string)
            op = OpStreamingHdf5SequenceReader(graph=Graph())

            assert op.Output.ready()
            assert op.Output.meta.axistags == expected_axistags
            assert (op.Output[5:10, 50:100, 100:150].wait() == data[5:10, 50:100, 100:150]).all()


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
