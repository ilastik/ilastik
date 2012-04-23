from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL, QObject
from PyQt4.QtGui import *
from PyQt4 import uic

import os

import utility # ilastik shell utility

class DataSelectionGui(QMainWindow):
    """
    Manages all GUI elements in the data selection applet.
    This class itself is the central widget and also owns/manages the applet drawer widgets.
    """
    def __init__(self, dataSelectionOperator):
        super(DataSelectionGui, self).__init__(self)
        self.mainOperator = dataSelectionOperator
        
        self.initCentralUic()
    
    def initCentralUic(self):
        """
        Load the GUI from the ui file into this class and connect it with event handlers.
        """
        # Load the ui file into this class (find it in our own directory)
        localDir = utility.getPathToLocalDirectory(__file__)
        uic.loadUi(localDir+"/dataSelection.ui", self)

        self.addFileButton.clicked.connect(self.addFileButtonClicked)
        
        
    def addFileButtonClicked(self):
        fileNames = QFileDialog.getOpenFileNames(
        self, "Select Image", os.path.abspath(__file__), "Numpy and h5 files (*.npy *.h5)")
        if fileNames.count() == 0:
            return
        
        # Put the data into an operator
        importer = DataImporter( self.g )
        inputProvider = importer.openFile(fileNames)
        
        print "Input Shape = ", inputProvider.Output.meta.shape
        print "Input dtype = ", inputProvider.Output.meta.dtype
        
        # Connect the operator to the pipeline input
        self.pipeline.setInputData(inputProvider)
