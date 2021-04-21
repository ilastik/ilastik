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
from typing import Optional, List, Callable, Iterable
import enum
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QLabel,
    QMessageBox,
    QGridLayout,
    QButtonGroup,
    QRadioButton,
    QPushButton,
    QLineEdit,
    QListWidget,
    QWidget,
)

from volumina.utility import preferences

import ilastik.config
from ilastik.widgets.hdf5SubvolumeSelectionDialog import SubvolumeSelectionDlg
from ilastik.utility.data_url import ArchiveDataPath, DataPath, Dataset

# pyright: strict


def _critical(message: str, parent: Optional[QWidget] = None) -> None:
    QMessageBox(
        QMessageBox.Critical, "File Selection Error", message, buttons=QMessageBox.Ok, parent=parent, flags=Qt.Window
    ).exec_()


def create_dataset(
    raw_file_paths: List[str], parent: Optional[QWidget] = None, internal_path_hints: Iterable[PurePosixPath] = ()
) -> Optional[Dataset]:
    if not raw_file_paths:
        return _critical(f"No selected paths", parent)

    def clean_path(raw_path: str) -> str:
        path = Path(raw_path)
        if path.name.lower() == "attributes.json" and any(p.suffix.lower() == ".n5" for p in path.parents):
            return path.parent.as_posix()
        return path.as_posix()

    raw_file_paths = [clean_path(p) for p in raw_file_paths]

    archive_paths = [Path(path) for path in raw_file_paths if ArchiveDataPath.is_archive_path(path)]
    internal_path = PurePosixPath("")
    if archive_paths:
        common_internal_paths = ArchiveDataPath.common_internal_paths(archive_paths)
        auto_internal_paths = set(internal_path_hints).intersection(common_internal_paths)
        if len(common_internal_paths) == 0:
            return _critical(
                "Selected files have no common internal path:\n" + "\n".join(str(p) for p in archive_paths), parent
            )
        if len(common_internal_paths) == 1:
            internal_path = common_internal_paths[0]
        elif len(auto_internal_paths) == 1:
            internal_path = auto_internal_paths.pop()
        else:
            dlg = SubvolumeSelectionDlg([str(p) for p in common_internal_paths], parent)
            if dlg.exec_() == QDialog.Rejected:
                return None
            selected_index = dlg.combo.currentIndex()
            internal_path = common_internal_paths[selected_index]

    all_data_paths = [
        ArchiveDataPath.from_paths(Path(path), internal_path)
        if ArchiveDataPath.is_archive_path(path)
        else DataPath.from_string(path)
        for path in raw_file_paths
    ]
    return Dataset(all_data_paths)


def select_files(*, single_file_mode: bool, parent: Optional[QWidget] = None) -> Optional[List[str]]:
    mostRecentStackDirectory = preferences.get("DataSelection", "recent stack directory")
    if mostRecentStackDirectory is not None:
        defaultDirectory = os.path.split(mostRecentStackDirectory)[0]
    else:
        defaultDirectory = os.path.expanduser("~")

    options = QFileDialog.Options(QFileDialog.ShowDirsOnly)
    if ilastik.config.cfg.getboolean("ilastik", "debug"):
        options |= QFileDialog.DontUseNativeDialog

    suffixes = DataPath.suffixes() + ["json"]
    filt = "Image files (" + " ".join("*." + s for s in suffixes) + ")"
    options = QFileDialog.Options()
    if ilastik.config.cfg.getboolean("ilastik", "debug"):
        options |= QFileDialog.DontUseNativeDialog
    if single_file_mode:
        file_name, _ = QFileDialog.getOpenFileName(parent, "Select Image", defaultDirectory, filt, options=options)
        file_names = [file_name]
    else:
        file_names, _ = QFileDialog.getOpenFileNames(parent, "Select Images", defaultDirectory, filt, options=options)
    return file_names or None


def select_single_file_datasets(
    parent: Optional[QWidget] = None, internal_path_hints: Iterable[PurePosixPath] = (), single_file_mode: bool = False
) -> Optional[List[Dataset]]:
    raw_paths = select_files(parent=parent, single_file_mode=single_file_mode)
    if not raw_paths:
        return None
    out: List[Dataset] = []
    for raw_path in raw_paths:
        dataset = create_dataset([raw_path], parent=parent, internal_path_hints=internal_path_hints)
        if dataset is None:
            return None
        out.append(dataset)
    return out


class DatasetSelectionMode(enum.Enum):
    MULTILANE = "Multilane"
    STACK = "Stack"


class DatasetSelectionWidget(QDialog):
    def __init__(
        self,
        selection_mode: DatasetSelectionMode = DatasetSelectionMode.STACK,
        show_selection_mode_controls: bool = False,
        stacking_axis: str = "t",
    ):
        super().__init__()
        self.selected_datasets: Optional[List[Dataset]] = None
        self.stacking_axis: str = stacking_axis

        layout = QGridLayout()
        self.setLayout(layout)

        self.selection_mode_radio_group = QButtonGroup()

        def add_radio_button(label: str, line_index: int, click_callback: Callable[[], None]) -> QRadioButton:
            radio = QRadioButton(label)
            self.selection_mode_radio_group.addButton(radio)
            layout.addWidget(radio, line_index, 0)
            radio.clicked.connect(click_callback)
            return radio

        self.selection_mode_gui_label = QLabel("Selection Mode:")
        self.selection_mode_gui_label.setVisible(show_selection_mode_controls)
        layout.addWidget(self.selection_mode_gui_label, 0, 0)
        self.selection_mode_selector = QComboBox(self)
        self.selection_mode_selector.setVisible(show_selection_mode_controls)
        layout.addWidget(self.selection_mode_selector, 0, 1)
        for index, mode in enumerate(DatasetSelectionMode):
            self.selection_mode_selector.addItem(mode.value, mode)
            if mode == selection_mode:
                self.selection_mode_selector.setCurrentIndex(index)
        self.selection_mode_selector.currentTextChanged.connect(lambda _: self.update_selection_mode())

        self.filesRadioButton = add_radio_button("Select Files", 1, self.activate_files_widgets)
        self.filesChooseButton = QPushButton("Choose...")
        self.filesChooseButton.clicked.connect(self._selectFiles)
        layout.addWidget(self.filesChooseButton, 1, 1)

        self.directoryRadioButton = add_radio_button("Whole Directory", 2, self.activate_whole_directory_widgets)
        self.directoryChooseButton = QPushButton("Choose...")
        self.directoryChooseButton.clicked.connect(self._chooseDirectory)
        layout.addWidget(self.directoryChooseButton, 2, 1)
        self.directoryEdit = QLineEdit()
        self.directoryEdit.setReadOnly(True)
        layout.addWidget(self.directoryEdit, 2, 2)

        self.patternRadioButton = add_radio_button("Specify Pattern", 3, self.activate_pattern_widgets)
        self.patternEdit = QLineEdit()
        self.patternEdit.returnPressed.connect(self._applyPattern)
        layout.addWidget(self.patternEdit, 3, 1, 1, 2)

        self.patternSeparatorLabel = QLabel("Separator:")
        layout.addWidget(self.patternSeparatorLabel, 4, 1)
        self.patternSeparatorEdit = QLineEdit(os.pathsep)
        self.patternSeparatorEdit.editingFinished.connect(
            lambda: self.patternSeparatorEdit.setText(self.patternSeparatorEdit.text().strip() or os.pathsep)
        )
        layout.addWidget(self.patternSeparatorEdit, 4, 2)

        self.patternApplyButton = QPushButton("Apply")
        self.patternApplyButton.clicked.connect(self._applyPattern)
        layout.addWidget(self.patternApplyButton, 5, 1)

        self.stacking_axis_gui_label = QLabel("Stacking Axis:")
        layout.addWidget(self.stacking_axis_gui_label, 6, 0)
        self.stacking_axis_selector = QComboBox(self)
        layout.addWidget(self.stacking_axis_selector, 6, 1)
        self.stacking_axis_selector.addItem("t", "t")
        self.stacking_axis_selector.addItem("z", "z")
        self.stacking_axis_selector.addItem("c", "c")
        self.stacking_axis_selector.currentTextChanged.connect(lambda _: self.update_stacking_axis())
        self.stacking_axis_selector.setCurrentText(stacking_axis)

        layout.addWidget(QLabel("Selections:"), 7, 0)

        self.fileListWidget = QListWidget()
        layout.addWidget(self.fileListWidget, 8, 0, 1, 3)

        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.reject)
        layout.addWidget(self.cancelButton, 9, 1)

        self.okButton = QPushButton("Ok")
        self.okButton.clicked.connect(self.accept)
        layout.addWidget(self.okButton, 9, 2)
        self.okButton.setEnabled(False)

        self.filesRadioButton.click()
        self.update_selection_mode()
        self.update_stacking_axis()

    @property
    def selection_mode(self) -> DatasetSelectionMode:
        return self.selection_mode_selector.currentData()

    def update_selection_mode(self):
        self.stacking_axis_gui_label.setVisible(self.selection_mode == DatasetSelectionMode.STACK)
        self.stacking_axis_selector.setVisible(self.selection_mode == DatasetSelectionMode.STACK)
        self.setWindowTitle(f"Select Files: {self.selection_mode.value}")

    def update_stacking_axis(self):
        self.stacking_axis = self.stacking_axis_selector.currentText().lower()

    def deactivate_all_selection_widgets(self):
        self.filesChooseButton.setEnabled(False)
        self.directoryChooseButton.setEnabled(False)
        self.directoryEdit.setEnabled(False)
        self.patternApplyButton.setEnabled(False)
        self.patternEdit.setEnabled(False)
        self.patternSeparatorLabel.setEnabled(False)
        self.patternSeparatorEdit.setEnabled(False)

    def activate_files_widgets(self):
        self.deactivate_all_selection_widgets()
        self.filesChooseButton.setEnabled(True)

    def activate_whole_directory_widgets(self):
        self.deactivate_all_selection_widgets()
        self.directoryChooseButton.setEnabled(True)
        self.directoryEdit.setEnabled(True)

    def activate_pattern_widgets(self):
        self.deactivate_all_selection_widgets()
        self.patternEdit.setEnabled(True)
        self.patternSeparatorLabel.setEnabled(True)
        self.patternSeparatorEdit.setEnabled(True)
        self.patternApplyButton.setEnabled(True)

    def create_datasets(self, raw_file_paths: List[str]) -> Optional[List[Dataset]]:
        if self.selection_mode == DatasetSelectionMode.MULTILANE:
            path_groups = [[raw_file_name] for raw_file_name in raw_file_paths]
        else:
            path_groups = [raw_file_paths]
        datasets: List[Dataset] = []
        for path_group in path_groups:
            dataset = create_dataset(parent=self, raw_file_paths=path_group)
            if dataset is None:
                return None
            datasets.append(dataset)
        return datasets

    def _selectFiles(self):
        file_names = select_files(parent=self, single_file_mode=False)
        if not file_names:
            return
        datasets = self.create_datasets(file_names)
        self.validate_and_select_datasets(datasets)

    def _chooseDirectory(self):
        mostRecentStackDirectory = preferences.get("DataSelection", "recent stack directory")
        if mostRecentStackDirectory is not None:
            defaultDirectory = os.path.split(mostRecentStackDirectory)[0]
        else:
            defaultDirectory = os.path.expanduser("~")

        options = QFileDialog.Options(QFileDialog.ShowDirsOnly)
        if ilastik.config.cfg.getboolean("ilastik", "debug"):
            options |= QFileDialog.DontUseNativeDialog

        directory = QFileDialog.getExistingDirectory(self, "Image Stack Directory", defaultDirectory, options=options)
        if not directory:
            return

        preferences.set("DataSelection", "recent stack directory", directory)
        self.directoryEdit.setText(directory)
        datasets = self.create_datasets(sorted(str(p.absolute()) for p in Path(directory).iterdir()))
        self.validate_and_select_datasets(datasets)

    def _applyPattern(self):
        pattern = self.patternEdit.text().strip()
        if not pattern:
            return
        try:
            data_paths = Dataset.split(pattern, deglob=True, separator=self.patternSeparatorEdit.text()).data_paths
            if self.selection_mode == DatasetSelectionMode.MULTILANE:
                datasets = [Dataset([dp]) for dp in data_paths]
            else:
                datasets = [Dataset(data_paths)]
        except Exception as e:
            return _critical(str(e), parent=self)
        self.validate_and_select_datasets(datasets)

    def validate_and_select_datasets(self, datasets: Optional[List[Dataset]]):
        self.fileListWidget.clear()
        self.okButton.setEnabled(False)
        if not datasets:
            return
        for dataset in datasets:
            if len(set(dataset.suffixes())) != 1:
                return _critical(
                    "Selected files have multiple different extensions:\n" + "\n".join(dataset.to_strings()),
                    parent=self,
                )
        for dataset in datasets:
            self.fileListWidget.addItem(f"New Dataset:")
            self.fileListWidget.addItems(dataset.to_strings())
        self.selected_datasets = datasets
        self.okButton.setEnabled(True)
