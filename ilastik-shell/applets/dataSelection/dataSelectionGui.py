from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL, QObject
from PyQt4.QtGui import *
from PyQt4 import uic

from opDataSelection import OpDataSelection
from opMultiInputDataReader import OpMultiInputDataReader

from functools import partial

import os

import utility # ilastik shell utility

class Column():
    Name = 0
    Location = 1
    InternalID = 2

class LocationOptions():
    Project = 0
    Path = 1
    ChooseNew = 2

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
        localDir = utility.getPathToLocalDirectory(__file__)
        # (We don't pass self here because we keep the drawer ui in a separate object.)
        self.drawer = uic.loadUi(localDir+"/dataSelectionDrawer.ui")
    
    def initCentralUic(self):
        """
        Load the GUI from the ui file into this class and connect it with event handlers.
        """
        # Load the ui file into this class (find it in our own directory)
        localDir = utility.getPathToLocalDirectory(__file__)
        uic.loadUi(localDir+"/dataSelection.ui", self)

        self.fileInfoTableWidget.resizeRowsToContents()
        self.fileInfoTableWidget.resizeColumnsToContents()
        self.fileInfoTableWidget.setAlternatingRowColors(True)
        self.fileInfoTableWidget.setShowGrid(False)
        self.fileInfoTableWidget.horizontalHeader().setResizeMode(0, QHeaderView.Interactive)
        
        self.fileInfoTableWidget.horizontalHeader().resizeSection(Column.Name, 200)
        self.fileInfoTableWidget.horizontalHeader().resizeSection(Column.Location, 400)
        self.fileInfoTableWidget.horizontalHeader().resizeSection(Column.InternalID, 100)
        self.fileInfoTableWidget.verticalHeader().hide()

        # Set up our handlers
        self.addFileButton.clicked.connect(self.handleAddButtonClicked)
        self.removeFileButton.clicked.connect(self.handleRemoveButtonClicked)
        self.fileInfoTableWidget.itemSelectionChanged(self.handleTableSelectionChange)
        
        
    def handleAddButtonClicked(self):
        # Launch the "Open File" dialog
        fileNames = QFileDialog.getOpenFileNames(
        self, "Select Image", os.path.abspath(__file__), "Numpy and h5 files (*.npy *.h5)")

        # If the user canceled, stop now.
        if fileNames.count() == 0:
            return
        
        # Add the new filename(s) to the operator input.
        oldNumFiles = len(self.mainOperator.FileNames)
        self.mainOperator.FileNames.resize( oldNumFiles+len(fileNames) )
        for i in range(0, len(fileNames)):
            self.mainOperator.FileNames[i+oldNumFiles].setValue( str(fileNames[i]) )

        # Which rows do we need to add?
        oldNumRows = self.fileInfoTableWidget.rowCount()
        numFiles = len(self.mainOperator.FileNames)

        # Make room in the table widget for the new rows
        self.fileInfoTableWidget.setRowCount( len(self.mainOperator.FileNames) )

        # Update the data in the new rows
        for row in range(oldNumRows, numFiles):
            filePath = self.mainOperator.FileNames[row].value
            fileName = os.path.split(filePath)[1]
            self.fileInfoTableWidget.setItem( row, Column.Name, QTableWidgetItem(fileName) )
            self.fileInfoTableWidget.setCellWidget( row, Column.Location, self.createLocationCombo(filePath) )

        # The gui and the operator should be in sync
        assert self.fileInfoTableWidget.rowCount() == len(self.mainOperator.FileNames)
    
    def updateFileListGui(self):
        pass

    def createLocationCombo(self, filePath):
        # Create a combo box with the right options
        combo = QComboBox()
        options = { LocationOptions.Project : "<project>",
                    LocationOptions.Path : filePath }
        for index, text in sorted(options.items()):
            combo.addItem(text)
        combo.currentIndexChanged.connect( partial(self.handleComboIndexChanged, combo) )
        return combo
        
    def handleRemoveButtonClicked(self):
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
            
                

    def handleComboIndexChanged(self, combo, newIndex):
        print "Combo selection changed: ", combo.itemText(1), newIndex 
        
    def handleTableSelectionChange(self):
        """
        Ensure that entire rows are selected at once.
        """
        






















































