import numpy

class PixelClassificationSerializer(object):
    """
    Encapsulate the serialization scheme for pixel classification workflow parameters and datasets.
    """
    def __init__(self, pipeline):
        self.pipeline = pipeline
    
    def serializeToHdf5(self, hdf5Group):
        pass
    
    def deserializeFromHdf5(self, hdf5Group):
        # The group we were given is the root (file).
        # Check the version
        ilastikVersion = hdf5Group["ilastikVersion"].value

        # TODO: Fix this when the version number scheme is more thought out
        if ilastikVersion != 0.6:
            # This class is for 0.6 projects only.
            # v0.5 projects are handled in a different serializer (below).
            return

    def isDirty(self):
        """
        Return true if the current state of this item 
        (in memory) does not match the state of the HDF5 group on disk.
        """
        return True

    def unload(self):
        """
        Called if either
        (1) the user closed the project or
        (2) the project opening process needs to be aborted for some reason
            (e.g. not all items could be deserialized properly due to a corrupted ilp)
        This way we can avoid invalid state due to a partially loaded project. """ 
        pass

class Ilastik05ImportDeserializer(object):
    """
    Special (de)serializer for importing ilastik 0.5 projects.
    For now, this class is import-only.  Only the deserialize function is implemented.
    If the project is not an ilastik0.5 project, this serializer does nothing.
    """
    def __init__(self, pipeline):
        self.pipeline = pipeline
    
    def serializeToHdf5(self, hdf5Group):
        """Not implemented. (See above.)"""
        pass
    
    def deserializeFromHdf5(self, hdf5File):
        """If (and only if) the given hdf5Group is the root-level group of an 
           ilastik 0.5 project, then the project is imported.  The pipeline is updated 
           with the saved parameters and datasets."""
        # The group we were given is the root (file).
        # Check the version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # The pixel classification workflow supports importing projects in the old 0.5 format
        if ilastikVersion == 0.5:
            print "Deserializing ilastik 0.5 project..."
            self.importProjectAttributes(hdf5File) # (e.g. description, labeler, etc.)
            self.importDataSets(hdf5File)
            self.importLabelSets(hdf5File)
            self.importFeatureSelections(hdf5File)
            self.importClassifier(hdf5File)
    
    def importProjectAttributes(self, hdf5File):
        description = hdf5File["Project"]["Description"].value
        labeler = hdf5File["Project"]["Labeler"].value
        name = hdf5File["Project"]["Name"].value
        # TODO: Actually store these values and show them in the GUI somewhere . . .
        
    def importFeatureSelections(self, hdf5File):
        """
        Import the feature selections from the v0.5 project file
        """
        # Create a feature selection matrix of the correct shape (all false by default)
        # TODO: The shape shouldn't be hard-coded.
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
            assert( userFriendlyFeatureMatrix.shape == (4, 7) )
            # Here's how features map to the old "feature groups"
            # (Note: Nothing maps to the orientation group.)
            # TODO: It is terrible that these indexes are hard-coded.
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
        self.pipeline.features.inputs['Matrix'].setValue( pipeLineSelectedFeatureMatrix )
        
    def importClassifier(self, hdf5File):
        """
        Import the random forest classifier (if any) from the v0.5 project file.
        """
        # Not implemented:
        # ilastik 0.5 can SAVE the RF, but it can't load it back (vigra doesn't provide a function for that).
        # For now, we simply emulate that behavior.
        # (Technically, v0.5 would retrieve the user's "number of trees" setting, 
        #  but this applet doesn't expose that setting to the user anyway.)
        pass
        
    def importDataSets(self, hdf5File):
        """
        Locate the raw input data from the v0.5 project file and give it to our pipeline.
        """
        # Locate the dataset within the hdf5File
        try:
            dataset = hdf5File["DataSets"]["dataItem00"]["data"]
        except KeyError:
            pass
        else:
            importer = DataImporter(self.pipeline.graph)
            inputProvider = importer.createArrayPiperFromHdf5Dataset(dataset)
        
            # Connect the new input operator to our pipeline
            #  (Pipeline signals the GUI.)
            self.pipeline.setInputData(inputProvider)
    
    def importLabelSets(self, hdf5File):
        try:
            data = hdf5File['DataSets/dataItem00/labels/data'].value
            print "data[0,0,0,0,0] = ", data[0,0,0,0,0]
        except KeyError:
            return # We'll get a KeyError if this project doesn't contain stored data.  That's allowed.
                
        self.pipeline.setAllLabelData(data)

        print "Pipeline labels: ", self.pipeline.getUniqueLabels()
    
    def isDirty(self):
        """Always returns False because we don't support saving to ilastik0.5 projects"""
        return False

    def unload(self):
        """ Called if either
            (1) the user closed the project or
            (2) the project opening process needs to be aborted for some reason
                (e.g. not all items could be deserialized properly due to a corrupted ilp)
            This way we can avoid invalid state due to a partially loaded project. """ 
        pass
