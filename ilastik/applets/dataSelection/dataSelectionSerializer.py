from __future__ import absolute_import

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
from typing import List, Tuple, Callable
from pathlib import Path


from .opDataSelection import (
    OpDataSelection,
    DatasetInfo,
    FilesystemDatasetInfo,
    RelativeFilesystemDatasetInfo,
    UrlDatasetInfo,
)
from .opDataSelection import PreloadedArrayDatasetInfo, ProjectInternalDatasetInfo
from lazyflow.operators.ioOperators import OpInputDataReader, OpStackLoader, OpH5N5WriterBigDataset
from lazyflow.operators.ioOperators.opTiffReader import OpTiffReader
from lazyflow.operators.ioOperators.opTiffSequenceReader import OpTiffSequenceReader
from lazyflow.operators.ioOperators.opStreamingH5N5SequenceReaderM import OpStreamingH5N5SequenceReaderM
from lazyflow.operators.ioOperators.opStreamingH5N5SequenceReaderS import OpStreamingH5N5SequenceReaderS
from lazyflow.graph import Graph

import os
import vigra
import numpy
from lazyflow.utility import PathComponents
from lazyflow.utility.timer import timeLogged
from ilastik.utility import bind
from lazyflow.utility.pathHelpers import getPathVariants, isUrl, isRelative, splitPath
import ilastik.utility.globals

from ilastik.applets.base.appletSerializer import AppletSerializer, getOrCreateGroup, deleteIfPresent

import logging

logger = logging.getLogger(__name__)


class DataSelectionSerializer(AppletSerializer):
    """
    Serializes the user's input data selections to an ilastik v0.6 project file.

    The model operator for this serializer is the ``OpMultiLaneDataSelectionGroup``
    """

    # Constants
    InfoClassNames = {
        klass.__name__: klass
        for klass in [ProjectInternalDatasetInfo, FilesystemDatasetInfo, RelativeFilesystemDatasetInfo, UrlDatasetInfo]
    }

    def __init__(self, topLevelOperator, projectFileGroupName):
        super(DataSelectionSerializer, self).__init__(projectFileGroupName)
        self.topLevelOperator = topLevelOperator
        self._dirty = False

        self._projectFilePath = None

        self.version = "0.2"

        def handleDirty():
            if not self.ignoreDirty:
                self._dirty = True

        self.topLevelOperator.ProjectFile.notifyDirty(bind(handleDirty))
        self.topLevelOperator.ProjectDataGroup.notifyDirty(bind(handleDirty))
        self.topLevelOperator.WorkingDirectory.notifyDirty(bind(handleDirty))

        def handleNewDataset(slot, roleIndex):
            slot[roleIndex].notifyDirty(bind(handleDirty))
            slot[roleIndex].notifyDisconnect(bind(handleDirty))

        def handleNewLane(multislot, laneIndex):
            assert multislot == self.topLevelOperator.DatasetGroup
            multislot[laneIndex].notifyInserted(bind(handleNewDataset))
            for roleIndex in range(len(multislot[laneIndex])):
                handleNewDataset(multislot[laneIndex], roleIndex)

        self.topLevelOperator.DatasetGroup.notifyInserted(bind(handleNewLane))

        # If a dataset was removed, we need to be reserialized.
        self.topLevelOperator.DatasetGroup.notifyRemoved(bind(handleDirty))

    @timeLogged(logger, logging.DEBUG)
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        getOrCreateGroup(topGroup, "local_data")
        deleteIfPresent(topGroup, "Role Names")
        role_names = [name.encode("utf-8") for name in self.topLevelOperator.DatasetRoles.value]
        topGroup.create_dataset("Role Names", data=role_names)

        # Access the info group
        infoDir = getOrCreateGroup(topGroup, "infos")

        # Delete all infos
        infoDir.clear()

        # Rebuild the list of infos
        roleNames = self.topLevelOperator.DatasetRoles.value
        internal_datasets_to_keep = set()
        for laneIndex, multislot in enumerate(self.topLevelOperator.DatasetGroup):
            laneGroupName = "lane{:04d}".format(laneIndex)
            laneGroup = infoDir.create_group(laneGroupName)
            for roleIndex, slot in enumerate(multislot):
                infoGroup = laneGroup.create_group(roleNames[roleIndex])
                if slot.ready():
                    datasetInfo = slot.value
                    if isinstance(datasetInfo, ProjectInternalDatasetInfo):
                        internal_datasets_to_keep.add(hdf5File[datasetInfo.inner_path])
                    for k, v in datasetInfo.to_json_data().items():
                        if v is not None:
                            infoGroup.create_dataset(k, data=v)
        if self.local_data_path.as_posix() in hdf5File:
            for dataset in hdf5File[self.local_data_path.as_posix()].values():
                if dataset not in internal_datasets_to_keep:
                    del hdf5File[dataset.name]
        self._dirty = False

    def importStackAsLocalDataset(
        self, abs_paths: List[str], sequence_axis: str = "z", progress_signal: Callable[[int], None] = None
    ):
        progress_signal = progress_signal or self.progressSignal
        progress_signal(0)
        op_reader = None
        op_writer = None
        try:
            colon_paths = os.path.pathsep.join(abs_paths)
            op_reader = OpInputDataReader(
                graph=self.topLevelOperator.graph, FilePath=colon_paths, SequenceAxis=sequence_axis
            )
            axistags = op_reader.Output.meta.axistags
            inner_path = self.local_data_path.joinpath(DatasetInfo.generate_id()).as_posix()
            project_file = self.topLevelOperator.ProjectFile.value
            op_writer = OpH5N5WriterBigDataset(
                graph=self.topLevelOperator.graph,
                h5N5File=project_file,
                h5N5Path=inner_path,
                CompressionEnabled=False,
                BatchSize=1,
                Image=op_reader.Output,
            )
            op_writer.progressSignal.subscribe(progress_signal)
            success = op_writer.WriteImage.value
            for index, tag in enumerate(axistags):
                project_file[inner_path].dims[index].label = tag.key
            project_file[inner_path].attrs["axistags"] = axistags.toJSON()
            if op_reader.Output.meta.get("drange"):
                project_file[inner_path].attrs["drange"] = op_reader.Output.meta.get("drange")
            return inner_path
        finally:
            if op_writer:
                op_writer.Image.disconnect()
            if op_reader:
                op_reader.cleanUp()
            progress_signal(100)

    def initWithoutTopGroup(self, hdf5File, projectFilePath):
        """
        Overridden from AppletSerializer.initWithoutTopGroup
        """
        # The 'working directory' for the purpose of constructing absolute
        #  paths from relative paths is the project file's directory.
        projectDir = os.path.split(projectFilePath)[0]
        self.topLevelOperator.DatasetGroup.resize(0)
        self.topLevelOperator.WorkingDirectory.setValue(projectDir)
        self.topLevelOperator.ProjectDataGroup.setValue(self.topGroupName + "/local_data")
        self.topLevelOperator.ProjectFile.setValue(hdf5File)

        self._dirty = False

    @property
    def local_data_path(self) -> Path:
        return Path(self.topGroupName).joinpath("local_data")

    @timeLogged(logger, logging.DEBUG)
    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath, headless):
        self._projectFilePath = projectFilePath
        self.initWithoutTopGroup(hdf5File, projectFilePath)

        # normally the serializer is not dirty after loading a project file
        # however, when the file was corrupted, the user has the possibility
        # to save the fixed file after loading it.
        infoDir = topGroup["infos"]

        assert self.topLevelOperator.DatasetRoles.ready(), "Expected dataset roles to be hard-coded by the workflow."
        workflow_role_names = self.topLevelOperator.DatasetRoles.value

        # If the project file doesn't provide any role names, then we assume this is an old pixel classification project
        force_dirty = False
        backwards_compatibility_mode = "Role Names" not in topGroup
        self.topLevelOperator.DatasetGroup.resize(len(infoDir))

        # The role names MAY be different than those that we have loaded in the workflow
        #   because we might be importing from a project file made with a different workflow.
        # Therefore, we don't assert here.
        # assert workflow_role_names == list(topGroup['Role Names'][...])

        # Use the WorkingDirectory slot as a 'transaction' guard.
        # To prevent setupOutputs() from being called a LOT of times during this loop,
        # We'll disconnect it so the operator is not 'configured' while we do this work.
        # We'll reconnect it after we're done so the configure step happens all at once.
        working_dir = self.topLevelOperator.WorkingDirectory.value
        self.topLevelOperator.WorkingDirectory.disconnect()

        missing_role_warning_issued = False
        for laneIndex, (_, laneGroup) in enumerate(sorted(infoDir.items())):

            # BACKWARDS COMPATIBILITY:
            # Handle projects that didn't support multiple datasets per lane
            if backwards_compatibility_mode:
                assert "location" in laneGroup
                datasetInfo, dirty = self._readDatasetInfo(laneGroup, projectFilePath, headless)
                force_dirty |= dirty

                # Give the new info to the operator
                self.topLevelOperator.DatasetGroup[laneIndex][0].setValue(datasetInfo)
            else:
                for roleName, infoGroup in sorted(laneGroup.items()):
                    datasetInfo, dirty = self._readDatasetInfo(infoGroup, projectFilePath, headless)
                    force_dirty |= dirty

                    # Give the new info to the operator
                    if datasetInfo is not None:
                        try:
                            # Look up the STORED role name in the workflow operator's list of roles.
                            roleIndex = workflow_role_names.index(roleName)
                        except ValueError:
                            if not missing_role_warning_issued:
                                msg = (
                                    'Your project file contains a dataset for "{}", but the current '
                                    "workflow has no use for it. The stored dataset will be ignored.".format(roleName)
                                )
                                logger.error(msg)
                                missing_role_warning_issued = True
                        else:
                            self.topLevelOperator.DatasetGroup[laneIndex][roleIndex].setValue(datasetInfo)

        # Finish the 'transaction' as described above.
        self.topLevelOperator.WorkingDirectory.setValue(working_dir)

        self._dirty = force_dirty

    def _readDatasetInfo(self, infoGroup, projectFilePath, headless):
        # Unready datasets are represented with an empty group.
        if len(infoGroup) == 0:
            return None, False

        if "__class__" in infoGroup:
            info_class = self.InfoClassNames[infoGroup["__class__"][()].decode("utf-8")]
        else:  # legacy support
            location = infoGroup["location"][()].decode("utf-8")
            if location == "FileSystem":  # legacy support: a lot of DatasetInfo types are saved as "Filesystem"
                filePath = infoGroup["filePath"][()].decode("utf-8")
                if isUrl(filePath):
                    info_class = UrlDatasetInfo
                elif isRelative(filePath):
                    info_class = RelativeFilesystemDatasetInfo
                else:
                    info_class = FilesystemDatasetInfo
            else:
                info_class = PreloadedArrayDatasetInfo

        dirty = False
        try:
            datasetInfo = info_class.from_h5_group(infoGroup)
        except FileNotFoundError as e:
            if headless:
                shape = tuple(infoGroup["shape"])
                return PreloadedArrayDatasetInfo(preloaded_array=numpy.zeros(shape, dtype=numpy.uint8)), True

            from PyQt5.QtWidgets import QMessageBox
            from ilastik.widgets.ImageFileDialog import ImageFileDialog

            repaired_paths = []
            for missing_path in e.filename.split(os.path.pathsep):
                should_repair = QMessageBox.question(
                    None,
                    "Missing file",
                    (
                        f"File {missing_path} could not be found "
                        "(maybe you moved either that file or the .ilp project file). "
                        "Would you like to look for it elsewhere?"
                    ),
                    QMessageBox.Yes | QMessageBox.No,
                )
                if should_repair == QMessageBox.No:
                    raise e
                paths = ImageFileDialog(None).getSelectedPaths()
                if not paths:
                    raise e
                dirty = True
                repaired_paths.extend([str(p) for p in paths])

            if "filePath" in infoGroup:
                del infoGroup["filePath"]
            infoGroup["filePath"] = os.path.pathsep.join(repaired_paths).encode("utf-8")
            datasetInfo = FilesystemDatasetInfo.from_h5_group(infoGroup)

        return datasetInfo, dirty

    def updateWorkingDirectory(self, newpath, oldpath):
        newdir = PathComponents(newpath).externalDirectory
        olddir = PathComponents(oldpath).externalDirectory

        if newdir == olddir:
            return

        # Disconnect the working directory while we make these changes.
        # All the changes will take effect when we set the new working directory.
        self.topLevelOperator.WorkingDirectory.disconnect()

        for laneIndex, multislot in enumerate(self.topLevelOperator.DatasetGroup):
            for roleIndex, slot in enumerate(multislot):
                if not slot.ready():
                    # Skip if there is no dataset in this lane/role combination yet.
                    continue
                datasetInfo = slot.value
                if isinstance(datasetInfo, FilesystemDatasetInfo):

                    # construct absolute path and recreate relative to the new path
                    fp = PathComponents(datasetInfo.filePath, olddir).totalPath()
                    abspath, relpath = getPathVariants(fp, newdir)

                    # Same convention as in dataSelectionGui:
                    # Relative by default, unless the file is in a totally different tree from the working directory.
                    if relpath is not None and len(os.path.commonprefix([fp, abspath])) > 1:
                        datasetInfo.filePath = relpath
                    else:
                        datasetInfo.filePath = abspath

                    slot.setValue(datasetInfo, check_changed=False)

        self.topLevelOperator.WorkingDirectory.setValue(newdir)
        self._projectFilePath = newdir

    def isDirty(self):
        """ Return true if the current state of this item
            (in memory) does not match the state of the HDF5 group on disk.
            SerializableItems are responsible for tracking their own dirty/notdirty state."""
        return self._dirty

    def unload(self):
        """ Called if either
            (1) the user closed the project or
            (2) the project opening process needs to be aborted for some reason
                (e.g. not all items could be deserialized properly due to a corrupted ilp)
            This way we can avoid invalid state due to a partially loaded project. """
        self.topLevelOperator.DatasetGroup.resize(0)

    @property
    def _shouldRetrain(self):
        """
        Check if '--retrain' flag was passed via workflow command line arguments
        """
        workflow = self.topLevelOperator.parent
        if hasattr(workflow, "retrain"):
            return workflow.retrain
        else:
            return False


class Ilastik05DataSelectionDeserializer(AppletSerializer):
    """
    Deserializes the user's input data selections from an ilastik v0.5 project file.
    """

    def __init__(self, topLevelOperator):
        super(Ilastik05DataSelectionDeserializer, self).__init__("")
        self.topLevelOperator = topLevelOperator

    def serializeToHdf5(self, hdf5File, projectFilePath):
        # This class is for DEserialization only.
        pass

    def deserializeFromHdf5(self, hdf5File, projectFilePath, headless=False):
        # Check the overall file version
        ilastikVersion = hdf5File["ilastikVersion"][()]

        # This is the v0.5 import deserializer.  Don't work with 0.6 projects (or anything else).
        if ilastikVersion != 0.5:
            return

        # The 'working directory' for the purpose of constructing absolute
        #  paths from relative paths is the project file's directory.
        projectDir = os.path.split(projectFilePath)[0]
        self.topLevelOperator.WorkingDirectory.setValue(projectDir)

        # Access the top group and the info group
        try:
            # dataset = hdf5File["DataSets"]["dataItem00"]["data"]
            dataDir = hdf5File["DataSets"]
        except KeyError:
            # If our group (or subgroup) doesn't exist, then make sure the operator is empty
            self.topLevelOperator.DatasetGroup.resize(0)
            return

        self.topLevelOperator.DatasetGroup.resize(len(dataDir))
        for index, (datasetDirName, datasetDir) in enumerate(sorted(dataDir.items())):
            # Some older versions of ilastik 0.5 stored the data in tzyxc order.
            # Some power-users can enable a command-line flag that tells us to
            #  transpose the data back to txyzc order when we import the old project.
            default_axis_order = ilastik.utility.globals.ImportOptions.default_axis_order
            if default_axis_order is not None:
                import warnings

                # todo:axisorder: this will apply for other old ilastik projects as well... adapt the formulation.
                warnings.warn(
                    "Using a strange axis order to import ilastik 0.5 projects: {}".format(default_axis_order)
                )
                datasetInfo.axistags = vigra.defaultAxistags(default_axis_order)

            # We'll set up the link to the dataset in the old project file,
            #  but we'll set the location to ProjectInternal so that it will
            #  be copied to the new file when the project is saved.
            datasetInfo = ProjectInternalDatasetInfo(
                inner_path=str(projectFilePath + "/DataSets/" + datasetDirName + "/data"),
                nickname=f"{datasetDirName} (imported from v0.5)",
            )

            # Give the new info to the operator
            self.topLevelOperator.DatasetGroup[index][0].setValue(datasetInfo)

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        assert False

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath, headless=False):
        # This deserializer is a special-case.
        # It doesn't make use of the serializer base class, which makes assumptions about the file structure.
        # Instead, if overrides the public serialize/deserialize functions directly
        assert False

    def isDirty(self):
        """ Return true if the current state of this item
            (in memory) does not match the state of the HDF5 group on disk.
            SerializableItems are responsible for tracking their own dirty/notdirty state."""
        return False

    def unload(self):
        """ Called if either
            (1) the user closed the project or
            (2) the project opening process needs to be aborted for some reason
                (e.g. not all items could be deserialized properly due to a corrupted ilp)
            This way we can avoid invalid state due to a partially loaded project. """
        self.topLevelOperator.DatasetGroup.resize(0)
