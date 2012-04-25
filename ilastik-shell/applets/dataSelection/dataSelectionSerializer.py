from utility import SimpleSignal # from the ilastik-shell utility module

#class StorageOptions():
#    ProjectInternal = 0
#    AbsoluteFilePath = 1
#    RelativeFilePath = 2
#
#class DataSetInfo(object):
#    def __init__(self):
#        self.filePath = None
#        self.dataSetName = None
#        self.dataSetStorageOption = None
#
#class DataSelectionSerializationSettings(object):
#    def __init__(self):
#        self.dataSetInfos = []
#        self.dataSetInfoChanged = SimpleSignal()

class DataSelectionSerializer(object):
    """
    Serializes the user's input data selections to an ilastik v0.6 project file.
    """
    CurrentVersion = 0.1
    OldestReadableVersion = 0.1
    GroupName = "Datasets"
    
    def __init__(self, mainOperator):
        self.mainOperator = mainOperator
    
    def serializeToHdf5(self, hdf5File):
        # Check the overall version.
        # We only support v0.6 at the moment.
        ilastikVersion = hdf5File["ilastikVersion"].value
        if ilastikVersion != 0.6:
            return
        
        # For now, datasets are not stored to the project file
        # Instead, we just store links to the original files.
        # TODO: Support project-local storage.
        # Create a group for this dataset
    
    def deserializeFromHdf5(self, hdf5File):
        # Check the overall version.
        # We only support v0.6 at the moment.
        ilastikVersion = hdf5File["ilastikVersion"].value
        if ilastikVersion != 0.6:
            return
        
        

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
