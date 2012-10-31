import os
import numpy
import h5py
from lazyflow.graph import Graph
from ilastik.applets.thresholdMasking.opThresholdMasking import OpThresholdMasking
from ilastik.applets.thresholdMasking.thresholdMaskingSerializer import ThresholdMaskingSerializer

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()

class TestThresholdMaskingSerializer(object):

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
        with h5py.File(testProjectName) as testProject:
            testProject.create_dataset("ilastikVersion", data=0.6)
            
            # Create an operator to work with and give it some input
            graph = Graph()
            operatorToSave = OpThresholdMasking(graph=graph)
        
            operatorToSave.MinValue.setValue( 10 )
            operatorToSave.MaxValue.setValue( 20 )
    
            # Serialize!
            serializer = ThresholdMaskingSerializer(operatorToSave, 'ThresholdMasking')
            serializer.serializeToHdf5(testProject, testProjectName)
            
            assert testProject['ThresholdMasking/MinValue'][()] == 10
            assert testProject['ThresholdMasking/MaxValue'][()] == 20
        
            # Deserialize into a fresh operator
            operatorToLoad = OpThresholdMasking(graph=graph)
            deserializer = ThresholdMaskingSerializer(operatorToLoad, 'ThresholdMasking')
            deserializer.deserializeFromHdf5(testProject, testProjectName)
    
            assert operatorToLoad.MinValue.value == 10
            assert operatorToLoad.MaxValue.value == 20

        os.remove(testProjectName)

if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})

