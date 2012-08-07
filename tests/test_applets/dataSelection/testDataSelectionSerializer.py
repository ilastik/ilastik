import os
import h5py
import vigra
import numpy
import tempfile
from lazyflow.graph import Graph, OperatorWrapper
from ilastik.applets.dataSelection.opDataSelection import OpDataSelection, DatasetInfo
from ilastik.applets.dataSelection.dataSelectionSerializer import DataSelectionSerializer

import logging
logger = logging.getLogger(__name__)

class TestDataSelectionSerializer(object):
    
    def setUp(self):
        self.tmpDir = tempfile.mkdtemp()
        self.tmpFilePath = self.tmpDir + "/testDataSelection.npy"
    
        self.testProjectName = 'test_project.ilp'
        self.testProjectName = os.path.split(__file__)[0] + '/' + self.testProjectName
        
        self.cleanupFiles = [self.tmpFilePath, self.testProjectName]

        data = numpy.indices((1,10,10,10,2)).sum(0)
        numpy.save(self.tmpFilePath, data)
        
    def tearDown(self):
        for f in self.cleanupFiles:
            try:
                os.remove(f)
            except:
                pass

        try:
            os.removedirs(self.tmpDir)
        except:
            pass
    
    def test06(self):
        """
        Test the basic functionality of the v0.6 project format serializer.
        """
        # Create an empty project
        testProject = h5py.File(self.testProjectName)
        testProject.create_dataset("ilastikVersion", data=0.6)
        
        ##
        ## Serialization
        ##
    
        # Create an operator to work with and give it some input
        graph = Graph()
        operatorToSave = OperatorWrapper( OpDataSelection(graph=graph) )
        serializer = DataSelectionSerializer(operatorToSave, 'DataSelectionTest')
        assert serializer._base_initialized
    
        operatorToSave.ProjectFile.setValue(testProject)
        operatorToSave.WorkingDirectory.setValue( os.path.split(__file__)[0] )
        operatorToSave.ProjectDataGroup.setValue( serializer.topGroupName + '/local_data' )
        
        info = DatasetInfo()
        info.filePath = self.tmpFilePath
        info.location = DatasetInfo.Location.ProjectInternal
        
        operatorToSave.Dataset.resize(1)
        operatorToSave.Dataset[0].setValue(info)
        
        # Now serialize!
        serializer.serializeToHdf5(testProject, self.testProjectName)
        
        # Check for dataset existence
        datasetInternalPath = serializer.topGroupName + '/local_data/' + info.datasetId
        dataset = testProject[datasetInternalPath][...]
        
        # Check axistags attribute
        axistags = vigra.AxisTags.fromJSON(testProject[datasetInternalPath].attrs['axistags'])
        
        # Debug info...
        #logging.basicConfig(level=logging.DEBUG)
        logger.debug('dataset.shape = ' + str(dataset.shape))
        logger.debug('should be ' + str(operatorToSave.Image[0].meta.shape))
        logger.debug('dataset axistags:')
        logger.debug(axistags)
        logger.debug('should be:')
        logger.debug(operatorToSave.Image[0].meta.axistags)
    
        originalShape = operatorToSave.Image[0].meta.shape
        originalAxisTags = operatorToSave.Image[0].meta.axistags
        
        # Now we can directly compare the shape and axis ordering
        assert dataset.shape == originalShape
        assert axistags == originalAxisTags
        
        ##
        ## Deserialization
        ##
    
        # Create an empty operator
        graph = Graph()
        operatorToLoad = OperatorWrapper( OpDataSelection(graph=graph) )
        
        deserializer = DataSelectionSerializer(operatorToLoad, serializer.topGroupName) # Copy the group name from the serializer we used.
        assert deserializer._base_initialized
        deserializer.deserializeFromHdf5(testProject, self.testProjectName)
        
        assert len(operatorToLoad.Dataset) == len(operatorToSave.Dataset)
        assert len(operatorToLoad.Image) == len(operatorToSave.Image)
        
        assert operatorToLoad.Image[0].meta.shape == operatorToSave.Image[0].meta.shape
        assert operatorToLoad.Image[0].meta.axistags == operatorToSave.Image[0].meta.axistags

        os.remove(self.testProjectName)
    
if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")
    sys.argv.append("--nologcapture")
    nose.run(defaultTest=__file__)
