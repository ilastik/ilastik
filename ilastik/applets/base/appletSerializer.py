from abc import ABCMeta, abstractmethod
from ilastik import isVersionCompatible
from ilastik.utility.simpleSignal import SimpleSignal
from ilastik.utility.maybe import maybe
import os
import tempfile
import vigra
import h5py
import numpy

#######################
# Convenience methods #
#######################

def getOrCreateGroup(parentGroup, groupName):
    """Returns parentGorup[groupName], creating first it if
    necessary.

    """
    try:
        return parentGroup[groupName]
    except KeyError:
        return parentGroup.create_group(groupName)

def deleteIfPresent(parentGroup, name):
    """Deletes parentGorup[groupName], if it exists."""
    try:
        del parentGroup[name]
    except KeyError:
        pass

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

    strSlicing = strSlicing[:-1] # Drop the last comma
    strSlicing += ']'
    return strSlicing

def stringToSlicing(strSlicing):
    """Parse a string of the form '[0:1,2:3,4:5]' into a slicing (i.e.
    list of slices)

    """
    slicing = []
    strSlicing = strSlicing[1:-1] # Drop brackets
    sliceStrings = strSlicing.split(',')
    for s in sliceStrings:
        ends = s.split(':')
        start = int(ends[0])
        stop = int(ends[1])
        slicing.append(slice(start, stop))

    return slicing


class SerialSlot(object):
    """Implements the logic for serializing a slot."""
    def __init__(self, slot, name=None, default=None, depends=None,
                 autodepends=True):
        """
        :param slot: the slot to save/load

        :param name: name used for the group in the hdf5 file.

            - For level 0 slots, this should just be a string, or None to
              use the slot's name.

            - For level 1 slots, this should be a tuple (groupname,
              subname), or None. If provided, subname should be able to be
              format()ed with a single argument: the index of the subslot.

        :param default: the default value when unload() is called. If it is
          None, the slot will just be disconnected (for level 0 slots) or
          resized to length 0 (for multislots)

        :param depends: a list of slots which must be ready before this slot
          can be serialized. If None, defaults to [].

        :param autodepends: whether 'slot' should be added to 'depends'

        """
        if slot.level > 1:
            # FIXME: recursive serialization, to support arbitrary levels
            raise Exception('slots of levels > 1 not supported')
        self.slot = slot
        self.default = default
        self.depends = maybe(depends, [])
        if autodepends:
            self.depends.append(slot)
        if name is None:
            if slot.level == 0:
                name = slot.name
            else:
                name = slot.name, "{0}"

        if slot.level == 0:
            self.name = name
        else:
            self.name, self.subname = name

        self._dirty = False
        self._bind()

    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, value):
        self._dirty = value

    def setDirty(self, *args, **kwargs):
        self.dirty = True

    def _bind(self, slot=None):
        """Setup so that when slot is dirty, set appropriate dirty
        flag.

        """
        slot = maybe(slot, self.slot)

        def doMulti(slot, index, size):
            slot[index].notifyDirty(self.setDirty)

        if slot.level == 0:
            slot.notifyDirty(self.setDirty)
        else:
            slot.notifyInserted(doMulti)

    def shouldSerialize(self, group):
        """Whether to serialize or not."""
        result = self.dirty
        result |= self.name not in group.keys()
        for s in self.depends:
            result &= s.ready()
        return result

    def serialize(self, group):
        """Performs tasks common to all serializations, like changing
        dirty status.

        Do not override (unless for some reason this function does not
        do the right thing in your case). Instead override
        _serialize().

        :param group: The parent group in which to create this slot's
            group.
        :type group: h5py.Group

        """
        if not self.shouldSerialize(group):
            return
        deleteIfPresent(group, self.name)
        self._serialize(group)
        self.dirty = False

    @staticmethod
    def _saveValue(group, name, value):
        """Seperate so that subclasses can override, if necessary.

        For instance, SerialListSlot needs to save an extra attribute
        if the value is an empty list.

        """
        group.create_dataset(name, data=value)

    def _serialize(self, group):
        """"
        :param group: The parent group.
        :type group: h5py.Group

        """
        if self.slot.level == 0:
            self._saveValue(group, self.name, self.slot.value)
        else:
            subgroup = group.create_group(self.name)
            for i, subslot in enumerate(self.slot):
                subname = self.subname.format(i)
                self._saveValue(subgroup, subname, self.slot[i].value)

    def deserialize(self, group):
        """Performs tasks common to all deserializations.

        Do not override (unless for some reason this function does not
        do the right thing in your case). Instead override
        _deserialize.

        :param group: The parent group in which to create this slot's
            group.
        :type group: h5py.Group

        """
        if not self.name in group:
            return
        self._deserialize(group[self.name])
        self.dirty = False

    def _deserialize(self, subgroup):
        """
        :param subgroup: *not* the parent group. This slot's group.
        :typpe subgroup: h5py.Group

        """
        if self.slot.level == 0:
            val = subgroup[()]
            self.slot.setValue(val)
        else:
            self.slot.resize(len(subgroup))
            for i, key in enumerate(subgroup):
                val = subgroup[key][()]
                self.slot[i].setValue(val)

    def unload(self):
        """see AppletSerializer.unload()"""
        if self.slot.level == 0:
            if self.default is None:
                self.slot.disconnect()
            else:
                self.slot.setValue(self.default)
        else:
            self.slot.resize(0)


#######################################################
# some serial slots that are used in multiple applets #
#######################################################

class SerialListSlot(SerialSlot):
    """As the name implies: used for serializing a list.

    The only differences from the base class are:

    - if deserializing fails, sets the slot value to [].

    - if it succeeds, applies a transform to every element of the list
      (for instance, to convert it to the proper type).

    """
    def __init__(self, slot, name=None, default=None, depends=None,
                 autodepends=False, transform=None):
        """
        :param transform: function applied to members on deserialization.

        """
        if slot.level > 0:
            raise NotImplementedError()

        super(SerialListSlot, self).__init__(slot, name, default, depends,
                                             autodepends)
        if transform is None:
            transform = lambda x: x
        self.transform = transform

    @staticmethod
    def _saveValue(group, name, value):
        isempty = (len(value) == 0)
        if isempty:
            value = numpy.empty((1,))
        sg = group.create_dataset(name, data=value)
        sg.attrs['isEmpty'] = isempty

    def deserialize(self, group):
        try:
            subgroup = group[self.name]
        except KeyError:
            self.unload()
        else:
            if 'isEmpty' in subgroup.attrs and subgroup.attrs['isEmpty']:
                self.unload()
            else:
                try:
                    self.slot.setValue(list(map(self.transform, subgroup[()])))
                except:
                    self.unload()
        finally:
            self.dirty = False

    def unload(self):
        if self.slot.level == 0:
            self.slot.setValue([])
        else:
            self.slot.resize(0)
        self.dirty = False


class SerialBlockSlot(SerialSlot):
    """A slot which only saves nonzero blocks."""
    def __init__(self, inslot, outslot, blockslot, name=None, default=None,
                 depends=None, autodepends=False):
        """
        :param inslot: where to put deserialized data.
        :param outslot: where to take data for serialization.
        :param blockslot: provides non-zero blocks.

        """
        super(SerialBlockSlot, self).__init__(inslot, name, default,
                                              depends, autodepends)
        self.inslot = inslot
        self.outslot = outslot
        self.blockslot = blockslot
        self._bind(outslot)

    def _serialize(self, group):
        mygroup = group.create_group(self.name)
        num = len(self.blockslot)
        for index in range(num):
            subsubname = self.subname.format(index)
            subsubgroup = mygroup.create_group(subsubname)
            nonZeroBlocks = self.blockslot[index].value
            for blockIndex, slicing in enumerate(nonZeroBlocks):
                block = self.outslot[index][slicing].wait()
                blockName = 'block{:04d}'.format(blockIndex)
                subsubgroup.create_dataset(blockName, data=block)
                subsubgroup[blockName].attrs['blockSlice'] = slicingToString(slicing)

    def _deserialize(self, mygroup):
        num = len(mygroup)
        self.inslot.resize(num)
        for index, t in enumerate(sorted(mygroup.items())):
            groupName, labelGroup = t
            for blockData in labelGroup.values():
                slicing = stringToSlicing(blockData.attrs['blockSlice'])
                self.inslot[index][slicing] = blockData[...]


class SerialClassifierSlot(SerialSlot):
    """For saving a random forest classifier."""
    def __init__(self, slot, cacheslot, name=None, default=None,
                 depends=None, autodepends=True):
        super(SerialClassifierSlot, self).__init__(slot, name,
                                                   default, depends,
                                                   autodepends)
        self.cacheslot = cacheslot
        if self.name is None:
            self.name = slot.name
            self.subname = "Forest{:04d}"
        self.name, self.subname = name

    def unload(self):
        self.cacheslot.Input.setDirty(slice(None))

    def _serialize(self, group):
        classifier_forests = self.slot.value

        # Classifier can be None if there isn't any training data yet.
        if classifier_forests is None:
            return
        for forest in classifier_forests:
            if forest is None:
                return

        # Due to non-shared hdf5 dlls, vigra can't write directly to
        # our open hdf5 group. Instead, we'll use vigra to write the
        # classifier to a temporary file.
        tmpDir = tempfile.mkdtemp()
        cachePath = os.path.join(tmpDir, 'tmp_classifier_cache.h5')
        for i, forest in enumerate(classifier_forests):
            targetname = '{0}/{1}'.format(self.name, self.subname.format(i))
            forest.writeHDF5(cachePath, targetname)

        # Open the temp file and copy to our project group
        with h5py.File(cachePath, 'r') as cacheFile:
            group.copy(cacheFile[self.name], self.name)

        os.remove(cachePath)
        os.removedirs(tmpDir)

    def deserialize(self, group):
        """
        Have to override this to ensure that dirty is always set False.
        """
        super(SerialClassifierSlot, self).deserialize(group)
        self.dirty = False

    def _deserialize(self, classifierGroup):
        # Due to non-shared hdf5 dlls, vigra can't read directly
        # from our open hdf5 group. Instead, we'll copy the
        # classfier data to a temporary file and give it to vigra.
        tmpDir = tempfile.mkdtemp()
        cachePath = os.path.join(tmpDir, 'tmp_classifier_cache.h5')
        with h5py.File(cachePath, 'w') as cacheFile:
            cacheFile.copy(classifierGroup, self.name)

        forests = []
        for name, forestGroup in sorted(classifierGroup.items()):
            targetname = '{0}/{1}'.format(self.name, name)
            forests.append(vigra.learning.RandomForest(cachePath, targetname))

        os.remove(cachePath)
        os.removedirs(tmpDir)

        # Now force the classifier into our classifier cache. The
        # downstream operators (e.g. the prediction operator) can
        # use the classifier without inducing it to be re-trained.
        # (This assumes that the classifier we are loading is
        # consistent with the images and labels that we just
        # loaded. As soon as training input changes, it will be
        # retrained.)
        self.cacheslot.forceValue(numpy.array(forests))


####################################
# the base applet serializer class #
####################################

class AppletSerializer(object):
    """
    Base class for all AppletSerializers.
    """
    # Force subclasses to override abstract methods and properties
    __metaclass__ = ABCMeta
    base_initialized = False

    # override if necessary
    version = "0.1"

    #########################
    # Semi-abstract methods #
    #########################

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):

        """Child classes should override this function, if
        necessary.

        """
        pass

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File,
                             projectFilePath):
        """Child classes should override this function, if
        necessary.

        """
        pass

    #############################
    # Base class implementation #
    #############################

    def __init__(self, topGroupName, slots=None, operator=None):
        """Constructor. Subclasses must call this method in their own
        __init__ functions. If they fail to do so, the shell raises an
        exception.

        Parameters:
        :param topGroupName: name of this applet's data group in the file.
            Defaults to the name of the operator.
        :param slots: a list of SerialSlots

        """
        self.progressSignal = SimpleSignal() # Signature: emit(percentComplete)
        self.base_initialized = True
        self.topGroupName = topGroupName
        self.serialSlots = maybe(slots, [])
        self.operator=operator

    def isDirty(self):
        """Returns true if the current state of this item (in memory)
        does not match the state of the HDF5 group on disk.

        Subclasses only need override this method if ORing the flags
        is not enough.

        """
        return any(list(ss.dirty for ss in self.serialSlots))

    def unload(self):
        """Called if either

        (1) the user closed the project or

        (2) the project opening process needs to be aborted for some
            reason (e.g. not all items could be deserialized
            properly due to a corrupted ilp)

        This way we can avoid invalid state due to a partially loaded
        project.

        """
        for ss in self.serialSlots:
            ss.unload()

    def progressIncrement(self, group=None):
        """Get the percentage progress for each slot.

        :param group: If None, all all slots are assumed to be
            processed. Otherwise, decides for each slot by calling
            slot.shouldSerialize(group).

        """
        if group is None:
            nslots = len(self.serialSlots)
        else:
            nslots = sum(ss.shouldSerialize(group) for ss in self.serialSlots)
        if nslots == 0:
            return 0
        return divmod(100, nslots)[0]

    def serializeToHdf5(self, hdf5File, projectFilePath):
        """Serialize the current applet state to the given hdf5 file.

        Subclasses should **not** override this method. Instead,
        subclasses override the 'private' version, *_serializetoHdf5*

        :param hdf5File: An h5py.File handle to the project file,
            which should already be open

        :param projectFilePath: The path to the given file handle.
            (Most serializers do not use this parameter.)

        """
        # Check the overall file version
        fileVersion = hdf5File["ilastikVersion"].value

        # Make sure we can find our way around the project tree
        if not isVersionCompatible(fileVersion):
            return

        topGroup = getOrCreateGroup(hdf5File, self.topGroupName)

        self.progressSignal.emit(0)

        # Set the version
        key = 'StorageVersion'
        deleteIfPresent(topGroup, key)
        topGroup.create_dataset(key, data=self.version)

        try:
            inc = self.progressIncrement(topGroup)
            for ss in self.serialSlots:
                ss.serialize(topGroup)
                self.progressSignal.emit(inc)

            # Call the subclass to do remaining work, if any
            self._serializeToHdf5(topGroup, hdf5File, projectFilePath)
        finally:
            self.progressSignal.emit(100)


    def deserializeFromHdf5(self, hdf5File, projectFilePath):
        """Read the the current applet state from the given hdf5File
        handle, which should already be open.

        Subclasses should **not** override this method. Instead,
        subclasses override the 'private' version,
        *_deserializeFromHdf5*

        :param hdf5File: An h5py.File handle to the project file,
            which should already be open

        :param projectFilePath: The path to the given file handle.
            (Most serializers do not use this parameter.)

        """
        # Check the overall file version
        fileVersion = hdf5File["ilastikVersion"].value

        # Make sure we can find our way around the project tree
        if not isVersionCompatible(fileVersion):
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
                inc = self.progressIncrement()
                for ss in self.serialSlots:
                    ss.deserialize(topGroup)
                    self.progressSignal.emit(inc)

                # Call the subclass to do remaining work
                self._deserializeFromHdf5(topGroup, groupVersion, hdf5File, projectFilePath)
            else:
                self.initWithoutTopGroup(hdf5File, projectFilePath)
        finally:
            self.progressSignal.emit(100)

    #######################
    # Optional methods    #
    #######################

    def initWithoutTopGroup(self, hdf5File, projectFilePath):
        """Optional override for subclasses. Called when there is no
        top group to deserialize.

        """
        pass
