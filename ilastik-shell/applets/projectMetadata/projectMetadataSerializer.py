class ProjectMetadataSerializer(object):
    def __init__(self, projectMetadata):
        self.projectMetadata = projectMetadata
    
    def serializeToHdf5(self, hdf5Group):
        pass
    
    def deserializeFromHdf5(self, hdf5Group):
        pass

    def isDirty(self):
        """ Return true if the current state of this item 
            (in memory) does not match the state of the HDF5 group on disk.
            SerializableItems are responsible for tracking their own dirty/notdirty state."""
        pass

    def unload(self):
        """ Called if either
            (1) the user closed the project or
            (2) the project opening process needs to be aborted for some reason
                (e.g. not all items could be deserialized properly due to a corrupted ilp)
            This way we can avoid invalid state due to a partially loaded project. """ 
        pass

class Ilastik05ProjectMetadataDeserializer(object):
    """
    Imports the project metadata (e.g. project name) from an v0.5 .ilp file.
    """
    def __init__(self, projectMetadata):
        self.projectMetadata = projectMetadata
    
    def serializeToHdf5(self, hdf5Group):
        pass
    
    def deserializeFromHdf5(self, hdf5File):

        # Read in what values we can, without failing if any of them are missing
        try:
            self.projectMetadata.labeler = hdf5File["Project/Labeler"].value
        except KeyError:
            pass

        try:
            self.projectMetadata.projectName = hdf5File["Project/Name"].value
        except KeyError:
            pass
            
        try:
            self.projectMetadata.description = hdf5File["Project/Description"].value
        except KeyError:
            pass

    def isDirty(self):
        """
        For now, this class is import-only.
        We always report our data as "clean" because we have nothing to write.
        """
        return False

    def unload(self):
        """ Called if either
            (1) the user closed the project or
            (2) the project opening process needs to be aborted for some reason
                (e.g. not all items could be deserialized properly due to a corrupted ilp)
            This way we can avoid invalid state due to a partially loaded project. """ 
        pass
