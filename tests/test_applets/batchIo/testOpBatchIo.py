import os
import h5py
import numpy.random
from lazyflow.graph import Graph
from lazyflow.operators import OpGaussianSmoothing
from lazyflow.operators.ioOperators import OpInputDataReader
from ilastik.applets.batchIo.opBatchIo import OpBatchIo, ExportFormat
from ilastik.applets.dataSelection.opDataSelection import DatasetInfo

class TestOpBatchIo(object):
    def setUp(self):
        self.testDataFileName = 'NpyTestData.npy'
        
        # Start by writing some test data to disk.
        self.testData = numpy.random.random((1,10,10,10,1))
        numpy.save(self.testDataFileName, self.testData)

    def tearDown(self):
        try:
            os.remove(self.testDataFileName)
        except:
            pass
    
    def testBasic(self):
        cwd = os.getcwd()
        info = DatasetInfo()
        info.filePath = cwd + '/NpyTestData.npy'
        
        graph = Graph()
        opBatchIo = OpBatchIo(graph=graph)
        opInput = OpInputDataReader(graph=graph)
        opInput.FilePath.setValue( info.filePath )
        
        # Our test "processing pipeline" is just a smoothing operator.
        opSmooth = OpGaussianSmoothing(graph=graph)
        opSmooth.Input.connect( opInput.Output )
        opSmooth.sigma.setValue(3.0)
        
        opBatchIo.ExportDirectory.setValue( '' )
        opBatchIo.Suffix.setValue( '_smoothed' )
        opBatchIo.Format.setValue( ExportFormat.H5 )
        opBatchIo.DatasetPath.setValue( info.filePath )
        
        internalPath = 'path/to/data'
        opBatchIo.InternalPath.setValue( internalPath )
        
        opBatchIo.ImageToExport.connect( opSmooth.Output )
        
        dirty = opBatchIo.Dirty.value
        assert dirty == True
        
        outputPath = opBatchIo.OutputDataPath.value
        assert outputPath == cwd + '/NpyTestData_smoothed.h5/' + internalPath
        
        result = opBatchIo.ExportResult.value
        assert result
        
        dirty = opBatchIo.Dirty.value
        assert dirty == False
        
        # Check the file
        f = h5py.File(cwd + '/NpyTestData_smoothed.h5', 'r')
        assert internalPath in f
        assert f[internalPath].shape == self.testData.shape
        
        
if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})
