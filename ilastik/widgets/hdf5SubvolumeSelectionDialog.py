###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2017, the ilastik developers
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
#          http://ilastik.org/license.html
###############################################################################

from typing import List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from lazyflow.utility import globList


class SubvolumeSelectionDlg(QDialog):
    """A window to ask the user to choose between multiple HDF5 datasets in a single file.

    If multi is True, user can select multiple datasets at once.
    """

    def __init__(self, datasetNames, parent, *, multi=False):
        super().__init__(parent)
        self.multi = multi

        layout = QVBoxLayout()
        self.setLayout(layout)

        label_lines = ["<p>Your file contains multiple images.</p>"]
        if multi:
            label_lines.append("<p>Select images that you would like to open.</p>")
        else:
            label_lines.append("<p>Select image that you would like to open.</p>")
        layout.addWidget(QLabel("".join(label_lines), parent=self))

        if multi:
            self.items = QListWidget(parent=self)
            self.items.setSelectionMode(QListWidget.MultiSelection)
            self.items.insertItems(0, datasetNames)
            layout.addWidget(self.items)
        else:
            self.combo = QComboBox(parent=self)
            self.combo.addItems(datasetNames)
            layout.addWidget(self.combo)

        buttons = QDialogButtonBox(Qt.Horizontal, parent=self)
        buttons.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selectPath(self) -> Optional[str]:
        """Select and return an item text, or None if the dialog has not been accepted."""
        if self.multi:
            raise ValueError("selectedPath can be used only when multi=False")
        if self.exec_() != self.Accepted:
            return None
        return self.combo.currentText()

    def selectPaths(self) -> Optional[List[str]]:
        """Select and return item texts, or None if the dialog has not been accepted."""
        if not self.multi:
            raise ValueError("selectedPaths can be used only when multi=True")
        if self.exec_() != self.Accepted:
            return None
        return [item.text() for item in self.items.selectedItems()]


class Hdf5StackSelectionWidget(QWidget):
    def __init__(self, parent=None, list_of_paths=None, pattern=None):
        super(Hdf5StackSelectionWidget, self).__init__(parent)
        self.input_text = QLineEdit()
        if pattern is None:
            pattern = "*"
        self.input_text.setText(pattern)
        self.list_of_paths = list_of_paths
        self.selected_paths = list_of_paths

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setToolTip(
            "Images included in the stack are displayed in black.\n"
            "Images not included in the stack are shown in grey."
        )
        info_label = QLabel("Resulting images used for stacking:\n")
        self.n_label = QLabel("")

        layout = QVBoxLayout()
        layout.addWidget(self.input_text)
        layout.addWidget(info_label)
        layout.addWidget(self.info_text)
        layout.addWidget(self.n_label)
        self.setLayout(layout)

        # connect the signals
        self.input_text.textEdited.connect(self.validate_globstring)

        self.validate_globstring(pattern)

    def validate_globstring(self, globstring):
        color_inside = "{}"
        color_outside = '<font color ="#777">{}</font>'
        self.selected_paths = globList(self.list_of_paths, str(self.input_text.text()))

        with_color = []
        for path in self.list_of_paths:
            if path in self.selected_paths:
                with_color.append(color_inside.format(path))
            else:
                with_color.append(color_outside.format(path))
        self.info_text.setText("<br>".join(with_color))
        self.n_label.setText("Selected {} images".format(len(self.selected_paths)))


class H5N5StackingDlg(QDialog):
    """Dialogue for subvolume stack selection within single HDF5/N5 files"""

    def __init__(self, parent=None, list_of_paths=None):
        super(H5N5StackingDlg, self).__init__(parent)
        self.setWindowTitle("Select images for stacking")
        if list_of_paths is None:
            list_of_paths = []

        self.list_of_paths = list_of_paths

        self.radio_group = QButtonGroup(parent=self)
        label = QLabel(
            "Your HDF5/N5 File contains multiple images.\n"
            "Please specify a pattern in order to stack multiple images."
        )

        self.stack_widget = Hdf5StackSelectionWidget(parent=self, list_of_paths=list_of_paths, pattern="*")
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.stack_widget)
        layout.addWidget(self._setup_buttonbox())

        self.setLayout(layout)
        self.setMinimumSize(600, 100)

    def _setup_buttonbox(self):
        buttonbox = QDialogButtonBox(Qt.Horizontal, parent=self)
        buttonbox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)
        return buttonbox

    def get_selected_datasets(self):
        return self.stack_widget.selected_paths

    def get_globstring(self):
        return self.stack_widget.input_text.text()
