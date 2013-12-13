#Python
import os
import threading
import h5py
from functools import partial
import logging
logger = logging.getLogger(__name__)

#PyQt
from PyQt4 import uic
from PyQt4.QtGui import QWidget, QStackedWidget, QMenu, QMessageBox, QFileDialog, QDialog

#lazyflow
from lazyflow.request import Request

#volumina
from volumina.utility import PreferencesManager, encode_from_qstring

#ilastik
from ilastik.config import cfg as ilastik_config
from ilastik.utility import bind
from ilastik.utility.gui import ThreadRouter, threadRouted
from lazyflow.utility.pathHelpers import getPathVariants, areOnSameDrive, PathComponents
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.applets.base.applet import DatasetConstraintError

from opDataSelection import OpDataSelection, DatasetInfo
from dataLaneSummaryTableModel import DataLaneSummaryTableModel 
from datasetInfoEditorWidget import DatasetInfoEditorWidget
from ilastik.widgets.stackFileSelectionWidget import StackFileSelectionWidget
from datasetDetailedInfoTableModel import DatasetDetailedInfoColumn, \
        DatasetDetailedInfoTableModel
from datasetDetailedInfoTableView import DatasetDetailedInfoTableView

try:
    import dvidclient
    _has_dvid_support = True
except:
    _has_dvid_support = False

#===----------------------------------------------------------------------------------------------------------------===

class LocationOptions():
    """ Enum for location menu options """
    Project = 0
    AbsolutePath = 1
    RelativePath = 2

class GuiMode():
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
        for editor in self.volumeEditors.values():
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
        # We assume that there's nothing to do here because THIS GUI initiated the lane removal
        if self.guiMode != GuiMode.Batch:
            assert len(self.topLevelOperator.DatasetGroup) == finalLength

    ###########################################
    ###########################################

    def __init__(self, parentApplet, dataSelectionOperator, serializer, instructionText, guiMode=GuiMode.Normal, max_lanes=None):
        """
        Constructor.
        
        :param dataSelectionOperator: The top-level operator.  Must be of type :py:class:`OpMultiLaneDataSelectionGroup`.
        :param serializer: The applet's serializer.  Must be of type :py:class:`DataSelectionSerializer`
        :param instructionText: A string to display in the applet drawer.
        :param guiMode: Either ``GuiMode.Normal`` or ``GuiMode.Batch``.  Currently, there is no difference between normal and batch mode.
        :param max_lanes: The maximum number of lanes that the user is permitted to add to this workflow.  If ``None``, there is no maximum.
        """
        super(DataSelectionGui, self).__init__()

        self.parentApplet = parentApplet
        self._max_lanes = max_lanes

        self._viewerControls = QWidget()
        self.topLevelOperator = dataSelectionOperator
        self.guiMode = guiMode
        self.serializer = serializer
        self.threadRouter = ThreadRouter(self)

        self._initCentralUic()
        self._initAppletDrawerUic(instructionText)
        
        self._viewerControlWidgetStack = QStackedWidget(self)

        def handleImageRemoved(multislot, index, finalLength):
            # Remove the viewer for this dataset
            imageSlot = self.topLevelOperator.Image[index]
            if imageSlot in self.volumeEditors.keys():
                editor = self.volumeEditors[imageSlot]
                self.viewerStack.removeWidget( editor )
                self._viewerControlWidgetStack.removeWidget( editor.viewerControlWidget() )
                editor.stopAndCleanUp()

        self.topLevelOperator.Image.notifyRemove( bind( handleImageRemoved ) )

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

        def _handle_lane_added( button, role_index, slot, lane_index ):
            slot[lane_index][role_index].notifyReady( bind(_update_button_status, button, role_index) )
            slot[lane_index][role_index].notifyUnready( bind(_update_button_status, button, role_index) )

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
            # Remove from the GUI
            self.laneSummaryTableView.model().removeRow(row)
            # Remove from the operator
            finalSize = len(self.topLevelOperator.DatasetGroup) - 1
            self.topLevelOperator.DatasetGroup.removeSlot(row, finalSize)
    
            # The gui and the operator should be in sync (model has one extra row for the button row)
            assert self.laneSummaryTableView.model().rowCount() == len(self.topLevelOperator.DatasetGroup)+1

    def showDataset(self, laneIndex, roleIndex=None):
        if laneIndex == -1:
            self.viewerStack.setCurrentIndex(0)
            return
        
        assert threading.current_thread().name == "MainThread"
        imageSlot = self.topLevelOperator.Image[laneIndex]

        # Create if necessary
        if imageSlot not in self.volumeEditors.keys():
            
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

            self.volumeEditors[imageSlot] = layerViewer
            self.viewerStack.addWidget( layerViewer )
            self._viewerControlWidgetStack.addWidget( layerViewer.viewerControlWidget() )

        # Show the right one
        viewer = self.volumeEditors[imageSlot]
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
        # Find the directory of the most recently opened image file
        mostRecentImageFile = PreferencesManager().get( 'DataSelection', 'recent image' )
        if mostRecentImageFile is not None:
            defaultDirectory = os.path.split(mostRecentImageFile)[0]
        else:
            defaultDirectory = os.path.expanduser('~')

        # Launch the "Open File" dialog
        fileNames = self.getImageFileNamesToOpen(defaultDirectory)

        # If the user didn't cancel
        if len(fileNames) > 0:
            PreferencesManager().set('DataSelection', 'recent image', fileNames[0])
            try:
                self.addFileNames(fileNames, roleIndex, startingLane)
            except RuntimeError as e:
                QMessageBox.critical(self, "Error loading file", str(e))

    def getImageFileNamesToOpen(self, defaultDirectory):
        """
        Launch an "Open File" dialog to ask the user for one or more image files.
        """
        file_dialog = QFileDialog(self, "Select Images")

        extensions = OpDataSelection.SupportedExtensions
        filter_strs = ["*." + x for x in extensions]
        filters = ["{filt} ({filt})".format(filt=x) for x in filter_strs]
        filt_all_str = "Image files (" + ' '.join(filter_strs) + ')'
        file_dialog.setFilters([filt_all_str] + filters)

        # do not display file types associated with a filter
        # the line for "Image files" is too long otherwise
        file_dialog.setNameFilterDetailsVisible(False)
        # select multiple files
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        if ilastik_config.getboolean("ilastik", "debug"):
            file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)

        if file_dialog.exec_():
            fileNames = file_dialog.selectedFiles()
            # Convert from QtString to python str
            fileNames = map(encode_from_qstring, fileNames)
            return fileNames

        return []

    def _findFirstEmptyLane(self, roleIndex):
        opTop = self.topLevelOperator
        
        # Determine the number of files this role already has
        # Search for the last valid value.
        firstNewLane = 0
        for laneIndex, slot in reversed(zip(range(len(opTop.DatasetGroup)), opTop.DatasetGroup)):
            if slot[roleIndex].ready():
                firstNewLane = laneIndex+1
                break
        return firstNewLane

    def addFileNames(self, fileNames, roleIndex, startingLane=None):
        """
        Add the given filenames to both the GUI table and the top-level operator inputs.
        If startingLane is None, the filenames will be *appended* to the role's list of files.
        """
        infos = []

        if startingLane is None or startingLane == -1:
            startingLane = len(self.topLevelOperator.DatasetGroup)
            endingLane = startingLane+len(fileNames)-1
        else:
            assert startingLane < len(self.topLevelOperator.DatasetGroup)
            max_files = len(self.topLevelOperator.DatasetGroup) - \
                    startingLane
            if len(fileNames) > max_files:
                msg = "You selected {num_selected} files for {num_slots} "\
                      "slots. To add new files use the 'Add new...' option "\
                      "in the context menu or the button in the last row."\
                              .format(num_selected=len(fileNames),
                                      num_slots=max_files)
                QMessageBox.critical( self, "Too many files", msg )
                return
            endingLane = min(startingLane+len(fileNames)-1,
                    len(self.topLevelOperator.DatasetGroup))
            
        if self._max_lanes and endingLane >= self._max_lanes:
            msg = "You may not add more than {} file(s) to this workflow.  Please try again.".format( self._max_lanes )
            QMessageBox.critical( self, "Too many files", msg )
            return

        # Assign values to the new inputs we just allocated.
        # The GUI will be updated by callbacks that are listening to slot changes
        for i, filePath in enumerate(fileNames):
            datasetInfo = DatasetInfo()
            cwd = self.topLevelOperator.WorkingDirectory.value
            
            absPath, relPath = getPathVariants(filePath, cwd)
            
            # Relative by default, unless the file is in a totally different tree from the working directory.
            if relPath is not None and len(os.path.commonprefix([cwd, absPath])) > 1:
                datasetInfo.filePath = relPath
            else:
                datasetInfo.filePath = absPath
                
            datasetInfo.nickname = PathComponents(absPath).filenameBase

            h5Exts = ['.ilp', '.h5', '.hdf5']
            if os.path.splitext(datasetInfo.filePath)[1] in h5Exts:
                datasetNames = self.getPossibleInternalPaths( absPath )
                if len(datasetNames) > 0:
                    datasetInfo.filePath += str(datasetNames[0])
                else:
                    raise RuntimeError("HDF5 file %s has no image datasets" % datasetInfo.filePath)

            # Allow labels by default if this gui isn't being used for batch data.
            datasetInfo.allowLabels = ( self.guiMode == GuiMode.Normal )
            infos.append(datasetInfo)

        # if no exception was thrown, set up the operator now
        opTop = self.topLevelOperator
        originalSize = len(opTop.DatasetGroup)
            
        if len( opTop.DatasetGroup ) < endingLane+1:
            opTop.DatasetGroup.resize( endingLane+1 )
        for laneIndex, info in zip(range(startingLane, endingLane+1), infos):
            try:
                self.topLevelOperator.DatasetGroup[laneIndex][roleIndex].setValue( info )
            except DatasetConstraintError as ex:
                return_val = [False]
                # Give the user a chance to fix the problem
                self.handleDatasetConstraintError(info, info.filePath, ex, roleIndex, laneIndex, return_val)
                if not return_val[0]:
                    # Not successfully repaired.  Roll back the changes and give up.
                    opTop.DatasetGroup.resize( originalSize )
                    break
            except OpDataSelection.InvalidDimensionalityError as ex:
                    opTop.DatasetGroup.resize( originalSize )
                    QMessageBox.critical( self, "Dataset has different dimensionality", ex.message )
                    break
            except:
                QMessageBox.critical( self, "Dataset Load Error", "Wasn't able to load your dataset into the workflow.  See console for details." )
                opTop.DatasetGroup.resize( originalSize )
                raise

        # Notify the workflow that something that could affect applet readyness has occurred.
        self.parentApplet.appletStateUpdateRequested.emit()

        self.updateInternalPathVisiblity()

    @threadRouted
    def handleDatasetConstraintError(self, info, filename, ex, roleIndex, laneIndex, return_val=[False]):
        msg = "Can't use default properties for dataset:\n\n" + \
              filename + "\n\n" + \
              "because it violates a constraint of the {} applet.\n\n".format( ex.appletName ) + \
              ex.message + "\n\n" + \
              "Please enter valid dataset properties to continue."
        QMessageBox.warning( self, "Dataset Needs Correction", msg )
        
        # The success of this is 'returned' via our special out-param
        # (We can't return a value from this func because it is @threadRouted.
        successfully_repaired = self.repairDatasetInfo( info, roleIndex, laneIndex )
        return_val[0] = successfully_repaired

    def repairDatasetInfo(self, info, roleIndex, laneIndex):
        """Open the dataset properties editor and return True if the new properties are acceptable."""
        defaultInfos = {}
        defaultInfos[laneIndex] = info
        editorDlg = DatasetInfoEditorWidget(self, self.topLevelOperator, roleIndex, [laneIndex], defaultInfos)
        dlg_state = editorDlg.exec_()
        return ( dlg_state == QDialog.Accepted )

    def getPossibleInternalPaths(self, absPath):
        datasetNames = []
        # Open the file as a read-only so we can get a list of the internal paths
        with h5py.File(absPath, 'r') as f:
            # Define a closure to collect all of the dataset names in the file.
            def accumulateDatasetPaths(name, val):
                if type(val) == h5py._hl.dataset.Dataset and 3 <= len(val.shape) <= 5:
                    datasetNames.append( '/' + name )
            # Visit every group/dataset in the file
            f.visititems(accumulateDatasetPaths)
        return datasetNames

    def addStack(self, roleIndex, laneIndex):
        """
        The user clicked the "Import Stack Files" button.
        """
        stackDlg = StackFileSelectionWidget(self)
        stackDlg.exec_()
        if stackDlg.result() != QDialog.Accepted :
            return
        files = stackDlg.selectedFiles
        if len(files) == 0:
            return

        info = DatasetInfo()
        info.filePath = "//".join( files )
        prefix = os.path.commonprefix(files)
        info.nickname = PathComponents(prefix).filenameBase
        # Add an underscore for each wildcard digit
        num_wildcards = len(files[-1]) - len(prefix) - len( os.path.splitext(files[-1])[1] )
        info.nickname += "_"*num_wildcards

        # Allow labels by default if this gui isn't being used for batch data.
        info.allowLabels = ( self.guiMode == GuiMode.Normal )
        info.fromstack = True

        originalNumLanes = len(self.topLevelOperator.DatasetGroup)

        if laneIndex is None:
            laneIndex = len(self.topLevelOperator.DatasetGroup)
        if len(self.topLevelOperator.DatasetGroup) < laneIndex+1:
            self.topLevelOperator.DatasetGroup.resize(laneIndex+1)

        def importStack():
            self.parentApplet.busy = True
            self.parentApplet.appletStateUpdateRequested.emit()

            # Serializer will update the operator for us, which will propagate to the GUI.
            try:
                self.serializer.importStackAsLocalDataset( info )
                try:
                    self.topLevelOperator.DatasetGroup[laneIndex][roleIndex].setValue(info)
                except DatasetConstraintError as ex:
                    # Give the user a chance to repair the problem.
                    filename = files[0] + "\n...\n" + files[-1]
                    return_val = [False]
                    self.handleDatasetConstraintError( info, filename, ex, roleIndex, laneIndex, return_val )
                    if not return_val[0]:
                        # Not successfully repaired.  Roll back the changes and give up.
                        self.topLevelOperator.DatasetGroup.resize(originalNumLanes)
            finally:
                self.parentApplet.busy = False
                self.parentApplet.appletStateUpdateRequested.emit()

        req = Request( importStack )
        req.notify_failed( partial(self.handleFailedStackLoad, files, originalNumLanes ) )
        req.submit()

    @threadRouted
    def handleFailedStackLoad(self, files, originalNumLanes, exc, exc_info):
        import traceback
        traceback.print_tb(exc_info[2])
        msg = "Failed to load stack due to the following error:\n{}".format( exc )
        msg += "Attempted stack files were:"
        for f in files:
            msg += f + "\n"
        QMessageBox.critical(self, "Failed to load image stack", msg)
        self.topLevelOperator.DatasetGroup.resize(originalNumLanes)

    def handleClearDatasets(self, roleIndex, selectedRows):
        for row in selectedRows:
            self.topLevelOperator.DatasetGroup[row][roleIndex].disconnect()

        # Remove all operators that no longer have any connected slots        
        last_valid = -1
        laneIndexes = range( len(self.topLevelOperator.DatasetGroup) )
        for laneIndex, multislot in reversed(zip(laneIndexes, self.topLevelOperator.DatasetGroup)):
            any_ready = False
            for slot in multislot:
                any_ready |= slot.ready()
            if not any_ready:
                self.topLevelOperator.DatasetGroup.removeSlot( laneIndex, len(self.topLevelOperator.DatasetGroup)-1 )

        # Notify the workflow that something that could affect applet readyness has occurred.
        self.parentApplet.appletStateUpdateRequested.emit()

    def editDatasetInfo(self, roleIndex, laneIndexes):
        editorDlg = DatasetInfoEditorWidget(self, self.topLevelOperator, roleIndex, laneIndexes)
        editorDlg.exec_()

    def updateInternalPathVisiblity(self):
        for view in self._detailViewerWidgets:
            model = view.model()
            view.setColumnHidden(DatasetDetailedInfoColumn.InternalID,
                                 not model.hasInternalPaths())
    
    def addDvidVolume(self, roleIndex, laneIndex):
        # First, ask for the server name.
        from PyQt4.QtGui import QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox, QSizePolicy
        from PyQt4.QtCore import Qt

        edit = QLineEdit(parent=self)
        edit.setText('localhost:8000')
        edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        buttonbox = QDialogButtonBox( Qt.Horizontal, parent=self )
        buttonbox.setStandardButtons( QDialogButtonBox.Ok | QDialogButtonBox.Cancel )
        buttonbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        
        layout = QVBoxLayout(self)
        layout.addWidget( edit )
        layout.addWidget( buttonbox )

        dlg = QDialog(parent=self)
        dlg.setLayout(layout)
        dlg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        dlg.setWindowTitle("Specify DVID hostname")
        dlg.setMinimumWidth(500)

        buttonbox.accepted.connect( dlg.accept )
        buttonbox.rejected.connect( dlg.reject )
        
        if dlg.exec_() == QDialog.Rejected:
            return
        
        hostname = str(edit.text())
        import socket
        from dvidclient.gui.contents_browser import ContentsBrowser
        try:
            browser = ContentsBrowser(hostname, parent=self)
        except socket.error as ex:
            msg = "Socket Error: {} (Error {})".format( ex.args[1], ex.args[0] )
            QMessageBox.critical(self, "Connection Error", msg)
            return

        if browser.exec_() == ContentsBrowser.Rejected:
            return

        dset_index, volume_name, uuid = browser.get_selection()
        dvid_url = 'http://{hostname}/api/node/{uuid}/{volume_name}'.format( **locals() )        
        self.addFileNames([dvid_url], roleIndex, laneIndex)







