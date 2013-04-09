from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpStreamingHdf5Reader
import h5py
import numpy
import os
import vigra

class TestOpStreamingHdf5Reader(object):

    def setUp(self):
        self.graph = Graph()
        self.testDataFileName = 'test.h5'
        self.op = OpStreamingHdf5Reader(graph=self.graph)

        self.h5File = h5py.File(self.testDataFileName)
        self.h5File.create_group('volume')

        # Create a test dataset
        datashape = (1,2,3,4,5)
        self.data = numpy.indices(datashape).sum(0).astype(numpy.float32)

    def tearDown(self):
        self.h5File.close()
        try:
            os.remove(self.testDataFileName)
        except:
            pass

    def test_plain(self):
        # Write the dataset to an hdf5 file
        self.h5File['volume'].create_dataset('data', data=self.data)

        # Read the data with an operator
        self.op.Hdf5File.setValue(self.h5File)
        self.op.InternalPath.setValue('volume/data')

        assert self.op.OutputImage.meta.shape == self.data.shape
        assert self.op.OutputImage[0,1,2,1,0].wait() == 4

    def test_withAxisTags(self):
        # Write it again, this time with weird axistags
        axistags = vigra.AxisTags(
            vigra.AxisInfo('x',vigra.AxisType.Space),
            vigra.AxisInfo('y',vigra.AxisType.Space),
            vigra.AxisInfo('z',vigra.AxisType.Space),
            vigra.AxisInfo('c',vigra.AxisType.Channels),
            vigra.AxisInfo('t',vigra.AxisType.Time))

        # Write the dataset to an hdf5 file
        # (Note: Don't use vigra to do this, which may reorder the axes)
        self.h5File['volume'].create_dataset('tagged_data', data=self.data)
        # Write the axistags attribute
        self.h5File['volume/tagged_data'].attrs['axistags'] = axistags.toJSON()

        # Read the data with an operator
        self.op.Hdf5File.setValue(self.h5File)
        self.op.InternalPath.setValue('volume/tagged_data')

        assert self.op.OutputImage.meta.shape == self.data.shape
        assert self.op.OutputImage[0,1,2,1,0].wait() == 4

if __name__ == "__main__":
    import nose
    ret = nose.run()
    if not ret: sys.exit(1)
