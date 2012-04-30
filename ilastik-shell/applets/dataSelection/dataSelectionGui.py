from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL, QObject
from PyQt4.QtGui import *
from PyQt4 import uic

from opDataSelection import OpDataSelection
from opMultiInputDataReader import OpMultiInputDataReader

from functools import partial
import os
import utility # This is the ilastik shell utility module

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
    # RelativePath # TODO
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
        oldNumFiles = len(self.mainOperator.FileNames)
        self.mainOperator.FileNames.resize( oldNumFiles+len(fileNames) )
        self.mainOperator.InvertFlags.resize( oldNumFiles+len(fileNames) )
        self.mainOperator.GrayConvertFlags.resize( oldNumFiles+len(fileNames) )

        # Assign values to the new inputs we just allocated.
        for i in range(0, len(fileNames)):
            self.mainOperator.FileNames[i+oldNumFiles].setValue( fileNames[i] )
            # (No inversion/conversion by default)
            self.mainOperator.InvertFlags[i+oldNumFiles].setValue( False )
            self.mainOperator.GrayConvertFlags[i+oldNumFiles].setValue( False )

        # Which rows do we need to add to the GUI?
        oldNumRows = self.fileInfoTableWidget.rowCount()
        numFiles = len(self.mainOperator.FileNames)

        # Make room in the table widget for the new rows
        self.fileInfoTableWidget.setRowCount( len(self.mainOperator.FileNames) )

        # Update the contents of the new rows in the GUI.        
        self.updateTableRows(oldNumRows, numFiles)

    def updateTableRows(self, startRow, stopRow):
        """
        Update the given rows using the top-level operator parameters
        """
        # Update the data in the new rows
        for row in range(startRow, stopRow):
            filePath = self.mainOperator.FileNames[row].value
            fileName = os.path.split(filePath)[1]

            tableWidget = self.fileInfoTableWidget

            # Show the filename in the table (defaults to edit widget)
            fileNameWidget = QTableWidgetItem(fileName)
            tableWidget.setItem( row, Column.Name, fileNameWidget )
            tableWidget.itemChanged.connect( self.handleFileNameEditChanged )
            
            # Create and add the combobox for storage location options
            self.updateStorageOptionComboBox(row, filePath)

            # Create and add the checkbox for color inversion
            invertCheckbox = QCheckBox()
            invertCheckbox.stateChanged.connect( partial(self.handleFlagCheckboxChange, Column.Invert, invertCheckbox) )
            invertCheckbox.setChecked( self.mainOperator.InvertFlags[row].value )
            tableWidget.setCellWidget( row, Column.Invert, invertCheckbox)
            
            # Create and add the checkbox for grayscale conversion
            convertToGrayCheckbox = QCheckBox()
            convertToGrayCheckbox.stateChanged.connect( partial(self.handleFlagCheckboxChange, Column.Grayscale, convertToGrayCheckbox) )
            invertCheckbox.setChecked( self.mainOperator.GrayConvertFlags[row].value )
            tableWidget.setCellWidget( row, Column.Grayscale, convertToGrayCheckbox)

        # The gui and the operator should be in sync
        assert tableWidget.rowCount() == len(self.mainOperator.FileNames)
    
    def updateStorageOptionComboBox(self, row, filePath):
        """
        Create and add the combobox for storage location options
        """
        combo = QComboBox()
        options = { LocationOptions.Project : "<project>",
                    LocationOptions.AbsolutePath : filePath }
        for index, text in sorted(options.items()):
            combo.addItem(text)
        combo.currentIndexChanged.connect( partial(self.handleStorageOptionComboIndexChanged, combo) )
        tableWidget = self.fileInfoTableWidget
        tableWidget.setCellWidget( row, Column.Location, combo )
        
    
    def handleFileNameEditChanged(self, fileNameWidget ):
        """
        The user manually edited a file name in the table.
        Update the operator and other GUI elements with the new file path.
        """
        # Figure out which row this checkbox is in
        tableWidget = self.fileInfoTableWidget
        changedRow = -1
        for row in range(0, tableWidget.rowCount()):
            widget = tableWidget.item(row, Column.Name)
            if widget == fileNameWidget:
                changedRow = row
                break
        assert changedRow != -1

        # Get the directory by inspecting the original operator path
        oldPath = self.mainOperator.FileNames[changedRow].value
        directory = os.path.split(oldPath)[0]
        newPath = directory + '/' + str(fileNameWidget.text())

        # TODO: First check to make sure this file exists!        
        self.mainOperator.FileNames[changedRow].setValue( newPath )

        # Update the storage option combo to show the new path        
        self.updateStorageOptionComboBox(changedRow, newPath)
        
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
            self.mainOperator.FileNames.removeSlot(row)
            
        # The gui and the operator should be in sync
        assert self.fileInfoTableWidget.rowCount() == len(self.mainOperator.FileNames)

    def handleStorageOptionComboIndexChanged(self, combo, newIndex):
        print "Combo selection changed: ", combo.itemText(1), newIndex
        # TODO: Store the new storage option selection.
        #       (Affects serialization.)
        
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
        
        # Now that we've found the row (and therefore the filename index),
        #  update this flag in the appropriate operator input slot
        if column == Column.Invert:
            self.mainOperator.InvertFlags[changedRow].setValue( checkState == Qt.Checked )
        elif column == Column.Grayscale:
            self.mainOperator.GrayConvertFlags[changedRow].setValue( checkState == Qt.Checked )
        else:
            assert False, "Invalid column for checkbox"






















































