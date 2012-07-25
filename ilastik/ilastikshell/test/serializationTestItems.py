# Simple classes to serve as serialization items during unit testing

class ExampleSerializableItem(object):
    def __init__(self, name):
        self.name = name        
        # Load up some default data.
        # Normally this would be pulled from the program state (e.g. the GUI)
        #  during the save process (i.e. in serializeToHdf5)
        self.subgroups = {
              "Example Subgroup 1" : { "SomeSetting" : "Elephant", "SomeOtherSetting" : "Tiger" },
              "Example Subgroup 2" : { "Population" : 12345 , "Elevation" : 16.0 }
              }
    
    def serializeToHdf5(self, hdf5Group, projectFilePath):
        """ Write some test data to the given HDF5 group."""

        # Add our data to a group that we own
        itemGroup = hdf5Group.create_group(self.name)
        
        # Write each of our subgroups and their datasets
        print self.subgroups
        for groupName, groupDataSets in self.subgroups.items():
            subgroup = itemGroup.create_group(groupName)
            for dataName, dataValue in groupDataSets.items():
                subgroup.create_dataset(dataName, data=dataValue)
    
    def deserializeFromHdf5(self, hdf5Group, projectFilePath):
        """ Read the data from the given HDF5 group."""
        # Obtain a handle to our own group in the file
        itemGroup = hdf5Group[self.name]

        # Populate our subgroups  
        self.subgroups = {}
        for groupName, groupDataSets in itemGroup.items():
            subgroup = itemGroup[groupName]
            self.subgroups[groupName] = {}
            for dataSetName, data in subgroup.items():
                self.subgroups[groupName][dataSetName] = data.value

    def isDirty(self):
        return False

    def unload(self):
        print "Unloading serializable item: " + self.name 
        # Here we would signal to the rest of the program that we've been unloaded,
        #  so internal state should be erased and the GUI should be blanked or disabled.

