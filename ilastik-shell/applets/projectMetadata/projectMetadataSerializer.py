from utility import VersionManager


class ProjectMetadataSerializer(object):
    SerializerVersion = 0.1
    TopGroupName = 'ProjectMetadata'     
    
    def __init__(self, projectMetadata):
        self.projectMetadata = projectMetadata
    
    def serializeToHdf5(self, hdf5File, filePath):
        # Check the overall file version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # Make sure we can find our way around the project tree
        if not VersionManager.isProjectFileVersionCompatible(ilastikVersion):
            return

        # Access the metadata group (create it if necessary)
        try:
            metadataGroup = hdf5File[ProjectMetadataSerializer.TopGroupName]
        except KeyError:
            metadataGroup = hdf5File.create_group(ProjectMetadataSerializer.TopGroupName)
        
        # Set the version
        if 'StorageVersion' not in metadataGroup.keys():
            metadataGroup.create_dataset('StorageVersion', data=self.SerializerVersion)
        else:
            metadataGroup['StorageVersion'][()] = self.SerializerVersion

        # Write each of our values to the group
        self.setDataset(metadataGroup, 'ProjectName', self.projectMetadata.projectName)
        self.setDataset(metadataGroup, 'Labeler', self.projectMetadata.labeler)
        self.setDataset(metadataGroup, 'Description', self.projectMetadata.description)
    
    def deserializeFromHdf5(self, hdf5File, filePath):
        # Check the overall file version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # Make sure we can find our way around the project tree
        if not VersionManager.isProjectFileVersionCompatible(ilastikVersion):
            return
        
        try:
            metadataGroup = hdf5File[ProjectMetadataSerializer.TopGroupName]
        except KeyError:
            self.projectMetadata.projectName = ''
            self.projectMetadata.labeler = ''
            self.projectMetadata.description = ''
            return

        self.projectMetadata.projectName = self.getDataset(metadataGroup, 'ProjectName')
        self.projectMetadata.labeler = self.getDataset(metadataGroup, 'Labeler')
        self.projectMetadata.description = self.getDataset(metadataGroup, 'Description')

    def isDirty(self):
        """ Return true if the current state of this item 
            (in memory) does not match the state of the HDF5 group on disk.
            SerializableItems are responsible for tracking their own dirty/notdirty state."""
        return False

    def unload(self):
        """ Called if either
            (1) the user closed the project or
            (2) the project opening process needs to be aborted for some reason
                (e.g. not all items could be deserialized properly due to a corrupted ilp)
            This way we can avoid invalid state due to a partially loaded project. """ 
        self.projectMetadata.projectName = ''
        self.projectMetadata.labeler = ''
        self.projectMetadata.description = ''

    def setDataset(self, group, dataName, dataValue):
        if dataName not in group.keys():
            # Create and assign
            group.create_dataset(dataName, data=dataValue)
        else:
            # Assign (this will fail if the dtype doesn't match)
            group[dataName][()] = dataValue
    
    def getDataset(self, group, dataName):
        try:
            result = group[dataName].value
        except KeyError:
            result = ''
        return result

class Ilastik05ProjectMetadataDeserializer(object):    
    def __init__(self, projectMetadata):
        self.projectMetadata = projectMetadata
    
    def serializeToHdf5(self, hdf5File, filePath):
        # This is for deserialization only.
        pass
        
    def deserializeFromHdf5(self, hdf5File, filePath):
        # Check the overall file version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # This is the v0.5 import deserializer.  Don't work with 0.6 projects (or anything else).
        if ilastikVersion != 0.5:
            return
        
        try:
            metadataGroup = hdf5File['Project']
        except KeyError:
            self.projectMetadata.projectName = ''
            self.projectMetadata.labeler = ''
            self.projectMetadata.description = ''
            return

        self.projectMetadata.projectName = self.getDataset(metadataGroup, 'Name')
        self.projectMetadata.labeler = self.getDataset(metadataGroup, 'Labeler')
        self.projectMetadata.description = self.getDataset(metadataGroup, 'Description')

    def isDirty(self):
        """ Return true if the current state of this item 
            (in memory) does not match the state of the HDF5 group on disk.
            SerializableItems are responsible for tracking their own dirty/notdirty state."""
        return False

    def unload(self):
        """ Called if either
            (1) the user closed the project or
            (2) the project opening process needs to be aborted for some reason
                (e.g. not all items could be deserialized properly due to a corrupted ilp)
            This way we can avoid invalid state due to a partially loaded project. """ 
        self.projectMetadata.projectName = ''
        self.projectMetadata.labeler = ''
        self.projectMetadata.description = ''
    
    def getDataset(self, group, dataName):
        try:
            result = group[dataName].value
        except KeyError:
            result = ''
        return result

# Simple test
if __name__ == "__main__":
    import os
    import h5py
    from projectMetadata import ProjectMetadata
    
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
    serializer = ProjectMetadataSerializer(metadata)
    serializer.serializeToHdf5(testProject)
    
    assert testProject[ProjectMetadataSerializer.TopGroupName]['ProjectName'].value == metadata.projectName
    assert testProject[ProjectMetadataSerializer.TopGroupName]['Labeler'].value == metadata.labeler
    assert testProject[ProjectMetadataSerializer.TopGroupName]['Description'].value == metadata.description
    
    # Now deserialize
    newMetadata = ProjectMetadata()
    deserializer = ProjectMetadataSerializer(newMetadata)
    deserializer.deserializeFromHdf5(testProject)
    
    assert newMetadata.projectName == metadata.projectName
    assert newMetadata.labeler == metadata.labeler
    assert newMetadata.description == metadata.description





































