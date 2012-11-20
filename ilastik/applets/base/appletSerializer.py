from abc import ABCMeta, abstractmethod
from ilastik import VersionManager
from ilastik.utility.simpleSignal import SimpleSignal

#######################################
# utility functions for serialization #
#######################################

def slicingToString(slicing):
    """Convert the given slicing into a string of the form
    '[0:1,2:3,4:5]'

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

def stringToSlicing(strSlicing):
    """Parse a string of the form '[0:1,2:3,4:5]' into a slicing (i.e.
    list of slices)

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



####################################
# the base applet serializer class #
####################################


class AppletSerializer(object):
    """
    Base class for all AppletSerializers.
    """
    __metaclass__ = ABCMeta # Force subclasses to override abstract methods and properties
    
    _base_initialized = False

    ####################
    # Abstract methods #
    ####################

    @abstractmethod
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        """
        Abstract Method.
        Write the applet's data to hdf5.
        
        :param topGroup: The hdf5Group object this serializer is responsible for
        :param hdf5File: An hdf5File object (already open)
        :param projectFilePath: The path to the project file (a string) \
                               (Most serializers don't need to use this parameter)        
        """
        raise NotImplementedError

    @abstractmethod
    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        """
        Abstract Method.
        Read the applet's data from hdf5.
        
        :param topGroup: The hdf5Group object this serializer is responsible for
        :param hdf5File: An hdf5File object (already open)
        :param projectFilePath: The path to the project file (a string) \
                               (Most serializers don't need to use this parameter)        
        """
        raise NotImplementedError

    @abstractmethod
    def isDirty(self):
        """
        Abstract Method.
        Return true if the current state of this item 
        (in memory) does not match the state of the HDF5 group on disk.
        SerializableItems are responsible for tracking their own dirty/notdirty state
        """
        raise NotImplementedError

    @abstractmethod
    def unload(self):
        """
        Abstract Method.
        Called if either
        (1) the user closed the project or
        (2) the project opening process needs to be aborted for some reason \
            (e.g. not all items could be deserialized properly due to a corrupted ilp)
        This way we can avoid invalid state due to a partially loaded project.
        """ 
        raise NotImplementedError

    #############################
    # Base class implementation #
    #############################

    def __init__(self, topGroupName, version):
        """
        Constructor.  Subclasses must call this method in their own __init__ functions.  If they fail to do so, the shell raises an exception.
        """
        self._version = version
        self._topGroupName = topGroupName
        
        self.progressSignal = SimpleSignal() # Signature: emit(percentComplete)

        self._base_initialized = True

    def serializeToHdf5(self, hdf5File, projectFilePath):
        """
        Serialize the current applet state to the given hdf5 file.
        Subclasses should **not** override this method.  Instead, subclasses override the 'private' version, *_serializetoHdf5*
        
        :param hdf5File: An h5py.File handle to the project file, which should already be open
        :param projectFilePath: The path to the given file handle.  (Most serializers do not use this parameter.)

        """
        # Check the overall file version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # Make sure we can find our way around the project tree
        if not VersionManager.isProjectFileVersionCompatible(ilastikVersion):
            return

        self.progressSignal.emit(0)
        
        topGroup = self.getOrCreateGroup(hdf5File, self.topGroupName)
        
        # Set the version
        if 'StorageVersion' not in topGroup.keys():
            topGroup.create_dataset('StorageVersion', data=self._version)
        else:
            topGroup['StorageVersion'][()] = self._version

        try:
            # Call the subclass to do the actual work
            self._serializeToHdf5(topGroup, hdf5File, projectFilePath)
        finally:
            self.progressSignal.emit(100)

    def deserializeFromHdf5(self, hdf5File, projectFilePath):
        """
        Read the the current applet state from the given hdf5File handle, which should already be open.
        Subclasses should **not** override this method.  Instead, subclasses override the 'private' version, *_deserializeFromHdf5*

        :param hdf5File: An h5py.File handle to the project file, which should already be open
        :param projectFilePath: The path to the given file handle.  (Most serializers do not use this parameter.)
        """
        # Check the overall file version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # Make sure we can find our way around the project tree
        if not VersionManager.isProjectFileVersionCompatible(ilastikVersion):
            return

        self.progressSignal.emit(0)

        # If the top group isn't there, call initWithoutTopGroup
        try:
            topGroup = hdf5File[self.topGroupName]
            groupVersion = topGroup['StorageVersion'][()]
        except KeyError:
            topGroup = None
            groupVersion = None

        try:
            if topGroup is not None:
                # Call the subclass to do the actual work
                self._deserializeFromHdf5(topGroup, groupVersion, hdf5File, projectFilePath)
            else:
                self.initWithoutTopGroup(hdf5File, projectFilePath)
        finally:
            self.progressSignal.emit(100)

    #######################
    # Optional methods    #
    #######################

    def initWithoutTopGroup(self, hdf5File, projectFilePath):
        """
        Optional override for subclasses.
        Called when there is no top group to deserialize
        Gives the applet a chance to inspect the hdf5File or project path, even though no top group is present in the file.
        Parameters as the same as in serializeToHdf5()
        """
        pass

    #######################
    # Convenience methods #
    #######################

    @classmethod
    def getOrCreateGroup(cls, parentGroup, groupName):
        """
        Convenience helper.
        Returns parentGorup[groupName], creating first it if necessary.
        """
        try:
            return parentGroup[groupName]
        except KeyError:
            return parentGroup.create_group(groupName)

    @classmethod
    def deleteIfPresent(cls, parentGroup, name):
        """
        Convenience helper.
        Deletes parentGorup[groupName], if it exists.
        """
        try:
            del parentGroup[name]
        except KeyError:
            pass

    @property
    def version(self):
        """
        Return the version of the serializer itself.
        """
        return self._version
    
    @property
    def topGroupName(self):
        return self._topGroupName

    @property
    def base_initialized(self):
        """
        Do not override this property.
        Used by the shell to ensure that Applet.__init__ was called by your subclass.
        """
        return self._base_initialized
