from abc import ABCMeta, abstractmethod

from ilastik.config import cfg as ilastik_config
from ilastik import isVersionCompatible
from ilastik.utility.simpleSignal import SimpleSignal
from ilastik.utility.maybe import maybe
import os
import tempfile
import vigra
import h5py
import numpy
import warnings

from lazyflow.roi import TinyVector, roiToSlice
from lazyflow.rtype import SubRegion
from lazyflow.slot import OutputSlot

#######################
# Convenience methods #
#######################

def getOrCreateGroup(parentGroup, groupName):
    """Returns parentGroup[groupName], creating first it if
    necessary.

    """
    if groupName in parentGroup:
        return parentGroup[groupName]
    return parentGroup.create_group(groupName)

def deleteIfPresent(parentGroup, name):
    """Deletes parentGroup[name], if it exists."""
    if name in parentGroup:
        del parentGroup[name]

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
    def __init__(self, slot, inslot=None, name=None, subname=None,
                 default=None, depends=None, selfdepends=True):
        """
        :param slot: where to get data to save

        :param inslot: where to put loaded data. If None, it is the
        same as 'slot'.

        :param name: name used for the group in the hdf5 file.

        :param subname: used for creating subgroups for multislots.
          should be able to call subname.format(i), where i is an
          integer.

        :param default: the default value when unload() is called. If it is
          None, the slot will just be disconnected (for level 0 slots) or
          resized to length 0 (for multislots)

        :param depends: a list of slots which must be ready before this slot
          can be serialized. If None, defaults to [].

        :param selfdepends: whether 'slot' should be added to 'depends'

        """
        if slot.level > 1:
            # FIXME: recursive serialization, to support arbitrary levels
            raise Exception('slots of levels > 1 not supported')
        self.slot = slot
        if inslot is None:
            inslot = slot
        self.inslot = inslot

        if isinstance(inslot, OutputSlot):
            # should this be an exception? Or maybe an exception in lazyflow?
            print 'Warning: this serial slot will try to call setValue on an OutputSlot.'
            print 'This is probably not what you wanted!'
            print 'inslot = %s, %s' % (type(inslot), inslot)
        self.default = default
        self.depends = maybe(depends, [])
        if selfdepends:
            self.depends.append(slot)
        if name is None:
            name = slot.name
        self.name = name
        if subname is None:
            subname = '{}'
        self.subname = subname

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
            slot[index].notifyValueChanged(self.setDirty)

        if slot.level == 0:
            slot.notifyDirty(self.setDirty)
            slot.notifyValueChanged(self.setDirty)
        else:
            slot.notifyInserted(doMulti)
            slot.notifyRemoved(self.setDirty)

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
        self._serialize(group, self.name, self.slot)
        self.dirty = False

    @staticmethod
    def _saveValue(group, name, value):
        """Seperate so that subclasses can override, if necessary.

        For instance, SerialListSlot needs to save an extra attribute
        if the value is an empty list.

        """
        group.create_dataset(name, data=value)

    def _serialize(self, group, name, slot):
        """
        :param group: The parent group.
        :type group: h5py.Group
        :param name: The name of the data or group
        :type name: string
        :param slot: the slot to serialize
        :type slot: SerialSlot

        """
        if slot.level == 0:
            try:
                self._saveValue(group, name, slot.value)
            except:
                self._saveValue(group, name, slot(()).wait())
        else:
            subgroup = group.create_group(name)
            for i, subslot in enumerate(slot):
                subname = self.subname.format(i)
                self._serialize(subgroup, subname, slot[i])

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
        self._deserialize(group[self.name], self.inslot)
        self.dirty = False

    @staticmethod
    def _getValue(subgroup, slot):
        val = subgroup[()]
        slot.setValue(val)

    def _deserialize(self, subgroup, slot):
        """
        :param subgroup: *not* the parent group. This slot's group.
        :type subgroup: h5py.Group

        """
        if slot.level == 0:
            self._getValue(subgroup, slot)
        else:
            slot.resize(len(subgroup))
            for i, key in enumerate(subgroup):
                assert key == self.subname.format(i)
                self._deserialize(subgroup[key], slot[i])

    def unload(self):
        """see AppletSerializer.unload()"""
        if self.slot.level == 0:
            if self.default is None:
                self.slot.disconnect()
            else:
                self.inslot.setValue(self.default)
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
    def __init__(self, slot, inslot=None, name=None, subname=None,
                 default=None, depends=None, selfdepends=True, transform=None):
        """
        :param transform: function applied to members on deserialization.

        """
        # TODO: implement for multislots
        if slot.level > 0:
            raise NotImplementedError()

        super(SerialListSlot, self).__init__(
            slot, inslot, name, subname, default, depends, selfdepends
        )
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
                    self.inslot.setValue(list(map(self.transform, subgroup[()])))
                except:
                    self.unload()
        finally:
            self.dirty = False

    def unload(self):
        if self.slot.level == 0:
            self.inslot.setValue([])
        else:
            self.slot.resize(0)
        self.dirty = False


class SerialBlockSlot(SerialSlot):
    """A slot which only saves nonzero blocks."""
    def __init__(self, slot, inslot, blockslot, name=None, subname=None,
                 default=None, depends=None, selfdepends=True):
        """
        :param blockslot: provides non-zero blocks.

        """
        super(SerialBlockSlot, self).__init__(
            slot, inslot, name, subname, default, depends, selfdepends
        )
        self.blockslot = blockslot
        self._bind(slot)

    def _serialize(self, group, name, slot):
        mygroup = group.create_group(name)
        num = len(self.blockslot)
        for index in range(num):
            subname = self.subname.format(index)
            subgroup = mygroup.create_group(subname)
            nonZeroBlocks = self.blockslot[index].value
            for blockIndex, slicing in enumerate(nonZeroBlocks):
                block = self.slot[index][slicing].wait()
                blockName = 'block{:04d}'.format(blockIndex)
                subgroup.create_dataset(blockName, data=block)
                subgroup[blockName].attrs['blockSlice'] = slicingToString(slicing)

    def _deserialize(self, mygroup, slot):
        num = len(mygroup)
        if len(self.inslot) < num:
            self.inslot.resize(num)
        for index, t in enumerate(sorted(mygroup.items())):
            groupName, labelGroup = t
            for blockData in labelGroup.values():
                slicing = stringToSlicing(blockData.attrs['blockSlice'])
                self.inslot[index][slicing] = blockData[...]

class SerialHdf5BlockSlot(SerialBlockSlot):

    def _serialize(self, group, name, slot):
        mygroup = group.create_group(name)
        num = len(self.blockslot)
        for index in range(num):
            subname = self.subname.format(index)
            subgroup = mygroup.create_group(subname)
            cleanBlockRois = self.blockslot[index].value
            for roi in cleanBlockRois:
                # The protocol for hdf5 slots is that they create appropriately 
                #  named datasets within the subgroup that we provide via writeInto()
                req = self.slot[index]( *roi )
                req.writeInto( subgroup )
                req.wait()

    def _deserialize(self, mygroup, slot):
        num = len(mygroup)
        if len(self.inslot) < num:
            self.inslot.resize(num)
        for index, t in enumerate(sorted(mygroup.items())):
            groupName, labelGroup = t
            for blockRoiString, blockDataset in labelGroup.items():
                blockRoi = eval(blockRoiString)
                roiShape = TinyVector(blockRoi[1]) - TinyVector(blockRoi[0])
                assert roiShape == blockDataset.shape

                self.inslot[index][roiToSlice( *blockRoi )] = blockDataset

class SerialClassifierSlot(SerialSlot):
    """For saving a random forest classifier."""
    def __init__(self, slot, cache, inslot=None, name=None, subname=None,
                 default=None, depends=None, selfdepends=True):
        super(SerialClassifierSlot, self).__init__(
            slot, inslot, name, subname, default, depends, selfdepends
        )
        self.cache = cache
        if self.name is None:
            self.name = slot.name
        if self.subname is None:
            self.subname = "Forest{:04d}"
        self._bind(cache.Output)

    def unload(self):
        self.cache.Input.setDirty(slice(None))

    def _serialize(self, group, name, slot):
        if self.cache._dirty:
            return

        classifier_forests = self.cache._value

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
        cachePath = os.path.join(tmpDir, 'tmp_classifier_cache.h5').replace('\\', '/')
        for i, forest in enumerate(classifier_forests):
            targetname = '{0}/{1}'.format(name, self.subname.format(i))
            forest.writeHDF5(cachePath, targetname)

        # Open the temp file and copy to our project group
        with h5py.File(cachePath, 'r') as cacheFile:
            group.copy(cacheFile[name], name)

        os.remove(cachePath)
        os.rmdir(tmpDir)

    def deserialize(self, group):
        """
        Have to override this to ensure that dirty is always set False.
        """
        super(SerialClassifierSlot, self).deserialize(group)
        self.dirty = False

    def _deserialize(self, classifierGroup, slot):
        # Due to non-shared hdf5 dlls, vigra can't read directly
        # from our open hdf5 group. Instead, we'll copy the
        # classfier data to a temporary file and give it to vigra.
        tmpDir = tempfile.mkdtemp()
        cachePath = os.path.join(tmpDir, 'tmp_classifier_cache.h5').replace('\\', '/')
        with h5py.File(cachePath, 'w') as cacheFile:
            cacheFile.copy(classifierGroup, self.name)

        forests = []
        for name, forestGroup in sorted(classifierGroup.items()):
            targetname = '{0}/{1}'.format(self.name, name)
            forests.append(vigra.learning.RandomForest(cachePath, targetname))

        os.remove(cachePath)
        os.rmdir(tmpDir)

        # Now force the classifier into our classifier cache. The
        # downstream operators (e.g. the prediction operator) can
        # use the classifier without inducing it to be re-trained.
        # (This assumes that the classifier we are loading is
        # consistent with the images and labels that we just
        # loaded. As soon as training input changes, it will be
        # retrained.)
        self.cache.forceValue(numpy.array(forests))


class SerialDictSlot(SerialSlot):
    """For saving a dictionary."""
    def __init__(self, slot, inslot=None, name=None, subname=None,
                 default=None, depends=None, selfdepends=True, transform=None):
        """
        :param transform: a function called on each key before
        inserting it into the dictionary.

        """
        super(SerialDictSlot, self).__init__(
            slot, inslot, name, subname, default, depends, selfdepends
        )
        if transform is None:
            transform = lambda x: x
        self.transform = transform

    def _saveValue(self, group, name, value):
        sg = group.create_group(name)
        for key, v in value.iteritems():
            if isinstance(v, dict):
                self._saveValue(sg, key, v)
            else:
                sg.create_dataset(str(key), data=v)


    def _getValueHelper(self, subgroup):
        result = {}
        for key in subgroup.keys():
            if isinstance(subgroup[key], h5py.Group):
                value = self._getValueHelper(subgroup[key])
            else:
                value = subgroup[key][()]
            result[self.transform(key)] = value
        return result

    def _getValue(self, subgroup, slot):
        result = self._getValueHelper(subgroup)
        try:
            slot.setValue(result)
        except AssertionError as e:
            warnings.warn('setValue() failed. message: {}'.format(e.message))


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
                             projectFilePath, headless = False):
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
        self.operator = operator
        self.caresOfHeadless = False # should _deserializeFromHdf5 should be called with headless-argument?

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

        progress = 0
        self.progressSignal.emit(progress)

        # Set the version
        key = 'StorageVersion'
        deleteIfPresent(topGroup, key)
        topGroup.create_dataset(key, data=self.version)

        try:
            inc = self.progressIncrement(topGroup)
            for ss in self.serialSlots:
                ss.serialize(topGroup)
                progress += inc
                self.progressSignal.emit(progress)

            # Call the subclass to do remaining work, if any
            self._serializeToHdf5(topGroup, hdf5File, projectFilePath)
        finally:
            self.progressSignal.emit(100)


    def deserializeFromHdf5(self, hdf5File, projectFilePath, headless = False):
        """Read the the current applet state from the given hdf5File
        handle, which should already be open.

        Subclasses should **not** override this method. Instead,
        subclasses override the 'private' version,
        *_deserializeFromHdf5*

        :param hdf5File: An h5py.File handle to the project file,
            which should already be open

        :param projectFilePath: The path to the given file handle.
            (Most serializers do not use this parameter.)
        
        :param headless: Are we called in headless mode?
            (in headless mode corrupted files cannot be fixed via the GUI)
        
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
                if self.caresOfHeadless:
                    self._deserializeFromHdf5(topGroup, groupVersion, hdf5File, projectFilePath, headless)
                else:
                    self._deserializeFromHdf5(topGroup, groupVersion, hdf5File, projectFilePath)
            else:
                self.initWithoutTopGroup(hdf5File, projectFilePath)
        finally:
            self.progressSignal.emit(100)
    
    def repairFile(self,path,filt = None):
        """get new path to lost file"""
        
        from PyQt4.QtGui import QFileDialog,QMessageBox
        
        text = "The file at {} could not be found any more. Do you want to search for it at another directory?".format(path)
        c = QMessageBox.critical(None, "update external data",text, QMessageBox.Ok | QMessageBox.Cancel)
        
        if c == QMessageBox.Cancel:
            raise RuntimeError("Could not find external data: " + path)
        
        options = QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |=  QFileDialog.DontUseNativeDialog
        fileName = QFileDialog.getOpenFileName( None, "repair files", path, filt, options=options)
        if fileName.isEmpty():
            raise RuntimeError("Could not find external data: " + path)
        else:
            return str(fileName)
        
    #######################
    # Optional methods    #
    #######################
    
    def initWithoutTopGroup(self, hdf5File, projectFilePath):
        """Optional override for subclasses. Called when there is no
        top group to deserialize.

        """
        pass
    
    def updateWorkingDirectory(self,newdir,olddir):
        """Optional override for subclasses. Called when the
        working directory is changed and relative paths have
        to be updated. Child Classes should overwrite this method
        if they store relative paths."""
        pass
