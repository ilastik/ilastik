#Python
from functools import partial
import os
import copy
import glob
import threading
import h5py
import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

#SciPy
import vigra

#PyQt
from PyQt4.QtCore import Qt, QVariant
from PyQt4.QtGui import *
from PyQt4 import uic

#lazyflow
from lazyflow.utility import Tracer
from lazyflow.request import Request

#volumina
from volumina.utility import PreferencesManager

#ilastik
from ilastik.config import cfg as ilastik_config
from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.utility import bind
from ilastik.utility.gui import ThreadRouter, threadRouted
from ilastik.utility.pathHelpers import getPathVariants, areOnSameDrive, PathComponents
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.applets.base.applet import ControlCommand, DatasetConstraintError
from ilastik.widgets.massFileLoader import MassFileLoader

from opDataSelection import OpDataSelection, DatasetInfo
from dataLaneSummaryTableModel import DataLaneSummaryTableModel 
from datasetDetailedInfoTableView import DatasetDetailedInfoTableView
from datasetDetailedInfoTableModel import DatasetDetailedInfoTableModel
from datasetInfoEditorWidget import DatasetInfoEditorWidget

from dataDetailViewerWidget import DataDetailViewerWidget
from ilastik.widgets.stackFileSelectionWidget import StackFileSelectionWidget

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
        pass # This applet doesn't care which image is currently selected.  It always lists all inputs.

    def stopAndCleanUp(self):
        for editor in self.volumeEditors.values():
            self.viewerStack.removeWidget( editor )
            editor.stopAndCleanUp()
        self.volumeEditors.clear()

    def imageLaneAdded(self, laneIndex):
        # We assume that there's nothing to do here because THIS GUI initiated the lane addition
        if self.guiMode != GuiMode.Batch:
            if(len(self.topLevelOperator.DatasetGroup) != laneIndex+1):
                import warnings
                warnings.warn("DataSelectionGui.imageLaneAdded(): length of dataset multislot out of sync with laneindex [%s != %s + 1]" % (len(self.topLevelOperator.Dataset), laneIndex))

    def imageLaneRemoved(self, laneIndex, finalLength):
        # We assume that there's nothing to do here because THIS GUI initiated the lane removal
        if self.guiMode != GuiMode.Batch:
            assert len(self.topLevelOperator.DatasetGroup) == finalLength

    ###########################################
    ###########################################

    def __init__(self, dataSelectionOperator, serializer, guiControlSignal, guiMode=GuiMode.Normal, title="Input Selection"):
        with Tracer(traceLogger):
            super(DataSelectionGui, self).__init__()

            self.title = title

            self._viewerControls = QWidget()
            self.topLevelOperator = dataSelectionOperator
            self.guiMode = guiMode
            self.serializer = serializer
            self.guiControlSignal = guiControlSignal
            self.threadRouter = ThreadRouter(self)

            self._initCentralUic()
            self._initAppletDrawerUic()
            
            self._viewerControlWidgetStack = QStackedWidget(self)

            def handleImageRemoved(multislot, index, finalLength):
                # Remove the viewer for this dataset
                imageSlot = self.topLevelOperator.Image[index]
                if imageSlot in self.volumeEditors.keys():
                    editor = self.volumeEditors[imageSlot]
                    self.viewerStack.removeWidget( editor )
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

    def _initAppletDrawerUic(self):
        """
        Load the ui file for the applet drawer, which we own.
        """
        localDir = os.path.split(__file__)[0]+'/'
        self._drawer = uic.loadUi(localDir+"/dataSelectionDrawer.ui")

    def _initTableViews(self):
        self.fileInfoTabWidget.setTabText( 0, "Summary" )
        self.laneSummaryTableView.setModel( DataLaneSummaryTableModel(self, self.topLevelOperator) )
        self.laneSummaryTableView.dataLaneSelected.connect( self.showDataset )
        self.laneSummaryTableView.addFilesRequested.connect( self.handleAddFiles )
        self.laneSummaryTableView.addStackRequested.connect( self.handleAddStack )
        self.laneSummaryTableView.addByPatternRequested.connect( self.handleAddByPattern )
        self.removeLaneButton.clicked.connect( self.handleRemoveLaneButtonClicked )
        self.laneSummaryTableView.removeLanesRequested.connect( self.handleRemoveLaneButtonClicked )

        self._retained = [] # Retain menus so they don't get deleted
        self._detailViewerWidgets = []
        for roleIndex, role in enumerate(self.topLevelOperator.DatasetRoles.value):
            detailViewer = DataDetailViewerWidget( self, self.topLevelOperator, roleIndex )
            self._detailViewerWidgets.append( detailViewer )

            # Button
            menu = QMenu()
            menu.addAction( "Add File(s)..." ).triggered.connect( partial(self.handleAddFiles, roleIndex) )
            menu.addAction( "Add Volume from Stack..." ).triggered.connect( partial(self.handleAddStack, roleIndex) )
            menu.addAction( "Add Many by Pattern..." ).triggered.connect( partial(self.handleAddByPattern, roleIndex) )
            detailViewer.appendButton.setMenu( menu )
            self._retained.append(menu)
            
            # Context menu            
            detailViewer.datasetDetailTableView.replaceWithFileRequested.connect( partial(self.handleReplaceFile, roleIndex) )
            detailViewer.datasetDetailTableView.replaceWithStackRequested.connect( partial(self.replaceWithStack, roleIndex) )
            detailViewer.datasetDetailTableView.editRequested.connect( partial(self.editDatasetInfo, roleIndex) )
            detailViewer.datasetDetailTableView.resetRequested.connect( partial(self.handleClearDatasets, roleIndex) )

            # Selection handling
            def showFirstSelectedDataset( lanes ):
                if lanes:
                    self.showDataset( lanes[0] )
            detailViewer.datasetDetailTableView.dataLaneSelected.connect( showFirstSelectedDataset )
            
            self.fileInfoTabWidget.insertTab(roleIndex, detailViewer, role)

        self.fileInfoTabWidget.setCurrentIndex(0)

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
        rows.discard( self.laneSummaryTableView.model().rowCount() )

        # Remove in reverse order so row numbers remain consistent
        for row in reversed(sorted(rows)):
            # Remove from the GUI
            self.laneSummaryTableView.model().removeRow(row)
            # Remove from the operator
            finalSize = len(self.topLevelOperator.DatasetGroup) - 1
            self.topLevelOperator.DatasetGroup.removeSlot(row, finalSize)
    
            # The gui and the operator should be in sync
            assert self.laneSummaryTableView.model().rowCount() == len(self.topLevelOperator.DatasetGroup)+1

    def showDataset(self, laneIndex):
        if laneIndex == -1:
            self.viewerStack.setCurrentIndex(0)
            return
        
        assert threading.current_thread().name == "MainThread"
        imageSlot = self.topLevelOperator.Image[laneIndex]

        # Create if necessary
        if imageSlot not in self.volumeEditors.keys():
            
            class DatasetViewer(LayerViewerGui):
                def setupLayers(self):
                    opLaneView = self.topLevelOperatorView
                    datasetRoles = opLaneView.DatasetRoles.value
                    layers = []
                    for roleIndex, slot in enumerate(opLaneView.ImageGroup):
                        if slot.ready():
                            roleName = datasetRoles[roleIndex]
                            layer = self.createStandardLayerFromSlot(slot)
                            layer.name = roleName
                            layers.append(layer)
                    return layers

            opLaneView = self.topLevelOperator.getLane(laneIndex)
            layerViewer = DatasetViewer(opLaneView, crosshair=False)
            
            # Maximize the x-y view by default.
            layerViewer.volumeEditorWidget.quadview.ensureMaximized(2)

            self.volumeEditors[imageSlot] = layerViewer
            self.viewerStack.addWidget( layerViewer )
            self._viewerControlWidgetStack.addWidget( layerViewer.viewerControlWidget() )

        # Show the right one
        self.viewerStack.setCurrentWidget( self.volumeEditors[imageSlot] )
        self._viewerControlWidgetStack.setCurrentWidget( self.volumeEditors[imageSlot].viewerControlWidget() )

    def handleAddFiles(self, roleIndex):
        self.addFiles(roleIndex)

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

    def handleAddByPattern(self, roleIndex):
        # Find the most recent directory

        # TODO: remove code duplication
        mostRecentDirectory = PreferencesManager().get( 'DataSelection', 'recent mass directory' )
        if mostRecentDirectory is not None:
            defaultDirectory = os.path.split(mostRecentDirectory)[0]
        else:
            defaultDirectory = os.path.expanduser('~')

        fileNames = self.getMass(defaultDirectory)

        # If the user didn't cancel
        if len(fileNames) > 0:
            PreferencesManager().set('DataSelection', 'recent mass directory', os.path.split(fileNames[0])[0])
            try:
                self.addFileNames(fileNames, roleIndex)
            except RuntimeError as e:
                QMessageBox.critical(self, "Error loading file", str(e))


    def getImageFileNamesToOpen(self, defaultDirectory):
        """
        Launch an "Open File" dialog to ask the user for one or more image files.
        """
        extensions = OpDataSelection.SupportedExtensions
        filt = "Image files (" + ' '.join('*.' + x for x in extensions) + ')'
        options = QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |=  QFileDialog.DontUseNativeDialog
        fileNames = QFileDialog.getOpenFileNames( self, "Select Images", 
                                 defaultDirectory, filt, options=options )
        # Convert from QtString to python str
        fileNames = [str(s) for s in fileNames]
        return fileNames

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

        if startingLane is None:        
            startingLane = self._findFirstEmptyLane(roleIndex)
            endingLane = startingLane+len(fileNames)-1
        else:
            assert startingLane < len(self.topLevelOperator.DatasetGroup)
            endingLane = startingLane+len(fileNames)-1

        # Assign values to the new inputs we just allocated.
        # The GUI will be updated by callbacks that are listening to slot changes
        for i, filePath in enumerate(fileNames):
            datasetInfo = DatasetInfo()
            cwd = self.topLevelOperator.WorkingDirectory.value
            
            if not areOnSameDrive(filePath,cwd):
                QMessageBox.critical(self, "Drive Error","Data must be on same drive as working directory.")
                return
                
            absPath, relPath = getPathVariants(filePath, cwd)
            
            # Relative by default, unless the file is in a totally different tree from the working directory.
            if len(os.path.commonprefix([cwd, absPath])) > 1:
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
            
        try:
            if len( opTop.DatasetGroup ) < endingLane+1:
                opTop.DatasetGroup.resize( endingLane+1 )
    
            for laneIndex, info in zip(range(startingLane, endingLane+1), infos):
                self.topLevelOperator.DatasetGroup[laneIndex][roleIndex].setValue( info )
        except DatasetConstraintError as ex:
            self.handleDatasetConstraintError(info.filePath, ex)
            opTop.DatasetGroup.resize( originalSize )
        except:
            QMessageBox.critical( self, "Dataset Load Error", "Wasn't able to load your dataset into the workflow.  See console for details." )
            opTop.DatasetGroup.resize( originalSize )
            raise

    def handleDatasetConstraintError(self, filename, ex):
            msg = "Can't use dataset:\n" + \
                  filename + "\n" + \
                  "because it violates a constraint of the {} applet.\n\n".format( ex.appletName ) + \
                  ex.message
            QMessageBox.critical( self, "Unacceptable Dataset", msg )

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

    def handleAddStack(self, roleIndex):
        self.replaceWithStack(roleIndex, laneIndex=None)

    def replaceWithStack(self, roleIndex, laneIndex):
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
        info.nickname = PathComponents(prefix).filenameBase + "..."

        # Allow labels by default if this gui isn't being used for batch data.
        info.allowLabels = ( self.guiMode == GuiMode.Normal )
        info.fromstack = True

        originalNumLanes = len(self.topLevelOperator.DatasetGroup)

        if laneIndex is None:
            laneIndex = self._findFirstEmptyLane(roleIndex)
        if len(self.topLevelOperator.DatasetGroup) < laneIndex+1:
            self.topLevelOperator.DatasetGroup.resize(laneIndex+1)

        def importStack():
            self.guiControlSignal.emit( ControlCommand.DisableAll )
            # Serializer will update the operator for us, which will propagate to the GUI.
            try:
                self.serializer.importStackAsLocalDataset( info )
                self.topLevelOperator.DatasetGroup[laneIndex][roleIndex].setValue(info)
            
            finally:
                self.guiControlSignal.emit( ControlCommand.Pop )

        req = Request( importStack )
        req.notify_failed( partial(self.handleFailedStackLoad, files, originalNumLanes ) )
        req.submit()

    @threadRouted
    def handleFailedStackLoad(self, files, originalNumLanes, exc, exc_info):
        if isinstance(exc, DatasetConstraintError):
            filename = files[0] + "\n...\n" + files[-1]
            self.handleDatasetConstraintError( filename, exc )
        else:
            import traceback
            traceback.print_tb(exc_info[2])
            msg = "Failed to load stack due to the following error:\n{}".format( exc )
            msg += "Attempted stack files were:"
            for f in files:
                msg += f + "\n"
            QMessageBox.critical(self, "Failed to load image stack", msg)
        
        self.topLevelOperator.DatasetGroup.resize(originalNumLanes)

    def getMass(self, defaultDirectory):
        # TODO: launch dialog and get files

        # Convert from QtString to python str
        loader = MassFileLoader(defaultDirectory=defaultDirectory)
        loader.exec_()
        if loader.result() == QDialog.Accepted:
            fileNames = [str(s) for s in loader.filenames]
        else:
            fileNames = []
        return fileNames

    def handleClearDatasets(self, roleIndex, selectedRows):
        for row in selectedRows:
            self.topLevelOperator.DatasetGroup[row][roleIndex].disconnect()
        
        # Search for the last lane that has any valid role
        # This would be cleaner in Python 3...
        last_valid = -1
        laneIndexes = range( len(self.topLevelOperator.DatasetGroup) )
        for laneIndex, multislot in reversed(zip(laneIndexes, self.topLevelOperator.DatasetGroup)):
            all_disconnected = True
            for slot in multislot:
                all_disconnected &= not slot.ready()
            if not all_disconnected:
                last_valid = laneIndex
                break
        self.topLevelOperator.DatasetGroup.resize( last_valid+1 )

    def editDatasetInfo(self, roleIndex, laneIndexes):
        editorDlg = DatasetInfoEditorWidget(self, self.topLevelOperator, roleIndex, laneIndexes)
        editorDlg.exec_()

#    def importStackFromGlobString(self, globString, roleIndex):
#        """
#        The word 'glob' is used loosely here.  See the OpStackLoader operator for details.
#        """
#        globString = globString.replace("\\","/")
#        info = DatasetInfo()
#        info.filePath = globString
#
#        # Allow labels by default if this gui isn't being used for batch data.
#        info.allowLabels = ( self.guiMode == GuiMode.Normal )
#
#        def importStack():
#            self.guiControlSignal.emit( ControlCommand.DisableAll )
#            # Serializer will update the operator for us, which will propagate to the GUI.
#            try:
#                self.serializer.importStackAsLocalDataset( info )
#            finally:
#                self.guiControlSignal.emit( ControlCommand.Pop )
#
#        req = Request( importStack )
#        req.notify_failed( partial(self.handleFailedStackLoad, globString ) )
#        req.submit()
#
#
#    @threadRouted
#    def updateTableForSlot(self, slot, *args):
#        """
#        Update the given rows using the top-level operator parameters
#        """
#        with Tracer(traceLogger):
#
#            # Don't update anything if the slot doesn't have data yet
#            if not slot.connected():
#                return
#
#            # Which index is this slot?
#            row = -1
#            for i in range( len(self.topLevelOperator.Dataset) ):
#                if slot == self.topLevelOperator.Dataset[i]:
#                    row = i
#                    break
#
#            assert row != -1, "Unknown input slot!"
#
#            totalPath = self.topLevelOperator.Dataset[row].value.filePath
#            lastDotIndex = totalPath.rfind('.')
#            extensionAndInternal = totalPath[lastDotIndex:]
#            extension = extensionAndInternal.split('/')[0]
#            externalPath = totalPath[:lastDotIndex] + extension
#
#            internalPath = ''
#            internalStart = extensionAndInternal.find('/')
#            if internalStart != -1:
#                internalPath = extensionAndInternal[internalStart:]
#
#            fileName = os.path.split(externalPath)[1]
#
#            tableWidget = self.fileInfoTableWidget
#
#            # Show the filename in the table (defaults to edit widget)
#            tableWidget.setItem( row, Column.Name, QTableWidgetItem(fileName) )
#
#            # Create and add the combobox for the internal path selection
#            self.updateInternalPathComboBox( row, externalPath, internalPath )
#    #        tableWidget.setItem( row, Column.InternalID, QTableWidgetItem(internalPath) )
#
#            # Subscribe to changes
#            tableWidget.itemChanged.connect( self.handleRowDataChange )
#
#            # Create and add the combobox for storage location options
#            self.updateStorageOptionComboBox(row, externalPath)
#
#            if self.guiMode != GuiMode.Batch:
#                # Create and add the checkbox for the 'allow labels' option
#                allowLabelsCheckbox = QCheckBox()
#                allowLabelsCheckbox.setChecked( self.topLevelOperator.Dataset[row].value.allowLabels )
#                tableWidget.setCellWidget( row, Column.LabelsAllowed, allowLabelsCheckbox )
#                allowLabelsCheckbox.stateChanged.connect( partial(self.handleAllowLabelsCheckbox, self.topLevelOperator.Dataset[row]) )
#
#            # Update the operator, in case we need to select a new internal path based on the updated combo options
#            # (Won't have any effect if nothing changed this time around.)
#            self.updateFilePath(row)
#
#            # Select a row if there isn't one already selected.
#            selectedRanges = self.fileInfoTableWidget.selectedRanges()
#            if len(selectedRanges) == 0:
#                self.fileInfoTableWidget.selectRow(0)
#
#    def handleAllowLabelsCheckbox(self, slot, checked):
#        """
#        The user (un)checked the "allow labels" checkbox in one of the table rows.
#        Update the corresponding dataset info in the operator (which is given in the parameter 'slot')
#        """
#        with Tracer(traceLogger):
#            # COPY the dataset so we trigger the slot to be dirty
#            newDatasetInfo = copy.copy(slot.value)
#            newDatasetInfo.allowLabels = ( checked == Qt.Checked )
#
#            # Only update if necessary
#            if newDatasetInfo.allowLabels != slot.value.allowLabels:
#                slot.setValue( newDatasetInfo )
#
#    def updateStorageOptionComboBox(self, row, filePath):
#        """
#        Create and add the combobox for storage location options
#        """
#        assert threading.current_thread().name == "MainThread"
#        with Tracer(traceLogger):
#            # Determine the relative path to this file
#            absPath, relPath = getPathVariants(filePath, self.topLevelOperator.WorkingDirectory.value)
#            # Add a prefixes to make the options clear
#            absPath = "Absolute Link: " + absPath
#            relPath = "Relative Link: <project directory>/" + relPath
#
#            combo = QComboBox()
#            options = {} # combo data -> combo text
#            options[ LocationOptions.AbsolutePath ] = absPath
#            options[ LocationOptions.RelativePath ] = relPath
#
#            options[ LocationOptions.Project ] = "Store in Project File"
#
#            for option, text in sorted(options.items()):
#                # Add to the combo, storing the option as the item data
#                combo.addItem(text, option)
#
#            # Select the combo index that matches the current setting
#            location = self.topLevelOperator.Dataset[row].value.location
#
#            if location == DatasetInfo.Location.ProjectInternal:
#                comboData = LocationOptions.Project
#            elif location == DatasetInfo.Location.FileSystem:
#                # Determine if the path is relative or absolute
#                if os.path.isabs(self.topLevelOperator.Dataset[row].value.filePath[0]):
#                    comboData = LocationOptions.AbsolutePath
#                else:
#                    comboData = LocationOptions.RelativePath
#
#            comboIndex = combo.findData( QVariant(comboData) )
#            combo.setCurrentIndex( comboIndex )
#
#            combo.currentIndexChanged.connect( partial(self.handleComboSelectionChanged, combo) )
#            self.fileInfoTableWidget.setCellWidget( row, Column.Location, combo )
#
#    def updateInternalPathComboBox( self, row, externalPath, internalPath ):
#        assert threading.current_thread().name == "MainThread"
#        with Tracer(traceLogger):
#            combo = QComboBox()
#            datasetNames = []
#
#            # Make sure we're dealing with the absolute path (to make this simple)
#            absPath, relPath = getPathVariants(externalPath, self.topLevelOperator.WorkingDirectory.value)
#            ext = os.path.splitext(absPath)[1]
#            h5Exts = ['.ilp', '.h5', '.hdf5']
#            if ext in h5Exts:
#                datasetNames = self.getPossibleInternalPaths(absPath)
#
#            # Add each dataset option to the combo
#            for path in datasetNames:
#                combo.addItem( path )
#
#            # If the internal path we used previously is in the combo list, select it.
#            prevSelection = combo.findText( internalPath )
#            if prevSelection != -1:
#                combo.setCurrentIndex( prevSelection )
#
#            # Define response to changes and add it to the GUI.
#            # Pass in the corresponding the table item so we can figure out which row this came from
#            combo.currentIndexChanged.connect( bind(self.handleComboSelectionChanged, combo) )
#            self.fileInfoTableWidget.setCellWidget( row, Column.InternalID, combo )
#
#            # Since we just selected a new internal path, call the handler
#            #self.handleComboSelectionChanged(combo, combo.currentIndex())
#
#    def handleRowDataChange(self, changedItem ):
#        """
#        The user manually edited a file name in the table.
#        Update the operator and other GUI elements with the new file path.
#        """
#        with Tracer(traceLogger):
#            # Figure out which row this widget is in
#            row = changedItem.row()
#            column = changedItem.column()
#
#            # Can't update until the row is fully initialized
#            needUpdate = True
#            needUpdate &= column == Column.Name or column == Column.InternalID
#            needUpdate &= self.fileInfoTableWidget.item(row, Column.Name) != None
#            needUpdate &= self.fileInfoTableWidget.cellWidget(row, Column.InternalID) != None
#            needUpdate &= self.fileInfoTableWidget.cellWidget(row, column) is not None
#
#            if needUpdate:
#                self.updateFilePath(row)

#    @threadRouted
#    def updateFilePath(self, index):
#        """
#        Update the operator's filePath input to match the gui
#        """
#        with Tracer(traceLogger):
#            oldLocationSetting = self.topLevelOperator.Dataset[index].value.location
#
#            # Get the directory by inspecting the original operator path
#            oldTotalPath = self.topLevelOperator.Dataset[index].value.filePath.replace('\\', '/')
#            # Split into directory, filename, extension, and internal path
#            lastDotIndex = oldTotalPath.rfind('.')
#            extensionAndInternal = oldTotalPath[lastDotIndex:]
#            extension = extensionAndInternal.split('/')[0]
#            oldFilePath = oldTotalPath[:lastDotIndex] + extension
#
#            fileNameText = str(self.fileInfoTableWidget.item(index, Column.Name).text())
#
#            internalPathCombo = self.fileInfoTableWidget.cellWidget(index, Column.InternalID)
#            #internalPath = str(self.fileInfoTableWidget.item(index, Column.InternalID).text())
#            internalPath = str(internalPathCombo.currentText())
#
#            directory = os.path.split(oldFilePath)[0]
#            newFileNamePath = fileNameText
#            if directory != '':
#                newFileNamePath = directory + '/' + fileNameText
#
#            newTotalPath = newFileNamePath
#            if internalPath != '':
#                if internalPath[0] != '/':
#                    newTotalPath += '/'
#                newTotalPath += internalPath
#
#            cwd = self.topLevelOperator.WorkingDirectory.value
#            absTotalPath, relTotalPath = getPathVariants( newTotalPath, cwd )
#            absTotalPath = absTotalPath.replace('\\','/')
#            relTotalPath = relTotalPath.replace('\\','/')
#
#            # Check the location setting
#            locationCombo = self.fileInfoTableWidget.cellWidget(index, Column.Location)
#            comboIndex = locationCombo.currentIndex()
#            newLocationSelection = locationCombo.itemData(comboIndex).toInt()[0] # In PyQt, toInt() returns a tuple
#
#            if newLocationSelection == LocationOptions.Project:
#                newLocationSetting = DatasetInfo.Location.ProjectInternal
#            elif newLocationSelection == LocationOptions.AbsolutePath:
#                newLocationSetting = DatasetInfo.Location.FileSystem
#                newTotalPath = absTotalPath
#            elif newLocationSelection == LocationOptions.RelativePath:
#                newLocationSetting = DatasetInfo.Location.FileSystem
#                newTotalPath = relTotalPath
#
#            if newTotalPath != oldTotalPath or newLocationSetting != oldLocationSetting:
#                # Be sure to copy so the slot notices the change when we setValue()
#                datasetInfo = copy.copy(self.topLevelOperator.Dataset[index].value)
#                datasetInfo.filePath = newTotalPath
#                datasetInfo.location = newLocationSetting
#
#                # TODO: First check to make sure this file exists!
#                self.topLevelOperator.Dataset[index].setValue( datasetInfo )
#
#                # Update the storage option combo to show the new path
#                self.updateStorageOptionComboBox(index, newFileNamePath)

#    def handleComboSelectionChanged(self, combo, index):
#        """
#        Handles changes to any combo change in the table (either external path or internal path)
#        """
#        with Tracer(traceLogger):
#            logger.debug("Combo selection changed: " + combo.itemText(1) + str(index))
#
#            # Figure out which row this combo is in
#            tableWidget = self.fileInfoTableWidget
#            changedRow = -1
#            for row in range(0, tableWidget.rowCount()):
#                for column in range(Column.NumColumns):
#                    widget = tableWidget.cellWidget(row, column)
#                    if widget == combo:
#                        changedRow = row
#                        break
#            assert changedRow != -1
#
#            self.updateFilePath( changedRow )
