class FeatureSelectionSerializer(object):
    """
    Serializes the user's pixel feature selections to an ilastik v0.6 project file.
    """
    SerializerVersion = 0.1
    TopGroupName = "FeatureSelections"
    
    def __init__(self, mainOperator):
        self.mainOperator = mainOperator
    
    def serializeToHdf5(self, hdf5File, filePath):
        # Check the overall version.
        # We only support v0.6 at the moment.
        ilastikVersion = hdf5File["ilastikVersion"].value
        if ilastikVersion != 0.6:
            return
    
        # Can't store anything without both scales and features
        if not self.mainOperator.Scales.connected() \
        or not self.mainOperator.FeatureIds.connected():
            return
    
        # Access our top group (create it if necessary)
        topGroup = self.getOrCreateGroup(hdf5File, self.TopGroupName)
        
        # Set the version
        if 'StorageVersion' not in topGroup.keys():
            topGroup.create_dataset('StorageVersion', data=self.SerializerVersion)
        else:
            topGroup['StorageVersion'][()] = self.SerializerVersion
        
        # Delete previous entries if they exist
        self.deleteIfPresent(topGroup, 'Scales')
        self.deleteIfPresent(topGroup, 'FeatureIds')
        self.deleteIfPresent(topGroup, 'SelectionMatrix')
        
        # Store the new values (as numpy arrays)
        topGroup.create_dataset('Scales', data=self.mainOperator.Scales.value)
        topGroup.create_dataset('FeatureIds', data=self.mainOperator.FeatureIds.value)
        if self.mainOperator.SelectionMatrix.connected():
            topGroup.create_dataset('SelectionMatrix', data=self.mainOperator.SelectionMatrix.value)

    def deserializeFromHdf5(self, hdf5File, filePath):
        # Check the overall version.
        # We only support v0.6 at the moment.
        ilastikVersion = hdf5File["ilastikVersion"].value
        if ilastikVersion != 0.6:
            return

        # Access the top group and all required datasets
        #  If something is missing we simply return without adding any input to the operator.
        try:
            topGroup = hdf5File[self.TopGroupName]
            scales = topGroup['Scales'].value
            featureIds = topGroup['FeatureIds'].value
        except KeyError:
            return
        
        self.mainOperator.Scales.setValue(scales)
        self.mainOperator.FeatureIds.setValue(featureIds)
        
        # If the matrix isn't there, just return
        try:
            selectionMatrix = topGroup['SelectionMatrix'].value
            self.mainOperator.SelectionMatrix.setValue(selectionMatrix)
            
            # Check matrix dimensions
            assert selectionMatrix.shape[0] == len(featureIds)
            assert selectionMatrix.shape[1] == len(scales)
        except KeyError:
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
        # Unloading shouldn't be necessary for the feature selection applet
        pass

    def getOrCreateGroup(self, parentGroup, groupName):
        try:
            return parentGroup[groupName]
        except KeyError:
            return parentGroup.create_group(groupName)

    def deleteIfPresent(self, parentGroup, name):
        try:
            del parentGroup[name]
        except KeyError:
            pass

if __name__ == "__main__":
    import os
    import numpy
    import h5py
    from lazyflow.graph import Graph
    from opFeatureSelection import OpFeatureSelection

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
    serializer.serializeToHdf5(testProject)
    
    assert (testProject['FeatureSelections/Scales'].value == scales).all()
    assert (testProject['FeatureSelections/FeatureIds'].value == featureIds).all()
    assert (testProject['FeatureSelections/SelectionMatrix'].value == selectionMatrix).all()

    # Deserialize into a fresh operator
    operatorToLoad = OpFeatureSelection(graph=graph)
    deserializer = FeatureSelectionSerializer(operatorToLoad)
    deserializer.deserializeFromHdf5(testProject)
    
    assert (operatorToLoad.Scales.value == scales).all()
    assert (operatorToLoad.FeatureIds.value == featureIds).all()
    assert (operatorToLoad.SelectionMatrix.value == selectionMatrix).all()
























