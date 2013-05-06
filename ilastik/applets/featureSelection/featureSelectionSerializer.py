import numpy
import h5py

from ilastik.applets.base.appletSerializer import \
    AppletSerializer, deleteIfPresent

from ilastik.utility import bind

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)

from lazyflow.utility import Tracer

class FeatureSelectionSerializer(AppletSerializer):
    """
    Serializes the user's pixel feature selections to an ilastik v0.6 project file.
    """
    def __init__(self, topLevelOperator, projectFileGroupName):
        super( FeatureSelectionSerializer, self ).__init__( projectFileGroupName)
        self.topLevelOperator = topLevelOperator    
        self._dirty = False

        def handleDirty():
            if not self.ignoreDirty:
                self._dirty = True

        self.topLevelOperator.Scales.notifyDirty( bind(handleDirty) )
        self.topLevelOperator.FeatureIds.notifyDirty( bind(handleDirty) )
        self.topLevelOperator.SelectionMatrix.notifyDirty( bind(handleDirty) )
    
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        with Tracer(traceLogger):
            # Can't store anything without both scales and features
            if not self.topLevelOperator.Scales.ready() \
            or not self.topLevelOperator.FeatureIds.ready():
                return
        
            # Delete previous entries if they exist
            deleteIfPresent(topGroup, 'Scales')
            deleteIfPresent(topGroup, 'FeatureIds')
            deleteIfPresent(topGroup, 'SelectionMatrix')
            deleteIfPresent(topGroup, 'FeatureListFilename')
            
            # Store the new values (as numpy arrays)
            
            topGroup.create_dataset('Scales', data=self.topLevelOperator.Scales.value)
            
            topGroup.create_dataset('FeatureIds', data=self.topLevelOperator.FeatureIds.value)
            
            if self.topLevelOperator.SelectionMatrix.ready():
                topGroup.create_dataset('SelectionMatrix', data=self.topLevelOperator.SelectionMatrix.value)
                
            if self.topLevelOperator.FeatureListFilename.ready():
                fname = str(self.topLevelOperator.FeatureListFilename.value) 
                if fname:
                    topGroup.create_dataset('FeatureListFilename', data=fname)
                
            self._dirty = False

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        with Tracer(traceLogger):
            try:
                scales = topGroup['Scales'].value
                featureIds = topGroup['FeatureIds'].value
                
                scales = list( map(float, scales) )
                featureIds = list( map(str, featureIds) )
            except KeyError:
                pass
            else:
                self.topLevelOperator.Scales.setValue(scales)

                # If the main operator already has a feature ordering (provided by the GUI),
                # then don't overwrite it.  We'll re-order the matrix to match the existing ordering.
                if not self.topLevelOperator.FeatureIds.ready():
                    self.topLevelOperator.FeatureIds.setValue(featureIds)
            
                # If the matrix isn't there, just return
                try:
                    savedMatrix = topGroup['SelectionMatrix'].value                
                    # Check matrix dimensions
                    assert savedMatrix.shape[0] == len(featureIds), "Invalid project data: feature selection matrix dimensions don't make sense"
                    assert savedMatrix.shape[1] == len(scales), "Invalid project data: feature selection matrix dimensions don't make sense"
                except KeyError:
                    pass
                else:
                    # If the feature order has changed since this project was last saved,
                    #  then we need to re-order the features.
                    # The 'new' order is provided by the operator
                    newFeatureOrder = list(self.topLevelOperator.FeatureIds.value)

                    newMatrixShape = ( len(newFeatureOrder), len(scales) )
                    newMatrix = numpy.zeros(newMatrixShape, dtype=bool)
                    for oldFeatureIndex, featureId in enumerate(featureIds):
                        newFeatureIndex = newFeatureOrder.index(featureId)
                        newMatrix[newFeatureIndex] = savedMatrix[oldFeatureIndex]

                    self.topLevelOperator.SelectionMatrix.setValue(newMatrix)
                    
            try:
                ffl = topGroup['FeatureListFilename'].value
                self.topLevelOperator.FeatureListFilename.setValue(ffl)
            except KeyError:
                pass
    
            self._dirty = False

    def isDirty(self):
        """ Return true if the current state of this item 
            (in memory) does not match the state of the HDF5 group on disk.
            SerializableItems are responsible for tracking their own dirty/notdirty state."""
        return self._dirty

    def unload(self):
        with Tracer(traceLogger):
            self.topLevelOperator.SelectionMatrix.disconnect()

class Ilastik05FeatureSelectionDeserializer(AppletSerializer):
    """
    Deserializes the user's pixel feature selections from an ilastik v0.5 project file.
    """
    def __init__(self, topLevelOperator):
        super( Ilastik05FeatureSelectionDeserializer, self ).__init__( '' )
        self.topLevelOperator = topLevelOperator
    
    def serializeToHdf5(self, hdf5File, filePath):
        # This class is only for DEserialization
        pass

    def deserializeFromHdf5(self, hdf5File, filePath):
        with Tracer(traceLogger):
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
    
            self.topLevelOperator.Scales.setValue(ScalesList)
            # If the main operator already has a feature ordering (provided by the GUI),
            # then don't overwrite it.  We'll re-order the matrix to match the existing ordering.
            if not self.topLevelOperator.FeatureIds.ready():
                self.topLevelOperator.FeatureIds.setValue(FeatureIds)
    
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
                featureToGroup = { 'GaussianSmoothing'              : 0,  # Gaussian Smoothing -> Color
                                   'LaplacianOfGaussian'            : 1,  # Laplacian of Gaussian -> Edge
                                   'StructureTensorEigenvalues'     : 3,  # Structure Tensor Eigenvalues -> Texture
                                   'HessianOfGaussianEigenvalues'   : 3,  # Eigenvalues of Hessian of Gaussian -> Texture
                                   'GaussianGradientMagnitude'      : 1,  # Gradient Magnitude of Gaussian -> Edge
                                   'DifferenceOfGaussians'          : 1 } # Difference of Gaussians -> Edge
    

                newFeatureIds = self.topLevelOperator.FeatureIds.value
                # For each feature, determine which group's settings to take
                for featureId, featureGroupIndex in featureToGroup.items():
                    newRow = newFeatureIds.index(featureId)
                    # Copy the whole row of selections from the feature group
                    pipeLineSelectedFeatureMatrix[newRow] = userFriendlyFeatureMatrix[featureGroupIndex]
            
            # Finally, update the pipeline with the feature selections
            self.topLevelOperator.SelectionMatrix.setValue( pipeLineSelectedFeatureMatrix )

    def isDirty(self):
        """ Return true if the current state of this item 
            (in memory) does not match the state of the HDF5 group on disk.
            SerializableItems are responsible for tracking their own dirty/notdirty state."""
        return False

    def unload(self):
        with Tracer(traceLogger):
            self.topLevelOperator.SelectionMatrix.disconnect()


    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        assert False

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        # This deserializer is a special-case.
        # It doesn't make use of the serializer base class, which makes assumptions about the file structure.
        # Instead, if overrides the public serialize/deserialize functions directly
        assert False











