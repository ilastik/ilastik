from abc import ABCMeta, abstractmethod
from ilastik import VersionManager
from ilastik.utility.simpleSignal import SimpleSignal

class AppletSerializer(object):
    __metaclass__ = ABCMeta # Force subclasses to override abstract methods and properties
    
    _base_initialized = False

    ####################
    # Abstract methods #
    ####################

    @abstractmethod
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        """
        Write the applet's data to hdf5.
        Args:
            topGroup -- The hdf5Group object this serializer is responsible for
            hdf5File -- An hdf5File object (already open)
            projectFilePath -- The path to the project file (a string)
                               (Most serializers don't need to use this parameter)        
        """
        raise NotImplementedError

    @abstractmethod
    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        """
        Read the applet's data from hdf5.
        Args:
            topGroup -- The hdf5Group object this serializer is responsible for
            hdf5File -- An hdf5File object (already open)
            projectFilePath -- The path to the project file (a string)
                               (Most serializers don't need to use this parameter)        
        """
        raise NotImplementedError

    @abstractmethod
    def isDirty(self):
        """
        Return true if the current state of this item 
        (in memory) does not match the state of the HDF5 group on disk.
        SerializableItems are responsible for tracking their own dirty/notdirty state
        """
        raise NotImplementedError

    @abstractmethod
    def unload(self):
        """
        Called if either
        (1) the user closed the project or
        (2) the project opening process needs to be aborted for some reason
            (e.g. not all items could be deserialized properly due to a corrupted ilp)
        This way we can avoid invalid state due to a partially loaded project.
        """ 
        raise NotImplementedError

    #######################
    # Optional methods    #
    #######################

    def initWithoutTopGroup(self, hdf5File, projectFilePath):
        """
        Optional override for subclasses.
        Called when there is no top group to deserialize
        Gives the applet a chance to inspect the hdf5File or project path, even though no top group is present in the file.
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

    #############################
    # Base class implementation #
    #############################

    def __init__(self, topGroupName, version):
        self._version = version
        self._topGroupName = topGroupName
        
        self.progressSignal = SimpleSignal() # Signature: emit(percentComplete)

        self._base_initialized = True

    def serializeToHdf5(self, hdf5File, projectFilePath):
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

    @property
    def base_initialized(self):
        """
        Do not override this property.
        Used by the shell to ensure that Applet.__init__ was called by your subclass.
        """
        return self._base_initialized
