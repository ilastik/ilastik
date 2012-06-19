import numpy

from ilastikshell.appletSerializer import AppletSerializer

class FeatureSelectionSerializer(AppletSerializer):
    """
    Serializes the user's pixel feature selections to an ilastik v0.6 project file.
    """
    SerializerVersion = 0.1
    
    def __init__(self, mainOperator, projectFileGroupName):
        super( FeatureSelectionSerializer, self ).__init__( projectFileGroupName, self.SerializerVersion )
        self.mainOperator = mainOperator
    
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        # Can't store anything without both scales and features
        if not self.mainOperator.Scales.connected() \
        or not self.mainOperator.FeatureIds.connected():
            return
    
        # Delete previous entries if they exist
        self.deleteIfPresent(topGroup, 'Scales')
        self.deleteIfPresent(topGroup, 'FeatureIds')
        self.deleteIfPresent(topGroup, 'SelectionMatrix')
        
        # Store the new values (as numpy arrays)
        topGroup.create_dataset('Scales', data=self.mainOperator.Scales.value)
        topGroup.create_dataset('FeatureIds', data=self.mainOperator.FeatureIds.value)
        if self.mainOperator.SelectionMatrix.connected():
            topGroup.create_dataset('SelectionMatrix', data=self.mainOperator.SelectionMatrix.value)

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        if topGroup is None:
            return
        # These keys are guaranteed to be present if we have a group at all 
        scales = topGroup['Scales'].value
        featureIds = topGroup['FeatureIds'].value
        
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
        return False

    def unload(self):
        self.mainOperator.Scales.disconnect()
        self.mainOperator.FeatureIds.disconnect()
        self.mainOperator.SelectionMatrix.disconnect()

class Ilastik05FeatureSelectionDeserializer(AppletSerializer):
    """
    Deserializes the user's pixel feature selections from an ilastik v0.5 project file.
    """
    SerializerVersion = 0.1
    def __init__(self, mainOperator):
        super( Ilastik05FeatureSelectionDeserializer, self ).__init__( '', self.SerializerVersion )
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
        return False

    def unload(self):
        self.mainOperator.Scales.disconnect()
        self.mainOperator.FeatureIds.disconnect()
        self.mainOperator.SelectionMatrix.disconnect()


    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        assert False

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        # This deserializer is a special-case.
        # It doesn't make use of the serializer base class, which makes assumptions about the file structure.
        # Instead, if overrides the public serialize/deserialize functions directly
        assert False











