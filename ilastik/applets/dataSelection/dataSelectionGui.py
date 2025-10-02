###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2025, the ilastik developers
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
import os
import threading
from functools import partial
from pathlib import Path
from typing import Dict, List, Set, Union, Optional

import h5py
from qtpy import uic
from qtpy.QtWidgets import QDialog, QMessageBox, QStackedWidget, QWidget, QApplication
from qtpy.QtCore import Qt
from vigra import AxisTags
from volumina.utility import preferences

from ilastik.applets.base.applet import DatasetConstraintError
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.utility import bind, log_exception
from ilastik.utility.gui import ThreadRouter, threadRouted
from ilastik.widgets.ImageFileDialog import ImageFileDialog
from ilastik.widgets.stackFileSelectionWidget import StackFileSelectionWidget, SubvolumeSelectionDlg
from lazyflow.slot import Slot
from lazyflow.utility.helpers import eq_shapes
from .dataLaneSummaryTableModel import DataLaneSummaryTableModel
from .datasetDetailedInfoTableModel import DatasetDetailedInfoTableModel
from .datasetDetailedInfoTableView import DatasetDetailedInfoTableView
from .datasetInfoEditorWidget import DatasetInfoEditorWidget
from .opDataSelection import (
    DatasetInfo,
    ProjectInternalDatasetInfo,
    MultiscaleUrlDatasetInfo,
)
from .multiscaleDatasetBrowser import MultiscaleDatasetBrowser

logger = logging.getLogger(__name__)


class LocationOptions(object):
    """Enum for location menu options"""

    Project = 0
    AbsolutePath = 1
    RelativePath = 2


class GuiMode(object):
    Normal = 0
    Batch = 1


class DataSelectionGui(QWidget):
    """
    Manages all GUI elements in the data selection applet.
    This class itself is the central widget and also owns/manages the applet drawer widgets.
    """

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################

    def centralWidget(self):
        return self

    def appletDrawer(self):
        return self._drawer

    def menus(self):
        return []

    def viewerControlWidget(self):
        return self._viewerControlWidgetStack

    def secondaryControlsWidget(self):
        return None

    def setImageIndex(self, imageIndex):
        if imageIndex is not None:
            self.laneSummaryTableView.selectRow(imageIndex)
            for detailWidget in self._detailViewerWidgets:
                detailWidget.selectRow(imageIndex)

    def stopAndCleanUp(self):
        self._cleaning_up = True
        for fn in self.__cleanup_fns:
            fn()

        for editor in list(self.volumeEditors.values()):
            self.viewerStack.removeWidget(editor)
            self._viewerControlWidgetStack.removeWidget(editor.viewerControlWidget())
            editor.stopAndCleanUp()
        self.volumeEditors.clear()

    def imageLaneAdded(self, laneIndex):
        if len(self.laneSummaryTableView.selectedIndexes()) == 0:
            self.laneSummaryTableView.selectRow(laneIndex)

        # We don't have any real work to do because this gui initiated the lane addition in the first place
        if self.guiMode != GuiMode.Batch:
            if len(self.topLevelOperator.DatasetGroup) != laneIndex + 1:
                import warnings

                warnings.warn(
                    "DataSelectionGui.imageLaneAdded(): length of dataset multislot out of sync with laneindex [%s != %s + 1]"
                    % (len(self.topLevelOperator.DatasetGroup), laneIndex)
                )

    def imageLaneRemoved(self, laneIndex, finalLength):
        # There's nothing to do here because the GUI already
        #  handles operator resizes via slot callbacks.
        pass

    def allowLaneSelectionChange(self):
        return False

    ###########################################
    ###########################################

    class UserCancelledError(BaseException):
        # This exception type is raised when the user cancels the
        #  addition of dataset files in the middle of the process somewhere.
        # It isn't an error -- it's used for control flow.
        pass

    def __init__(
        self,
        parentApplet,
        dataSelectionOperator,
        serializer,
        instructionText,
        guiMode=GuiMode.Normal,
        max_lanes=None,
        show_axis_details=False,
    ):
        """
        Constructor.

        :param dataSelectionOperator: The top-level operator.  Must be of type :py:class:`OpMultiLaneDataSelectionGroup`.
        :param serializer: The applet's serializer.  Must be of type :py:class:`DataSelectionSerializer`
        :param instructionText: A string to display in the applet drawer.
        :param guiMode: Either ``GuiMode.Normal`` or ``GuiMode.Batch``.  Currently, there is no difference between normal and batch mode.
        :param max_lanes: The maximum number of lanes that the user is permitted to add to this workflow.  If ``None``, there is no maximum.
        """
        super().__init__()
        self._cleaning_up = False
        self.__cleanup_fns = []
        self.parentApplet = parentApplet
        self._max_lanes = max_lanes
        self.show_axis_details = show_axis_details

        self._viewerControls = QWidget()
        self.topLevelOperator = dataSelectionOperator
        self.guiMode = guiMode
        self.serializer = serializer
        self.threadRouter = ThreadRouter(self)

        self._initCentralUic()
        self._initAppletDrawerUic(instructionText)

        self._viewerControlWidgetStack = QStackedWidget(self)
        self._default_h5n5_volumes: Dict[int, Set[str]] = {}

        self.__cleanup_fns.append(self.topLevelOperator.DatasetGroup.notifyRemove(bind(self._handleImageRemove)))

        opWorkflow = self.topLevelOperator.parent
        assert hasattr(
            opWorkflow.shell, "onSaveProjectActionTriggered"
        ), "This class uses the IlastikShell.onSaveProjectActionTriggered function.  Did you rename it?"

    def get_project_file(self) -> h5py.File:
        return self.topLevelOperator.ProjectFile.value

    def _initCentralUic(self):
        """
        Load the GUI from the ui file into this class and connect it with event handlers.
        """
        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0] + "/"
        uic.loadUi(localDir + "/dataSelection.ui", self)

        self._initTableViews()
        self._initViewerStack()
        self.splitter.setSizes([150, 850])

    def _initAppletDrawerUic(self, instructionText):
        """
        Load the ui file for the applet drawer, which we own.
        """
        localDir = os.path.split(__file__)[0] + "/"
        self._drawer = uic.loadUi(localDir + "/dataSelectionDrawer.ui")
        self._drawer.instructionLabel.setText(instructionText)

    @threadRouted
    def _handleImageRemove(self, multislot, index, finalLength):
        # Remove the viewer for this dataset
        datasetSlot = self.topLevelOperator.DatasetGroup[index]
        if datasetSlot in list(self.volumeEditors.keys()):
            editor = self.volumeEditors[datasetSlot]
            self.viewerStack.removeWidget(editor)
            self._viewerControlWidgetStack.removeWidget(editor.viewerControlWidget())
            editor.stopAndCleanUp()

    @threadRouted
    def _update_add_button_status(self, viewer):
        if self._max_lanes:
            opTop = self.topLevelOperator
            status = len(opTop.DatasetGroup) < self._max_lanes
            viewer.setEnabled(status)

    @threadRouted
    def _update_summary_buttons_status(self, *args):
        if self._max_lanes:
            opTop = self.topLevelOperator
            status = len(opTop.DatasetGroup) < self._max_lanes
            for button in self.laneSummaryTableView.addFilesButtons.values():
                try:
                    button.setEnabled(status)
                except RuntimeError:
                    # FIXME: Button might be deleted due to a bug (https://github.com/ilastik/ilastik/issues/2380)
                    logger.debug("Summary button seems to be deleted, cannot execute callback")

    def _initTableViews(self):
        self.fileInfoTabWidget.setTabText(0, "Summary")
        self.laneSummaryTableView.setModel(DataLaneSummaryTableModel(self, self.topLevelOperator))
        self.laneSummaryTableView.dataLaneSelected.connect(self.showDataset)
        self.laneSummaryTableView.addFilesRequested.connect(self.addFiles)
        self.laneSummaryTableView.addStackRequested.connect(self.addStack)
        self.laneSummaryTableView.removeLanesRequested.connect(self.handleRemoveLaneButtonClicked)

        # Monitor Lane-changes to enable/disable add files buttons in summary table
        self.__cleanup_fns.append(self.topLevelOperator.DatasetGroup.notifyRemoved(self._update_summary_buttons_status))
        self.__cleanup_fns.append(
            self.topLevelOperator.DatasetGroup.notifyInserted(self._update_summary_buttons_status)
        )

        self._detailViewerWidgets = []

        for roleIndex, role in enumerate(self.topLevelOperator.DatasetRoles.value):
            detailViewer = DatasetDetailedInfoTableView(self)
            detailViewer.setModel(DatasetDetailedInfoTableModel(self, self.topLevelOperator, roleIndex))
            self._detailViewerWidgets.append(detailViewer)

            # Button
            detailViewer.addFilesRequested.connect(partial(self.addFiles, roleIndex))
            detailViewer.addStackRequested.connect(partial(self.addStack, roleIndex))
            detailViewer.addMultiscaleRequested.connect(partial(self.addMultiscaleDataset, roleIndex))
            detailViewer.addDvidVolumeRequested.connect(partial(self.addDvidVolume, roleIndex))

            # Monitor changes to each lane so we can enable/disable the 'add lanes' button for each tab
            self.__cleanup_fns.append(
                self.topLevelOperator.DatasetGroup.notifyInserted(bind(self._update_add_button_status, detailViewer))
            )
            self.__cleanup_fns.append(
                self.topLevelOperator.DatasetGroup.notifyRemoved(bind(self._update_add_button_status, detailViewer))
            )

            # Context menu
            detailViewer.replaceWithFileRequested.connect(partial(self.handleReplaceFile, roleIndex))
            detailViewer.replaceWithStackRequested.connect(partial(self.addStack, roleIndex))
            detailViewer.editRequested.connect(partial(self.editDatasetInfo, roleIndex))
            detailViewer.resetRequested.connect(partial(self.handleClearDatasets, roleIndex))

            # Drag-and-drop
            detailViewer.addFilesRequestedDrop.connect(partial(self.addFileNames, roleIndex=roleIndex))

            # Selection handling
            def showFirstSelectedDataset(_roleIndex, lanes):
                if lanes:
                    self.showDataset(lanes[0], _roleIndex)

            detailViewer.dataLaneSelected.connect(partial(showFirstSelectedDataset, roleIndex))

            # Scale selection handling
            detailViewer.scaleSelected.connect(self.handleScaleSelected)

            self.fileInfoTabWidget.insertTab(roleIndex, detailViewer, role)

        self.fileInfoTabWidget.currentChanged.connect(self.handleSwitchTabs)
        self.fileInfoTabWidget.setCurrentIndex(0)

    def handleSwitchTabs(self, tabIndex):
        if tabIndex < len(self._detailViewerWidgets):
            roleIndex = tabIndex  # If summary tab is moved to the front, change this line.
            detailViewer = self._detailViewerWidgets[roleIndex]
            detailViewer.refresh_scale_options()
            selectedLanes = detailViewer.selectedLanes
            if selectedLanes:
                self.showDataset(selectedLanes[0], roleIndex)

    def _initViewerStack(self):
        self.volumeEditors = {}
        self.viewerStack.addWidget(QWidget())

    def handleRemoveLaneButtonClicked(self):
        """
        The user clicked the "Remove" button.
        Remove the currently selected row(s) from both the GUI and the top-level operator.
        """
        # Figure out which lanes to remove
        selectedIndexes = self.laneSummaryTableView.selectedIndexes()
        rows = set()
        for modelIndex in selectedIndexes:
            rows.add(modelIndex.row())

        # Don't remove the last row, which is just buttons.
        rows.discard(self.laneSummaryTableView.model().rowCount() - 1)

        # Remove in reverse order so row numbers remain consistent
        for row in reversed(sorted(rows)):
            # Remove lanes from the operator.
            # The table model will notice the changes and update the rows accordingly.
            finalSize = len(self.topLevelOperator.DatasetGroup) - 1
            self.topLevelOperator.DatasetGroup.removeSlot(row, finalSize)

    @threadRouted
    def showDataset(self, laneIndex, roleIndex=None):
        if self._cleaning_up:
            return
        if laneIndex == -1:
            self.viewerStack.setCurrentIndex(0)
            return

        assert threading.current_thread().name == "MainThread"

        if laneIndex >= len(self.topLevelOperator.DatasetGroup):
            return
        datasetSlot = self.topLevelOperator.DatasetGroup[laneIndex]

        # Create if necessary
        if datasetSlot not in list(self.volumeEditors.keys()):

            class DatasetViewer(LayerViewerGui):
                def moveToTop(self, roleIndex):
                    opLaneView = self.topLevelOperatorView
                    if not opLaneView.DatasetRoles.ready():
                        return
                    datasetRoles = opLaneView.DatasetRoles.value
                    if roleIndex >= len(datasetRoles):
                        return
                    roleName = datasetRoles[roleIndex]
                    try:
                        layerIndex = [l.name for l in self.layerstack].index(roleName)
                    except ValueError:
                        return
                    else:
                        self.layerstack.selectRow(layerIndex)
                        self.layerstack.moveSelectedToTop()

                def setupLayers(self):
                    opLaneView = self.topLevelOperatorView
                    if not opLaneView.DatasetRoles.ready():
                        return []
                    layers = []
                    datasetRoles = opLaneView.DatasetRoles.value
                    for roleIndex, slot in enumerate(opLaneView.ImageGroup):
                        if slot.ready():
                            roleName = datasetRoles[roleIndex]
                            layer = self.createStandardLayerFromSlot(slot)
                            layer.name = roleName
                            layers.append(layer)
                    return layers

            opLaneView = self.topLevelOperator.getLane(laneIndex)
            layerViewer = DatasetViewer(self.parentApplet, opLaneView, crosshair=False)

            # Maximize the x-y view by default.
            layerViewer.volumeEditorWidget.quadview.ensureMaximized(2)

            self.volumeEditors[datasetSlot] = layerViewer
            self.viewerStack.addWidget(layerViewer)
            self._viewerControlWidgetStack.addWidget(layerViewer.viewerControlWidget())

        # Show the right one
        viewer = self.volumeEditors[datasetSlot]
        displayedRole = self.fileInfoTabWidget.currentIndex()
        viewer.moveToTop(displayedRole)
        self.viewerStack.setCurrentWidget(viewer)
        self._viewerControlWidgetStack.setCurrentWidget(viewer.viewerControlWidget())

    def handleReplaceFile(self, roleIndex, startingLaneNum):
        self.addFiles(roleIndex, startingLaneNum)

    def addFiles(self, roleIndex, startingLaneNum=None):
        """
        The user clicked the "Add File" button.
        Ask him to choose a file (or several) and add them to both
          the GUI table and the top-level operator inputs.
        """
        # Launch the "Open File" dialog
        paths = ImageFileDialog(self).getSelectedPaths()
        self.addFileNames(paths, startingLaneNum, roleIndex)

    def addFileNames(self, paths: Optional[List[Path]], startingLaneNum: Optional[int], roleIndex: int):
        if not paths:
            return

        infos = []
        for path in paths:
            try:
                full_path = self._get_dataset_full_path(path, roleIndex=roleIndex)
                info = self.instantiate_dataset_info(url=str(full_path), role=roleIndex)
                infos.append(info)
            except DataSelectionGui.UserCancelledError:
                pass

        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.addLanes(infos, roleIndex=roleIndex, startingLaneNum=startingLaneNum)
        except Exception as ex:
            log_exception(logger)
            QMessageBox.critical(self, "Error loading file", str(ex))
        finally:
            QApplication.restoreOverrideCursor()

    def _findFirstEmptyLane(self, roleIndex):
        opTop = self.topLevelOperator

        # Determine the number of files this role already has
        # Search for the last valid value.
        firstNewLane = 0
        for laneIndex, slot in reversed(list(zip(list(range(len(opTop.DatasetGroup))), opTop.DatasetGroup))):
            if slot[roleIndex].ready():
                firstNewLane = laneIndex + 1
                break
        return firstNewLane

    def getNumLanes(self) -> int:
        return len(self.topLevelOperator.DatasetGroupOut)

    def getInfoSlots(self, roleIndex: int):
        return [self.topLevelOperator.DatasetGroup[laneIndex][roleIndex] for laneIndex in range(self.getNumLanes())]

    def addLanes(self, new_infos: List[DatasetInfo], roleIndex, startingLaneNum=None):
        """
        Add the given filenames to both the GUI table and the top-level operator inputs.
        If startingLaneNum is None, the filenames will be *appended* to the role's list of files.
        """
        originalNumLanes = self.getNumLanes()
        startingLaneNum, endingLaneNum = self._determineLaneRange(new_infos, startingLaneNum)
        if originalNumLanes < endingLaneNum + 1:
            self.topLevelOperator.DatasetGroup.resize(endingLaneNum + 1)
        info_slots = self.getInfoSlots(roleIndex)[startingLaneNum : endingLaneNum + 1]

        try:
            if not self.applyDatasetInfos(new_infos, info_slots):
                self.topLevelOperator.DatasetGroup.resize(originalNumLanes)
                return

            self._checkDataFormatWarnings(roleIndex, startingLaneNum, endingLaneNum)

            # Show the first image
            self.showDataset(startingLaneNum, roleIndex)

            # if only adding new lanes, notify the workflow
            if startingLaneNum >= originalNumLanes:
                workflow = self.parentApplet.topLevelOperator.parent
                workflow.handleNewLanesAdded()

            # Notify the workflow that something that could affect applet readyness has occurred.
            self.parentApplet.appletStateUpdateRequested()
        except Exception as e:
            self.topLevelOperator.DatasetGroup.resize(originalNumLanes)
            QMessageBox.critical(self, "File selection error", str(e))
            logger.error(e, exc_info=True)

    def applyDatasetInfos(self, new_infos: List[DatasetInfo], info_slots: List[Slot]):
        original_infos = []

        def revert():
            for slot, original_info in zip(info_slots, original_infos):
                if original_info is not None:
                    slot.setValue(original_info)
                else:
                    slot.disconnect()

        try:
            for new_info, info_slot in zip(new_infos, info_slots):
                original_infos.append(info_slot.value if info_slot.ready() else None)
                while True:
                    try:
                        info_slot.setValue(new_info)
                        break
                    except DatasetConstraintError as e:
                        try:
                            self._switch_scale_in_other_roles_to_match(new_info, info_slot)
                        except DatasetConstraintError:
                            # Pop up the warning with the original error
                            QMessageBox.warning(self, "Incompatible dataset", str(e))
                            info_editor = DatasetInfoEditorWidget(self, [new_info], self.serializer)
                            if info_editor.exec_() == QDialog.Rejected:
                                revert()
                                return False
                            new_info = info_editor.edited_infos[0]
            return True
        except Exception as e:
            revert()
            raise e
        finally:
            self.parentApplet.appletStateUpdateRequested()

    def _switch_scale_in_other_roles_to_match(self, new_info: DatasetInfo, new_slot: Slot):
        """
        Find out which lane this slot belongs to and check if
        - any other datasets in this lane are multiscale
        - all of them have a scale that would match `info`
        If so, switch them to this matching scale.
        """
        lane_index = None
        for i in range(self.getNumLanes()):
            if new_slot in self.topLevelOperator.DatasetGroup[i]:
                lane_index = i
                break
        assert lane_index is not None, "Bug (please report): Tried to add dataset to slot that doesn't exist"
        dataset_group = self.topLevelOperator.get_lane(lane_index).DatasetGroupOut
        other_slots_with_multiscales = [s for s in dataset_group if s is not new_slot and s.ready() and s.value.scales]
        if not other_slots_with_multiscales:
            raise DatasetConstraintError(
                "DataSelection", "Can't make this dataset work by switching scale in other roles (no multiscales)"
            )
        other_slots_single_scale = [s for s in dataset_group if s is not new_slot and s.ready() and not s.value.scales]
        new_tagged_shape = dict(zip(new_info.axistags.keys(), new_info.laneShape))
        other_single_scale_shapes = [
            dict(zip(slot.value.axistags.keys(), slot.value.laneShape)) for slot in other_slots_single_scale
        ]
        matches_other_singles = all(
            eq_shapes(new_tagged_shape, other_shape) for other_shape in other_single_scale_shapes
        )
        matches_other_multis = all(
            other_slot.value.has_scale_matching_shape(new_tagged_shape) and not other_slot.value.scale_locked
            for other_slot in other_slots_with_multiscales
        )
        if matches_other_singles and matches_other_multis:
            target_scale = other_slots_with_multiscales[0].value.get_scale_matching_shape(new_tagged_shape)
            self.handleScaleSelected(lane_index, target_scale)
        else:
            raise DatasetConstraintError(
                "DataSelection", "Can't make this dataset work by switching scale in other roles (no matching scale)"
            )

    def _determineLaneRange(self, infos: List[DatasetInfo], startingLaneNum=None):
        """
        Determine which lanes should be configured if the user wants to add the given infos starting at startingLaneNum.
        If startingLaneNum is None, assume the user wants to APPEND the files to the role's slots.
        """
        if startingLaneNum is None or startingLaneNum == -1:
            startingLaneNum = len(self.topLevelOperator.DatasetGroup)
            endingLane = startingLaneNum + len(infos) - 1
        else:
            assert startingLaneNum < len(self.topLevelOperator.DatasetGroup)
            max_files = len(self.topLevelOperator.DatasetGroup) - startingLaneNum
            if len(infos) > max_files:
                raise Exception(
                    f"You selected {len(infos)} files for {max_files} slots. To add new files use "
                    "the 'Add new...' option in the context menu or the button in the last row."
                )
            endingLane = min(startingLaneNum + len(infos) - 1, len(self.topLevelOperator.DatasetGroup))

        if self._max_lanes and endingLane >= self._max_lanes:
            raise Exception(f"You may not add more than {self._max_lanes} file(s) to this workflow.")

        return (startingLaneNum, endingLane)

    def _add_default_inner_path(self, roleIndex: int, inner_path: str):
        paths = self._default_h5n5_volumes.get(roleIndex, set())
        paths.add(inner_path)
        self._default_h5n5_volumes[roleIndex] = paths

    def _get_previously_used_inner_paths(self, roleIndex: int) -> Set[str]:
        previous_paths = self._default_h5n5_volumes.get(roleIndex, set())
        return previous_paths.copy()

    def _get_dataset_full_path(self, filePath: Path, roleIndex: int) -> Path:
        if not DatasetInfo.fileHasInternalPaths(filePath):
            return filePath
        datasetNames = DatasetInfo.getPossibleInternalPathsFor(filePath.absolute())
        if len(datasetNames) == 0:
            raise RuntimeError(f"File {filePath} has no image datasets")
        keep_selected_as_default = False
        if len(datasetNames) == 1:
            selected_dataset = datasetNames.pop()
            keep_selected_as_default = True
        else:
            auto_inner_paths = self._get_previously_used_inner_paths(roleIndex).intersection(set(datasetNames))
            if len(auto_inner_paths) == 1:
                selected_dataset = auto_inner_paths.pop()
            else:
                # Ask the user which dataset to choose
                dlg = SubvolumeSelectionDlg(datasetNames, self, offer_remember_dataset=True)
                if dlg.exec_() != QDialog.Accepted:
                    raise DataSelectionGui.UserCancelledError()
                selected_index = dlg.combo.currentIndex()
                keep_selected_as_default = dlg.checkbox.isChecked()
                selected_dataset = str(datasetNames[selected_index])
        if keep_selected_as_default:
            self._add_default_inner_path(roleIndex=roleIndex, inner_path=selected_dataset)
        return filePath / selected_dataset.lstrip("/")

    def _get_custom_axistags_from_previous_lane(self, role: Union[str, int], info: DatasetInfo) -> Optional[AxisTags]:
        if self.parentApplet.num_lanes == 0:
            return None
        lane = self.parentApplet.get_lane(-1)
        previous_info = lane.get_dataset_info(role)
        if (
            previous_info is not None
            and previous_info.default_tags != previous_info.axistags
            and previous_info.shape5d.c == info.shape5d.c
            and len(previous_info.axistags) == len(info.axistags)
        ):
            return previous_info.axistags
        return None

    def instantiate_dataset_info(self, url: str, role: Union[str, int], *info_args, **info_kwargs) -> DatasetInfo:
        info = self.parentApplet.create_dataset_info(url=url, *info_args, **info_kwargs)
        if "axistags" in info_kwargs:
            return info  # This lane has custom axistags already
        custom_axistags = self._get_custom_axistags_from_previous_lane(role=role, info=info)
        if custom_axistags:
            return self.parentApplet.create_dataset_info(url=url, *info_args, **info_kwargs, axistags=custom_axistags)
        return info

    def _checkDataFormatWarnings(self, roleIndex, startingLaneNum, endingLane):
        warn_needed = False
        opTop = self.topLevelOperator
        for lane_index in range(startingLaneNum, endingLane + 1):
            output_slot = opTop.ImageGroup[lane_index][roleIndex]
            if output_slot.meta.inefficient_format:
                warn_needed = True

        if warn_needed:
            QMessageBox.warning(
                self,
                "Inefficient Data Format",
                "Your data cannot be accessed efficiently in its current format.  "
                "Check the console output for details.\n"
                "(For HDF5 files, be sure to enable chunking on your dataset.)",
            )

    def addStack(self, roleIndex, laneIndex):
        """
        The user clicked the "Import Stack Files" button.
        """
        stackDlg = StackFileSelectionWidget(self)
        stackDlg.exec_()
        if stackDlg.result() != QDialog.Accepted or not stackDlg.selectedFiles:
            return

        # FIXME: ask first if stack should be internalized to project file
        # also, check prefer_2d, size/volume and presence of 'z' to determine this
        url = os.path.pathsep.join(stackDlg.selectedFiles)
        stack_info = self.instantiate_dataset_info(url=url, role=roleIndex, sequence_axis=stackDlg.sequence_axis)

        try:
            # FIXME: do this inside a Request
            self.parentApplet.busy = True
            inner_path = stack_info.importAsLocalDataset(project_file=self.get_project_file())
            internal_info = ProjectInternalDatasetInfo(
                inner_path=inner_path, nickname=stack_info.nickname, project_file=self.get_project_file()
            )
        finally:
            self.parentApplet.busy = False
        self.addLanes([internal_info], roleIndex, laneIndex)

    def handleClearDatasets(self, roleIndex, selectedRows):
        for row in selectedRows:
            self.topLevelOperator.DatasetGroup[row][roleIndex].disconnect()

        # Remove all operators that no longer have any connected slots
        laneIndexes = list(range(len(self.topLevelOperator.DatasetGroup)))
        for laneIndex, multislot in reversed(list(zip(laneIndexes, self.topLevelOperator.DatasetGroup))):
            any_ready = False
            for slot in multislot:
                any_ready |= slot.ready()
            if not any_ready:
                self.topLevelOperator.DatasetGroup.removeSlot(laneIndex, len(self.topLevelOperator.DatasetGroup) - 1)

        # Notify the workflow that something that could affect applet readyness has occurred.
        self.parentApplet.appletStateUpdateRequested()

    def editDatasetInfo(self, roleIndex, laneIndexes):
        all_info_slots = self.getInfoSlots(roleIndex)
        selected_info_slots = [all_info_slots[idx] for idx in laneIndexes]
        infos = [slot.value for slot in selected_info_slots]
        editorDlg = DatasetInfoEditorWidget(self, infos, self.serializer)
        if editorDlg.exec_() == QDialog.Accepted:
            self.applyDatasetInfos(editorDlg.edited_infos, selected_info_slots)

    def addMultiscaleDataset(self, roleIndex, laneIndex):
        PREFERENCES_GROUP = "DataSelection"
        RECENT_URIS_KEY = "recent urls"
        history = preferences.get(PREFERENCES_GROUP, RECENT_URIS_KEY) or []
        browser = MultiscaleDatasetBrowser(history=history, parent=self)

        if browser.exec_() == MultiscaleDatasetBrowser.Rejected:
            return

        uri = browser.selected_uri
        if uri in history:
            history.remove(uri)
        preferences.set(PREFERENCES_GROUP, RECENT_URIS_KEY, [uri] + history[:9])

        info = self.instantiate_dataset_info(url=uri, role=roleIndex)
        assert isinstance(info, MultiscaleUrlDatasetInfo)

        is_not_new_lane = laneIndex > -1
        if is_not_new_lane:
            # Adding a multiscale to another role: switch to the scale that matches the dataset(s) in other role(s)
            dataset_group = self.topLevelOperator.get_lane(laneIndex).DatasetGroupOut
            for other_role_index, role_dataset_slot in enumerate(dataset_group):
                if not role_dataset_slot.ready() or other_role_index == roleIndex:
                    continue
                shape_in_other_role = dict(
                    zip(role_dataset_slot.value.axistags.keys(), role_dataset_slot.value.laneShape)
                )
                try:
                    info.switch_to_scale_with_shape(shape_in_other_role)
                    info.scale_locked = role_dataset_slot.value.scale_locked
                except DatasetConstraintError:
                    other_role = self.topLevelOperator.DatasetRoles.value[other_role_index]
                    QMessageBox.warning(
                        self,
                        "Incompatible dataset",
                        f"None of the scales in the chosen multiscale dataset have the same shape as the dataset in {other_role}.",
                    )
                    return

        self.addLanes([info], roleIndex=roleIndex, startingLaneNum=laneIndex)

    def addDvidVolume(self, roleIndex, laneIndex):
        group = "DataSelection"
        recent_hosts_key = "Recent DVID Hosts"
        recent_hosts = preferences.get(group, recent_hosts_key)
        if not recent_hosts:
            recent_hosts = ["localhost:8000"]
        recent_hosts = [
            h for h in recent_hosts if h
        ]  # There used to be a bug where empty strings could be saved. Filter those out.

        recent_nodes_key = "Recent DVID Nodes"
        recent_nodes = preferences.get(group, recent_nodes_key) or {}

        from .dvidDataSelectionBrowser import DvidDataSelectionBrowser

        browser = DvidDataSelectionBrowser(recent_hosts, recent_nodes, parent=self)
        if browser.exec_() == DvidDataSelectionBrowser.Rejected:
            return

        if None in browser.get_selection():
            QMessageBox.critical("Couldn't use your selection.")
            return

        rois = None
        hostname, repo_uuid, volume_name, node_uuid, typename = browser.get_selection()
        dvid_url = f"http://{hostname}/api/node/{node_uuid}/{volume_name}"
        subvolume_roi = browser.get_subvolume_roi()

        # Relocate host to top of 'recent' list, and limit list to 10 items.
        try:
            i = recent_hosts.index(hostname)
            del recent_hosts[i]
        except ValueError:
            pass
        finally:
            recent_hosts.insert(0, hostname)
            recent_hosts = recent_hosts[:10]

        # Save pref
        preferences.set(group, recent_hosts_key, recent_hosts)

        recent_nodes[hostname] = node_uuid
        preferences.set(group, recent_nodes_key, recent_nodes)

        self.addLanes([MultiscaleUrlDatasetInfo(url=dvid_url, subvolume_roi=subvolume_roi)], roleIndex)

    def handleScaleSelected(self, laneIndex, scale_key):
        op_lane = self.topLevelOperator.get_lane(laneIndex)
        op_lane.ScaleChangeFinished.disconnect()
        op_lane.ActiveScaleGroup.setValue(scale_key)
        op_lane.ScaleChangeFinished.setValue(True)
        self.showDataset(laneIndex)  # Update layer order according to current role tab
