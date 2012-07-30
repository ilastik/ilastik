import os
import h5py
import vigra
from lazyflow.graph import Graph, OperatorWrapper
from ilastik.applets.dataSelection.opDataSelection import OpDataSelection, DatasetInfo
from ilastik.applets.dataSelection.dataSelectionSerializer import DataSelectionSerializer

import logging
logger = logging.getLogger(__name__)

class TestDataSelectionSerializer(object):
    
    def test06(self):
        """
        Test the basic functionality of the v0.6 project format serializer.
        """
        # Define the files we'll be making    
        testProjectName = 'test_project.ilp'
        testProjectName = os.path.split(__file__)[0] + '/' + testProjectName
        # Clean up: Remove the test data files we created last time (just in case)
        for f in [testProjectName]:
            try:
                os.remove(f)
            except:
                pass
    
        # Create an empty project
        testProject = h5py.File(testProjectName)
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
        info.filePath = '/home/bergs/5d.npy'
        info.location = DatasetInfo.Location.ProjectInternal
        
        operatorToSave.Dataset.resize(1)
        operatorToSave.Dataset[0].setValue(info)
        
        # Now serialize!
        serializer.serializeToHdf5(testProject, testProjectName)
        
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
        deserializer.deserializeFromHdf5(testProject, testProjectName)
        
        assert len(operatorToLoad.Dataset) == len(operatorToSave.Dataset)
        assert len(operatorToLoad.Image) == len(operatorToSave.Image)
        
        assert operatorToLoad.Image[0].meta.shape == operatorToSave.Image[0].meta.shape
        assert operatorToLoad.Image[0].meta.axistags == operatorToSave.Image[0].meta.axistags

        os.remove(testProjectName)
    
if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})
    
    


































