import numpy
from utility.dataImporter import DataImporter

class PixelClassificationSerializer(object):
    """
    Encapsulate the serialization scheme for pixel classification workflow parameters and datasets.
    """
    TopGroupName = 'PixelClassification'
    SerializerVersion = 0.1
    
    def __init__(self, topLevelOperator):
        self.mainOperator = topLevelOperator
    
    def serializeToHdf5(self, hdf5File):
        # The group we were given is the root (file).
        # Check the version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # TODO: Fix this when the version number scheme is more thought out
        if ilastikVersion != 0.6:
            # This class is for 0.6 projects only.
            # v0.5 projects are handled in a different serializer (below).
            return

        # Access our top group (create it if necessary)
        topGroup = self.getOrCreateGroup(hdf5File, self.TopGroupName)
        
        # Set the version
        if 'StorageVersion' not in topGroup.keys():
            topGroup.create_dataset('StorageVersion', data=self.SerializerVersion)
        else:
            topGroup['StorageVersion'][()] = self.SerializerVersion
        
        # Delete all labels from the file
        self.deleteIfPresent(topGroup, 'LabelSets')
        labelSetDir = topGroup.create_group('LabelSets')

        numImages = len(self.mainOperator.NonzeroLabelBlocks)
        for imageIndex in range(numImages):
            # Create a group for this image
            labelGroupName = 'labels{:03d}'.format(imageIndex)
            labelGroup = labelSetDir.create_group(labelGroupName)
            
            # Get a list of slicings that contain labels
            nonZeroBlocks = self.mainOperator.NonzeroLabelBlocks[imageIndex].value
            for blockIndex, slicing in enumerate(nonZeroBlocks):
                # Read the block from the label output
                block = self.mainOperator.LabelImages[imageIndex][slicing].wait()
                
                # Store the block as a new dataset
                blockName = 'block{:04d}'.format(blockIndex)
                labelGroup.create_dataset(blockName, data=block)
                
                # Add the slice this block came from as an attribute of the dataset
                labelGroup[blockName].attrs['blockSlice'] = self.slicingToString(slicing)

    def deserializeFromHdf5(self, hdf5File):
        # Check the overall version.
        # We only support v0.6 at the moment.
        ilastikVersion = hdf5File["ilastikVersion"].value
        if ilastikVersion != 0.6:
            return

        # Access the top group and all required datasets
        #  If something is missing we simply return without adding any input to the operator.
        try:
            topGroup = hdf5File[self.TopGroupName]
            labelSetGroup = topGroup['LabelSets']
        except KeyError:
            return

        numImages = len(labelSetGroup)
        self.mainOperator.LabelInputs.resize(numImages)

        # For each image in the file
        for index, (groupName, labelGroup) in enumerate( sorted(labelSetGroup.items()) ):
            # For each block of label data in the file
            for blockData in labelGroup.values():
                # The location of this label data block within the image is stored as an attribute
                slicing = self.stringToSlicing( blockData.attrs['blockSlice'] )
                # Slice in this data to the label input
                self.mainOperator.LabelInputs[index][slicing] = blockData[...]
        
        # For now, the OpPixelClassification operator has a special signal for notifying the GUI that the label data has changed.
        # In the future, this should be done with some sort of callback on the graph
        self.mainOperator.labelsChangedSignal.emit()

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

    def slicingToString(self, slicing):
        strSlicing = '['
        for s in slicing:
            strSlicing += str(s.start)
            strSlicing += ':'
            strSlicing += str(s.stop)
            strSlicing += ','
        
        # Drop the last comma
        strSlicing = strSlicing[:-1]
        strSlicing += ']'
        return strSlicing
        
    def stringToSlicing(self, strSlicing):
        slicing = []
        # Drop brackets
        strSlicing = strSlicing[1:-1]
        sliceStrings = strSlicing.split(',')
        for s in sliceStrings:
            ends = s.split(':')
            start = int(ends[0])
            stop = int(ends[1])
            slicing.append(slice(start, stop))
        
        return slicing
            

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
