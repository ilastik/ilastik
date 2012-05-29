from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL, QObject, QVariant
from PyQt4.QtGui import *
from PyQt4 import uic

from opDataSelection import OpDataSelection, DatasetInfo

from functools import partial
import os
import sys
import copy
import utility # This is the ilastik shell utility module
from utility import bind
from utility.pathHelpers import getPathVariants

import logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.addFilter(logging.Filter(__name__))
logger.addHandler(handler)
logger.setLevel(logging.WARN)

class Column():
    """ Enum for table column positions """
    Name = 0
    Location = 1
    InternalID = 2
    LabelsAllowed = 3 # Note: For now, this column must come last because it gets removed in batch mode.

class LocationOptions():
    """ Enum for location menu options """
    Project = 0
    AbsolutePath = 1
    RelativePath = 2

class GuiMode():
    Normal = 0
    Batch = 1

class DataSelectionGui(QMainWindow):
    """
    Manages all GUI elements in the data selection applet.
    This class itself is the central widget and also owns/manages the applet drawer widgets.
    """
    
    def __init__(self, dataSelectionOperator, guiMode=GuiMode.Normal):
        super(DataSelectionGui, self).__init__()

        self.drawer = None
        self.mainOperator = dataSelectionOperator
        self.menuBar = QMenuBar()
        self.guiMode = guiMode
        
        self.initAppletDrawerUic()
        self.initCentralUic()

        def handleNewDataset( multislot, index ):
            assert multislot == self.mainOperator.Dataset
            # Make room in the table
            self.fileInfoTableWidget.insertRow( index )
            
            # Update the table row data when this slot has new data
            # We can't bind in the row here because the row may change in the meantime.
            self.mainOperator.Dataset[index].notifyDirty( bind( self.updateTableForSlot ) )

        self.mainOperator.Dataset.notifyInserted( bind( handleNewDataset ) )
        
        def handleDatasetRemoved( multislot, index ):
            assert multislot == self.mainOperator.Dataset
            
            # Simply remove the row we don't need any more
            self.fileInfoTableWidget.removeRow( index )

        self.mainOperator.Dataset.notifyRemove( bind( handleDatasetRemoved ) )
        
    def initAppletDrawerUic(self):
        """
        Load the ui file for the applet drawer, which we own.
        """
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]+'/'
        # (We don't pass self here because we keep the drawer ui in a separate object.)
        self.drawer = uic.loadUi(localDir+"/dataSelectionDrawer.ui")

        # Set up our handlers
        self.drawer.addFileButton.clicked.connect(self.handleAddFileButtonClicked)
        self.drawer.addStackButton.clicked.connect(self.handleAddStackButtonClicked)
        self.drawer.removeFileButton.clicked.connect(self.handleRemoveButtonClicked)
        
        def enableAppletDrawerControls(enabled):
            """
            Enable or disable all of the controls in this applet's drawer widget.
            """
            # All the controls in our GUI
            controlList = [ self.drawer.addFileButton,
                            self.drawer.addStackButton,
                            self.drawer.removeFileButton ]
    
            # Enable/disable all of them
            for control in controlList:
                control.setEnabled(enabled)

        # Expose the enable function with the name the shell expects
        self.drawer.enableControls = enableAppletDrawerControls
    
    def initCentralUic(self):
        """
        Load the GUI from the ui file into this class and connect it with event handlers.
        """
        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]+'/'
        uic.loadUi(localDir+"/dataSelection.ui", self)

        self.fileInfoTableWidget.resizeRowsToContents()
        self.fileInfoTableWidget.resizeColumnsToContents()
        self.fileInfoTableWidget.setAlternatingRowColors(True)
        self.fileInfoTableWidget.setShowGrid(False)
        self.fileInfoTableWidget.horizontalHeader().setResizeMode(0, QHeaderView.Interactive)
        
        self.fileInfoTableWidget.horizontalHeader().resizeSection(Column.Name, 200)
        self.fileInfoTableWidget.horizontalHeader().resizeSection(Column.Location, 250)
        self.fileInfoTableWidget.horizontalHeader().resizeSection(Column.InternalID, 100)

        if self.guiMode == GuiMode.Batch:
            # It doesn't make sense to provide a labeling option in batch mode
            self.fileInfoTableWidget.removeColumn( Column.LabelsAllowed )
        
        self.fileInfoTableWidget.verticalHeader().hide()

        # Set up handlers
        self.fileInfoTableWidget.itemSelectionChanged.connect(self.handleTableSelectionChange)
        
    def handleAddFileButtonClicked(self):
        """
        The user clicked the "Add File" button.
        Ask him to choose a file (or several) and add them to both 
          the GUI table and the top-level operator inputs.
        """
        # Launch the "Open File" dialog
        fileNames = QFileDialog.getOpenFileNames(
                        self, "Select Image", os.path.abspath(__file__), "Numpy, h5, and image files (*.npy *.h5)")
        
        # Convert from QtString to python str
        fileNames = [str(s) for s in fileNames]

        # If the user didn't cancel        
        if len(fileNames) > 0:
            self.addFileNames(fileNames)
    
    def handleAddStackButtonClicked(self):
        """
        The user clicked the "Add Stack" button.
        Ask him to choose a file (or several) and add them to both 
          the GUI table and the top-level operator inputs.
        """
        # Launch the "Open File" dialog
        directoryName = QFileDialog.getExistingDirectory(self, "Image Stack Directory", os.path.abspath(__file__))

        # If the user didn't cancel        
        if not directoryName.isNull():
            # We assume png by default, but the user can change 
            #  the extension in the table if they use a different image format
            # TODO: Examine the directory contents and guess the user's image format
            globString = str(directoryName) + '/*.png'
            
            # Simply add the globstring as though it were a regular file path.
            # The top-level operator knows how to deal with it.
            self.addFileNames([globString])

    def addFileNames(self, fileNames):
        """
        Add the given filenames to both the GUI table and the top-level operator inputs.
        """
        # Allocate additional subslots in the operator inputs.
        oldNumFiles = len(self.mainOperator.Dataset)
        self.mainOperator.Dataset.resize( oldNumFiles+len(fileNames) )

        # Assign values to the new inputs we just allocated.
        # The GUI will be updated by callbacks that are listening to slot changes
        for i in range(0, len(fileNames)):
            datasetInfo = DatasetInfo()
            datasetInfo.filePath = fileNames[i]
            
            # Allow labels by default if this gui isn't being used for batch data.
            datasetInfo.allowLabels = ( self.guiMode == GuiMode.Normal )
            
            self.mainOperator.Dataset[i+oldNumFiles].setValue( datasetInfo )

    def updateTableForSlot(self, slot):
        """
        Update the given rows using the top-level operator parameters
        """
        
        # Don't update anything if the slot doesn't have data yet
        if not slot.connected():
            return
        
        # Which index is this slot?
        row = -1
        for i in range( len(self.mainOperator.Dataset) ):
            if slot == self.mainOperator.Dataset[i]:
                row = i
                break

        assert row != -1, "Unknown input slot!"
        
        totalPath = self.mainOperator.Dataset[row].value.filePath
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
        tableWidget.setItem( row, Column.InternalID, QTableWidgetItem(internalPath) )

        # Subscribe to changes        
        tableWidget.itemChanged.connect( self.handleRowDataChange )
        
        # Create and add the combobox for storage location options
        self.updateStorageOptionComboBox(row, externalPath)
        
        if self.guiMode != GuiMode.Batch:
            # Create and add the checkbox for the 'allow labels' option
            allowLabelsCheckbox = QCheckBox()
            allowLabelsCheckbox.setChecked( self.mainOperator.Dataset[row].value.allowLabels )
            tableWidget.setCellWidget( row, Column.LabelsAllowed, allowLabelsCheckbox )
            allowLabelsCheckbox.stateChanged.connect( partial(self.handleAllowLabelsCheckbox, self.mainOperator.Dataset[row]) )
    
    def handleAllowLabelsCheckbox(self, slot, checked):
        """
        The user (un)checked the "allow labels" checkbox in one of the table rows.
        Update the corresponding dataset info in the operator (which is given in the parameter 'slot')
        """
        # COPY the dataset so we trigger the slot to be dirty
        newDatasetInfo = copy.copy(slot.value)
        newDatasetInfo.allowLabels = ( checked == Qt.Checked )
        
        # Only update if necessary
        if newDatasetInfo != slot.value:
            slot.setValue( newDatasetInfo )
    
    def updateStorageOptionComboBox(self, row, filePath):
        """
        Create and add the combobox for storage location options
        """
        
        # Determine the relative path to this file
        absPath, relPath = getPathVariants(filePath, self.mainOperator.WorkingDirectory.value)
        # Add a prefix to make it clear that it's a relative path
        relPath = "<project dir>/" + relPath
        
        combo = QComboBox()
        options = {} # combo data -> combo text
        options[ LocationOptions.AbsolutePath ] = absPath
        options[ LocationOptions.RelativePath ] = relPath
        
        # Saving data to the project file is not an option in batch mode
        if self.guiMode == GuiMode.Normal:
            options[ LocationOptions.Project ] = "<project>"
                
        for option, text in sorted(options.items()):
            # Add to the combo, storing the option as the item data
            combo.addItem(text, option)

        # Select the combo index that matches the current setting
        location = self.mainOperator.Dataset[row].value.location

        if location == DatasetInfo.Location.ProjectInternal:
            comboData = LocationOptions.Project
        elif location == DatasetInfo.Location.FileSystem:
            # Determine if the path is relative or absolute
            if self.mainOperator.Dataset[row].value.filePath[0] == '/':
                comboData = LocationOptions.AbsolutePath
            else:
                comboData = LocationOptions.RelativePath

        comboIndex = combo.findData( QVariant(comboData) )
        combo.setCurrentIndex( comboIndex )

        combo.currentIndexChanged.connect( partial(self.handleStorageOptionComboIndexChanged, combo) )
        self.fileInfoTableWidget.setCellWidget( row, Column.Location, combo )
    
    def handleRowDataChange(self, changedItem ):
        """
        The user manually edited a file name in the table.
        Update the operator and other GUI elements with the new file path.
        """
        # Figure out which row this widget is in
        row = changedItem.row()
        column = changedItem.column()
        
        # Can't update until the row is fully initialized
        needUpdate = True
        needUpdate &= column == Column.Name or column == Column.InternalID
        needUpdate &= self.fileInfoTableWidget.item(row, Column.Name) != None 
        needUpdate &= self.fileInfoTableWidget.item(row, Column.InternalID) != None
        needUpdate &= self.fileInfoTableWidget.cellWidget(row, column) is not None
        
        if needUpdate:
            self.updateFilePath(row)
    
    def updateFilePath(self, index):
        """
        Update the operator's filePath input to match the gui
        """
        oldLocationSetting = self.mainOperator.Dataset[index].value.location
        
        # Get the directory by inspecting the original operator path
        oldTotalPath = self.mainOperator.Dataset[index].value.filePath
        # Split into directory, filename, extension, and internal path
        lastDotIndex = oldTotalPath.rfind('.')
        extensionAndInternal = oldTotalPath[lastDotIndex:]
        extension = extensionAndInternal.split('/')[0]
        oldFilePath = oldTotalPath[:lastDotIndex] + extension
        
        fileNameText = str(self.fileInfoTableWidget.item(index, Column.Name).text())
        internalPath = str(self.fileInfoTableWidget.item(index, Column.InternalID).text())
        
        directory = os.path.split(oldFilePath)[0]
        newFileNamePath = fileNameText
        if directory != '':
            newFileNamePath = directory + '/' + fileNameText
        
        newTotalPath = newFileNamePath
        if internalPath != '':
            if internalPath[0] != '/':
                newTotalPath += '/'
            newTotalPath += internalPath

        cwd = self.mainOperator.WorkingDirectory.value
        absTotalPath, relTotalPath = getPathVariants( newTotalPath, cwd )

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
            datasetInfo = copy.copy(self.mainOperator.Dataset[index].value)
            datasetInfo.filePath = newTotalPath
            datasetInfo.location = newLocationSetting
    
            # TODO: First check to make sure this file exists!
            self.mainOperator.Dataset[index].setValue( datasetInfo )
    
            # Update the storage option combo to show the new path        
            self.updateStorageOptionComboBox(index, newFileNamePath)
        
    def handleRemoveButtonClicked(self):
        """
        The user clicked the "Remove" button.
        Remove the currently selected row(s) from both the GUI and the top-level operator.
        """
        # Figure out which dataset to remove
        rowsToDelete = set()
        selectedRanges = self.fileInfoTableWidget.selectedRanges()
        for rng in selectedRanges:
            for row in range(rng.topRow(), rng.bottomRow()+1):
                rowsToDelete.add(row)
        
        # Remove files in reverse order so we don't have to switch indexes as we go
        for row in sorted(rowsToDelete, reverse=True):
            # Remove from the GUI
            self.fileInfoTableWidget.removeRow(row)
            # Remove from the operator input
            finalSize = len(self.mainOperator.Dataset) - 1
            self.mainOperator.Dataset.removeSlot(row, finalSize)
            
        # The gui and the operator should be in sync
        assert self.fileInfoTableWidget.rowCount() == len(self.mainOperator.Dataset)

    def handleStorageOptionComboIndexChanged(self, combo, newLocationSetting):
        logger.debug("Combo selection changed: " + combo.itemText(1) + str(newLocationSetting))

        # Figure out which row this combo is in
        tableWidget = self.fileInfoTableWidget
        changedRow = -1
        for row in range(0, tableWidget.rowCount()):
            widget = tableWidget.cellWidget(row, Column.Location)
            if widget == combo:
                changedRow = row
                break
        assert changedRow != -1
        
        self.updateFilePath( changedRow )
                
    def handleTableSelectionChange(self):
        """
        Any time the user selects a new item, select the whole row.
        """
        # Figure out which dataset to remove
        selectedItemRows = set()
        selectedRanges = self.fileInfoTableWidget.selectedRanges()
        for rng in selectedRanges:
            for row in range(rng.topRow(), rng.bottomRow()+1):
                selectedItemRows.add(row)
        
        # Disconnect from selection change notifications while we do this
        self.fileInfoTableWidget.itemSelectionChanged.disconnect(self.handleTableSelectionChange)
        for row in selectedItemRows:
            self.fileInfoTableWidget.selectRow(row)
            
        # Reconnect now that we're finished
        self.fileInfoTableWidget.itemSelectionChanged.connect(self.handleTableSelectionChange)
    
    def enableControls(self, enabled):
        """
        Enable or disable all of the controls in this applet's central widget.
        """
        # All the controls in our GUI
        controlList = [ self.fileInfoTableWidget ]

        # Enable/disable all of them
        for control in controlList:
            control.setEnabled(enabled)
















































