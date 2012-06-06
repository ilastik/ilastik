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
    
    def serializeToHdf5(self, hdf5File, filePath):
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
            labelSetGroup = topGroup['LabelSets']
        except KeyError:
            # There's no label data in the project.  Make sure the operator doesn't have any label data.
            self.mainOperator.LabelInputs.resize(0)
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
        """
        Convert the given slicing into a string of the form '[0:1,2:3,4:5]'
        """
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
        """
        Parse a string of the form '[0:1,2:3,4:5]' into a slicing (i.e. list of slices)
        """
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
        return False

    def unload(self):
        """
        Called if either
        (1) the user closed the project or
        (2) the project opening process needs to be aborted for some reason
            (e.g. not all items could be deserialized properly due to a corrupted ilp)
        This way we can avoid invalid state due to a partially loaded project. """ 
        self.mainOperator.LabelInputs.resize(0)

class Ilastik05ImportDeserializer(object):
    """
    Special (de)serializer for importing ilastik 0.5 projects.
    For now, this class is import-only.  Only the deserialize function is implemented.
    If the project is not an ilastik0.5 project, this serializer does nothing.
    """
    def __init__(self, topLevelOperator):
        self.mainOperator = topLevelOperator
    
    def serializeToHdf5(self, hdf5Group, projectFilePath):
        """Not implemented. (See above.)"""
        pass
    
    def deserializeFromHdf5(self, hdf5File, projectFilePath):
        """If (and only if) the given hdf5Group is the root-level group of an 
           ilastik 0.5 project, then the project is imported.  The pipeline is updated 
           with the saved parameters and datasets."""
        # The group we were given is the root (file).
        # Check the version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # The pixel classification workflow supports importing projects in the old 0.5 format
        if ilastikVersion == 0.5:
            numImages = len(hdf5File['DataSets'])
            self.mainOperator.LabelInputs.resize(numImages)

            for index, (datasetName, datasetGroup) in enumerate( sorted( hdf5File['DataSets'].items() ) ):
                try:
                    dataset = datasetGroup['labels/data']
                except KeyError:
                    # We'll get a KeyError if this project doesn't have labels for this dataset.
                    # That's allowed, so we simply continue.
                    continue
                self.mainOperator.LabelInputs[index][...] = dataset.value[...]

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
    
    def isDirty(self):
        """Always returns False because we don't support saving to ilastik0.5 projects"""
        return False

    def unload(self):
        # This is a special-case import deserializer.  Let the real deserializer handle unloading.
        pass 

