from lazyflow.operators import OpH5WriterBigDataset
import numpy
import h5py
import os
import sys
import lazyflow.graph

#import logging
#logger = logging.getLogger(__file__)
#logger.addHandler(logging.StreamHandler(sys.stdout))
#logger.setLevel(logging.DEBUG)

class TestOpH5WriterBigDataset(object):

    def setUp(self):
        self.graph = lazyflow.graph.Graph()
        self.testDataFileName = 'bigH5TestData.h5'
        self.datasetInternalPath = 'volume/data'

        # Generate some test data
        self.dataShape = (1, 10, 128, 128, 1)
        self.testData = numpy.zeros(self.dataShape)
        def addIndexSums(a):
            """
            For each element e located at pos = (i0, i1,...iN),
            e += sum(pos)
            """
            if len(a.shape) > 0:
                for index in range(a.shape[0]):
                    addIndexSums( a[index,...] )
                    a[index,...] += index
        addIndexSums(self.testData)

    def tearDown(self):
        pass
        # Clean up: Delete the test file.
        #os.remove(self.testDataFileName)

    def test_Writer(self):
        # Now read back our test data using an OpNpyFileReader operator
        opWriter = OpH5WriterBigDataset(graph=self.graph)
        opWriter.Filename.setValue( self.testDataFileName )
        opWriter.hdf5Path.setValue( self.datasetInternalPath )
        opWriter.Image.setValue( self.testData )

        # Force the operator to execute by asking for the output (a bool)
        success = opWriter.WriteImage.value
        assert success

        opWriter.close()

        # Check the file.
        f = h5py.File(self.testDataFileName, 'r')
        dataset = f[self.datasetInternalPath]
        assert dataset.shape == self.dataShape
        assert numpy.all( dataset[...] == self.testData[...] )



if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})
