import numpy

from opSeededWatershed import GCSegmentor, MSTSegmentorKruskal, MSTSegmentor, PerturbMSTSegmentor

class SeededWatershedSerializer(object):
    """
    Encapsulate the serialization scheme for pixel classification workflow parameters and datasets.
    """
    TopGroupName = 'InteractiveSeededWatershed'
    SerializerVersion = 0.1
    
    def __init__(self, topLevelOperator):
        self.mainOperator = topLevelOperator
    
    def serializeToHdf5(self, hdf5File, filePath):
        print "===================================  segmentor serialize ========================================"
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
        self.deleteIfPresent(topGroup, 'segmentors')
        segDir = topGroup.create_group('segmentors')

        numImages = len(self.mainOperator.image)
        for imageIndex in range(numImages):
            # Create a group for this image
            segGroupName = 'segmentor{:03d}'.format(imageIndex)
            segGroup = segDir.create_group(segGroupName)

            mst = self.mainOperator.segmentor[imageIndex].value

            mst.saveH5G(segGroup)
            

    def deserializeFromHdf5(self, hdf5File, filePath):
        print "===================================  segmentor deserialize ========================================"
        # Check the overall version.
        # We only support v0.6 at the moment.
        ilastikVersion = hdf5File["ilastikVersion"].value
        if ilastikVersion != 0.6:
            return

        # Access the top group and all required datasets
        #  If something is missing we simply return without adding any input to the operator.
        try:
            topGroup = hdf5File[self.TopGroupName]
        except KeyError:
            return

        segDir = topGroup["segmentors"]
        numImages = len(segDir)
        self.mainOperator.initial_segmentor.resize(numImages)
       
        # For each image in the file
        for index, (groupName, group) in enumerate( sorted(segDir.items()) ):
          mst = MSTSegmentor.loadH5G(group)
          self.mainOperator.initial_segmentor[index].setValue(mst)






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
