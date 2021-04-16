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
# 		   http://ilastik.org/license.html
###############################################################################
import os
from pathlib import Path, PurePosixPath
import sys
import glob
from functools import partial
from typing import Optional, List, Sequence

from PyQt5 import uic
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QDialogButtonBox, QComboBox, QDialog, QFileDialog, QLabel, QMessageBox, QVBoxLayout

import vigra

from volumina.utility import preferences

import ilastik.config
from ilastik.widgets.hdf5SubvolumeSelectionDialog import H5N5StackingDlg, SubvolumeSelectionDlg

from lazyflow.operators.ioOperators import (
    OpStackLoader,
    OpStreamingH5N5Reader,
    OpStreamingH5N5SequenceReaderM,
    OpStreamingH5N5SequenceReaderS,
    OpInputDataReader,
)
from lazyflow.utility import lsH5N5, PathComponents
from ilastik.utility.data_url import ArchiveDataPath, DataPath, SimpleDataPath, StackPath


class StackFileSelectionWidget(QDialog):
    def __init__(self):
        super(StackFileSelectionWidget, self).__init__()

        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        uiFilePath = os.path.join(localDir, "stackFileSelectionWidget.ui")
        uic.loadUi(uiFilePath, self)

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        self.selectFilesRadioButton.clicked.connect(partial(self._configureGui, "files"))
        self.directoryRadioButton.clicked.connect(partial(self._configureGui, "directory"))
        self.patternRadioButton.clicked.connect(partial(self._configureGui, "pattern"))

        self.selectFilesChooseButton.clicked.connect(self._selectFiles)
        self.directoryChooseButton.clicked.connect(self._chooseDirectory)
        self.patternApplyButton.clicked.connect(self._applyPattern)
        self.patternEdit.returnPressed.connect(self._applyPattern)

        # Default to "select files" option, since it's most generic
        self.selectFilesRadioButton.setChecked(True)
        self._configureGui("files")

        self.stackAcrossTButton.setChecked(True)
        self.selectedStack: Optional[StackPath] = None
        self.okButton.setEnabled(False)

    @property
    def sequence_axis(self):
        if self.stackAcrossTButton.isChecked():
            return "t"
        elif self.stackAcrossZButton.isChecked():
            return "z"
        return "c"

    def _configureGui(self, mode):
        """
        Configure the gui to select files via one of our three selection modes.
        """
        self.directoryChooseButton.setEnabled(mode == "directory")
        self.directoryEdit.setEnabled(mode == "directory")
        self.directoryEdit.clear()

        self.selectFilesChooseButton.setEnabled(mode == "files")

        self.patternApplyButton.setEnabled(mode == "pattern")
        self.patternEdit.setEnabled(mode == "pattern")
        if mode != "pattern":
            self.patternEdit.clear()

    def _chooseDirectory(self):
        # Find the directory of the most recently opened image file
        mostRecentStackDirectory = preferences.get("DataSelection", "recent stack directory")
        if mostRecentStackDirectory is not None:
            defaultDirectory = os.path.split(mostRecentStackDirectory)[0]
        else:
            defaultDirectory = os.path.expanduser("~")

        options = QFileDialog.Options(QFileDialog.ShowDirsOnly)
        if ilastik.config.cfg.getboolean("ilastik", "debug"):
            options |= QFileDialog.DontUseNativeDialog

        # Launch the "Open File" dialog
        directory = QFileDialog.getExistingDirectory(self, "Image Stack Directory", defaultDirectory, options=options)

        if not directory:
            # User cancelled
            return

        preferences.set("DataSelection", "recent stack directory", directory)
        self.directoryEdit.setText(directory)
        stack = self.create_stack([str(p.absolute()) for p in Path(directory).iterdir()])
        self.select_stack(stack)

    def _selectFiles(self):
        # Find the directory of the most recently opened image file
        mostRecentStackDirectory = preferences.get("DataSelection", "recent stack directory")
        if mostRecentStackDirectory is not None:
            defaultDirectory = os.path.split(mostRecentStackDirectory)[0]
        else:
            defaultDirectory = os.path.expanduser("~")

        options = QFileDialog.Options(QFileDialog.ShowDirsOnly)
        if ilastik.config.cfg.getboolean("ilastik", "debug"):
            options |= QFileDialog.DontUseNativeDialog

        # Launch the "Open File" dialog
        filt = "Image files (" + " ".join("*." + x for x in DataPath.suffixes()) + ")"
        options = QFileDialog.Options()
        if ilastik.config.cfg.getboolean("ilastik", "debug"):
            options |= QFileDialog.DontUseNativeDialog
        if self.single_file_mode:
            fileName, _filter = QFileDialog.getOpenFileName(
                self, "Select Image", defaultDirectory, filt, options=options
            )
            fileNames = [fileName]
        else:
            fileNames, _filter = QFileDialog.getOpenFileNames(
                self, "Select Images for Stack", defaultDirectory, filt, options=options
            )

        # For the n5 extension, the attributes.json file has to be selected in the file dialog.
        # However we need just the n5 directory-file.
        for i in range(len(fileNames)):
            if os.path.join("n5", "attributes.json") in fileNames[i]:
                fileNames[i] = fileNames[i].replace(os.path.sep + "attributes.json", "")
        stack = self.create_stack(fileNames)
        self.select_stack(stack)

    def _applyPattern(self):
        pattern = self.patternEdit.text().strip()
        if not pattern:
            return
        try:
            stack = StackPath.split(pattern, deglob=True)
        except Exception as e:
            return self.warn(str(e))
        self.select_stack(stack)

    def create_stack(self, raw_file_names: List[str]) -> Optional[StackPath]:
        if not raw_file_names:
            return self.warn(f"No selected paths")
        simple_data_paths = [
            DataPath.from_string(path) for path in sorted(raw_file_names) if not ArchiveDataPath.is_archive_path(path)
        ]

        raw_archive_paths = [Path(path) for path in raw_file_names if ArchiveDataPath.is_archive_path(path)]
        archive_data_paths: List[ArchiveDataPath] = []
        if raw_archive_paths:
            common_internal_paths = ArchiveDataPath.common_internal_paths(raw_archive_paths)
            if len(common_internal_paths) == 0:
                return self.warn(
                    "Selected files have no common internal path:\n" + "\n".join(str(p) for p in raw_archive_paths)
                )
            if len(common_internal_paths) == 1:
                internal_path = common_internal_paths[0]
            else:
                # Ask the user which dataset to choose
                dlg = SubvolumeSelectionDlg([str(p) for p in common_internal_paths], self)
                if dlg.exec_() == QDialog.Rejected:
                    return
                selected_index = dlg.combo.currentIndex()
                internal_path = common_internal_paths[selected_index]
            archive_data_paths = [
                ArchiveDataPath.from_paths(external_path, internal_path) for external_path in raw_archive_paths
            ]

        all_data_paths: Sequence[DataPath] = tuple(simple_data_paths) + tuple(archive_data_paths)
        return StackPath(all_data_paths)

    def warn(self, message: str) -> None:
        QMessageBox.warning(self, "Stack Creation Error", message)

    def select_stack(self, stack: Optional[StackPath]):
        self.fileListWidget.clear()
        self.okButton.setEnabled(False)
        if stack is None:
            return
        for data_path in stack.data_paths:
            self.fileListWidget.addItem(str(data_path))
        if len(set(stack.suffixes())) != 1:
            return self.warn("Selected files have multiple different extensions")

        self.selectedStack = stack
        self.okButton.setEnabled(True)
