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
import os
import glob
from functools import partial

from PyQt4 import uic
from PyQt4.QtCore import Qt, QEvent
from PyQt4.QtGui import QDialog, QFileDialog, QMessageBox

import vigra

from volumina.utility import PreferencesManager

import ilastik.config
from volumina.utility import encode_from_qstring, decode_to_qstring

from lazyflow.operators.ioOperators import OpStackLoader

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

        self.selectFilesRadioButton.clicked.connect( partial( self._configureGui, 'files' ) )
        self.directoryRadioButton.clicked.connect( partial( self._configureGui, 'directory' ) )
        self.patternRadioButton.clicked.connect( partial( self._configureGui, 'pattern' ) )

        self.selectFilesChooseButton.clicked.connect( self._selectFiles )
        self.directoryChooseButton.clicked.connect( self._chooseDirectory )
        self.patternApplyButton.clicked.connect( self._applyPattern )
        self.patternEdit.installEventFilter( self )
    
        # Default to "select files" option, since it's most generic
        self.selectFilesRadioButton.setChecked(True)
        self._configureGui("files")

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

        if directory.isNull():
            # User cancelled
            return

        directory = encode_from_qstring( directory )
        PreferencesManager().set('DataSelection', 'recent stack directory', directory)

        self.directoryEdit.setText( decode_to_qstring(directory) )
        globstring = self._getGlobString(directory)
        if globstring:
            filenames = OpStackLoader.expandGlobStrings(globstring)
            self._updateFileList( sorted(filenames) )
            # As a convenience, also show the glob string in the pattern field
            self.patternEdit.setText( decode_to_qstring(globstring) )

    def _getGlobString(self, directory):
        all_filenames = []
        globstrings = []

        exts = vigra.impex.listExtensions().split()
        for ext in exts:
            fullGlob = directory + '/*.' + ext
            globFileNames = glob.glob(fullGlob)
            new_filenames = [k.replace('\\', '/') for k in globFileNames]

            if len(new_filenames) > 0:
                # Be helpful: find the longest globstring we can
                prefix = os.path.commonprefix(new_filenames)
                globstring = prefix + '*.' + ext
                globstrings.append(globstring)
                all_filenames += new_filenames

        if len(all_filenames) == 0:
            msg = 'Cannot create stack: There were no image files in the selected directory:\n'
            msg += directory
            QMessageBox.warning(self, "Invalid selection", msg )
            return None

        if len(all_filenames) == 1:
            msg = 'Cannot create stack: There is only one image file in the selected directory:\n'
            msg += directory + '\n'
            msg += 'If your stack is contained in a single file (e.g. a multi-page tiff or hdf5 volume),'
            msg += ' please use the "Add File" button.'
            QMessageBox.warning(self, "Invalid selection", msg )
            return None

        # Combine into one string, delimited with os.path.sep
        return os.path.pathsep.join(globstrings)

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
        
        fileNames = map(encode_from_qstring, fileNames)

        if len(fileNames) == 0:
            return

        if len(fileNames) == 1:
            msg = 'Cannot create stack: You only chose a single file.  '
            msg += 'If your stack is contained in a single file (e.g. a multi-page tiff or hdf5 volume),'
            msg += ' please use the "Add File" button.'
            QMessageBox.warning(self, "Invalid selection", msg )
            return None

        directory = os.path.split(fileNames[0])[0]
        PreferencesManager().set('DataSelection', 'recent stack directory', directory)

        self._updateFileList( fileNames )

    def _applyPattern(self):
        globStrings = encode_from_qstring(self.patternEdit.text())
        filenames = OpStackLoader.expandGlobStrings(globStrings)
        self._updateFileList(filenames)

    def _updateFileList(self, files):
        self.selectedFiles = files
        
        self.fileListWidget.clear()
        
        for f in self.selectedFiles:
            self.fileListWidget.addItem(decode_to_qstring(f))

    def eventFilter(self, watched, event):
        if watched == self.patternEdit:
            return self._filterPatternEditEvent(event)
        return False

    def _filterPatternEditEvent(self, event):
        # If the user presses "enter" while editing the pattern, auto-click "Apply".
        if  event.type() == QEvent.KeyPress and\
          ( event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return):
            self.patternApplyButton.click()
            return True
        return False

if __name__ == "__main__":
    from PyQt4.QtGui import QApplication
    
    app = QApplication([])
    w = StackFileSelectionWidget(None)
    w.show()
    app.exec_()


