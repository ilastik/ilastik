import os
import numpy
import h5py
from lazyflow.graph import Graph
from applets.featureSelection.opFeatureSelection import OpFeatureSelection
from applets.featureSelection.featureSelectionSerializer import FeatureSelectionSerializer

class TestFeatureSelectionSerializer(object):

    def test(self):    
        # Define the files we'll be making    
        testProjectName = 'test_project.ilp'
        # Clean up: Remove the test data files we created last time (just in case)
        for f in [testProjectName]:
            try:
                os.remove(f)
            except:
                pass
    
        # Create an empty project
        testProject = h5py.File(testProjectName)
        testProject.create_dataset("ilastikVersion", data=0.6)
        
        # Create an operator to work with and give it some input
        graph = Graph()
        operatorToSave = OpFeatureSelection(graph=graph)
    
        # Configure scales        
        scales = [0.1, 0.2, 0.3, 0.4, 0.5]
        operatorToSave.Scales.setValue(scales)
    
        # Configure feature types
        featureIds = [ 'GaussianSmoothing',
                       'LaplacianOfGaussian' ]
        operatorToSave.FeatureIds.setValue(featureIds)
    
        # All False (no features selected)
        selectionMatrix = numpy.zeros((2, 5), dtype=bool)
    
        # Change a few to True
        selectionMatrix[0,0] = True
        selectionMatrix[1,0] = True
        selectionMatrix[0,2] = True
        selectionMatrix[1,4] = True
        operatorToSave.SelectionMatrix.setValue(selectionMatrix)
        
        # Serialize!
        serializer = FeatureSelectionSerializer(operatorToSave)
        serializer.serializeToHdf5(testProject, testProjectName)
        
        assert (testProject['FeatureSelections/Scales'].value == scales).all()
        assert (testProject['FeatureSelections/FeatureIds'].value == featureIds).all()
        assert (testProject['FeatureSelections/SelectionMatrix'].value == selectionMatrix).all()
    
        # Deserialize into a fresh operator
        operatorToLoad = OpFeatureSelection(graph=graph)
        deserializer = FeatureSelectionSerializer(operatorToLoad)
        deserializer.deserializeFromHdf5(testProject, testProjectName)
        
        assert (operatorToLoad.Scales.value == scales).all()
        assert (operatorToLoad.FeatureIds.value == featureIds).all()
        assert (operatorToLoad.SelectionMatrix.value == selectionMatrix).all()

        os.remove(testProjectName)

if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})

