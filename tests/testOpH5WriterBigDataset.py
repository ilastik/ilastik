from lazyflow.operators import OpH5WriterBigDataset
import numpy
import vigra
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
        self.testData = vigra.VigraArray( self.dataShape, axistags=vigra.defaultAxistags('txyzc'), order='C' )
        self.testData[...] = numpy.indices(self.dataShape).sum(0)

    def tearDown(self):
        # Clean up: Delete the test file.
        try:
            os.remove(self.testDataFileName)
        except:
            pass

    def test_Writer(self):
        # Create the h5 file
        hdf5File = h5py.File(self.testDataFileName)
        
        
        opWriter = OpH5WriterBigDataset(graph=self.graph)
        opWriter.hdf5File.setValue( hdf5File )
        opWriter.hdf5Path.setValue( self.datasetInternalPath )
        opWriter.Image.setValue( self.testData )

        # Force the operator to execute by asking for the output (a bool)
        success = opWriter.WriteImage.value
        assert success

        hdf5File.close()

        # Check the file.
        f = h5py.File(self.testDataFileName, 'r')
        dataset = f[self.datasetInternalPath]
        assert dataset.shape == self.dataShape
        assert numpy.all( dataset[...] == self.testData.view(numpy.ndarray)[...] )
        f.close()

class TestOpH5WriterBigDataset_2(object):

    def setUp(self):
        self.graph = lazyflow.graph.Graph()
        self.testDataFileName = 'bigH5TestData.h5'
        self.datasetInternalPath = 'volume/data'

        # Generate some test data
        self.dataShape = (1, 10, 128, 128, 1)
        self.testData = vigra.VigraArray( self.dataShape, axistags=vigra.defaultAxistags('txyzc') ) # default vigra order this time...
        self.testData[...] = numpy.indices(self.dataShape).sum(0)

    def tearDown(self):
        # Clean up: Delete the test file.
        try:
            os.remove(self.testDataFileName)
        except:
            pass

    def test_Writer(self):
        
        # Create the h5 file
        hdf5File = h5py.File(self.testDataFileName)
        
        
        opWriter = OpH5WriterBigDataset(graph=self.graph)
        
        # This checks that you can give a preexisting group as the file
        g = hdf5File.create_group('volume')
        opWriter.hdf5File.setValue( g )
        opWriter.hdf5Path.setValue( "data" )
        opWriter.Image.setValue( self.testData )

        # Force the operator to execute by asking for the output (a bool)
        success = opWriter.WriteImage.value
        assert success

        hdf5File.close()

        # Check the file.
        f = h5py.File(self.testDataFileName, 'r')
        dataset = f[self.datasetInternalPath]
        assert dataset.shape == self.dataShape
        assert numpy.all( dataset[...] == self.testData.view(numpy.ndarray)[...] )
        f.close()

if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})
