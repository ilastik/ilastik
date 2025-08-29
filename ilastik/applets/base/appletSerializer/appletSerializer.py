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
# 		   http://ilastik.org/license.html
###############################################################################
import logging
from abc import ABC

import h5py

from ilastik.config import cfg as ilastik_config
from ilastik.utility.maybe import maybe
from lazyflow.utility.orderedSignal import OrderedSignal

from .serializerUtils import deleteIfPresent

logger = logging.getLogger(__name__)


class AppletSerializer(ABC):
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

    def _serializeToHdf5(self, topGroup: h5py.Group, hdf5File: h5py.File, projectFilePath):
        """Child classes should override this function, if
        necessary.

        """
        pass

    def _deserializeFromHdf5(
        self, topGroup: h5py.Group, groupVersion, hdf5File: h5py.File, projectFilePath, headless=False
    ):
        """Child classes should override this function, if
        necessary.

        """
        pass

    #############################
    # Base class implementation #
    #############################

    def __init__(self, topGroupName: str, slots=None, operator=None):
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

    def shouldSerialize(self, hdf5File: h5py.File):
        """Whether to serialize or not."""

        if self.isDirty():
            return True

        # Need to check if slots should be serialized. First must verify that self.topGroupName is not an empty string
        # (as this seems to happen sometimes).
        if self.topGroupName:
            topGroup = hdf5File.require_group(self.topGroupName)
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

    def serializeToHdf5(self, hdf5File: h5py.File, projectFilePath):
        """Serialize the current applet state to the given hdf5 file.

        Subclasses should **not** override this method. Instead,
        subclasses override the 'private' version, *_serializetoHdf5*

        :param hdf5File: An h5py.File handle to the project file,
            which should already be open

        :param projectFilePath: The path to the given file handle.
            (Most serializers do not use this parameter.)

        """
        topGroup = hdf5File.require_group(self.topGroupName)

        progress = 0
        self.progressSignal(progress)

        # Set the version
        key = "StorageVersion"
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

    def deserializeFromHdf5(self, hdf5File, projectFilePath, headless=False):
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
            groupVersion = topGroup["StorageVersion"][()]
            if isinstance(groupVersion, bytes):
                groupVersion = groupVersion.decode("utf-8")
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

    def repairFile(self, path, filt=None):
        """get new path to lost file"""

        from qtpy.QtWidgets import QFileDialog, QMessageBox

        text = "The file at {} could not be found any more. Do you want to search for it at another directory?".format(
            path
        )
        logger.info(text)
        c = QMessageBox.critical(None, "update external data", text, QMessageBox.Ok | QMessageBox.Cancel)

        if c == QMessageBox.Cancel:
            raise RuntimeError("Could not find external data: " + path)

        options = QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |= QFileDialog.DontUseNativeDialog
        fileName, _filter = QFileDialog.getOpenFileName(None, "repair files", path, filt, options=options)
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

    def updateWorkingDirectory(self, newdir, olddir):
        """Optional override for subclasses. Called when the
        working directory is changed and relative paths have
        to be updated. Child Classes should overwrite this method
        if they store relative paths."""
        pass
