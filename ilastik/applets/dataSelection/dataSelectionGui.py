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
#		   http://ilastik.org/license.html
###############################################################################
#Python
import os
from pathlib import Path
from typing import List
import sys
import threading
import h5py
import z5py
import numpy
from functools import partial
import logging
logger = logging.getLogger(__name__)

#PyQt
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QFileDialog, QMessageBox, QStackedWidget, QWidget
)
#lazyflow
from lazyflow.request import Request

#volumina
from volumina.utility import PreferencesManager

#ilastik
from ilastik.config import cfg as ilastik_config
from ilastik.utility import bind, log_exception
from ilastik.utility.gui import ThreadRouter, threadRouted
from lazyflow.utility.pathHelpers import getPathVariants, PathComponents
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.applets.base.applet import DatasetConstraintError

from .opDataSelection import OpDataSelection, DatasetInfo
from .dataLaneSummaryTableModel import DataLaneSummaryTableModel
from .datasetInfoEditorWidget import DatasetInfoEditorWidget
from ilastik.widgets.stackFileSelectionWidget import StackFileSelectionWidget, H5N5VolumeSelectionDlg
from .datasetDetailedInfoTableModel import DatasetDetailedInfoColumn, DatasetDetailedInfoTableModel
from .datasetDetailedInfoTableView import DatasetDetailedInfoTableView
from .precomputedVolumeBrowser import PrecomputedVolumeBrowser
from .ImageFileDialog import ImageFileDialog

try:
    import libdvid
    _has_dvid_support = True
except:
    _has_dvid_support = False

#===----------------------------------------------------------------------------------------------------------------===

class LocationOptions(object):
    """ Enum for location menu options """
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

    def centralWidget( self ):
        return self

    def appletDrawer( self ):
        return self._drawer

    def menus( self ):
        return []

    def viewerControlWidget(self):
        return self._viewerControlWidgetStack

    def setImageIndex(self, imageIndex):
        if imageIndex is not None:
            self.laneSummaryTableView.selectRow(imageIndex)
            for detailWidget in self._detailViewerWidgets:
                detailWidget.selectRow(imageIndex)

    def stopAndCleanUp(self):
        self._cleaning_up = True
        for editor in list(self.volumeEditors.values()):
            self.viewerStack.removeWidget( editor )
            self._viewerControlWidgetStack.removeWidget( editor.viewerControlWidget() )
            editor.stopAndCleanUp()
        self.volumeEditors.clear()

    def imageLaneAdded(self, laneIndex):
        if len(self.laneSummaryTableView.selectedIndexes()) == 0:
            self.laneSummaryTableView.selectRow(laneIndex)
        
        # We don't have any real work to do because this gui initiated the lane addition in the first place
        if self.guiMode != GuiMode.Batch:
            if(len(self.topLevelOperator.DatasetGroup) != laneIndex+1):
                import warnings
                warnings.warn("DataSelectionGui.imageLaneAdded(): length of dataset multislot out of sync with laneindex [%s != %s + 1]" % (len(self.topLevelOperator.DatasetGroup), laneIndex))

    def imageLaneRemoved(self, laneIndex, finalLength):
        # There's nothing to do here because the GUI already 
        #  handles operator resizes via slot callbacks.
        pass

    def allowLaneSelectionChange(self):
        return False

    ###########################################
    ###########################################

    class UserCancelledError(Exception):
        # This exception type is raised when the user cancels the 
        #  addition of dataset files in the middle of the process somewhere.
        # It isn't an error -- it's used for control flow.
        pass

    def __init__(self, parentApplet, dataSelectionOperator, serializer, instructionText, guiMode=GuiMode.Normal, max_lanes=None, show_axis_details=False):
        """
        Constructor.
        
        :param dataSelectionOperator: The top-level operator.  Must be of type :py:class:`OpMultiLaneDataSelectionGroup`.
        :param serializer: The applet's serializer.  Must be of type :py:class:`DataSelectionSerializer`
        :param instructionText: A string to display in the applet drawer.
        :param guiMode: Either ``GuiMode.Normal`` or ``GuiMode.Batch``.  Currently, there is no difference between normal and batch mode.
        :param max_lanes: The maximum number of lanes that the user is permitted to add to this workflow.  If ``None``, there is no maximum.
        """
        super(DataSelectionGui, self).__init__()
        self._cleaning_up = False
        self.parentApplet = parentApplet
        self._max_lanes = max_lanes
        self._default_h5n5_volumes = {}
        self.show_axis_details = show_axis_details

        self._viewerControls = QWidget()
        self.topLevelOperator = dataSelectionOperator
        self.guiMode = guiMode
        self.serializer = serializer
        self.threadRouter = ThreadRouter(self)

        self._initCentralUic()
        self._initAppletDrawerUic(instructionText)
        
        self._viewerControlWidgetStack = QStackedWidget(self)

        def handleImageRemove(multislot, index, finalLength):
            # Remove the viewer for this dataset
            datasetSlot = self.topLevelOperator.DatasetGroup[index]
            if datasetSlot in list(self.volumeEditors.keys()):
                editor = self.volumeEditors[datasetSlot]
                self.viewerStack.removeWidget( editor )
                self._viewerControlWidgetStack.removeWidget( editor.viewerControlWidget() )
                editor.stopAndCleanUp()

        self.topLevelOperator.DatasetGroup.notifyRemove( bind( handleImageRemove ) )
        
        opWorkflow = self.topLevelOperator.parent
        assert hasattr(opWorkflow.shell, 'onSaveProjectActionTriggered'), \
            "This class uses the IlastikShell.onSaveProjectActionTriggered function.  Did you rename it?"


    def _initCentralUic(self):
        """
        Load the GUI from the ui file into this class and connect it with event handlers.
        """
        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]+'/'
        uic.loadUi(localDir+"/dataSelection.ui", self)

        self._initTableViews()
        self._initViewerStack()
        self.splitter.setSizes( [150, 850] )

    def _initAppletDrawerUic(self, instructionText):
        """
        Load the ui file for the applet drawer, which we own.
        """
        localDir = os.path.split(__file__)[0]+'/'
        self._drawer = uic.loadUi(localDir+"/dataSelectionDrawer.ui")
        self._drawer.instructionLabel.setText( instructionText )

    def _initTableViews(self):
        self.fileInfoTabWidget.setTabText( 0, "Summary" )
        self.laneSummaryTableView.setModel( DataLaneSummaryTableModel(self, self.topLevelOperator) )
        self.laneSummaryTableView.dataLaneSelected.connect( self.showDataset )
        self.laneSummaryTableView.addFilesRequested.connect( self.addFiles )
        self.laneSummaryTableView.addStackRequested.connect( self.addStack )
        self.laneSummaryTableView.removeLanesRequested.connect( self.handleRemoveLaneButtonClicked )

        # These two helper functions enable/disable an 'add files' button for a given role  
        #  based on the the max lane index for that role and the overall permitted max_lanes
        def _update_button_status(viewer, role_index):
            if self._max_lanes:
                viewer.setEnabled( self._findFirstEmptyLane(role_index) < self._max_lanes )

        def _handle_lane_added( button, role_index, lane_slot, lane_index ):
            def _handle_role_slot_added( role_slot, added_slot_index, *args ):
                if added_slot_index == role_index:
                    role_slot.notifyReady( bind(_update_button_status, button, role_index) )
                    role_slot.notifyUnready( bind(_update_button_status, button, role_index) )
            lane_slot[lane_index].notifyInserted( _handle_role_slot_added )

        self._retained = [] # Retain menus so they don't get deleted
        self._detailViewerWidgets = []
        for roleIndex, role in enumerate(self.topLevelOperator.DatasetRoles.value):
            detailViewer = DatasetDetailedInfoTableView(self)
            detailViewer.setModel(DatasetDetailedInfoTableModel(self,
                self.topLevelOperator, roleIndex))
            self._detailViewerWidgets.append( detailViewer )

            # Button
            detailViewer.addFilesRequested.connect(
                    partial(self.addFiles, roleIndex))
            detailViewer.addStackRequested.connect(
                    partial(self.addStack, roleIndex))
            detailViewer.addPrecomputedVolumeRequested.connect(
                partial(self.addPrecomputedVolume, roleIndex))
            detailViewer.addRemoteVolumeRequested.connect(
                    partial(self.addDvidVolume, roleIndex))

            # Monitor changes to each lane so we can enable/disable the 'add lanes' button for each tab
            self.topLevelOperator.DatasetGroup.notifyInserted( bind( _handle_lane_added, detailViewer, roleIndex ) )
            self.topLevelOperator.DatasetGroup.notifyRemoved( bind( _update_button_status, detailViewer, roleIndex ) )
            
            # While we're at it, do the same for the buttons in the summary table, too
            self.topLevelOperator.DatasetGroup.notifyInserted( bind( _handle_lane_added, self.laneSummaryTableView.addFilesButtons[roleIndex], roleIndex ) )
            self.topLevelOperator.DatasetGroup.notifyRemoved( bind( _update_button_status, self.laneSummaryTableView.addFilesButtons[roleIndex], roleIndex ) )
            
            # Context menu
            detailViewer.replaceWithFileRequested.connect(
                    partial(self.handleReplaceFile, roleIndex) )
            detailViewer.replaceWithStackRequested.connect(
                    partial(self.addStack, roleIndex) )
            detailViewer.editRequested.connect(
                    partial(self.editDatasetInfo, roleIndex) )
            detailViewer.resetRequested.connect(
                    partial(self.handleClearDatasets, roleIndex) )

            # Drag-and-drop
            detailViewer.addFilesRequestedDrop.connect( partial( self.addFileNames, roleIndex=roleIndex ) )

            # Selection handling
            def showFirstSelectedDataset( _roleIndex, lanes ):
                if lanes:
                    self.showDataset( lanes[0], _roleIndex )
            detailViewer.dataLaneSelected.connect( partial(showFirstSelectedDataset, roleIndex) )

            self.fileInfoTabWidget.insertTab(roleIndex, detailViewer, role)
                
        self.fileInfoTabWidget.currentChanged.connect( self.handleSwitchTabs )
        self.fileInfoTabWidget.setCurrentIndex(0)

    def handleSwitchTabs(self, tabIndex ):
        if tabIndex < len(self._detailViewerWidgets):
            roleIndex = tabIndex # If summary tab is moved to the front, change this line.
            detailViewer = self._detailViewerWidgets[roleIndex]
            selectedLanes = detailViewer.selectedLanes
            if selectedLanes:
                self.showDataset( selectedLanes[0], roleIndex )

    def _initViewerStack(self):
        self.volumeEditors = {}
        self.viewerStack.addWidget( QWidget() )

    def handleRemoveLaneButtonClicked(self):
        """
        The user clicked the "Remove" button.
        Remove the currently selected row(s) from both the GUI and the top-level operator.
        """
        # Figure out which lanes to remove
        selectedIndexes = self.laneSummaryTableView.selectedIndexes()
        rows = set()
        for modelIndex in selectedIndexes:
            rows.add( modelIndex.row() )

        # Don't remove the last row, which is just buttons.
        rows.discard( self.laneSummaryTableView.model().rowCount()-1 )

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
            self.viewerStack.addWidget( layerViewer )
            self._viewerControlWidgetStack.addWidget( layerViewer.viewerControlWidget() )

        # Show the right one
        viewer = self.volumeEditors[datasetSlot]
        displayedRole = self.fileInfoTabWidget.currentIndex()
        viewer.moveToTop(displayedRole)
        self.viewerStack.setCurrentWidget( viewer )
        self._viewerControlWidgetStack.setCurrentWidget( viewer.viewerControlWidget() )


    def handleReplaceFile(self, roleIndex, startingLane):
        self.addFiles(roleIndex, startingLane)

    def addFiles(self, roleIndex, startingLane=None):
        """
        The user clicked the "Add File" button.
        Ask him to choose a file (or several) and add them to both
          the GUI table and the top-level operator inputs.
        """

        # Launch the "Open File" dialog
        paths = ImageFileDialog(self).getSelectedPaths()
        self.addFileNames(paths, roleIndex, startingLane)

    def addFileNames(self, paths:List[str], roleIndex:int, startingLane:int):
        # If the user didn't cancel
        if len(paths) > 0:
            try:
                new_infos = self._createDatasetInfos(roleIndex, paths)
                self.addLanes(new_infos, roleIndex=roleIndex, startingLane=startingLane)
            except DataSelectionGui.UserCancelledError:
                pass
            except Exception as ex:
                log_exception( logger )
                QMessageBox.critical(self, "Error loading file", str(ex))

    def _findFirstEmptyLane(self, roleIndex):
        opTop = self.topLevelOperator
        
        # Determine the number of files this role already has
        # Search for the last valid value.
        firstNewLane = 0
        for laneIndex, slot in reversed(list(zip(list(range(len(opTop.DatasetGroup))), opTop.DatasetGroup))):
            if slot[roleIndex].ready():
                firstNewLane = laneIndex+1
                break
        return firstNewLane

    def getNumLanes(self) -> int:
        return len(self.topLevelOperator.DatasetGroup)

    def getInfoSlots(self, roleIndex:int):
        return [self.topLevelOperator.DatasetGroup[laneIndex][roleIndex] for laneIndex in range(self.getNumLanes())]

    def getImageSlots(self, roleIndex):
        return [self.topLevelOperator.ImageGroup[lane_index][roleIndex] for laneIndex in range(self.getNumLanes())]

    def addLanes(self, new_infos:List[DatasetInfo], roleIndex, startingLane=None, rois=None):
        """
        Add the given filenames to both the GUI table and the top-level operator inputs.
        If startingLane is None, the filenames will be *appended* to the role's list of files.
        
        If rois is provided, it must be a list of (start,stop) tuples (one for each fileName)
        """
        originalNumLanes = self.getNumLanes()
        startingLane, endingLane = self._determineLaneRange(new_infos, startingLane)
        if originalNumLanes < endingLane+1:
            self.topLevelOperator.DatasetGroup.resize(endingLane+1)
        info_slots = self.getInfoSlots(roleIndex)[startingLane:endingLane+1]

        try:
            if not self.applyDatasetInfos(new_infos, info_slots):
                self.topLevelOperator.DatasetGroup.resize(originalNumLanes)
                return

            # Now check the resulting slots.
            # If they should be copied to the project file, say so.
            self._reconfigureDatasetLocations(roleIndex, startingLane, endingLane)

            self._checkDataFormatWarnings(roleIndex, startingLane, endingLane)

            # Show the first image
            self.showDataset(startingLane, roleIndex)

            # if only adding new lanes, notify the workflow
            if startingLane >= originalNumLanes:
                workflow = self.parentApplet.topLevelOperator.parent
                workflow.handleNewLanesAdded()

            # Notify the workflow that something that could affect applet readyness has occurred.
            self.parentApplet.appletStateUpdateRequested()

            self.updateInternalPathVisiblity()
        except Exception as e:
            self.topLevelOperator.DatasetGroup.resize(originalNumLanes)
            QMessageBox.critical(self, "File selection error", str(e))

    def applyDatasetInfos(self, new_infos:List[DatasetInfo], info_slots:List['Slot'], fixed_once=False):
        original_infos = []
        def revert():
            for slot, original_info in zip(info_slots, original_infos):
                if original_info is not None:
                    slot.setValue(original_info)
        try:
            for new_info, info_slot in zip(new_infos, info_slots):
                original_infos.append(info_slot.value if info_slot.ready() else None)
                while True:
                    try:
                        info_slot.setValue(new_info)
                        break
                    except DatasetConstraintError as e:
                        if fixed_once:
                            QMessageBox.warning(self, "Incompatible dataset", str(e))
                        info_editor = DatasetInfoEditorWidget(self, [new_info], self.topLevelOperator.WorkingDirectory.value)
                        fixed_once = True
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

    def _determineLaneRange(self, infos:List[DatasetInfo], startingLane=None):
        """
        Determine which lanes should be configured if the user wants to add the 
            given infos to the specified role, starting at startingLane.
        If startingLane is None, assume the user wants to APPEND the 
            files to the role's slots.
        """
        if startingLane is None or startingLane == -1:
            startingLane = len(self.topLevelOperator.DatasetGroup)
            endingLane = startingLane+len(infos)-1
        else:
            assert startingLane < len(self.topLevelOperator.DatasetGroup)
            max_files = len(self.topLevelOperator.DatasetGroup) - startingLane
            if len(infos) > max_files:
                msg = "You selected {num_selected} files for {num_slots} "\
                      "slots. To add new files use the 'Add new...' option "\
                      "in the context menu or the button in the last row."\
                              .format(num_selected=len(infos),
                                      num_slots=max_files)
                raise Exception(msg)
            endingLane = min(startingLane+len(infos)-1, len(self.topLevelOperator.DatasetGroup))
            
        if self._max_lanes and endingLane >= self._max_lanes:
            msg = "You may not add more than {} file(s) to this workflow.  Please try again.".format( self._max_lanes )
            raise Exception(msg)

        return (startingLane, endingLane)

    def _createDatasetInfos(self, roleIndex:int, filePaths:List[Path], rois=None):
        """
        Create a list of DatasetInfos for the given filePaths and rois
        rois may be None, in which case it is ignored.
        """
        filePaths = [Path(p) for p in filePaths]
        if rois is None:
            rois = [None]*len(filePaths)
        assert len(rois) == len(filePaths)

        infos = []
        for filePath, roi in zip(filePaths, rois):
            info = self._createDatasetInfo(roleIndex, filePath, roi)
            infos.append(info)
        return infos

    def _createDatasetInfo(self, roleIndex:int, filePath:Path, roi):
        """
        Create a DatasetInfo object for the given filePath and roi.
        roi may be None, in which case it is ignored.
        """
        cwd = self.topLevelOperator.WorkingDirectory.value
        try:
            data_path = filePath.absolute().relative_to(cwd)
        except ValueError:
            data_path = filePath.absolute()

        if DatasetInfo.fileHasInternalPaths(data_path):
            datasetNames = DatasetInfo.getPossibleInternalPathsFor(absPath)
            if len(datasetNames) == 0:
                raise RuntimeError(f"{file_extension} file {data_path} has no image datasets")
            if len(datasetNames) == 1:
                data_path += str(datasetNames[0])
            else:
                # If exactly one of the file's datasets matches a user's previous choice, use it.
                if roleIndex not in self._default_h5n5_volumes:
                    self._default_h5n5_volumes[roleIndex] = set()
                previous_selections = self._default_h5n5_volumes[roleIndex]
                possible_auto_selections = previous_selections.intersection(datasetNames)
                if len(possible_auto_selections) == 1:
                    data_path += str(list(possible_auto_selections)[0])
                else:
                    # Ask the user which dataset to choose
                    dlg = H5N5VolumeSelectionDlg(datasetNames, self)
                    if dlg.exec_() == QDialog.Accepted:
                        selected_index = dlg.combo.currentIndex()
                        selected_dataset = str(datasetNames[selected_index])
                        data_path += selected_dataset
                        self._default_h5n5_volumes[roleIndex].add(selected_dataset)
                    else:
                        raise DataSelectionGui.UserCancelledError()

        return DatasetInfo.default(
            filepath=data_path.as_posix(), #FIXME: it would be much better to use Path rather than str
            cwd=cwd,
            allowLabels=(self.guiMode == GuiMode.Normal),
            subvolume_roi=roi)

    def _opTopRemoveDset(self, laneNum, laneIndex, roleIndex):
        """
        Removes a dataset in topLevelOperator and sets the number of lanes to laneNum
        :param laneNum: total number of lanes after the cleanup
        :param laneIndex: the lane index of the dataset which is to be removed
        :param roleIndex: role index of the dataset
        """
        self.topLevelOperator.DatasetGroup.resize(laneNum)
        self.topLevelOperator.DatasetGroup[laneIndex][roleIndex].setValue(None)

    def _reconfigureDatasetLocations(self, roleIndex, startingLane, endingLane):
        """
        Check the metadata for the given slots.  
        If the data is stored a format that is poorly optimized for 3D access, 
        then configure it to be copied to the project file.
        Finally, save the project if we changed something. 
        """
        save_needed = False
        opTop = self.topLevelOperator
        for lane_index in range(startingLane, endingLane+1):
            output_slot = opTop.ImageGroup[lane_index][roleIndex]
            if output_slot.meta.prefer_2d and 'z' in output_slot.meta.axistags:
                shape = numpy.array(output_slot.meta.shape)
                total_volume = numpy.prod(shape)
                
                # Only copy to the project file if the total volume is reasonably small
                if total_volume < 0.5e9:
                    info_slot = opTop.DatasetGroup[lane_index][roleIndex]
                    info = info_slot.value
                    info.location = DatasetInfo.Location.ProjectInternal
                    info_slot.setValue( info, check_changed=False )
                    save_needed = True

        if save_needed:
            logger.info("Some of your data cannot be accessed efficiently in 3D in its current format."
                        "  It will now be copied to the project file.")
            opWorkflow = self.topLevelOperator.parent
            opWorkflow.shell.onSaveProjectActionTriggered()

    def _checkDataFormatWarnings(self, roleIndex, startingLane, endingLane):
        warn_needed = False
        opTop = self.topLevelOperator
        for lane_index in range(startingLane, endingLane+1):
            output_slot = opTop.ImageGroup[lane_index][roleIndex]
            if output_slot.meta.inefficient_format:
                warn_needed = True

        if warn_needed:        
            QMessageBox.warning( self, "Inefficient Data Format", 
                              "Your data cannot be accessed efficiently in its current format.  "
                              "Check the console output for details.\n"
                              "(For HDF5 files, be sure to enable chunking on your dataset.)" )

    def addStack(self, roleIndex, laneIndex):
        """
        The user clicked the "Import Stack Files" button.
        """
        stackDlg = StackFileSelectionWidget(self)
        stackDlg.exec_()
        if stackDlg.result() != QDialog.Accepted or len(stackDlg.selectedFiles) == 0:
            return
        globstring = os.path.pathsep.join(stackDlg.selectedFiles)
        sequence_axis = stackDlg.sequence_axis
        cwd = self.topLevelOperator.WorkingDirectory.value
        self.parentApplet.busy = True
        stack_internal_id = self.serializer.importStackAsLocalDataset(globstring, sequence_axis)
        self.parentApplet.busy = False
        info = DatasetInfo.default(globstring, sequence_axis=sequence_axis,
                                   cwd=cwd, fromstack=True,
                                   location=DatasetInfo.Location.ProjectInternal,
                                   datasetId=stack_internal_id)
        self.addLanes([info], roleIndex, laneIndex)

    @threadRouted
    def handleFailedStackLoad(self, files, originalNumLanes, exc, exc_info):
        msg = "Failed to load stack due to the following error:\n{}".format( exc )
        msg += "\nAttempted stack files were:\n"
        msg += "\n".join(files)
        log_exception( logger, msg, exc_info )
        QMessageBox.critical(self, "Failed to load image stack", msg)
        self.topLevelOperator.DatasetGroup.resize(originalNumLanes)

    def handleClearDatasets(self, roleIndex, selectedRows):
        for row in selectedRows:
            self.topLevelOperator.DatasetGroup[row][roleIndex].disconnect()

        # Remove all operators that no longer have any connected slots        
        laneIndexes = list(range( len(self.topLevelOperator.DatasetGroup)))
        for laneIndex, multislot in reversed(list(zip(laneIndexes, self.topLevelOperator.DatasetGroup))):
            any_ready = False
            for slot in multislot:
                any_ready |= slot.ready()
            if not any_ready:
                self.topLevelOperator.DatasetGroup.removeSlot( laneIndex, len(self.topLevelOperator.DatasetGroup)-1 )

        # Notify the workflow that something that could affect applet readyness has occurred.
        self.parentApplet.appletStateUpdateRequested()

    def editDatasetInfo(self, roleIndex, laneIndexes):
        all_info_slots = self.getInfoSlots(roleIndex)
        selected_info_slots = [all_info_slots[idx] for idx in laneIndexes]
        infos = [slot.value for slot in selected_info_slots]
        editorDlg = DatasetInfoEditorWidget(self, infos, self.topLevelOperator.WorkingDirectory.value)
        if editorDlg.exec_() == QDialog.Accepted:
            self.applyDatasetInfos(editorDlg.edited_infos, selected_info_slots, fixed_once=True)

    def updateInternalPathVisiblity(self):
        for view in self._detailViewerWidgets:
            model = view.model()
            view.setColumnHidden(DatasetDetailedInfoColumn.InternalID,
                                 not model.hasInternalPaths())

    def addPrecomputedVolume(self, roleIndex, laneIndex):
        # add history...
        history = []
        browser = PrecomputedVolumeBrowser(history=history, parent=self)

        if browser.exec_() == PrecomputedVolumeBrowser.Rejected:
            return

        precomputed_url = browser.selected_url
        self.addFileNames([precomputed_url], roleIndex, laneIndex)

    def addDvidVolume(self, roleIndex, laneIndex):
        recent_hosts_pref = PreferencesManager.Setting("DataSelection", "Recent DVID Hosts")
        recent_hosts = recent_hosts_pref.get()
        if not recent_hosts:
            recent_hosts = ["localhost:8000"]
        recent_hosts = [h for h in recent_hosts if h] # There used to be a bug where empty strings could be saved. Filter those out.

        recent_nodes_pref = PreferencesManager.Setting("DataSelection", "Recent DVID Nodes")
        recent_nodes = recent_nodes_pref.get() or {}
            
        from .dvidDataSelectionBrowser import DvidDataSelectionBrowser
        browser = DvidDataSelectionBrowser(recent_hosts, recent_nodes, parent=self)
        if browser.exec_() == DvidDataSelectionBrowser.Rejected:
            return

        if None in browser.get_selection():
            QMessageBox.critical("Couldn't use your selection.")
            return

        rois = None
        hostname, repo_uuid, volume_name, node_uuid, typename = browser.get_selection()
        dvid_url = 'http://{hostname}/api/node/{node_uuid}/{volume_name}'.format( **locals() )
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
        recent_hosts_pref.set(recent_hosts)
        
        recent_nodes[hostname] = node_uuid
        recent_nodes_pref.set(recent_nodes)

        if subvolume_roi is None:
            self.addFileNames([dvid_url], roleIndex, laneIndex)
        else:
            start, stop = subvolume_roi
            self.addFileNames([dvid_url], roleIndex, laneIndex, [(start, stop)])
