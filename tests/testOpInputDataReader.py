from lazyflow.operators.ioOperators import OpInputDataReader
import os
import numpy
import vigra
import lazyflow.graph

class TestOpInputDataReader(object):

    @classmethod
    def setupClass(cls):
        cls.graph = lazyflow.graph.Graph()
        cls.testNpyDataFileName = 'test.npy'
        cls.testImageFileName = 'test.png'
        cls.testH5FileName = 'test.h5'

    @classmethod
    def teardownClass(cls):
        # Clean up: Delete the test data files.
        os.remove(cls.testNpyDataFileName)
        os.remove(cls.testImageFileName)
        os.remove(cls.testH5FileName)

    def test_npy(self):
        # Create Numpy test data
        a = numpy.zeros((10, 11))
        for x in range(0,10):
            for y in range(0,11):
                a[x,y] = x+y
        numpy.save(self.testNpyDataFileName, a)

        # Now read back our test data using an OpInputDataReader operator
        npyReader = OpInputDataReader(graph=self.graph)
        npyReader.FilePath.setValue(self.testNpyDataFileName)
        cwd = os.path.split(__file__)[0]
        npyReader.WorkingDirectory.setValue( cwd )

        # Read the entire NPY file and verify the contents
        npyData = npyReader.Output[:].wait()
        assert npyData.shape == (10,11,1)
        for x in range(0,10):
            for y in range(0,11):
                assert npyData[x,y] == x+y


    def test_png(self):
        # Create PNG test data
        a = numpy.zeros((100,200))
        for x in range(a.shape[0]):
            for y in range(a.shape[1]):
                a[x,y] = (x+y) % 256
        vigra.impex.writeImage(a, self.testImageFileName)

        # Read the entire PNG file and verify the contents
        pngReader = OpInputDataReader(graph=self.graph)
        pngReader.FilePath.setValue(self.testImageFileName)
        cwd = os.path.split(__file__)[0]
        pngReader.WorkingDirectory.setValue( cwd )
        pngData = pngReader.Output[:].wait()
        for x in range(pngData.shape[0]):
            for y in range(pngData.shape[1]):
                assert pngData[x,y,0] == (x+y) % 256

    def test_h5(self):
        # Create HDF5 test data
        import h5py
        f = h5py.File(self.testH5FileName)
        f.create_group('volume')
        shape = (1,2,3,4,5)
        f['volume'].create_dataset('data', shape)

        for i in range(0,shape[0]):
            for j in range(0,shape[1]):
                for k in range(0,shape[2]):
                    for l in range(0,shape[3]):
                        for m in range(0,shape[4]):
                            f['volume/data'][i,j,k,l,m] = i + j + k + l + m
        f.close()

        # Read the entire HDF5 file and verify the contents
        h5Reader = OpInputDataReader(graph=self.graph)
        h5Reader.FilePath.setValue(self.testH5FileName + '/volume/data') # Append internal path
        cwd = os.path.split(__file__)[0]
        h5Reader.WorkingDirectory.setValue( cwd )

        # Grab a section of the h5 data
        h5Data = h5Reader.Output[0,0,:,:,:].wait()
        assert h5Data.shape == (1,1,3,4,5)
        # (Just check part of the data)
        for k in range(0,shape[2]):
            for l in range(0,shape[3]):
                for m in range(0,shape[4]):
                    assert h5Data[0,0,k,l,m] == k + l + m

if __name__ == "__main__":
    import nose
    nose.main(defaultTest=__file__)
