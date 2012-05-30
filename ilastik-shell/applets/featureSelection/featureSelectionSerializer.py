import numpy

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
            # There's no data in the project, so make sure the operator has no inputs.
            self.mainOperator.Scales.setValue(None)
            self.mainOperator.FeatureIds.setValue(None)
            self.mainOperator.SelectionMatrix.setValue(None)
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
        self.mainOperator.Scales.setValue(None)
        self.mainOperator.FeatureIds.setValue(None)
        self.mainOperator.SelectionMatrix.setValue(None)

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

class Ilastik05FeatureSelectionDeserializer(object):
    """
    Deserializes the user's pixel feature selections from an ilastik v0.5 project file.
    """
    def __init__(self, mainOperator):
        self.mainOperator = mainOperator
    
    def serializeToHdf5(self, hdf5File, filePath):
        # This class is only for DEserialization
        pass

    def deserializeFromHdf5(self, hdf5File, filePath):
        # Check the overall file version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # This is the v0.5 import deserializer.  Don't work with 0.6 projects (or anything else).
        if ilastikVersion != 0.5:
            return

        # Use the hard-coded ilastik v0.5 scales and feature ids
        ScalesList = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
        FeatureIds = [ 'GaussianSmoothing',
                       'LaplacianOfGaussian',
                       'StructureTensorEigenvalues',
                       'HessianOfGaussianEigenvalues',
                       'GaussianGradientMagnitude',
                       'DifferenceOfGaussians' ]

        self.mainOperator.Scales.setValue(ScalesList)
        self.mainOperator.FeatureIds.setValue(FeatureIds)

        # Create a feature selection matrix of the correct shape (all false by default)
        pipeLineSelectedFeatureMatrix = numpy.array(numpy.zeros((6,7)), dtype=bool)

        try:
            # In ilastik 0.5, features were grouped into user-friendly selections.  We have to split these 
            #  selections apart again into the actual features that must be computed.
            userFriendlyFeatureMatrix = hdf5File['Project']['FeatureSelection']['UserSelection'].value
        except KeyError:
            # If the project file doesn't specify feature selections,
            #  we'll just use the default (blank) selections as initialized above
            pass
        else:
            # Number of feature types must be correct or something is totally wrong
            assert userFriendlyFeatureMatrix.shape[0] == 4

            # Some older versions of ilastik had only 6 scales.            
            # Add columns of zeros until we have 7 columns.
            while userFriendlyFeatureMatrix.shape[1] < 7:
                userFriendlyFeatureMatrix = numpy.append( userFriendlyFeatureMatrix, numpy.zeros((4, 1), dtype=bool), axis=1 )
            
            # Here's how features map to the old "feature groups"
            # (Note: Nothing maps to the orientation group.)
            featureToGroup = { 0 : 0,  # Gaussian Smoothing -> Color
                               1 : 1,  # Laplacian of Gaussian -> Edge
                               2 : 3,  # Structure Tensor Eigenvalues -> Texture
                               3 : 3,  # Eigenvalues of Hessian of Gaussian -> Texture
                               4 : 1,  # Gradient Magnitude of Gaussian -> Edge
                               5 : 1 } # Difference of Gaussians -> Edge

            # For each feature, determine which group's settings to take
            for featureIndex, featureGroupIndex in featureToGroup.items():
                # Copy the whole row of selections from the feature group
                pipeLineSelectedFeatureMatrix[featureIndex] = userFriendlyFeatureMatrix[featureGroupIndex]
        
        # Finally, update the pipeline with the feature selections
        self.mainOperator.SelectionMatrix.setValue( pipeLineSelectedFeatureMatrix )

    def isDirty(self):
        """ Return true if the current state of this item 
            (in memory) does not match the state of the HDF5 group on disk.
            SerializableItems are responsible for tracking their own dirty/notdirty state."""
        pass

    def unload(self):
        self.mainOperator.Scales.setValue(None)
        self.mainOperator.FeatureIds.setValue(None)
        self.mainOperator.SelectionMatrix.setValue(None)

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
























