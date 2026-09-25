###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2026, the ilastik developers
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
import logging
from enum import StrEnum
from pathlib import Path
from typing import Union

import h5py
import pydantic
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from ilastik.experimental.parser.types.applets import ProjectBase
from ilastik.utility import log_exception

logger = logging.getLogger(__name__)


class ImportProjectDialog(QDialog):

    class Messages(StrEnum):
        DESTINATION_PLACEHOLDER = "Click Browse button to select new project file."
        IMPORTING_TO = "Importing from workflow type {workflow_name}."
        INVALID_DEST_NAME = "File name must have the `.ilp` suffix."
        INVALID_SRC_ILP = "Not a valid ilastik project (`.ilp`) file."
        SOURCE_PLACEHOLDER = "Click Browse button select an existing ilastik project to import from."
        SRC_DEST_EQ = "Cannot import into the same project file."

    def __init__(self, workflow_list: list[str], base_path: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import project file...")
        self.setMinimumWidth(800)
        self.setModal(True)

        self._base_path = base_path

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        src_layout = QHBoxLayout()
        self.src_edit = QLineEdit()
        self.src_edit.setPlaceholderText(self.Messages.SOURCE_PLACEHOLDER)
        self.src_edit.setReadOnly(True)
        self.src_button = QPushButton("Browse...")
        src_layout.addWidget(self.src_edit)
        src_layout.addWidget(self.src_button)
        src_layout.setContentsMargins(0, 0, 0, 0)
        form.addRow(QLabel("Import from project:"), src_layout)
        self.src_hint_label = QLabel()
        form.addRow(QLabel(), self.src_hint_label)

        form.addRow(QLabel())

        new_layout = QHBoxLayout()
        self.dst_edit = QLineEdit()
        self.dst_edit.setPlaceholderText(self.Messages.DESTINATION_PLACEHOLDER)
        self.dst_edit.setReadOnly(True)
        self.dst_button = QPushButton("Browse...")
        new_layout.addWidget(self.dst_edit)
        new_layout.addWidget(self.dst_button)
        new_layout.setStretch(2, 0)
        new_layout.setContentsMargins(0, 0, 0, 0)
        form.addRow(QLabel("New file:"), new_layout)
        self.dst_hint_label = QLabel()
        form.addRow(QLabel(), self.dst_hint_label)

        form.addRow(QLabel())

        combo_layout = QHBoxLayout()
        self.combo = QComboBox()
        self.combo.addItems(["-- Select workflow type --"] + workflow_list)
        self.combo.setPlaceholderText("Workflow type")
        combo_layout.addWidget(self.combo)
        combo_layout.setContentsMargins(0, 0, 0, 0)
        form.addRow(QLabel("Workflow type:"), combo_layout)

        form.setVerticalSpacing(0)

        layout.addLayout(form)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addStretch()
        layout.addWidget(self.button_box)

        self.ok_button = self.button_box.button(QDialogButtonBox.Ok)
        self.setLayout(layout)

        self.src_button.clicked.connect(self.choose_src)
        self.dst_button.clicked.connect(self.choose_dst)

        self.src_edit.textChanged.connect(self.validate)
        self.dst_edit.textChanged.connect(self.validate)
        self.combo.currentIndexChanged.connect(self.validate)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.validate()

    def choose_src(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select existing file", directory=str(self._base_path), filter="*.ilp"
        )
        if path:
            self.src_edit.setText(path)

    def choose_dst(self):
        src: Union[Path, None] = None
        if self.src_edit.text() != "":
            src = Path(self.src_edit.text())

        default_name = src.parent / f"{src.stem}_imported.ilp" if src else self._base_path / "imported.ilp"
        path, _ = QFileDialog.getSaveFileName(self, "Select new file", directory=str(default_name), filter="*.ilp")
        if path:
            self.dst_edit.setText(path)

    def _is_source_valid(self) -> bool:
        if self.src_edit.text() != "":
            src = Path(self.src_edit.text())
        else:
            self.dst_hint_label.setText("")
            return False

        if not src.exists() or not src.is_file() or src.suffix != ".ilp":
            self.src_hint_label.setText(self.Messages.INVALID_SRC_ILP)
            return False

        try:
            with h5py.File(src, "r") as f:
                try:
                    m = ProjectBase.model_validate(f)
                except pydantic.ValidationError as e:
                    log_exception(logger, str(e))
                    self.src_hint_label.setText(self.Messages.INVALID_SRC_ILP)
                    return False
                else:
                    self.src_hint_label.setText(self.Messages.IMPORTING_TO.format(workflow_name=m.workflow_name))
                    return True
        except OSError as e:
            log_exception(logger, str(e))
            self.src_hint_label.setText(self.Messages.INVALID_SRC_ILP)
            return False

    def _is_dest_valid(self) -> bool:
        src = Path(self.src_edit.text())
        if self.dst_edit.text() != "":
            dst = Path(self.dst_edit.text())
        else:
            self.dst_hint_label.setText("")
            return False

        if dst == src:
            self.dst_hint_label.setText(self.Messages.SRC_DEST_EQ)
            return False
        elif dst.suffix != ".ilp":
            self.dst_hint_label.setText(self.Messages.INVALID_DEST_NAME)
            return False

        self.dst_hint_label.setText("")
        return True

    def validate(self):
        valid = self._is_source_valid()
        valid &= self._is_dest_valid()

        self.combo.setEnabled(valid)

        valid &= self.combo.currentIndex() != 0
        self.ok_button.setEnabled(valid)

    def get_values(self) -> tuple[Path, Path, str]:
        return Path(self.src_edit.text()), Path(self.dst_edit.text()), self.combo.currentText()
