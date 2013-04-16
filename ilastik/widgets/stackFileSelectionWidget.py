import os
import glob
from functools import partial

from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal, Qt, QEvent
from PyQt4.QtGui import  QDialog, QFileDialog, QMessageBox

import vigra

from volumina.utility import PreferencesManager

import ilastik.config

class StackFileSelectionWidget(QDialog):
    
    def __init__(self, parent, files=None):
        super( StackFileSelectionWidget, self ).__init__( parent )
    
        self._initUi()
        
        if files is None:
            files = []
        self._updateFileList( files )
    
    def _initUi(self):
        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        uiFilePath = os.path.join( localDir, 'stackFileSelectionWidget.ui' )
        uic.loadUi(uiFilePath, self)

        self.okButton.clicked.connect( self.accept )
        self.cancelButton.clicked.connect( self.reject )

        self.directoryRadioButton.clicked.connect( partial( self._configureGui, 'directory' ) )
        self.selectFilesRadioButton.clicked.connect( partial( self._configureGui, 'files' ) )
        self.patternRadioButton.clicked.connect( partial( self._configureGui, 'pattern' ) )

        self.directoryChooseButton.clicked.connect( self._chooseDirectory )
        self.selectFilesChooseButton.clicked.connect( self._selectFiles )
        self.patternApplyButton.clicked.connect( self._applyPattern )
        self.patternEdit.installEventFilter( self )
    
        # Default to "select files" option, since it's most generic
        self.selectFilesRadioButton.setChecked(True)

    def accept(self):
        self.patternEdit.removeEventFilter(self)
        super( StackFileSelectionWidget, self ).accept()

    def reject(self):
        self.patternEdit.removeEventFilter(self)
        super( StackFileSelectionWidget, self ).reject()

    def _configureGui(self, mode):
        """
        Configure the gui to select files via one of our three selection modes.
        """
        self.directoryChooseButton.setEnabled( mode == 'directory' )
        self.directoryEdit.setEnabled( mode == 'directory' )
        self.directoryEdit.clear()
        
        self.selectFilesChooseButton.setEnabled( mode == 'files' )
        
        self.patternApplyButton.setEnabled( mode == 'pattern' )
        self.patternEdit.setEnabled( mode == 'pattern' )
        if mode != 'pattern':
            self.patternEdit.clear()

    def _chooseDirectory(self):
        # Find the directory of the most recently opened image file
        mostRecentStackDirectory = PreferencesManager().get( 'DataSelection', 'recent stack directory' )
        if mostRecentStackDirectory is not None:
            defaultDirectory = os.path.split(mostRecentStackDirectory)[0]
        else:
            defaultDirectory = os.path.expanduser('~')

        options = QFileDialog.Options(QFileDialog.ShowDirsOnly)
        if ilastik.config.cfg.getboolean("ilastik", "debug"):
            options |= QFileDialog.DontUseNativeDialog

        # Launch the "Open File" dialog
        directory = QFileDialog.getExistingDirectory( 
                     self, "Image Stack Directory", defaultDirectory, options=options )

        # If the user didn't cancel
        if not directory.isNull():
            PreferencesManager().set('DataSelection', 'recent stack directory', str(directory))

        self.directoryEdit.setText( directory )
        directory = str(directory)
        globstring = self._getGlobString(directory)
        if globstring is not None:
            self._updateFileList( sorted(glob.glob(globstring)) )
        
            # As a convenience, also show the glob string in the pattern field
            self.patternEdit.setText( globstring )

    def _getGlobString(self, directory):
        exts = vigra.impex.listExtensions().split()
        for ext in exts:
            fullGlob = directory + '/*.' + ext
            filenames = glob.glob(fullGlob)

            if len(filenames) == 0:
                QMessageBox.warning(self, "Invalid selection", 'Cannot create stack: There were no image files in the selected directory.' )
                return None

            if len(filenames) == 1:
                QMessageBox.warning(self, "Invalid selection", 'Cannot create stack: There is only one image file in the selected directory.  If your stack is contained in a single file (e.g. a multi-page tiff or hdf5 volume), please use the "Add File" button.' )
                return None

            if len(filenames) > 0:
                # Be helpful: find the longest globstring we can
                prefix = os.path.commonprefix(filenames)
                return prefix + '*.' + ext

        # Couldn't find an image file in the directory...
        return None

    def _selectFiles(self):
        # Find the directory of the most recently opened image file
        mostRecentStackDirectory = PreferencesManager().get( 'DataSelection', 'recent stack directory' )
        if mostRecentStackDirectory is not None:
            defaultDirectory = os.path.split(mostRecentStackDirectory)[0]
        else:
            defaultDirectory = os.path.expanduser('~')

        options = QFileDialog.Options(QFileDialog.ShowDirsOnly)
        if ilastik.config.cfg.getboolean("ilastik", "debug"):
            options |= QFileDialog.DontUseNativeDialog

        # Launch the "Open File" dialog
        extensions = vigra.impex.listExtensions().split()
        filt = "Image files (" + ' '.join('*.' + x for x in extensions) + ')'
        options = QFileDialog.Options()
        if ilastik.config.cfg.getboolean("ilastik", "debug"):
            options |=  QFileDialog.DontUseNativeDialog
        fileNames = QFileDialog.getOpenFileNames( 
                     self, "Select Images for Stack", defaultDirectory, filt, options=options )
        fileNames = map(str, fileNames)

        if len(fileNames) == 0:
            return

        if len(fileNames) == 1:
            QMessageBox.warning(self, "Invalid selection", 'Cannot create stack: There is only one image file in the selected directory.  If your stack is contained in a single file (e.g. a multi-page tiff or hdf5 volume), please use the "Add File" button.' )
            return

        directory = os.path.split(fileNames[0])[0]        
        PreferencesManager().set('DataSelection', 'recent stack directory', directory)

        self._updateFileList( fileNames )

    def _applyPattern(self):
        globstring = str( self.patternEdit.text() )
        self._updateFileList( sorted(glob.glob(globstring)) )

    def _updateFileList(self, files):
        self.selectedFiles = files
        
        self.fileListWidget.clear()
        
        for f in self.selectedFiles:
            self.fileListWidget.addItem( f )

    def eventFilter(self, watched, event):
        if watched == self.patternEdit:
            return self._filterPatternEditEvent(event)
        return False

    def _filterPatternEditEvent(self, event):
        # If the user presses "enter" while editing the pattern, auto-click "Apply".
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Enter:
            self.patternApplyButton.click()
            return True
        return False






















