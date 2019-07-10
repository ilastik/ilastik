from __future__ import absolute_import
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
import copy
from enum import Enum, unique
from pathlib import Path
from typing import List

import h5py
import numpy
import vigra

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QMessageBox, QDoubleSpinBox, QApplication

from ilastik.utility import log_exception
from ilastik.applets.base.applet import DatasetConstraintError
from lazyflow.utility import getPathVariants, PathComponents, isUrl
from .opDataSelection import OpDataSelection, DatasetInfo

import logging
logger = logging.getLogger(__name__)

@unique
class StorageLocation(Enum):
    Default = "Default"
    ProjectFile = "Copied into Project File"
    AbsoluteLink = "Absolute Link"
    RelativeLink = "Relative Link"

    @classmethod
    def from_datasetinfo(cls, info:DatasetInfo):
        if info.location == DatasetInfo.Location.ProjectInternal:
            return cls.ProjectFile
        if isUrl(info.filePath) or os.path.isabs(info.filePath):
            return cls.AbsoluteLink
        return cls.RelativeLink

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

    def handle_invalid_axeskeys(self, message:str):
        self.axes_error_display.setText(message)
        self.okButton.setEnabled(False)

    def handle_valid_axeskeys(self):
        self.axes_error_display.setText("")
        self.okButton.setEnabled(True)

    def validate_new_axiskeys(self, new_axiskeys:str):
        if not new_axiskeys:
            return self.handle_valid_axeskeys()

        dataset_dims = self.axesEdit.maxLength()
        if 0 != len(new_axiskeys) < dataset_dims:
            return self.handle_invalid_axeskeys(f"Dataset has {dataset_dims} dimensions, so you need to provide that many axes keys")

        if not set(new_axiskeys).issubset(set("xyztc")):
            return self.handle_invalid_axeskeys("Axes must be a combination of \"xyztc\"")

        if len(set(new_axiskeys)) < len(new_axiskeys):
            return self.handle_invalid_axeskeys("Repeated axis keys")

        if not set('xy').issubset(set(new_axiskeys)):
            return self.handle_invalid_axeskeys("x and y need to be present")

        self.handle_valid_axeskeys()

    def __init__(self, parent, infos:List[DatasetInfo], projectFileDir:str):
        """
        :param infos: DatasetInfo infos to be edited by this widget
        :param projectFileDir: path containing the current project file
        """
        super( DatasetInfoEditorWidget, self ).__init__(parent)
        self.current_infos = infos
        self.projectFileDir = projectFileDir
        self.edited_infos = []

        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        uiFilePath = os.path.join( localDir, 'datasetInfoEditorWidget.ui' )
        uic.loadUi(uiFilePath, self)

        self.rangeMinSpinBox.setSpecialValueText("--")
        self.rangeMaxSpinBox.setSpecialValueText("--")
        self.clearRangeButton.clicked.connect(self._clearNormalizationRanges)
        self._clearNormalizationRanges()

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        input_axiskeys = [info.axiskeys for info in infos]
        self.multi_axes_display.setEnabled(False)
        self.multi_axes_display.setText("Current: " + ", ".join(input_axiskeys))
        if all(len(keys) == len(input_axiskeys[0]) for keys in input_axiskeys):
            self.axesEdit.setMaxLength(len(input_axiskeys[0]))
            self.axesEdit.textChanged.connect(self.validate_new_axiskeys)
            different_axiskeys = set(input_axiskeys)
            if len(different_axiskeys) == 1:
                self.axesEdit.setText(different_axiskeys.pop())
        else:
            self.multi_axes_display.setToolTip("Select lanes with same number of axes to change their interpretation here")
            self.axesEdit.setEnabled(False)
            self.axesEdit.setVisible(False)


        self.nicknameEdit.setText(', '.join(str(info.nickname) for info in self.current_infos))
        if len(infos) == 1:
            self.nicknameEdit.setEnabled(True)
        else:
            self.nicknameEdit.setEnabled(False)
            self.nicknameEdit.setToolTip("Edit a single lane to modify its nickname")


        self.shapeLabel.setText(", ".join(str(info.shape) for info in infos))
        self.dtypeLabel.setText(", ".join(info.dtype.__name__ for info in infos))

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

        hdf5_infos = [info for info in infos if info.isHdf5()]
        if not hdf5_infos:
            self.internalDatasetNameLabel.setVisible(False)
            self.internalDatasetNameComboBox.setVisible(False)
            self.internalDatasetNameComboBox.setEnabled(False)
        else:
            allInternalPaths = set()
            commonInternalPaths = None
            for info in hdf5_infos:
                internalPaths = set(info.getPossibleInternalPaths())
                commonInternalPaths = commonInternalPaths or internalPaths
                allInternalPaths |= internalPaths
                commonInternalPaths &= internalPaths
                if len( commonInternalPaths ) == 0:
                    self.internalDatasetNameComboBox.addItem( "Couldn't find a dataset name common to all selected files." )
                    self.internalDatasetNameComboBox.setEnabled(False)
                    break

            # Add all common paths to the combo
            for path in sorted(commonInternalPaths):
                self.internalDatasetNameComboBox.addItem( path )

            # Add the remaining ones, but disable them since they aren't common to all files:
            for path in sorted(allInternalPaths - commonInternalPaths):
                self.internalDatasetNameComboBox.addItem( path )
                # http://theworldwideinternet.blogspot.com/2011/01/disabling-qcombobox-items.html
                model = self.internalDatasetNameComboBox.model()
                index = model.index( self.internalDatasetNameComboBox.count()-1, 0 )
                model.setData( index, 0, Qt.UserRole-1 )

            internalPaths = [info.internalPath for info in hdf5_infos]
            self.internalDatasetNameComboBox.setCurrentIndex(-1)
            if all(ip == internalPaths[0] for ip in internalPaths):
                self.internalDatasetNameComboBox.setCurrentText(internalPaths[0])

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
            self.displayModeComboBox.setCurrentIndex(0)


        self.storageComboBox.addItem(StorageLocation.Default.value, userData=StorageLocation.Default)
        self.storageComboBox.addItem(StorageLocation.ProjectFile.value, userData=StorageLocation.ProjectFile)
        self.storageComboBox.addItem(StorageLocation.AbsoluteLink.value, userData=StorageLocation.AbsoluteLink)
        for info in infos:
            try:
                Path(info.filePath).relative_to(projectFileDir)
            except ValueError:
                break
        else:
            self.storageComboBox.addItem(StorageLocation.RelativeLink.value, userData=StorageLocation.RelativeLink)

        current_locations = {StorageLocation.from_datasetinfo(info) for info in infos}
        if len(current_locations) == 1:
            comboIndex = self.storageComboBox.findData(current_locations.pop())
        else:
            comboIndex = self.storageComboBox.findData(StorageLocation.Default)
        self.storageComboBox.setCurrentIndex(comboIndex)

        if any(info.fromstack for info in self.current_infos):
            # If any of the files were loaded from a stack, then you can't refer to them via a link.
            absIndex = self.storageComboBox.findData( StorageLocation.AbsoluteLink )
            relIndex = self.storageComboBox.findData( StorageLocation.RelativeLink )

            # http://theworldwideinternet.blogspot.com/2011/01/disabling-qcombobox-items.html
            model = self.storageComboBox.model()
            model.setData( model.index( absIndex, 0 ), 0, Qt.UserRole-1 )
            model.setData( model.index( relIndex, 0 ), 0, Qt.UserRole-1 )

    def get_new_axes_tags(self):
        if self.axesEdit.isEnabled() and self.axesEdit.text():
            return vigra.defaultAxistags(self.axesEdit.text())
        return None

    def accept(self):
        try:
            saved_datasetinfos = []
            normalize = self.normalizeDisplayComboBox.currentData()
            new_drange = (self.rangeMinSpinBox.value(), self.rangeMaxSpinBox.value())
            if normalize:
                if new_drange[0] >= new_drange[1]:
                    raise InvalidDatasetinfoException("Can't apply data range values: Data range MIN must be lesser than MAX.")
                for info in self.current_infos:
                    dtype_info = get_dtype_info(info.dtype)
                    if new_drange[0] < dtype_info.min or new_drange[1] > dtype_info.max:
                        raise InvalidDatasetinfoException(f"Data range values {new_drange} conflicts with the data type in lane {lane_idx}, "
                                        f"which has range {(dtype_info.min, dtype_info.max)}")

            newStorageLocation = self.storageComboBox.currentData()
            new_display_mode = self.displayModeComboBox.currentData()

            self.edited_infos = []
            for info in self.current_infos:
                if self.internalDatasetNameComboBox.isEnabled():
                    pathComponents = PathComponents(info.filePath)
                    pathComponents.internalPath = self.internalDatasetNameComboBox.currentText()
                    filePath = pathComponents.totalPath()
                else:
                    filePath = info.filePath

                if newStorageLocation == StorageLocation.ProjectFile:
                    location = DatasetInfo.Location.ProjectInternal
                elif newStorageLocation == StorageLocation.Default:
                    location = info.location
                else:
                    location = DatasetInfo.Location.FileSystem
                    if newStorageLocation == StorageLocation.RelativeLink:
                        filePath = Path(filePath).absolute().relative_to(self.projectFileDir).as_posix()
                    else:
                        filePath = Path(filePath).absolute().as_posix()

                edited_info = info.modified_with(
                    nickname=self.nicknameEdit.text() if self.nicknameEdit.isEnabled() else info.nickname,
                    axistags=self.get_new_axes_tags() or info.axistags,
                    normalizeDisplay=info.normalizeDisplay if normalize is None else normalize,
                    drange=(info.dtype(new_drange[0]), info.dtype(new_drange[1])) if normalize else info.drange,
                    display_mode=new_display_mode if new_display_mode != 'default' else info.display_mode,
                    location=location,
                    filePath=filePath)
                self.edited_infos.append(edited_info)
            super(DatasetInfoEditorWidget, self).accept()
        except InvalidDatasetinfoException as e:
            QMessageBox.warning(self, "File selection error", str(e))

    def _clearNormalizationRanges(self):
        self.rangeMinSpinBox.setValue(self.rangeMinSpinBox.minimum())
        self.rangeMaxSpinBox.setValue(self.rangeMaxSpinBox.minimum())

    def _handleNormalizeDisplayChanged(self):
        normalize = bool(self.normalizeDisplayComboBox.currentData())
        self.rangeMinSpinBox.setEnabled(normalize)
        self.rangeMaxSpinBox.setEnabled(normalize)
        self.clearRangeButton.setEnabled(normalize)
