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
from ilastik.utility.pathHelpers import getPathVariants,areOnSameDrive
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.applets.base.applet import ControlCommand
from ilastik.widgets.massFileLoader import MassFileLoader

from opDataSelection import OpDataSelection, DatasetInfo
from dataLaneSummaryTableModel import DataLaneSummaryTableModel 
from datasetDetailedInfoTableView import DatasetDetailedInfoTableView
from datasetDetailedInfoTableModel import DatasetDetailedInfoTableModel

from dataDetailViewerWidget import DataDetailViewerWidget

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
        return self.drawer

    def menus( self ):
        return []

    def viewerControlWidget(self):
        return QWidget() # No viewer controls for this applet.

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

            self.drawer = None
            self.topLevelOperator = dataSelectionOperator
            self.guiMode = guiMode
            self.serializer = serializer
            self.guiControlSignal = guiControlSignal
            self.threadRouter = ThreadRouter(self)

            self._initAppletDrawerUic()
            self._initCentralUic()

            def handleImageRemoved(multislot, index, finalLength):
                # Remove the viewer for this dataset
                imageSlot = self.topLevelOperator.Image[index]
                if imageSlot in self.volumeEditors.keys():
                    editor = self.volumeEditors[imageSlot]
                    self.viewerStack.removeWidget( editor )
                    editor.stopAndCleanUp()

            self.topLevelOperator.Image.notifyRemove( bind( handleImageRemoved ) )

    def _initAppletDrawerUic(self):
        """
        Load the ui file for the applet drawer, which we own.
        """
        localDir = os.path.split(__file__)[0]+'/'
        self.drawer = uic.loadUi(localDir+"/dataSelectionDrawer.ui")

#        # Set up our handlers
#        self.drawer.addFileButton.clicked.connect(self.handleAddFileButtonClicked)
#        self.drawer.addFileButton.setIcon( QIcon(ilastikIcons.AddSel) )
#
#        self.drawer.addMassButton.clicked.connect(self.handleMassAddButtonClicked)
#        self.drawer.addMassButton.setIcon( QIcon(ilastikIcons.AddSel) )
#
#        self.drawer.addStackButton.clicked.connect(self.handleAddStackButtonClicked)
#        self.drawer.addStackButton.setIcon( QIcon(ilastikIcons.AddSel) )
#
#        self.drawer.addStackFilesButton.clicked.connect(self.handleAddStackFilesButtonClicked)
#        self.drawer.addStackFilesButton.setIcon( QIcon(ilastikIcons.AddSel) )
#
#        self.drawer.removeFileButton.setEnabled(False)
#        self.drawer.removeFileButton.clicked.connect(self.handleRemoveButtonClicked)
#        self.drawer.removeFileButton.setIcon( QIcon(ilastikIcons.RemSel) )

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

    def _initTableViews(self):
        self.fileInfoTabWidget.setTabText( 0, "Summary" )
        self.laneSummaryTableView.setModel( DataLaneSummaryTableModel(self, self.topLevelOperator) )
        self.laneSummaryTableView.dataLaneSelected.connect( self.showDataset )
        self.removeLaneButton.clicked.connect( self.handleRemoveLaneButtonClicked )

        self._retained = [] # Retain menus so they don't get deleted
        for roleIndex, role in enumerate(self.topLevelOperator.DatasetRoles.value):
            detailViewer = DataDetailViewerWidget( self, self.topLevelOperator, roleIndex )
            
            addOneMenu = QMenu()
            addOneMenu.addAction( "Select File..." ).triggered.connect( partial(self.handleAddFiles, roleIndex) )
            addOneMenu.addAction( "Specify Stack..." ).triggered.connect( partial(self.handleAddStack, roleIndex) )
            detailViewer.addOneButton.setMenu( addOneMenu )
            self._retained.append(addOneMenu)
            
            addManyMenu = QMenu()
            addManyMenu.addAction( "Select Files..." ).triggered.connect( partial(self.handleAddFiles, roleIndex) )
            addManyMenu.addAction( "Give Pattern..." ).triggered.connect( partial(self.handleAddByPattern, roleIndex) )
            detailViewer.addManyButton.setMenu( addManyMenu )
            self._retained.append(addManyMenu)
            
            #detailViewer.addFileButton.clicked.connect( partial(self.handleAddFileButtonClicked, roleIndex) )
            #detailViewer.addByPatternButton.clicked.connect( partial(self.handleMassAddButtonClicked, roleIndex) )
            #detailViewer.importStackFilesButton.clicked.connect( partial(self.handleAddStackFilesButtonClicked, roleIndex) )
            #detailViewer.clearButton.clicked( partial(self.yadayada, roleIndex) )
            
            self.fileInfoTabWidget.insertTab(roleIndex, detailViewer, role)

    def _initViewerStack(self):
        self.volumeEditors = {}
        self.viewerStack.addWidget( QWidget() )

    def handleAddFiles(self, roleIndex):
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
                self.addFileNames(fileNames, roleIndex)
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


    def handleAddStackButtonClicked(self, roleIndex):
        """
        The user clicked the "Import Stack Directory" button.
        """
        # Find the directory of the most recently opened image file
        mostRecentStackDirectory = PreferencesManager().get( 'DataSelection', 'recent stack directory' )
        if mostRecentStackDirectory is not None:
            defaultDirectory = os.path.split(mostRecentStackDirectory)[0]
        else:
            defaultDirectory = os.path.expanduser('~')

        options = QFileDialog.Options(QFileDialog.ShowDirsOnly)
        if ilastik_config.getboolean("ilastik", "debug"):
            options |= QFileDialog.DontUseNativeDialog

        # Launch the "Open File" dialog
        directoryName = QFileDialog.getExistingDirectory(self,
                                                         "Image Stack Directory",
                                                         defaultDirectory,
                                                         options=options)

        # If the user didn't cancel
        if not directoryName.isNull():
            PreferencesManager().set('DataSelection', 'recent stack directory', str(directoryName))
            globString = self.getGlobString( str(directoryName).replace("\\","/" ) )        
            if globString is not None:
                self.importStackFromGlobString( globString )

    def getGlobString(self, directory):
        exts = vigra.impex.listExtensions().split()
        for ext in exts:
            fullGlob = directory + '/*.' + ext
            filenames = glob.glob(fullGlob)

            if len(filenames) == 1:
                QMessageBox.warning(self, "Invalid selection", 'Cannot create stack: There is only one image file in the selected directory.  If your stack is contained in a single file (e.g. a multi-page tiff or hdf5 volume), please use the "Add File" button.' )
                return None

            if len(filenames) > 0:
                # Be helpful: find the longest globstring we can
                prefix = os.path.commonprefix(filenames)
                return prefix + '*.' + ext

        # Couldn't find an image file in the directory...
        return None

    def handleAddStack(self, roleIndex):
        """
        The user clicked the "Import Stack Files" button.
        """
        # Find the directory of the most recently opened image file
        mostRecentStackImageFile = PreferencesManager().get( 'DataSelection', 'recent stack image' )
        if mostRecentStackImageFile is not None:
            defaultDirectory = os.path.split(mostRecentStackImageFile)[0]
        else:
            defaultDirectory = os.path.expanduser('~')

        # Launch the "Open File" dialog
        fileNames = self.getImageFileNamesToOpen(defaultDirectory)

        if len(fileNames) == 1:
            QMessageBox.warning(self, "Invalid selection", 'Cannot create stack: You only selected one file.  If your stack is contained in a single file (e.g. a multi-page tiff or hdf5 volume), please use the "Add File" button.' )
            return

        # If the user didn't cancel
        if len(fileNames) > 0:
            PreferencesManager().set('DataSelection', 'recent stack image', fileNames[0])
            # Convert into one big string, which is accepted by the stack loading operator
            bigString = "//".join( fileNames )
            self.importStackFromGlobString(bigString, roleIndex)

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

    def importStackFromGlobString(self, globString, roleIndex):
        """
        The word 'glob' is used loosely here.  See the OpStackLoader operator for details.
        """
        globString = globString.replace("\\","/")
        info = DatasetInfo()
        info.filePath = globString

        # Allow labels by default if this gui isn't being used for batch data.
        info.allowLabels = ( self.guiMode == GuiMode.Normal )

        def importStack():
            self.guiControlSignal.emit( ControlCommand.DisableAll )
            # Serializer will update the operator for us, which will propagate to the GUI.
            try:
                self.serializer.importStackAsLocalDataset( info )
            finally:
                self.guiControlSignal.emit( ControlCommand.Pop )

        req = Request( importStack )
        req.notify_failed( partial(self.handleFailedStackLoad, globString ) )
        req.submit()

    @threadRouted
    def handleFailedStackLoad(self, globString, exc, exc_info):
        import traceback
        traceback.print_tb(exc_info[2])
        msg = "Failed to load stack: {}\n".format(globString)
        msg += "Due to the following error:\n{}".format( exc )
        QMessageBox.critical(self, "Failed to load image stack", msg)

    def addFileNames(self, fileNames, roleIndex):
        """
        Add the given filenames to both the GUI table and the top-level operator inputs.
        The filenames will be *appended* to the role's list of files.
        """
        infos = []
        
        opTop = self.topLevelOperator
        
        # Determine the number of files this role already has
        # Search for the last valid value.
        firstNewLane = 0
        for laneIndex, slot in reversed(zip(range(len(opTop.DatasetGroup)), opTop.DatasetGroup)):
            if slot[roleIndex].ready():
                firstNewLane = laneIndex+1
                break
        totalLanes = firstNewLane+len(fileNames)

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
        if len( opTop.DatasetGroup ) < totalLanes:
            opTop.DatasetGroup.resize( totalLanes )

        for laneIndex, info in zip(range(firstNewLane, totalLanes), infos):
            self.topLevelOperator.DatasetGroup[laneIndex][roleIndex].setValue( info )

    @threadRouted
    def updateTableForSlot(self, slot, *args):
        """
        Update the given rows using the top-level operator parameters
        """
        with Tracer(traceLogger):

            # Don't update anything if the slot doesn't have data yet
            if not slot.connected():
                return

            # Which index is this slot?
            row = -1
            for i in range( len(self.topLevelOperator.Dataset) ):
                if slot == self.topLevelOperator.Dataset[i]:
                    row = i
                    break

            assert row != -1, "Unknown input slot!"

            totalPath = self.topLevelOperator.Dataset[row].value.filePath
            lastDotIndex = totalPath.rfind('.')
            extensionAndInternal = totalPath[lastDotIndex:]
            extension = extensionAndInternal.split('/')[0]
            externalPath = totalPath[:lastDotIndex] + extension

            internalPath = ''
            internalStart = extensionAndInternal.find('/')
            if internalStart != -1:
                internalPath = extensionAndInternal[internalStart:]

            fileName = os.path.split(externalPath)[1]

            tableWidget = self.fileInfoTableWidget

            # Show the filename in the table (defaults to edit widget)
            tableWidget.setItem( row, Column.Name, QTableWidgetItem(fileName) )

            # Create and add the combobox for the internal path selection
            self.updateInternalPathComboBox( row, externalPath, internalPath )
    #        tableWidget.setItem( row, Column.InternalID, QTableWidgetItem(internalPath) )

            # Subscribe to changes
            tableWidget.itemChanged.connect( self.handleRowDataChange )

            # Create and add the combobox for storage location options
            self.updateStorageOptionComboBox(row, externalPath)

            if self.guiMode != GuiMode.Batch:
                # Create and add the checkbox for the 'allow labels' option
                allowLabelsCheckbox = QCheckBox()
                allowLabelsCheckbox.setChecked( self.topLevelOperator.Dataset[row].value.allowLabels )
                tableWidget.setCellWidget( row, Column.LabelsAllowed, allowLabelsCheckbox )
                allowLabelsCheckbox.stateChanged.connect( partial(self.handleAllowLabelsCheckbox, self.topLevelOperator.Dataset[row]) )

            # Update the operator, in case we need to select a new internal path based on the updated combo options
            # (Won't have any effect if nothing changed this time around.)
            self.updateFilePath(row)

            # Select a row if there isn't one already selected.
            selectedRanges = self.fileInfoTableWidget.selectedRanges()
            if len(selectedRanges) == 0:
                self.fileInfoTableWidget.selectRow(0)

    def handleAllowLabelsCheckbox(self, slot, checked):
        """
        The user (un)checked the "allow labels" checkbox in one of the table rows.
        Update the corresponding dataset info in the operator (which is given in the parameter 'slot')
        """
        with Tracer(traceLogger):
            # COPY the dataset so we trigger the slot to be dirty
            newDatasetInfo = copy.copy(slot.value)
            newDatasetInfo.allowLabels = ( checked == Qt.Checked )

            # Only update if necessary
            if newDatasetInfo.allowLabels != slot.value.allowLabels:
                slot.setValue( newDatasetInfo )

    def updateStorageOptionComboBox(self, row, filePath):
        """
        Create and add the combobox for storage location options
        """
        assert threading.current_thread().name == "MainThread"
        with Tracer(traceLogger):
            # Determine the relative path to this file
            absPath, relPath = getPathVariants(filePath, self.topLevelOperator.WorkingDirectory.value)
            # Add a prefixes to make the options clear
            absPath = "Absolute Link: " + absPath
            relPath = "Relative Link: <project directory>/" + relPath

            combo = QComboBox()
            options = {} # combo data -> combo text
            options[ LocationOptions.AbsolutePath ] = absPath
            options[ LocationOptions.RelativePath ] = relPath

            options[ LocationOptions.Project ] = "Store in Project File"

            for option, text in sorted(options.items()):
                # Add to the combo, storing the option as the item data
                combo.addItem(text, option)

            # Select the combo index that matches the current setting
            location = self.topLevelOperator.Dataset[row].value.location

            if location == DatasetInfo.Location.ProjectInternal:
                comboData = LocationOptions.Project
            elif location == DatasetInfo.Location.FileSystem:
                # Determine if the path is relative or absolute
                if os.path.isabs(self.topLevelOperator.Dataset[row].value.filePath[0]):
                    comboData = LocationOptions.AbsolutePath
                else:
                    comboData = LocationOptions.RelativePath

            comboIndex = combo.findData( QVariant(comboData) )
            combo.setCurrentIndex( comboIndex )

            combo.currentIndexChanged.connect( partial(self.handleComboSelectionChanged, combo) )
            self.fileInfoTableWidget.setCellWidget( row, Column.Location, combo )

    def updateInternalPathComboBox( self, row, externalPath, internalPath ):
        assert threading.current_thread().name == "MainThread"
        with Tracer(traceLogger):
            combo = QComboBox()
            datasetNames = []

            # Make sure we're dealing with the absolute path (to make this simple)
            absPath, relPath = getPathVariants(externalPath, self.topLevelOperator.WorkingDirectory.value)
            ext = os.path.splitext(absPath)[1]
            h5Exts = ['.ilp', '.h5', '.hdf5']
            if ext in h5Exts:
                datasetNames = self.getPossibleInternalPaths(absPath)

            # Add each dataset option to the combo
            for path in datasetNames:
                combo.addItem( path )

            # If the internal path we used previously is in the combo list, select it.
            prevSelection = combo.findText( internalPath )
            if prevSelection != -1:
                combo.setCurrentIndex( prevSelection )

            # Define response to changes and add it to the GUI.
            # Pass in the corresponding the table item so we can figure out which row this came from
            combo.currentIndexChanged.connect( bind(self.handleComboSelectionChanged, combo) )
            self.fileInfoTableWidget.setCellWidget( row, Column.InternalID, combo )

            # Since we just selected a new internal path, call the handler
            #self.handleComboSelectionChanged(combo, combo.currentIndex())

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

    def handleRowDataChange(self, changedItem ):
        """
        The user manually edited a file name in the table.
        Update the operator and other GUI elements with the new file path.
        """
        with Tracer(traceLogger):
            # Figure out which row this widget is in
            row = changedItem.row()
            column = changedItem.column()

            # Can't update until the row is fully initialized
            needUpdate = True
            needUpdate &= column == Column.Name or column == Column.InternalID
            needUpdate &= self.fileInfoTableWidget.item(row, Column.Name) != None
            needUpdate &= self.fileInfoTableWidget.cellWidget(row, Column.InternalID) != None
            needUpdate &= self.fileInfoTableWidget.cellWidget(row, column) is not None

            if needUpdate:
                self.updateFilePath(row)

    @threadRouted
    def updateFilePath(self, index):
        """
        Update the operator's filePath input to match the gui
        """
        with Tracer(traceLogger):
            oldLocationSetting = self.topLevelOperator.Dataset[index].value.location

            # Get the directory by inspecting the original operator path
            oldTotalPath = self.topLevelOperator.Dataset[index].value.filePath.replace('\\', '/')
            # Split into directory, filename, extension, and internal path
            lastDotIndex = oldTotalPath.rfind('.')
            extensionAndInternal = oldTotalPath[lastDotIndex:]
            extension = extensionAndInternal.split('/')[0]
            oldFilePath = oldTotalPath[:lastDotIndex] + extension

            fileNameText = str(self.fileInfoTableWidget.item(index, Column.Name).text())

            internalPathCombo = self.fileInfoTableWidget.cellWidget(index, Column.InternalID)
            #internalPath = str(self.fileInfoTableWidget.item(index, Column.InternalID).text())
            internalPath = str(internalPathCombo.currentText())

            directory = os.path.split(oldFilePath)[0]
            newFileNamePath = fileNameText
            if directory != '':
                newFileNamePath = directory + '/' + fileNameText

            newTotalPath = newFileNamePath
            if internalPath != '':
                if internalPath[0] != '/':
                    newTotalPath += '/'
                newTotalPath += internalPath

            cwd = self.topLevelOperator.WorkingDirectory.value
            absTotalPath, relTotalPath = getPathVariants( newTotalPath, cwd )
            absTotalPath = absTotalPath.replace('\\','/')
            relTotalPath = relTotalPath.replace('\\','/')

            # Check the location setting
            locationCombo = self.fileInfoTableWidget.cellWidget(index, Column.Location)
            comboIndex = locationCombo.currentIndex()
            newLocationSelection = locationCombo.itemData(comboIndex).toInt()[0] # In PyQt, toInt() returns a tuple

            if newLocationSelection == LocationOptions.Project:
                newLocationSetting = DatasetInfo.Location.ProjectInternal
            elif newLocationSelection == LocationOptions.AbsolutePath:
                newLocationSetting = DatasetInfo.Location.FileSystem
                newTotalPath = absTotalPath
            elif newLocationSelection == LocationOptions.RelativePath:
                newLocationSetting = DatasetInfo.Location.FileSystem
                newTotalPath = relTotalPath

            if newTotalPath != oldTotalPath or newLocationSetting != oldLocationSetting:
                # Be sure to copy so the slot notices the change when we setValue()
                datasetInfo = copy.copy(self.topLevelOperator.Dataset[index].value)
                datasetInfo.filePath = newTotalPath
                datasetInfo.location = newLocationSetting

                # TODO: First check to make sure this file exists!
                self.topLevelOperator.Dataset[index].setValue( datasetInfo )

                # Update the storage option combo to show the new path
                self.updateStorageOptionComboBox(index, newFileNamePath)

    def handleRemoveLaneButtonClicked(self):
        """
        The user clicked the "Remove" button.
        Remove the currently selected row(s) from both the GUI and the top-level operator.
        """
        # Figure out which lane to remove
        selectedIndexes = self.laneSummaryTableView.selectedIndexes()
        row = selectedIndexes[0].row()

        # Remove from the GUI
        self.laneSummaryTableView.model().removeRow(row)
        # Remove from the operator
        finalSize = len(self.topLevelOperator.DatasetGroup) - 1
        self.topLevelOperator.DatasetGroup.removeSlot(row, finalSize)

        # The gui and the operator should be in sync
        assert self.laneSummaryTableView.model().rowCount() == len(self.topLevelOperator.DatasetGroup)

    def handleComboSelectionChanged(self, combo, index):
        """
        Handles changes to any combo change in the table (either external path or internal path)
        """
        with Tracer(traceLogger):
            logger.debug("Combo selection changed: " + combo.itemText(1) + str(index))

            # Figure out which row this combo is in
            tableWidget = self.fileInfoTableWidget
            changedRow = -1
            for row in range(0, tableWidget.rowCount()):
                for column in range(Column.NumColumns):
                    widget = tableWidget.cellWidget(row, column)
                    if widget == combo:
                        changedRow = row
                        break
            assert changedRow != -1

            self.updateFilePath( changedRow )

    def showDataset(self, laneIndex):
        if laneIndex == -1:
            self.viewerStack.setCurrentIndex(0)
            return
        
        assert threading.current_thread().name == "MainThread"
        imageSlot = self.topLevelOperator.Image[laneIndex]

        # Create if necessary
        if imageSlot not in self.volumeEditors.keys():
            layerViewer = LayerViewerGui(self.topLevelOperator.getLane(laneIndex), crosshair=False)

            # Maximize the x-y view by default.
            layerViewer.volumeEditorWidget.quadview.ensureMaximized(2)

            self.volumeEditors[imageSlot] = layerViewer
            self.viewerStack.addWidget( layerViewer )

        # Show the right one
        self.viewerStack.setCurrentWidget( self.volumeEditors[imageSlot] )
