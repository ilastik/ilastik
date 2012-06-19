import os
import numpy
import h5py
from lazyflow.graph import Graph
from applets.projectMetadata import ProjectMetadata
from applets.projectMetadata.projectMetadataSerializer import ProjectMetadataSerializer

class TestProjectMetadataSerializer(object):
    
    def test(self):
        testProjectName = 'test_project.ilp'
        # Clean up: Delete any lingering test files from the previous run.
        try:
            os.remove(testProjectName)
        except:
            pass
        
        testProject = h5py.File(testProjectName)
        testProject.create_dataset('ilastikVersion', data=0.6)
        
        metadata = ProjectMetadata()
        metadata.projectName = "Test Project"
        metadata.labeler = "Test Labeler"
        metadata.description = "Test Description"
        
        # Create an empty hdf5 file to serialize to.
        serializer = ProjectMetadataSerializer(metadata, 'ProjectMetadata')
        serializer.serializeToHdf5(testProject, testProjectName)
        
        assert testProject['ProjectMetadata']['ProjectName'].value == metadata.projectName
        assert testProject['ProjectMetadata']['Labeler'].value == metadata.labeler
        assert testProject['ProjectMetadata']['Description'].value == metadata.description
        
        # Now deserialize
        newMetadata = ProjectMetadata()
        deserializer = ProjectMetadataSerializer(newMetadata, 'ProjectMetadata')
        deserializer.deserializeFromHdf5(testProject, testProjectName)
        
        assert newMetadata.projectName == metadata.projectName
        assert newMetadata.labeler == metadata.labeler
        assert newMetadata.description == metadata.description

        os.remove(testProjectName)

if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})
