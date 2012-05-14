from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL, QObject
from PyQt4.QtGui import *
from PyQt4 import uic

from opDataSelection import OpDataSelection

from functools import partial
import os
import sys
import copy
import utility # This is the ilastik shell utility module

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
    Invert = 3
    Grayscale = 4

class LocationOptions():
    """ Enum for location menu options """
    Project = 0
    AbsolutePath = 1
    RelativePath = 2
    # ChooseNew    # TODO

class DataSelectionGui(QMainWindow):
    """
    Manages all GUI elements in the data selection applet.
    This class itself is the central widget and also owns/manages the applet drawer widgets.
    """
    def __init__(self, dataSelectionOperator):
        super(DataSelectionGui, self).__init__()

        self.drawer = None
        self.mainOperator = dataSelectionOperator
        self.menuBar = QMenuBar()
        
        self.initAppletDrawerUic()
        self.initCentralUic()

        # Closure for handling a change to an individual dataset        
        def handleItemChange( row, slot ):
            self.updateTableForSlot(slot)
        
        # Closure for handling input list resizes
        def handleInputListChange(slot, oldsize, newsize):
            # Our file list widget should match the length of the operator input list
            self.fileInfoTableWidget.setRowCount( newsize )

            for i, slot in enumerate(self.mainOperator.DatasetInfos):
                # Update now
                self.updateTableForSlot( slot )
                # Update if data changes
                slot.notifyMetaChanged( self.updateTableForSlot )

        self.mainOperator.DatasetInfos.notifyResized(handleInputListChange)
        
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
        # (Leave the checkbox column widths alone.  They will be auto-sized.)
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
        oldNumFiles = len(self.mainOperator.DatasetInfos)
        self.mainOperator.DatasetInfos.resize( oldNumFiles+len(fileNames) )

        # Assign values to the new inputs we just allocated.
        # The GUI will be updated by callbacks that are listening to slot changes
        for i in range(0, len(fileNames)):
            datasetInfo = OpDataSelection.DatasetInfo()
            datasetInfo.filePath = fileNames[i]
            datasetInfo.invertColors = False
            datasetInfo.convertToGrayscale = False
            self.mainOperator.DatasetInfos[i+oldNumFiles].setValue( datasetInfo )

    def updateTableForSlot(self, slot):
        """
        Update the given rows using the top-level operator parameters
        """
        
        # Don't update anything if the slot doesn't have data yet
        if not slot.connected():
            return
        
        # Which index is this slot?
        row = -1
        for i in range( len(self.mainOperator.DatasetInfos) ):
            if slot == self.mainOperator.DatasetInfos[i]:
                row = i
                break

        assert row != -1, "Unknown input slot!"
        
        totalPath = self.mainOperator.DatasetInfos[row].value.filePath
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

        # Create and add the checkbox for color inversion
        invertCheckbox = QCheckBox()
        invertCheckbox.setChecked( self.mainOperator.DatasetInfos[row].value.invertColors )
        tableWidget.setCellWidget( row, Column.Invert, invertCheckbox)
        invertCheckbox.stateChanged.connect( partial(self.handleFlagCheckboxChange, Column.Invert, invertCheckbox) )
        
        # Create and add the checkbox for grayscale conversion
        convertToGrayCheckbox = QCheckBox()
        convertToGrayCheckbox.setChecked( self.mainOperator.DatasetInfos[row].value.convertToGrayscale )
        tableWidget.setCellWidget( row, Column.Grayscale, convertToGrayCheckbox)
        convertToGrayCheckbox.stateChanged.connect( partial(self.handleFlagCheckboxChange, Column.Grayscale, convertToGrayCheckbox) )
    
    def updateStorageOptionComboBox(self, row, filePath):
        """
        Create and add the combobox for storage location options
        """
        
        # Determine the relative path to this file
        absPath, relPath = getPathVariants(filePath, self.mainOperator.WorkingDirectory.value)
        # Add a prefix to make it clear that it's a relative path
        relPath = "<project dir>/" + relPath
        
        combo = QComboBox()
        options = { LocationOptions.Project : "<project>",
                    LocationOptions.AbsolutePath : absPath,
                    LocationOptions.RelativePath : relPath }
        for index, text in sorted(options.items()):
            combo.addItem(text)

        if self.mainOperator.DatasetInfos[row].value.location == OpDataSelection.DatasetInfo.Location.ProjectInternal:
            combo.setCurrentIndex( LocationOptions.Project )
        elif self.mainOperator.DatasetInfos[row].value.location == OpDataSelection.DatasetInfo.Location.FileSystem:
            if self.mainOperator.DatasetInfos[row].value.filePath[0] == '/':
                combo.setCurrentIndex( LocationOptions.AbsolutePath )
            else:
                combo.setCurrentIndex( LocationOptions.RelativePath )

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
        oldLocationSetting = self.mainOperator.DatasetInfos[index].value.location
        
        # Get the directory by inspecting the original operator path
        oldTotalPath = self.mainOperator.DatasetInfos[index].value.filePath
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
        newLocationSelection = locationCombo.currentIndex()

        if newLocationSelection == LocationOptions.Project:
            newLocationSetting = OpDataSelection.DatasetInfo.Location.ProjectInternal
        elif newLocationSelection == LocationOptions.AbsolutePath:
            newLocationSetting = OpDataSelection.DatasetInfo.Location.FileSystem
            newTotalPath = absTotalPath
        elif newLocationSelection == LocationOptions.RelativePath:
            newLocationSetting = OpDataSelection.DatasetInfo.Location.FileSystem
            newTotalPath = relTotalPath
        
        if newTotalPath != oldTotalPath or newLocationSetting != oldLocationSetting:
            # Be sure to copy so the slot notices the change when we setValue()
            datasetInfo = copy.copy(self.mainOperator.DatasetInfos[index].value)
            datasetInfo.filePath = newTotalPath
            datasetInfo.location = newLocationSetting
    
            # TODO: First check to make sure this file exists!
            self.mainOperator.DatasetInfos[index].setValue( datasetInfo )
    
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
            finalSize = len(self.mainOperator.DatasetInfos) - 1
            self.mainOperator.DatasetInfos.removeSlot(row, finalSize)
            
        # The gui and the operator should be in sync
        assert self.fileInfoTableWidget.rowCount() == len(self.mainOperator.DatasetInfos)

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
    
    def handleFlagCheckboxChange(self, column, checkboxWidget, checkState):
        """
        The user clicked on a checkbox in the table.
        Set the appropriate flag in the operator based on which checkbox it was.
        """
        # Figure out which row this checkbox is in
        tableWidget = self.fileInfoTableWidget
        changedRow = -1
        for row in range(0, tableWidget.rowCount()):
            widget = tableWidget.cellWidget(row, column)
            if widget == checkboxWidget:
                changedRow = row
                break
        assert changedRow != -1
        
        # Be sure to copy so the slot notices the change when we setValue()
        datasetInfo = copy.copy(self.mainOperator.DatasetInfos[changedRow].value)

        # Now that we've found the row (and therefore the dataset index),
        #  update this flag in the appropriate operator input slot
        if column == Column.Invert:
            datasetInfo.invertColors = (checkState == Qt.Checked)
            logger.debug("Invert Colors: " + str(datasetInfo.invertColors))
        elif column == Column.Grayscale:
            datasetInfo.convertToGrayscale = (checkState == Qt.Checked)
            logger.debug("Convert to Grayscale: " + str(datasetInfo.convertToGrayscale))
        else:
            assert False, "Invalid column for checkbox"
        self.mainOperator.DatasetInfos[changedRow].setValue( datasetInfo )

    def enableControls(self, enabled):
        """
        Enable or disable all of the controls in this applet's central widget.
        """
        # All the controls in our GUI
        controlList = [ self.fileInfoTableWidget ]

        # Enable/disable all of them
        for control in controlList:
            control.setEnabled(enabled)

def getPathVariants(originalPath, workingDirectory):
    """
    Take the given filePath (which can be absolute or relative, and may include an internal path suffix),
    and return a tuple of the absolute and relative paths to the file.
    """
    lastDotIndex = originalPath.rfind('.')
    extensionAndInternal = originalPath[lastDotIndex:]
    extension = extensionAndInternal.split('/')[0]

    relPath = originalPath
    
    if originalPath[0] == '/':
        absPath = originalPath
        relPath = os.path.relpath(absPath, workingDirectory)
    else:
        relPath = originalPath
        absPath = os.path.normpath( os.path.join(workingDirectory, relPath) )
        
    return (absPath, relPath)

if __name__ == "__main__":
    
    abs, rel = getPathVariants('/aaa/bbb/ccc/ddd.txt', '/aaa/bbb/ccc/eee')
    assert abs == '/aaa/bbb/ccc/ddd.txt'
    assert rel == '../ddd.txt'

    abs, rel = getPathVariants('../ddd.txt', '/aaa/bbb/ccc/eee')
    assert abs == '/aaa/bbb/ccc/ddd.txt'
    assert rel == '../ddd.txt'

    abs, rel = getPathVariants('ddd.txt', '/aaa/bbb/ccc')
    assert abs == '/aaa/bbb/ccc/ddd.txt'
    assert rel == 'ddd.txt'















































