from __future__ import absolute_import
from ilastik.utility.data_url import StackPath

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
from pathlib import Path
from typing import List, Tuple, Optional
from numbers import Number
from functools import partial

import numpy
import vigra

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

from ilastik.applets.dataSelection.dataSelectionSerializer import DataSelectionSerializer
from .opDataSelection import (
    DatasetInfo,
    ProjectInternalDatasetInfo,
    FilesystemDatasetInfo,
    RelativeFilesystemDatasetInfo,
    UrlDatasetInfo,
)

import logging

logger = logging.getLogger(__name__)


def get_dtype_info(dtype):
    try:
        return numpy.iinfo(dtype)
    except ValueError:
        return numpy.finfo(dtype)


class InvalidDatasetinfoException(Exception):
    pass


class DatasetInfoEditorWidget(QDialog):
    """
    This dialog allows the user to edit the settings of one **OR MORE** datasets for a given role.
    """

    def __init__(self, parent, infos: List[DatasetInfo], serializer: DataSelectionSerializer):
        """
        :param infos: DatasetInfo infos to be edited by this widget
        :param serializer: a configured DataSelectionSerializer
        """
        super(DatasetInfoEditorWidget, self).__init__(parent)
        self.current_infos = infos
        self.fs_infos = [info for info in infos if isinstance(info, FilesystemDatasetInfo)]
        self.serializer = serializer
        self.edited_infos = []
        self.project_file = self.serializer.topLevelOperator.ProjectFile.value
        self.project_file_path = Path(self.project_file.filename)

        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        uiFilePath = os.path.join(localDir, "datasetInfoEditorWidget.ui")
        uic.loadUi(uiFilePath, self)

        self.rangeMinSpinBox.valueChanged.connect(self.validate_new_data)
        self.rangeMaxSpinBox.setMinimum(max(get_dtype_info(info.laneDtype).min for info in infos))
        self.rangeMaxSpinBox.valueChanged.connect(self.validate_new_data)
        self.rangeMaxSpinBox.setMaximum(min(get_dtype_info(info.laneDtype).max for info in infos))
        self.clearRangeButton.clicked.connect(self.clearNormalization)
        self.clearNormalization()

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        input_axiskeys = [info.axiskeys for info in infos]
        self.multi_axes_display.setEnabled(False)
        self.multi_axes_display.setText("Current: " + ", ".join(input_axiskeys))
        if all(len(keys) == len(input_axiskeys[0]) for keys in input_axiskeys):
            self.axesEdit.setMaxLength(len(input_axiskeys[0]))
            self.axesEdit.textChanged.connect(self.validate_new_data)
            different_axiskeys = set(input_axiskeys)
            if len(different_axiskeys) == 1:
                self.axesEdit.setText(different_axiskeys.pop())
        else:
            axes_uneditable_reason = "Select lanes with same number of axes to change their interpretation here"
            self.multi_axes_display.setToolTip(axes_uneditable_reason)
            self.axesEdit.setToolTip(axes_uneditable_reason)
            self.axesEdit.setEnabled(False)

        self.nicknameEdit.setText(", ".join(str(info.nickname) for info in self.current_infos))
        if len(infos) == 1:
            self.nicknameEdit.setEnabled(True)
        else:
            self.nicknameEdit.setEnabled(False)
            self.nicknameEdit.setToolTip("Edit a single lane to modify its nickname")

        self.shapeLabel.setText(", ".join(str(info.laneShape) for info in infos))
        self.dtypeLabel.setText(", ".join(info.laneDtype.__name__ for info in infos))

        self.normalizeDisplayComboBox.addItem("True", userData=True)
        self.normalizeDisplayComboBox.addItem("False", userData=False)
        self.normalizeDisplayComboBox.addItem("Default", userData=None)
        self.normalizeDisplayComboBox.currentIndexChanged.connect(self._handleNormalizeDisplayChanged)
        current_normalize_display = {info.normalizeDisplay for info in infos}
        normalize = current_normalize_display.pop() if len(current_normalize_display) == 1 else None

        dranges = {info.drange for info in infos if info.drange is not None}
        if len(dranges) == 1:
            common_drange = dranges.pop()
            self.rangeMinSpinBox.setValue(common_drange[0])
            self.rangeMaxSpinBox.setValue(common_drange[1])
        else:
            normalize = None

        selected_normalize_index = self.normalizeDisplayComboBox.findData(normalize)
        self.normalizeDisplayComboBox.setCurrentIndex(selected_normalize_index)

        archive_dataset_paths = [info.dataset for info in self.fs_infos if info.dataset.uses_archive()]
        self.internalDatasetNameComboBox.setEnabled(False)
        if not archive_dataset_paths:
            self.internalDatasetNameLabel.setVisible(False)
            self.internalDatasetNameComboBox.setVisible(False)
            self.internalDatasetNameComboBoxMessage.setVisible(False)
        else:
            common_internal_paths = StackPath.common_internal_paths(archive_dataset_paths)
            common_current_internal_paths = set(archive_dataset_paths[0].archive_internal_paths()).intersection(
                *[dsp.archive_internal_paths() for dsp in archive_dataset_paths[1:]]
            )

            for path in sorted(common_internal_paths):
                self.internalDatasetNameComboBox.addItem(str(path))
                self.internalDatasetNameComboBox.setEnabled(True)

            if len(common_current_internal_paths) == 1:
                self.internalDatasetNameComboBox.setCurrentText(str(common_current_internal_paths.pop()))
            else:
                self.internalDatasetNameComboBox.setCurrentIndex(-1)
        self.internalDatasetNameComboBox.currentTextChanged.connect(self._handle_inner_path_change)

        self.displayModeComboBox.addItem("Default", userData="default")
        self.displayModeComboBox.addItem("Grayscale", userData="grayscale")
        self.displayModeComboBox.addItem("RGBA", userData="rgba")
        self.displayModeComboBox.addItem("Random Colortable", userData="random-colortable")
        self.displayModeComboBox.addItem("Alpha Modulated", userData="alpha-modulated")
        self.displayModeComboBox.addItem("Binary Mask", userData="binary-mask")
        modes = {info.display_mode or "default" for info in infos}
        if len(modes) == 1:
            index = self.displayModeComboBox.findData(modes.pop())
            self.displayModeComboBox.setCurrentIndex(index)
        else:
            self.displayModeComboBox.setCurrentIndex(-1)

        self.storageComboBox.addItem("Copy into project file", userData=ProjectInternalDatasetInfo)
        if self.fs_infos == infos:
            self.storageComboBox.addItem("Store absolute path", userData=FilesystemDatasetInfo)
            if all(info.dataset.is_under(self.project_file_path.parent) for info in self.fs_infos):
                self.storageComboBox.addItem("Store relative path", userData=RelativeFilesystemDatasetInfo)

        current_locations = {info.__class__ for info in infos}
        if len(current_locations) == 1:
            comboIndex = self.storageComboBox.findData(current_locations.pop())
        else:
            comboIndex = -1
        self.storageComboBox.setCurrentIndex(comboIndex)

    def _handle_inner_path_change(self, new_internal_path: str):
        msg = ""
        for info in self.fs_infos:
            if new_internal_path and {new_internal_path} != set(info.internal_paths):
                msg = "Note: Changing internal dataset path will reset the other fields to defaults"
                break
        self.internalDatasetNameComboBoxMessage.setText(msg)

    def get_new_axes_tags(self):
        if self.axesEdit.isEnabled() and self.axesEdit.text():
            return vigra.defaultAxistags(self.axesEdit.text())
        return None

    def get_new_normalization(self) -> bool:
        return self.normalizeDisplayComboBox.currentData()

    def get_new_drange(self) -> Optional[Tuple[Number, Number]]:
        if self.get_new_normalization():
            return (self.rangeMinSpinBox.value(), self.rangeMaxSpinBox.value())
        return None

    def validate_new_data(self, *args, **kwargs):
        invalid_inputs = False

        axis_error_msg = ""
        new_axiskeys = self.axesEdit.text()
        if new_axiskeys:
            dataset_dims = self.axesEdit.maxLength()
            if len(new_axiskeys) in range(1, dataset_dims):
                axis_error_msg = f"Dataset has {dataset_dims} dimensions, so you need to provide that many axes keys"
            elif not set(new_axiskeys).issubset(set("xyztc")):
                axis_error_msg = 'Axes must be a combination of "xyztc"'
            elif len(set(new_axiskeys)) < len(new_axiskeys):
                axis_error_msg = "Repeated axis keys"
            elif not set("xy").issubset(set(new_axiskeys)):
                axis_error_msg = "x and y need to be present"
        self.axes_error_display.setText(axis_error_msg)
        invalid_inputs |= bool(axis_error_msg)

        drange_error_msg = ""
        new_drange = self.get_new_drange()
        if self.get_new_normalization() and new_drange[0] >= new_drange[1]:
            drange_error_msg = "MIN must be lesser than MAX."
        self.drange_error_display.setText(drange_error_msg)
        invalid_inputs = invalid_inputs or bool(drange_error_msg)

        self.okButton.setEnabled(not invalid_inputs)

    def accept(self):
        normalize = self.get_new_normalization()
        new_drange = self.get_new_drange()
        project_file = self.serializer.topLevelOperator.ProjectFile.value

        self.edited_infos = []
        for info in self.current_infos:
            new_display_mode = self.displayModeComboBox.currentData() or info.display_mode
            new_info_class = self.storageComboBox.currentData() or info.__class__
            if new_info_class == ProjectInternalDatasetInfo:
                project_inner_path = info.importAsLocalDataset(project_file=project_file)
                info_constructor = partial(
                    ProjectInternalDatasetInfo, inner_path=project_inner_path, project_file=project_file
                )
            elif new_info_class == UrlDatasetInfo:
                assert isinstance(info, UrlDatasetInfo)
                info_constructor = partial(UrlDatasetInfo, url=info.url)
            else:
                assert isinstance(info, FilesystemDatasetInfo)
                new_internal_path = self.internalDatasetNameComboBox.currentText()
                if new_internal_path:
                    new_dataset = info.dataset.with_internal_path(new_internal_path)
                else:
                    new_dataset = info.dataset
                if new_info_class == RelativeFilesystemDatasetInfo:
                    info_constructor = partial(
                        RelativeFilesystemDatasetInfo,
                        dataset=new_dataset,
                        project_file=project_file,
                        sequence_axis=info.sequence_axis,
                    )
                else:  # new_info_class == FilesystemDatasetInfo
                    info_constructor = partial(
                        FilesystemDatasetInfo, dataset=new_dataset, sequence_axis=info.sequence_axis
                    )
            edited_info = info_constructor(
                nickname=self.nicknameEdit.text() if self.nicknameEdit.isEnabled() else info.nickname,
                axistags=self.get_new_axes_tags() or info.axistags,
                normalizeDisplay=info.normalizeDisplay if normalize is None else normalize,
                drange=(info.laneDtype(new_drange[0]), info.laneDtype(new_drange[1])) if normalize else info.drange,
                display_mode=new_display_mode,
            )
            self.edited_infos.append(edited_info)
        super(DatasetInfoEditorWidget, self).accept()

    def clearNormalization(self):
        selected_normalize_index = self.normalizeDisplayComboBox.findData(None)
        self.normalizeDisplayComboBox.setCurrentIndex(selected_normalize_index)
        self.rangeMinSpinBox.setValue(self.rangeMinSpinBox.minimum())
        if all(numpy.dtype(info.laneDtype).kind == "f" for info in self.current_infos):
            self.rangeMaxSpinBox.setValue(1.0)
        else:
            self.rangeMaxSpinBox.setValue(self.rangeMaxSpinBox.maximum())

    def _handleNormalizeDisplayChanged(self):
        normalize = bool(self.normalizeDisplayComboBox.currentData())
        self.rangeMinSpinBox.setEnabled(normalize)
        self.rangeMaxSpinBox.setEnabled(normalize)
        self.clearRangeButton.setEnabled(normalize)
