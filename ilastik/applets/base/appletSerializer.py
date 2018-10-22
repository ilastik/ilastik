###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
from future import standard_library
standard_library.install_aliases()
from builtins import range
import logging
from future.utils import with_metaclass
logger = logging.getLogger(__name__)

from abc import ABCMeta

from ilastik.config import cfg as ilastik_config
from lazyflow.utility.orderedSignal import OrderedSignal
from ilastik.utility.maybe import maybe
from ilastik.utility.commandLineProcessing import convertStringToList
import os
import sys
import re
import tempfile
import h5py
import numpy
import warnings
import pickle as pickle

from lazyflow.roi import TinyVector, roiToSlice, sliceToRoi
from lazyflow.utility import timeLogged
from lazyflow.slot import OutputSlot

#######################
# Convenience methods #
#######################

def getOrCreateGroup(parentGroup, groupName):
    """Returns parentGroup[groupName], creating first it if
    necessary.

    """

    return parentGroup.require_group(groupName)

def deleteIfPresent(parentGroup, name):
    """Deletes parentGroup[name], if it exists."""
    # Check first. If we try to delete a non-existent key, 
    # hdf5 will complain on the console.
    if name in parentGroup:
        del parentGroup[name]

def slicingToString(slicing):
    """Convert the given slicing into a string of the form
    '[0:1,2:3,4:5]'

    The result is a utf-8 encoded bytes, for easy storage via h5py
    """
    strSlicing = '['
    for s in slicing:
        strSlicing += str(s.start)
        strSlicing += ':'
        strSlicing += str(s.stop)
        strSlicing += ','

    strSlicing = strSlicing[:-1] # Drop the last comma
    strSlicing += ']'
    return strSlicing.encode('utf-8')

def stringToSlicing(strSlicing):
    """Parse a string of the form '[0:1,2:3,4:5]' into a slicing (i.e.
    list of slices)

    """
    if isinstance(strSlicing, bytes):
        strSlicing = strSlicing.decode('utf-8')
    
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

        :param default: DEPRECATED

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

        self.default = default
        self.depends = maybe(depends, [])
        if selfdepends:
            self.depends.append(slot)
        if name is None:
            name = slot.name
        self.name = name
        if subname is None:
            subname = '{:04d}'
        self.subname = subname

        self._dirty = False
        self._bind()
        self.ignoreDirty = False

    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, isDirty):
        if not isDirty or (isDirty and not self.ignoreDirty):
            self._dirty = isDirty

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
        result |= self.name not in list(group.keys())
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
        if self.slot.ready():
            self._serialize(group, self.name, self.slot)
        self.dirty = False

    @staticmethod
    def _saveValue(group, name, value):
        """Separate so that subclasses can override, if necessary.

        For instance, SerialListSlot needs to save an extra attribute
        if the value is an empty list.

        """
        if isinstance(value, str):
            # h5py can't store unicode, so we store all strings as encoded utf-8 bytes
            value = value.encode('utf-8')
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
        if isinstance(val, bytes):
            # h5py can't store unicode, so we store all strings as encoded utf-8 bytes
            val = val.decode('utf-8')
        slot.setValue(val)

    def _deserialize(self, subgroup, slot):
        """
        :param subgroup: *not* the parent group. This slot's group.
        :type subgroup: h5py.Group

        """
        if slot.level == 0:
            self._getValue(subgroup, slot)
        else:
            # Pair stored indexes with their keys,
            # e.g. [(0,'0'), (2, '2'), (3, '3')]
            # Note that in some cases an index might be intentionally skipped.
            indexes_to_keys = { int(k) : k for k in list(subgroup.keys()) }
            
            # Ensure the slot is at least big enough to deserialize into.
            if list(indexes_to_keys.keys()) == []:
                max_index = 0
            else:
                max_index = max( indexes_to_keys.keys() )
            if len(slot) < max_index+1:
                slot.resize(max_index+1)

            # Now retrieve the data
            for i, subslot in enumerate(slot):
                if i in indexes_to_keys:
                    key = indexes_to_keys[i]
                    # Sadly, we can't use the following assertion because it would break  
                    #  backwards compatibility with a bug we used to have in the key names.
                    #assert key == self.subname.format(i)
                    self._deserialize(subgroup[key], subslot)
                else:
                    # Since there was no data for this subslot in the project file,
                    # we disconnect the subslot.
                    subslot.disconnect()

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
                 default=None, depends=None, selfdepends=True, transform=None, store_transform=None, iterable=list):
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
        
        self._iterable = iterable
        self._store_transform = store_transform
        if store_transform is None:
            self._store_transform = lambda x:x

    def _saveValue(self, group, name, value):
        isempty = (len(value) == 0)
        if isempty:
            value = numpy.empty((1,))
        
        data = list(map(self._store_transform, value))
        
        # h5py can't store unicode, so we store all strings as encoded utf-8 bytes
        for i in range(len(data)):
            if isinstance(data[i], str):
                data[i] = data[i].encode('utf-8')

        sg = group.create_dataset(name, data=data)
        sg.attrs['isEmpty'] = isempty

    @timeLogged(logger, logging.DEBUG)
    def deserialize(self, group):
        logger.debug("Deserializing ListSlot: {}".format(self.name))
        try:
            subgroup = group[self.name]
        except:
            if logger.isEnabledFor(logging.DEBUG):
                # Only show this warning when debugging serialization
                warnings.warn("Deserialization: Could not locate value for slot '{}'.  Skipping.".format( self.name ))
            return
        if 'isEmpty' in subgroup.attrs and subgroup.attrs['isEmpty']:
            self.inslot.setValue( self._iterable([]) )
        else:
            if len(subgroup.shape) == 0 or subgroup.shape[0] == 0:
                # How can this happen, anyway...?
                return
            else:
                data = list(map(self.transform, subgroup[()]))
                
                # h5py can't store unicode, so we store all strings as encoded utf-8 bytes
                for i in range(len(data)):
                    if isinstance(data[i], bytes):
                        data[i] = data[i].decode('utf-8')
                self.inslot.setValue(self._iterable(data))
        self.dirty = False

class SerialBlockSlot(SerialSlot):
    """A slot which only saves nonzero blocks."""
    def __init__(self, slot, inslot, blockslot, name=None, subname=None,
                 default=None, depends=None, selfdepends=True, shrink_to_bb=False, compression_level=0):
        """
        :param blockslot: provides non-zero blocks.
        :param shrink_to_bb: If true, reduce each block of data from the slot to  
                             its nonzero bounding box before feeding saving it.

        """
        assert isinstance(slot, OutputSlot), "slot is of wrong type: '{}' is not an OutputSlot".format( slot.name )
        super(SerialBlockSlot, self).__init__(
            slot, inslot, name, subname, default, depends, selfdepends
        )
        self.blockslot = blockslot
        self._bind(slot)
        self._shrink_to_bb = shrink_to_bb
        self.compression_level = compression_level

    def shouldSerialize(self, group):
        # Should this be a docstring?
        #
        # Must be overloaded as SerialBlockSlot does not serialize itself in the simple way that other SerialSlot do
        # as a consequence of the nesting of groups required. Follows the same logic as _serialize and checks to see
        # if each relevant subgroup has been created and if any are missing or their data is missing it should be
        # serialized. Otherwise, if everything is intact, it doesn't suggest serialization unless the state has changed.

        logger.debug("Checking whether to serialize BlockSlot: {}".format( self.name ))

        if self.dirty:
            logger.debug("BlockSlot \"" + self.name + "\" appears to be dirty. Should serialize.")
            return True

        # SerialSlot interchanges self.name and name when they frequently are the same thing. It is not clear if using
        # self.name would be acceptable here or whether name should be an input to shouldSerialize or if there should be
        # a _shouldSerialize method, which takes the name.
        if self.name not in group:
            logger.debug("Missing \"" + self.name + "\" in group \"" + repr(group) + "\" belonging to BlockSlot \"" + self.name + "\". Should serialize.")
            return True
        else:
            logger.debug("Found \"" + self.name + "\" in group \"" + repr(group) + "\" belonging to BlockSlot \"" + self.name + "\".")

        # Just because the group was serialized doesn't mean that the relevant data was.
        mygroup = group[self.name]
        num = len(self.blockslot)
        for index in range(num):
            subname = self.subname.format(index)

            # Check to se if each subname has been created as a group
            if subname not in mygroup:
                logger.debug("Missing \"" + subname + "\" from \"" + repr(mygroup) + "\" belonging to BlockSlot \"" + self.name + "\". Should serialize.")
                return True
            else:
                logger.debug("Found \"" + subname + "\" from \"" + repr(mygroup) + "\" belonging to BlockSlot \"" + self.name + "\".")

            subgroup = mygroup[subname]

            nonZeroBlocks = self.blockslot[index].value
            for blockIndex in range(len(nonZeroBlocks)):
                blockName = 'block{:04d}'.format(blockIndex)

                if blockName not in subgroup:
                    logger.debug("Missing \"" + blockName + "\" from \"" + repr(subgroup) + "\". Should serialize.")
                    return True
                else:
                    logger.debug("Found \"" + blockName + "\" from \"" + repr(subgroup) + "\" belonging to BlockSlot \"" + self.name + "\".")

        logger.debug("Everything belonging to BlockSlot \"" + self.name + "\" appears to be in order. Should not serialize.")

        return False

    @timeLogged(logger, logging.DEBUG)
    def _serialize(self, group, name, slot):
        logger.debug("Serializing BlockSlot: {}".format( self.name ))
        mygroup = group.create_group(name)
        num = len(self.blockslot)
        for index in range(num):
            subname = self.subname.format(index)
            subgroup = mygroup.create_group(subname)
            nonZeroBlocks = self.blockslot[index].value
            for blockIndex, slicing in enumerate(nonZeroBlocks):
                if not isinstance(slicing[0], slice):
                    slicing = roiToSlice(*slicing)

                block = self.slot[index][slicing].wait()
                blockName = 'block{:04d}'.format(blockIndex)

                if self._shrink_to_bb:
                    nonzero_coords = numpy.nonzero(block)
                    if len(nonzero_coords[0]) > 0:
                        block_start = sliceToRoi( slicing, (0,)*len(slicing) )[0]
                        block_bounding_box_start = numpy.array( list(map( numpy.min, nonzero_coords )) )
                        block_bounding_box_stop = 1 + numpy.array( list(map( numpy.max, nonzero_coords )) )
                        block_slicing = roiToSlice( block_bounding_box_start, block_bounding_box_stop )
                        bounding_box_roi = numpy.array([block_bounding_box_start, block_bounding_box_stop])
                        bounding_box_roi += block_start
                        
                        # Overwrite the vars that are written to the file
                        slicing = roiToSlice(*bounding_box_roi)
                        block = block[block_slicing]

                # If we have a masked array, convert it to a structured array so that h5py can handle it.
                if slot[index].meta.has_mask:
                    mygroup.attrs["meta.has_mask"] = True

                    block_group = subgroup.create_group(blockName)

                    if self.compression_level:
                        block_group.create_dataset("data",
                                                   data=block.data,
                                                   compression='gzip',
                                                   compression_opts=compression_level)
                    else:
                        block_group.create_dataset("data", data=block.data)
                        
                    block_group.create_dataset(
                        "mask",
                        data=block.mask,
                        compression="gzip",
                        compression_opts=2
                    )
                    block_group.create_dataset("fill_value", data=block.fill_value)

                    block_group.attrs['blockSlice'] = slicingToString(slicing)
                else:
                    subgroup.create_dataset(blockName, data=block)
                    subgroup[blockName].attrs['blockSlice'] = slicingToString(slicing)

    @timeLogged(logger, logging.DEBUG)
    def _deserialize(self, mygroup, slot):
        logger.debug("Deserializing BlockSlot: {}".format( self.name ))
        num = len(mygroup)
        if len(self.inslot) < num:
            self.inslot.resize(num)
        # Annoyingly, some applets store their groups with names like, img0,img1,img2,..,img9,img10,img11
        # which means that sorted() needs a special key to avoid sorting img10 before img2
        # We have to find the index and sort according to its numerical value.
        index_capture = re.compile(r'[^0-9]*(\d*).*')
        def extract_index(s):
            return int(index_capture.match(s).groups()[0])
        for index, t in enumerate(sorted(list(mygroup.items()), key=lambda k_v: extract_index(k_v[0]))):
            groupName, labelGroup = t
            for blockData in list(labelGroup.values()):
                slicing = stringToSlicing(blockData.attrs['blockSlice'])

                # If it is suppose to be a masked array,
                # deserialize the pieces and rebuild the masked array.
                assert slot[index].meta.has_mask == mygroup.attrs.get("meta.has_mask"), \
                       "The slot and stored data have different values for" + \
                       " `has_mask`. They are" + \
                       " `bool(slot[index].meta.has_mask)`=" + \
                       repr(bool(slot[index].meta.has_mask)) + " and" + \
                       " `mygroup.attrs.get(\"meta.has_mask\", False)`=" + \
                       repr(mygroup.attrs.get("meta.has_mask", False)) + \
                       ". Please fix this to proceed with deserialization."
                if slot[index].meta.has_mask:
                    blockArray = numpy.ma.masked_array(
                        blockData["data"][()],
                        mask=blockData["mask"][()],
                        fill_value=blockData["fill_value"][()],
                        shrink=False
                    )
                else:
                    blockArray = blockData[...]

                self.inslot[index][slicing] = blockArray

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
        
        # Annoyingly, some applets store their groups with names like, img0,img1,img2,..,img9,img10,img11
        # which means that sorted() needs a special key to avoid sorting img10 before img2
        # We have to find the index and sort according to its numerical value.
        index_capture = re.compile(r'[^0-9]*(\d*).*')
        def extract_index(s):
            return int(index_capture.match(s).groups()[0])
        for index, t in enumerate(sorted(list(mygroup.items()), key=lambda k_v1: extract_index(k_v1[0]))):
            groupName, labelGroup = t
            assert extract_index(groupName) == index, "subgroup extraction order should be numerical order!"
            for blockRoiString, blockDataset in list(labelGroup.items()):
                blockRoi = convertStringToList(blockRoiString)
                roiShape = TinyVector(blockRoi[1]) - TinyVector(blockRoi[0])
                assert roiShape == blockDataset.shape

                self.inslot[index][roiToSlice( *blockRoi )] = blockDataset

class SerialClassifierSlot(SerialSlot):
    """For saving a classifier.  Here we assume the classifier is stored in the ."""
    def __init__(self, slot, cache, inslot=None, name=None,
                 default=None, depends=None, selfdepends=True):
        super(SerialClassifierSlot, self).__init__(
            slot, inslot, name, None, default, depends, selfdepends
        )
        self.cache = cache
        if self.name is None:
            self.name = slot.name
        
        # We want to bind to the INPUT, not Output:
        # - if the input becomes dirty, we want to make sure the cache is deleted
        # - if the input becomes dirty and then the cache is reloaded, we'll save the classifier.
        self._bind(cache.Input)

    def _serialize(self, group, name, slot):
        # Is the cache up-to-date?
        # if not, we'll just return (don't recompute the classifier just to save it)
        if self.cache._dirty:
            return

        classifier = self.cache.Output.value

        # Classifier can be None if there isn't any training data yet.
        if classifier is None:
            return

        classifier_group = group.create_group( name )
        classifier.serialize_hdf5( classifier_group )

    def deserialize(self, group):
        """
        Have to override this to ensure that dirty is always set False.
        """
        super(SerialClassifierSlot, self).deserialize(group)
        self.dirty = False

    def _deserialize(self, classifierGroup, slot):
        try:
            classifier_type = pickle.loads( classifierGroup['pickled_type'][()] )
        except KeyError:
            # For compatibility with old project files, choose the default classifier.
            from lazyflow.classifiers import ParallelVigraRfLazyflowClassifier
            classifier_type = ParallelVigraRfLazyflowClassifier
        
        try:
            classifier = classifier_type.deserialize_hdf5( classifierGroup )
        except:
            warnings.warn( "Wasn't able to deserialize the saved classifier.  "
                           "It will need to be retrainied" )
            return

        # Now force the classifier into our classifier cache. The
        # downstream operators (e.g. the prediction operator) can
        # use the classifier without inducing it to be re-trained.
        # (This assumes that the classifier we are loading is
        # consistent with the images and labels that we just
        # loaded. As soon as training input changes, it will be
        # retrained.)
        self.cache.forceValue( classifier )


class SerialCountingSlot(SerialSlot):
    """For saving a random forest classifier."""
    def __init__(self, slot, cache, inslot=None, name=None,
                 default=None, depends=None, selfdepends=True):
        super(SerialCountingSlot, self).__init__(
            slot, inslot, name, "wrapper{:04d}", default, depends, selfdepends
        )
        self.cache = cache
        if self.name is None:
            self.name = slot.name
        if self.subname is None:
            self.subname = "wrapper{:04d}"

        # We want to bind to the INPUT, not Output:
        # - if the input becomes dirty, we want to make sure the cache is deleted
        # - if the input becomes dirty and then the cache is reloaded, we'll save the classifier.
        self._bind(cache.Input)

    def _serialize(self, group, name, slot):
        if self.cache._dirty:
            return

        classifier_forests = self.cache.Output.value

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
        super(SerialCountingSlot, self).deserialize(group)
        self.dirty = False

    def _deserialize(self, classifierGroup, slot):
        # Due to non-shared hdf5 dlls, vigra can't read directly
        # from our open hdf5 group. Instead, we'll copy the
        # classfier data to a temporary file and give it to vigra.
        tmpDir = tempfile.mkdtemp()
        cachePath = os.path.join(tmpDir, 'tmp_classifier_cache.h5').replace('\\', '/')
        with h5py.File(cachePath, 'w') as cacheFile:
            cacheFile.copy(classifierGroup, self.name)

        try:
            forests = []
            for name, forestGroup in sorted(classifierGroup.items()):
                targetname = '{0}/{1}'.format(self.name, name)
                #forests.append(vigra.learning.RandomForest(cachePath, targetname))
                from ilastik.applets.counting.countingsvr import SVR
                forests.append(SVR.load(cachePath, targetname))
        except:
            warnings.warn( "Wasn't able to deserialize the saved classifier.  "
                           "It will need to be retrainied" )
            return
        finally:
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
        for key, v in value.items():
            if isinstance(v, dict):
                self._saveValue(sg, key, v)
            else:
                if isinstance(v, str):
                    # h5py can't store unicode, so we store all strings as encoded utf-8 bytes
                    v = v.encode('utf-8')
                if isinstance(v, list):
                    vv = []
                    for a in v:
                        if isinstance(a, str):
                            vv.append(a.encode('utf-8'))
                        else:
                            vv.append(a)
                    v = vv
                sg.create_dataset(str(key), data=v)

    def _getValueHelper(self, subgroup):
        result = {}
        for key in list(subgroup.keys()):
            if isinstance(subgroup[key], h5py.Group):
                value = self._getValueHelper(subgroup[key])
            else:
                value = subgroup[key][()]
                if isinstance(value, bytes):
                    # h5py can't store unicode, so we store all strings as encoded utf-8 bytes
                    value = value.decode('utf-8')

            result[self.transform(key)] = value
        return result

    def _getValue(self, subgroup, slot):
        result = self._getValueHelper(subgroup)
        try:
            slot.setValue(result)
        except AssertionError as e:
            warnings.warn('setValue() failed. message: {}'.format(e.message))

class SerialObjectFeatureNamesSlot(SerialDictSlot):
    """Backwards compatible serializer for DictSlot containing feature names"""

    def _getValue(self, subgroup, slot):
        """Retrieves value for Slot "slot" from the h5 subgroup "subgroup"

        Global feature names used to be saved into .ilp files under a '0' key.
        That is no longer the case, so this method peels that extra level off when
        it is present."""
        if list(subgroup.keys()) == ['0']:
            subgroup = subgroup['0']
        return super()._getValue(subgroup, slot)

class SerialClassifierFactorySlot(SerialSlot):
    def __init__(self, slot, name=None):
        super( SerialClassifierFactorySlot, self ).__init__( slot, name=name )
        self._failed_to_deserialize = False
        assert slot.ready(), \
            "ClassifierFactory slots must be given a default value "\
            "(in case the classifier can't be deserialized in a future version of ilastik)."
    
    def _saveValue(self, group, name, value):
        pickled = pickle.dumps( value, 0 )
        group.create_dataset(name, data=pickled)
        self._failed_to_deserialize = False

    def shouldSerialize(self, group):
        if self._failed_to_deserialize:
            return True
        else:
            return super(SerialClassifierFactorySlot, self).shouldSerialize(group)

    def _getValue(self, dset, slot):
        pickled = dset[()]
        try:
            # Attempt to unpickle
            value = pickle.loads(pickled)
            
            # Verify that the VERSION of the classifier factory in the currently executing code
            #  has not changed since this classifier was stored.
            assert 'VERSION' in value.__dict__ and value.VERSION == type(value).VERSION
        except:
            self._failed_to_deserialize = True
            warnings.warn("This project file uses an old or unsupported classifier storage format. "
                          "The classifier will be stored in the new format when you save your project.")
        else:
            slot.setValue( value )


class SerialPickleableSlot(SerialSlot):
    def __init__(self, slot, version, default=None, name=None):
        super( SerialPickleableSlot, self ).__init__( slot, name=name )
        self._failed_to_deserialize = False
        self._version = version
        self._default = default

    def _saveValue(self, group, name, value):
        # we pickle to a string and convert to numpy.void,
        # because HDF5 has some limitations as to which strings it can serialize
        # (see http://docs.h5py.org/en/latest/strings.html)
        pickled = numpy.void(pickle.dumps(value, 0))
        dset = group.create_dataset(name, data=pickled)
        dset.attrs['version'] = self._version
        self._failed_to_deserialize = False

    def shouldSerialize(self, group):
        if self._failed_to_deserialize:
            return True
        else:
            return super(SerialPickleableSlot, self).shouldSerialize(group)

    def _getValue(self, dset, slot):
        # first check that the version of the deserialized and the expected value are the same
        try:
            loaded_version = dset.attrs['version']
        except KeyError as e:
            loaded_version = None
            logger.debug('No `version` attribute found.')
        if not loaded_version == self._version:
            logger.warning(
                f'PickleableSlot version mismatch detected. (loaded: {loaded_version}, running:{self._version})'
                'Trying to load slot value.')
        try:
            # Attempt to unpickle
            pickled = dset[()]
            if isinstance(pickled, numpy.void):
                # get the numpy.void object from the HDF5 dataset and convert it to bytes
                pickled = pickled.tobytes()
            value = pickle.loads(pickled)
        except Exception as e:
            self._failed_to_deserialize = True
            warnings.warn("This project file uses an old or unsupported storage format. "
                          "When save the project the next time, it will be stored in the new format.\n"
                          "Encountered exception:\n"
                          "{}".format(e))
            slot.setValue(self._default)
        else:
            slot.setValue(value)

####################################
# the base applet serializer class #
####################################

class AppletSerializer(with_metaclass(ABCMeta, object)):
    """
    Base class for all AppletSerializers.
    """
    base_initialized = False

    # override if necessary
    version = "0.1"

    class IncompatibleProjectVersionError(Exception):
        pass

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
        self.progressSignal = OrderedSignal()  # Signature: __call__(percentComplete)
        self.base_initialized = True
        self.topGroupName = topGroupName
        self.serialSlots = maybe(slots, [])
        self.operator = operator
        self._ignoreDirty = False

    def isDirty(self):
        """Returns true if the current state of this item (in memory)
        does not match the state of the HDF5 group on disk.

        Subclasses only need override this method if ORing the flags
        is not enough.

        """
        return any(list(ss.dirty for ss in self.serialSlots))

    def shouldSerialize(self, hdf5File):
        """Whether to serialize or not."""

        if self.isDirty():
            return True

        # Need to check if slots should be serialized. First must verify that self.topGroupName is not an empty string
        # (as this seems to happen sometimes).
        if self.topGroupName:
            topGroup = getOrCreateGroup(hdf5File, self.topGroupName)
            return any([ss.shouldSerialize(topGroup) for ss in self.serialSlots])

        return False

    @property
    def ignoreDirty(self):
        return self._ignoreDirty

    @ignoreDirty.setter
    def ignoreDirty(self, value):
        self._ignoreDirty = value
        for ss in self.serialSlots:
            ss.ignoreDirty = value

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
        topGroup = getOrCreateGroup(hdf5File, self.topGroupName)

        progress = 0
        self.progressSignal(progress)

        # Set the version
        key = 'StorageVersion'
        deleteIfPresent(topGroup, key)
        topGroup.create_dataset(key, data=self.version)

        try:
            inc = self.progressIncrement(topGroup)
            for ss in self.serialSlots:
                ss.serialize(topGroup)
                progress += inc
                self.progressSignal(progress)

            # Call the subclass to do remaining work, if any
            self._serializeToHdf5(topGroup, hdf5File, projectFilePath)
        finally:
            self.progressSignal(100)

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
        self.progressSignal(0)

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
                    self.progressSignal(inc)

                # Call the subclass to do remaining work
                self._deserializeFromHdf5(topGroup, groupVersion, hdf5File, projectFilePath, headless)
            else:
                self.initWithoutTopGroup(hdf5File, projectFilePath)
        finally:
            self.progressSignal(100)

    def repairFile(self,path,filt = None):
        """get new path to lost file"""
        
        from PyQt5.QtWidgets import QFileDialog,QMessageBox
        
        text = "The file at {} could not be found any more. Do you want to search for it at another directory?".format(path)
        logger.info(text)
        c = QMessageBox.critical(None, "update external data",text, QMessageBox.Ok | QMessageBox.Cancel)

        if c == QMessageBox.Cancel:
            raise RuntimeError("Could not find external data: " + path)

        options = QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |=  QFileDialog.DontUseNativeDialog
        fileName, _filter = QFileDialog.getOpenFileName( None, "repair files", path, filt, options=options)
        if not fileName:
            raise RuntimeError("Could not find external data: " + path)
        else:
            return fileName

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
