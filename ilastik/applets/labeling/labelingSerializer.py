from ilastik.applets.base.appletSerializer import \
    AppletSerializer, stringToSlicing, slicingToString

class LabelingSerializer(AppletSerializer):
    """
    Encapsulate the serialization scheme for pixel classification workflow parameters and datasets.
    """
    SerializerVersion = 0.1
    
    def __init__(self, mainOperator, projectFileGroupName):
        super( LabelingSerializer, self ).__init__( projectFileGroupName, self.SerializerVersion )
        self.mainOperator = mainOperator
        self._dirty = False
    
        # Set up handlers for dirty detection
        def handleDirty(slot, *args):
            self._dirty = True
    
        def handleNewImage(slot, index, *args):
            slot[index].notifyDirty( handleDirty )
    
        # These are multi-slots, so subscribe to dirty callbacks on each of their subslots as they are created
        self.mainOperator.LabelImages.notifyInserted( handleNewImage )
                
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
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
                labelGroup[blockName].attrs['blockSlice'] = slicingToString(slicing)

        self._dirty = False

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        labelSetGroup = topGroup['LabelSets']
        numImages = len(labelSetGroup)
        self.mainOperator.LabelInputs.resize(numImages)

        # For each image in the file
        for index, (groupName, labelGroup) in enumerate( sorted(labelSetGroup.items()) ):
            # For each block of label data in the file
            for blockData in labelGroup.values():
                # The location of this label data block within the image is stored as an hdf5 attribute
                slicing = stringToSlicing( blockData.attrs['blockSlice'] )
                # Slice in this data to the label input
                self.mainOperator.LabelInputs[index][slicing] = blockData[...]

        self._dirty = False

    def isDirty(self):
        """
        Return true if the current state of this item 
        (in memory) does not match the state of the HDF5 group on disk.
        """
        return self._dirty

    def unload(self):
        """
        Called if either
        (1) the user closed the project or
        (2) the project opening process needs to be aborted for some reason
            (e.g. not all items could be deserialized properly due to a corrupted ilp)
        This way we can avoid invalid state due to a partially loaded project. """ 
        self.mainOperator.LabelInputs.resize(0)
        self._dirty = False

