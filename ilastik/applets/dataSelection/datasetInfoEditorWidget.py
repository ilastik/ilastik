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

class DatasetInfoEditorWidget(QDialog):
    """
    This dialog allows the user to edit the settings of one **OR MORE** datasets for a given role.
    """
    def __init__(self, parent, topLevelOperator, roleIndex, laneIndexes, defaultInfos={}, show_axis_details=False):
        """
        :param topLevelOperator: The applet's OpMultiLaneDataSelectionGroup instance
        :param roleIndex: The role of the dataset(s) we're editing
        :param laneIndexes: A list of lanes this dialog will apply settings to. (Same role for each lane.)
        :param defaultInfos: ignored
        """
        assert len(laneIndexes) > 0
        super( DatasetInfoEditorWidget, self ).__init__(parent)
        self._op = topLevelOperator
        self._laneIndexes = laneIndexes
        self.selected_ops = [topLevelOperator.innerOperators[li]._opDatasets[roleIndex]  for li in laneIndexes]
        self.datasetinfo_slots = [topLevelOperator.DatasetGroup[li][roleIndex] for li in laneIndexes]
        self.current_infos = [op.Dataset.value for op in self.selected_ops]

        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        uiFilePath = os.path.join( localDir, 'datasetInfoEditorWidget.ui' )
        uic.loadUi(uiFilePath, self)
        self.setObjectName(f"DatasetInfoEditorWidget_Role_{roleIndex}")

        self.normalizeDisplayComboBox.addItem("True", userData=True)
        self.normalizeDisplayComboBox.addItem("False", userData=False)
        self.normalizeDisplayComboBox.addItem("Default", userData=None)
        self.normalizeDisplayComboBox.currentIndexChanged.connect(self._handleNormalizeDisplayChanged)
        self.normalizeDisplayComboBox.setCurrentText("Default")

        self.rangeMinSpinBox.setSpecialValueText("--")
        self.rangeMaxSpinBox.setSpecialValueText("--")
        self.clearRangeButton.clicked.connect(self._clearNormalizationRanges)
        self._clearNormalizationRanges()

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        input_axiskeys = []
        for op in self.selected_ops:
            tags = op.Image.meta.original_axistags or op.Image.meta.axistags
            keys = "".join(tag.key for tag in tags)
            input_axiskeys.append(keys)

        self.multi_axes_display.setEnabled(False)
        self.multi_axes_display.setText("Current: " + ", ".join(input_axiskeys))
        if all(len(keys) == len(input_axiskeys[0]) for keys in input_axiskeys):
            selector_keys = input_axiskeys[0]
        else:
            selector_keys = ''
            self.multi_axes_display.setToolTip("Select lanes with same number of axes to change their interpretation here")

        for axis_index in range(5):
            axis_selector = getattr(self, f"axesEdit_{axis_index}")
            within_bounds = axis_index < len(selector_keys)
            axis_selector.setVisible(within_bounds)
            axis_selector.setEnabled(within_bounds)
            axis_selector.setCurrentText(selector_keys[axis_index] if within_bounds else 'x')


        self.nicknameEdit.setText(', '.join(str(info.nickname) for info in self.current_infos))
        if len(self.selected_ops) == 1:
            self.nicknameEdit.setEnabled(True)
        else:
            self.nicknameEdit.setEnabled(False)
            self.nicknameEdit.setToolTip("Edit a single lane to modify its nickname")


        self.shapeLabel.setText(", ".join(str(op.Image.meta.shape) for op in self.selected_ops))
        self.dtypeLabel.setText(", ".join(op.Image.meta.dtype.__name__ for op in self.selected_ops))

        current_normalize_display = {op.Image.meta.normalizeDisplay for op in self.selected_ops}
        dranges = {op.Image.meta.drange for op in self.selected_ops if op.Image.meta.drange is not None}
        if len(current_normalize_display) == 1:
            normalize = current_normalize_display.pop()
            if normalize:
                self.normalizeDisplayComboBox.setCurrentIndex(0)
                if len(dranges) == 1:
                    common_drange = dranges.pop()
                    self.rangeMinSpinBox.setValue(common_drange[0])
                    self.rangeMaxSpinBox.setValue(common_drange[1])
            else:
                self.normalizeDisplayComboBox.setCurrentIndex(1)
        else:
            self.normalizeDisplayComboBox.setCurrentIndex(2)




        hdf5_infos = [info for info in self.current_infos if info.isHdf5()]
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
        modes = {op.Image.meta.display_mode or "default" for op in self.selected_ops}
        if len(modes) == 1:
            index = self.displayModeComboBox.findData(modes.pop())
            self.displayModeComboBox.setCurrentIndex(index)
        else:
            self.displayModeComboBox.setCurrentIndex(0)

        for location in StorageLocation:
            self.storageComboBox.addItem(location.value, userData=location)

        current_locations = {StorageLocation.from_datasetinfo(info) for info in self.current_infos}
        self.storageComboBox.setCurrentIndex(-1)
        if len(current_locations) == 1:
            comboIndex = self.storageComboBox.findData(current_locations.pop())
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
        new_axes_keys = ''
        for axis_index in range(5):
            axis_selector = getattr(self, f"axesEdit_{axis_index}")
            if not axis_selector.isVisible():
                break
            new_axes_keys += axis_selector.currentText()
        if len(set(new_axes_keys)) != len(new_axes_keys):
            raise Exception(f"Repeated axes: {new_axes_keys}")
        return vigra.defaultAxistags(new_axes_keys) if new_axes_keys else None

    def accept(self):
        try:
            saved_datasetinfos = []
            normalize = self.normalizeDisplayComboBox.currentData()
            new_drange = (self.rangeMinSpinBox.value(), self.rangeMaxSpinBox.value())
            if normalize:
                if new_drange[0] >= new_drange[1]:
                    raise Exception("Can't apply data range values: Data range MIN must be lesser than MAX.")
                for op in self.selected_ops:
                    dtype_info = get_dtype_info(op.Image.meta.dtype)
                    if new_drange[0] < dtype_info.min or new_drange[1] > dtype_info.max:
                        raise Exception(f"Data range values {new_drange} conflicts with the data type in lane {lane_idx}, "
                                        f"which has range {(dtype_info.min, dtype_info.max)}")

            newStorageLocation = self.storageComboBox.currentData()
            new_display_mode = self.displayModeComboBox.currentData()

            for op, datasetinfo_slot in zip(self.selected_ops, self.datasetinfo_slots):
                info = copy.copy( op.Dataset.value )
                saved_datasetinfos.append(info)

                if self.internalDatasetNameComboBox.isEnabled():
                    pathComponents = PathComponents(info.filePath)
                    pathComponents.internalPath = self.internalDatasetNameComboBox.currentText()
                    filePath = pathComponents.totalPath()
                else:
                    filePath = info.filePath

                if newStorageLocation == StorageLocation.ProjectFile:
                    location = DatasetInfo.Location.ProjectInternal
                else:
                    location = DatasetInfo.Location.FileSystem
                    absPath, relPath = getPathVariants(filePath, op.WorkingDirectory.value)
                    if newStorageLocation == StorageLocation.RelativeLink:
                        filePath = relPath
                    else:
                        filePath = absPath

                dtype = get_dtype_info(op.Image.meta.dtype).dtype.type

                info.nickname = self.nicknameEdit.text() if self.nicknameEdit.isEnabled() else info.nickname
                info.axistags = self.get_new_axes_tags() or info.axistags
                info.normalizeDisplay = info.normalizeDisplay if normalize is None else normalize
                info.drange = (dtype(new_drange[0]), dtype(new_drange[1])) if normalize else info.drange
                info.display_mode = new_display_mode if new_display_mode != 'default' else info.display_mode
                info.location = location
                info.filePath = filePath
                datasetinfo_slot.setValue(info)
            super(DatasetInfoEditorWidget, self).accept()
        except Exception as e:
            for idx, datasetinfo in enumerate(saved_datasetinfos):
                self.datasetinfo_slots[idx].setValue(datasetinfo)
            QMessageBox.warning(self, "Error", str(e))

    def _clearNormalizationRanges(self):
        self.rangeMinSpinBox.setValue(self.rangeMinSpinBox.minimum())
        self.rangeMaxSpinBox.setValue(self.rangeMaxSpinBox.minimum())

    def _handleNormalizeDisplayChanged(self):
        normalize = bool(self.normalizeDisplayComboBox.currentData())
        self.rangeMinSpinBox.setEnabled(normalize)
        self.rangeMaxSpinBox.setEnabled(normalize)
        self.clearRangeButton.setEnabled(normalize)
