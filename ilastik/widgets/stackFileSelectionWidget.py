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
from PyQt4.QtGui import (
    QDialogButtonBox, QComboBox, QDialog, QFileDialog, QLabel, QMessageBox, QVBoxLayout
)

import vigra

from volumina.utility import PreferencesManager

import ilastik.config
from volumina.utility import encode_from_qstring, decode_to_qstring

from lazyflow.operators.ioOperators import (
    OpStackLoader, OpStreamingHdf5SequenceReaderM,
    OpStreamingHdf5SequenceReaderS
)
from lazyflow.utility import lsHdf5, PathComponents
import h5py


class H5VolumeSelectionDlg(QDialog):
    """
    A window to ask the user to choose between multiple HDF5 datasets in a single file.
    """
    def __init__(self, datasetNames, parent):
        super(H5VolumeSelectionDlg, self).__init__(parent)
        label = QLabel("Your HDF5 File contains multiple image volumes.\n"
                       "Please select the one you would like to open.")

        self.combo = QComboBox()
        for name in datasetNames:
            self.combo.addItem(name)

        buttonbox = QDialogButtonBox(Qt.Horizontal, parent=self)
        buttonbox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.combo)
        layout.addWidget(buttonbox)

        self.setLayout(layout)


class StackFileSelectionWidget(QDialog):

    class DetermineStackError(Exception):
        """Class related to errors in determining the stack of files"""
        def __init__(self, message):
            super(StackFileSelectionWidget.DetermineStackError, self).__init__(message)

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

        self.stackAcrossTButton.setChecked(True)

    def accept(self):
        self.patternEdit.removeEventFilter(self)
        super( StackFileSelectionWidget, self ).accept()

    def reject(self):
        self.patternEdit.removeEventFilter(self)
        super( StackFileSelectionWidget, self ).reject()

    @property
    def sequence_axis(self):
        if self.stackAcrossTButton.isChecked():
            return 't'
        return 'z'

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
        try:
            globstring = self._getGlobString(directory)
        except StackFileSelectionWidget.DetermineStackError, e:
            QMessageBox.warning(self, "Invalid selection", str(e))
        if globstring:
            self.patternEdit.setText(decode_to_qstring(globstring))
            self._applyPattern()

    def _getGlobString(self, directory):
        all_filenames = []
        globstrings = []

        msg = ''
        h5exts = [x.lstrip('.') for x in OpStreamingHdf5SequenceReaderM.H5EXTS]
        exts = vigra.impex.listExtensions().split()
        exts.extend(h5exts)
        for ext in exts:
            fullGlob = directory + '/*.' + ext
            globFileNames = glob.glob(fullGlob)
            new_filenames = [k.replace('\\', '/') for k in globFileNames]

            if len(new_filenames) > 0:
                # Be helpful: find the longest globstring we can
                prefix = os.path.commonprefix(new_filenames)
                globstring = prefix + '*.' + ext
                # Special handling for h5-files: Try to add internal path
                if ext in h5exts:
                    # be even more helpful and try to find a common internal path
                    internal_paths = self._findCommonInternal(new_filenames)
                    if len(internal_paths) == 0:
                        msg += 'Could not find a unique common internal path in'
                        msg += directory + '\n'
                        raise StackFileSelectionWidget.DetermineStackError(msg)
                    elif len(internal_paths) == 1:
                        new_filenames = ['{}/{}'.format(fn, internal_paths[0])
                                         for fn in new_filenames]
                        globstring = '{}/{}'.format(globstring, internal_paths[0])
                    elif len(internal_paths) > 1:
                        # Ask the user which dataset to choose
                        dlg = H5VolumeSelectionDlg(internal_paths, self)
                        if dlg.exec_() == QDialog.Accepted:
                            selected_index = dlg.combo.currentIndex()
                            selected_dataset = str(internal_paths[selected_index])
                            new_filenames = ['{}/{}'.format(fn, selected_dataset)
                                             for fn in new_filenames]
                            globstring = '{}/{}'.format(globstring, selected_dataset)
                        else:
                            msg = 'No valid internal path selected.'
                            raise StackFileSelectionWidget.DetermineStackError(msg)

                globstrings.append(globstring)
                all_filenames += new_filenames

        if len(all_filenames) == 0:
            msg += 'Cannot create stack: There were no image files in the selected directory:\n'
            msg += directory
            raise StackFileSelectionWidget.DetermineStackError(msg)

        if len(all_filenames) == 1:
            msg += 'Cannot create stack: There is only one image file in the selected directory:\n'
            msg += directory + '\n'
            msg += 'If your stack is contained in a single file (e.g. a multi-page tiff or '
            msg += 'hdf5 volume), please use the "Add File" button.'
            raise StackFileSelectionWidget.DetermineStackError(msg)

        # Combine into one string, delimited with os.path.sep
        return os.path.pathsep.join(globstrings)

    @staticmethod
    def _findCommonInternal(h5Files):
        """Tries to find common internal path (containing data)

        Method is used, when a directory is selected and the internal path is,
        thus, unclear.

        Args:
            h5_files (list of strings): h5 files to be globbed internally

        Returns:
            list of internal paths
        """
        h5 = h5py.File(h5Files[0], mode='r')
        internal_paths = set([x['name'] for x in lsHdf5(h5, minShape=2)])
        h5.close()
        for h5File in h5Files[1::]:
            h5 = h5py.File(h5File, 'r')
            # get all files with with at least 2D shape
            tmp = set([x['name'] for x in lsHdf5(h5, minShape=2)])
            internal_paths = internal_paths.intersection(tmp)

        return list(internal_paths)


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

        h5exts = [x.lstrip('.') for x in OpStreamingHdf5SequenceReaderM.H5EXTS]
        # Launch the "Open File" dialog
        extensions = vigra.impex.listExtensions().split()
        extensions.extend(h5exts)
        filt = "Image files (" + ' '.join('*.' + x for x in extensions) + ')'
        options = QFileDialog.Options()
        if ilastik.config.cfg.getboolean("ilastik", "debug"):
            options |=  QFileDialog.DontUseNativeDialog
        fileNames = QFileDialog.getOpenFileNames( 
                     self, "Select Images for Stack", defaultDirectory, filt, options=options )
        
        fileNames = map(encode_from_qstring, fileNames)

        msg = ''
        if len(fileNames) == 0:
            return

        if len(fileNames) == 1:
            msg += 'Cannot create stack: You only chose a single file.  '
            msg += 'If your stack is contained in a single file (e.g. a multi-page tiff or hdf5 volume),'
            msg += ' please use the "Add File" button.'
            QMessageBox.warning(self, "Invalid selection", msg )
            return None

        pathComponents = PathComponents(fileNames[0])
        directory = pathComponents.externalPath
        PreferencesManager().set('DataSelection', 'recent stack directory', directory)

        if pathComponents.extension in OpStreamingHdf5SequenceReaderM.H5EXTS:
            # check for internal paths!
            internal_paths = self._findCommonInternal(fileNames)
            if len(internal_paths) != 1:
                msg += 'Could not find a unique common internal path in'
                msg += directory + '\n'
                QMessageBox.warning(self, "Invalid selection", msg)
                return None
            else:
                fileNames = ['{}/{}'.format(fn, internal_paths[0]) for fn in fileNames]

        self._updateFileList( fileNames )

    def _applyPattern(self):
        globStrings = encode_from_qstring(self.patternEdit.text())
        H5EXTS = OpStreamingHdf5SequenceReaderM.H5EXTS
        filenames = []
        # see if some glob strings include HDF5 files
        globStrings = globStrings.split(os.path.pathsep)
        pcs = [PathComponents(x) for x in globStrings]
        ish5 = [x.extension in H5EXTS for x in pcs]

        h5GlobStrings = os.path.pathsep.join([x for x, y in zip(globStrings, ish5) if y is True])
        globStrings = os.path.pathsep.join([x for x, y in zip(globStrings, ish5) if y is False])

        filenames.extend(OpStackLoader.expandGlobStrings(globStrings))

        try:
            OpStreamingHdf5SequenceReaderS.checkGlobString(h5GlobStrings)
            # OK, if nothing raised there is a single h5 file in h5GlobStrings:
            pathComponents = PathComponents(h5GlobStrings.split(os.path.pathsep)[0])
            h5file = h5py.File(pathComponents.externalPath, mode='r')
            filenames.extend(
                "{}/{}".format(external, internal)
                for external, internal
                in zip(*OpStreamingHdf5SequenceReaderS.expandGlobStrings(h5file, h5GlobStrings))
            )
        except (
                OpStreamingHdf5SequenceReaderS.WrongFileTypeError,
                OpStreamingHdf5SequenceReaderS.NotTheSameFileError,
                OpStreamingHdf5SequenceReaderS.NoInternalPlaceholderError,
                OpStreamingHdf5SequenceReaderS.ExternalPlaceholderError):
            pass

        try:
            OpStreamingHdf5SequenceReaderM.checkGlobString(h5GlobStrings)
            filenames.extend(
                "{}/{}".format(external, internal)
                for external, internal
                in zip(*OpStreamingHdf5SequenceReaderM.expandGlobStrings(h5GlobStrings))
            )
        except (
                OpStreamingHdf5SequenceReaderM.WrongFileTypeError,
                OpStreamingHdf5SequenceReaderM.SameFileError,
                OpStreamingHdf5SequenceReaderM.NoExternalPlaceholderError,
                OpStreamingHdf5SequenceReaderM.InternalPlaceholderError):
            pass

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


