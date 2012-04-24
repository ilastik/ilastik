class DataSelectionSerializer(object):
    """
    Serializes the user's input data selections to an ilastik v0.6 project file.
    """
    def __init__(self, mainOperator):
        pass
    
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
