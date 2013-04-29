from lazyflow.operators.ioOperators import OpNpyFileReader
import numpy
import os
import lazyflow.graph

class TestOpNpyFileReader(object):

    def setUp(self):
        self.graph = lazyflow.graph.Graph()
        self.testDataFileName = 'NptTestData.npy'

        # Start by writing some test data to disk.
        self.testData = numpy.zeros((10, 11))
        for x in range(0,10):
            for y in range(0,11):
                self.testData[x,y] = x+y
        numpy.save(self.testDataFileName, self.testData)

    def tearDown(self):
        # Clean up: Delete the test file.
        os.remove(self.testDataFileName)

    def test_OpNpyFileReader(self):
        # Now read back our test data using an OpNpyFileReader operator
        npyReader = OpNpyFileReader(graph=self.graph)
        npyReader.FileName.setValue(self.testDataFileName)

        # Read the entire file and verify the contents
        a = npyReader.Output[:].wait()
        assert a.shape == (10,11) # OpNpyReader automatically added a channel axis
        assert npyReader.Output.meta.dtype == self.testData.dtype

        # Why doesn't this work?  Numpy bug?
        # cmp = ( a == self.testData )
        # assert cmp.all()

        # Check each of the values
        for i in range(10):
            for j in range(11):
                assert a[i,j] == self.testData[i,j]
        npyReader.cleanUp()

if __name__ == "__main__":
    import nose
    ret = nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})
    if not ret: sys.exit(1)
