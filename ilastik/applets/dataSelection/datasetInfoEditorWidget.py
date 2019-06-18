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
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QDialog, QMessageBox, QDoubleSpinBox, QApplication

from ilastik.utility import log_exception
from ilastik.applets.base.applet import DatasetConstraintError
from lazyflow.utility import getPathVariants, PathComponents, isUrl
from .opDataSelection import OpDataSelection, DatasetInfo

import logging
logger = logging.getLogger(__name__)

@unique
class StorageLocation(Enum):
    ProjectFile = "Copied to Project File"
    AbsoluteLink = "Absolute Link"
    RelativeLink = "Relative Link"

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
        self.current_infos = [op.Dataset.value for op in self.selected_ops]
        self.show_axis_details = show_axis_details
        self.encountered_exception = None

        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        uiFilePath = os.path.join( localDir, 'datasetInfoEditorWidget.ui' )
        uic.loadUi(uiFilePath, self)
        self.setObjectName(f"DatasetInfoEditorWidget_Role_{roleIndex}")

        self.displayModeComboBox.addItem("Default", userData="default")
        self.displayModeComboBox.addItem("Grayscale", userData="grayscale")
        self.displayModeComboBox.addItem("RGBA", userData="rgba")
        self.displayModeComboBox.addItem("Random Colortable", userData="random-colortable")
        self.displayModeComboBox.addItem("Alpha Modulated", userData="alpha-modulated")
        self.displayModeComboBox.addItem("Binary Mask", userData="binary-mask")

        self.normalizeDisplayComboBox.addItem("True", userData=True)
        self.normalizeDisplayComboBox.addItem("False", userData=False)
        self.normalizeDisplayComboBox.addItem("Default", userData=None)
        self.normalizeDisplayComboBox.setCurrentIndex(1)

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        self.clearRangeButton.clicked.connect(self._handleClearRangeButton)


        input_axiskeys = []
        for op in self.selected_ops:
            tags = op.Image.meta.original_axistags or op.Image.meta.axistags
            keys = "".join(tag.key for tag in tags)
            if not input_axiskeys or input_axiskeys[-1] != keys:
                input_axiskeys.append(keys)

        if len(input_axiskeys) > 1:
            self.multi_axes_display.setText(", ".join(keys))
            self.multi_axes_display.setVisible(True)
            key = ''
        else:
            self.multi_axes_display.setVisible(False)
            key = input_axiskeys[0]
        self.multi_axes_display.setEnabled(False)

        for axis_index in range(5):
            axis_selector = getattr(self, f"axesEdit_{axis_index}")
            within_bounds = axis_index < len(key)
            axis_selector.setVisible(within_bounds)
            axis_selector.setCurrentText(key[axis_index] if within_bounds else 'x')


        self.nicknameEdit.setText(', '.join(str(info.nickname) for info in self.current_infos))
        self.nicknameEdit.setEnabled(len(self.selected_ops) == 1)

        self.shapeLabel.setText(", ".join(str(op.Image.meta.shape) for op in self.selected_ops))
        self.dtypeLabel.setText(", ".join(op.Image.meta.dtype.__name__ for op in self.selected_ops))

        modes = [op.Image.meta.display_mode or "default" for op in self.selected_ops]
        if all(md == modes[0] for md in modes):
            index = self.displayModeComboBox.findData(modes[0])
            self.displayModeComboBox.setCurrentIndex(index)
            self.displayModeComboBox.setEnabled(True)
        else:
            self.displayModeComboBox.setEnabled(False)

        #FIXME: range?
        #self.rangeMinSpinBox.setValue( drange[0] )
        #self.rangeMaxSpinBox.setValue( drange[1] )

        current_normalize_display = [op.Image.meta.normalizeDisplay for op in self.selected_ops]
        if all(norm == True for norm in current_normalize_display):
            self.normalizeDisplayComboBox.setCurrentIndex(0)
        if all(norm == False for norm in current_normalize_display):
            self.normalizeDisplayComboBox.setCurrentIndex(1)
        else:
            self.normalizeDisplayComboBox.setCurrentIndex(2)
            self.normalizeDisplayComboBox.setEnabled(False)

    def accept(self):
        newAxisOrder = 'yxc'#FIXME: recover axes   str(self.axesEdit.currentText())
        new_norm = self.normalizeDisplayComboBox.currentData()
        new_drange = ( self.rangeMinSpinBox.value(), self.rangeMaxSpinBox.value() )

        if len(set(newAxisOrder)) != len(newAxisOrder):
            raise Exception("Axis order has repeated axes.")

        def get_dtype_info(dtype):
            try:
                return numpy.iinfo(dtype)
            except ValueError:
                return numpy.finfo(dtype)

        if new_drange is not None:
            if new_drange[0] >= new_drange[1]:
                raise Exception("Can't apply data range values: Data range MAX must be greater than MIN.")

            for op in self.selected_ops:
                dtype_info = get_dtype_info(op.Image.meta.dtype)
                if new_drange[0] < dtype_info.min or new_drange[1] > dtype_info.max:
                    raise Exception(f"Data range values {new_drange} conflicts with the data type in lane {lane_idx}")

        newDisplayMode = self.displayModeComboBox.currentData()

        for op in self.selected_ops:
            info = copy.copy( op.Dataset.value )
            dtype_info = get_dtype_info(op.Image.meta.dtype)
            dtype = dtype_info.dtype.type
            info.drange = ( dtype(new_drange[0]), dtype(new_drange[1]) )
            info.normalizeDisplay = new_norm
            info.axistags = newTags
            if self.nicknameEdit.isEnabled():
                info.nickname = self.nicknameEdit.text()
            info.display_mode = newDisplayMode
            op.Dataset.setValue( info )

        super(DatasetInfoEditorWidget, self).accept()

    def _initInternalDatasetNameCombo(self):
        # If any dataset is either (1) not hdf5 or (2) project-internal, then we can't change the internal path.
        h5Exts = ['.ilp', '.h5', '.hdf5']
        for info in self.current_infos:
            externalPath = PathComponents(info.filePath).externalPath
            if os.path.splitext(externalPath)[1] not in h5Exts \
            or datasetInfo.location == DatasetInfo.Location.ProjectInternal:
                self.internalDatasetNameComboBox.addItem( "N/A" )
                self.internalDatasetNameComboBox.setEnabled(False)
                return
        
        # Enable IFF all datasets have at least one common internal dataset, and only show COMMON datasets
        allInternalPaths = set()
        commonInternalPaths = None
        
        for laneIndex in self._laneIndexes:
            tmpOp = self.tempOps[laneIndex]
            datasetInfo = tmpOp.Dataset.value
            
            externalPath = PathComponents( datasetInfo.filePath ).externalPath
            absPath, _ = getPathVariants( externalPath, tmpOp.WorkingDirectory.value )
            internalPaths = set( self._getPossibleInternalPaths(absPath) )
            
            if commonInternalPaths is None:
                # Init with the first file's set of paths
                commonInternalPaths = internalPaths
            
            # Set operations
            allInternalPaths |= internalPaths
            commonInternalPaths &= internalPaths
            if len( commonInternalPaths ) == 0:
                self.internalDatasetNameComboBox.addItem( "Couldn't find a dataset name common to all selected files." )
                self.internalDatasetNameComboBox.setEnabled(False)
                return

        uncommonInternalPaths = allInternalPaths - commonInternalPaths
        # Add all common paths to the combo
        for path in sorted(commonInternalPaths):
            self.internalDatasetNameComboBox.addItem( path )
        
        # Add the remaining ones, but disable them since they aren't common to all files:
        for path in sorted(uncommonInternalPaths):
            self.internalDatasetNameComboBox.addItem( path )
            # http://theworldwideinternet.blogspot.com/2011/01/disabling-qcombobox-items.html
            model = self.internalDatasetNameComboBox.model()
            index = model.index( self.internalDatasetNameComboBox.count()-1, 0 )
            model.setData( index, 0, Qt.UserRole-1 )

        # Finally, initialize with NO item selected
        self.internalDatasetNameComboBox.setCurrentIndex(-1)

    def _getPossibleInternalPaths(self, absPath):
        datasetNames = []
        with h5py.File(absPath, 'r') as f:
            def accumulateDatasetPaths(name, val):
                if type(val) == h5py._hl.dataset.Dataset and 3 <= len(val.shape) <= 5:
                    datasetNames.append( '/' + name )
            f.visititems(accumulateDatasetPaths)
        return datasetNames

    def _updateInternalDatasetSelection(self):
        # If all lanes have the same dataset selected, choose that item.
        # Otherwise, leave it uninitialized
        if not self.internalDatasetNameComboBox.isEnabled():
            return
        
        internalPath = None
        
        for laneIndex in self._laneIndexes:
            tmpOp = self.tempOps[laneIndex]
            datasetInfo = tmpOp.Dataset.value
            
            nextPath = PathComponents( datasetInfo.filePath ).internalPath
            if internalPath is None:
                internalPath = nextPath # init
            if internalPath != nextPath:
                self.internalDatasetNameComboBox.setCurrentIndex(-1)
                return

        # Make sure the correct index is selected.        
        index = self.internalDatasetNameComboBox.findText( internalPath )
        self.internalDatasetNameComboBox.setCurrentIndex( index )

    def _applyInternalPathToTempOps(self, index):
        newInternalPath = str( self.internalDatasetNameComboBox.currentText() )

        for laneIndex, op in list(self.tempOps.items()):
            info = copy.copy( op.Dataset.value )
            pathComponents = PathComponents(info.filePath)
            if pathComponents.internalPath != newInternalPath:
                pathComponents.internalPath = newInternalPath
                info.filePath = pathComponents.totalPath()
                op.Dataset.setValue( info )
        self._error_fields.discard('Internal Dataset Name')
        return True

    def _initStorageCombo(self):
        # If there's only one dataset, show the path in the combo
        showpaths = False
        relPath = None
        if len( self._laneIndexes ) == 1:
            op = list(self.tempOps.values())[0]
            info = op.Dataset.value
            cwd = op.WorkingDirectory.value
            filePath = PathComponents(info.filePath).externalPath
            absPath, relPath = getPathVariants(filePath, cwd)
            
            # commented out: 
            # Show the paths even if the data is from a stack (they are grayed out, but potentially informative)
            #showpaths = not info.fromstack
            showpaths = True

        if showpaths:
            self.storageComboBox.addItem( "Copied to Project File", userData=StorageLocation.ProjectFile )
            self.storageComboBox.addItem( ("Absolute Link: " + absPath), userData=StorageLocation.AbsoluteLink )
            if relPath is not None:
                self.storageComboBox.addItem( ("Relative Link: " + relPath), userData=StorageLocation.RelativeLink )
        else:
            self.storageComboBox.addItem( "Copied to Project File", userData=StorageLocation.ProjectFile )
            self.storageComboBox.addItem( "Absolute Link", userData=StorageLocation.AbsoluteLink )
            self.storageComboBox.addItem( "Relative Link", userData=StorageLocation.RelativeLink )

        self.storageComboBox.setCurrentIndex(-1)

    def _updateStorageCombo(self):
        sharedStorageSetting = None
        for laneIndex in self._laneIndexes:
            op = self.tempOps[laneIndex]
            info = op.Dataset.value

            # Determine the current setting
            location = info.location
    
            if location == DatasetInfo.Location.ProjectInternal:
                storageSetting = StorageLocation.ProjectFile
            elif location == DatasetInfo.Location.FileSystem:
                # Determine if the path is relative or absolute
                if isUrl(info.filePath) or os.path.isabs(info.filePath):
                    storageSetting = StorageLocation.AbsoluteLink
                else:
                    storageSetting = StorageLocation.RelativeLink
        
            if sharedStorageSetting is None:
                sharedStorageSetting = storageSetting
            elif sharedStorageSetting != storageSetting:
                # Not all lanes have the same setting
                sharedStorageSetting = -1
                break

        if sharedStorageSetting == -1:
            self.storageComboBox.setCurrentIndex(-1)
        else:
            comboIndex = self.storageComboBox.findData( sharedStorageSetting )
            self.storageComboBox.setCurrentIndex( comboIndex )

        disableLinks = False
        for laneIndex in self._laneIndexes:
            op = self.tempOps[laneIndex]
            info = op.Dataset.value
            
            disableLinks |= info.fromstack
        
        if disableLinks:
            # If any of the files were loaded from a stack, then you can't refer to them via a link.
            absIndex = self.storageComboBox.findData( StorageLocation.AbsoluteLink )
            relIndex = self.storageComboBox.findData( StorageLocation.RelativeLink )

            # http://theworldwideinternet.blogspot.com/2011/01/disabling-qcombobox-items.html
            model = self.storageComboBox.model()
            model.setData( model.index( absIndex, 0 ), 0, Qt.UserRole-1 )
            model.setData( model.index( relIndex, 0 ), 0, Qt.UserRole-1 )

    def _applyStorageComboToTempOps(self, index):
        newStorageLocation = self.storageComboBox.itemData( index )
        for op in self.selected_ops:
            if info.location == DatasetInfo.Location.ProjectInternal:
                thisLaneStorage = StorageLocation.ProjectFile
            elif info.location == DatasetInfo.Location.FileSystem:
                # Determine if the path is relative or absolute
                if isUrl(info.filePath) or os.path.isabs(info.filePath):
                    thisLaneStorage = StorageLocation.AbsoluteLink
                else:
                    thisLaneStorage = StorageLocation.RelativeLink

            if thisLaneStorage != newStorageLocation:
                if newStorageLocation == StorageLocation.ProjectFile:
                    info.location = DatasetInfo.Location.ProjectInternal
                else:
                    info.location = DatasetInfo.Location.FileSystem 
                    cwd = op.WorkingDirectory.value
                    absPath, relPath = getPathVariants( info.filePath, cwd )
                    if relPath is not None and newStorageLocation == StorageLocation.RelativeLink:
                        info.filePath = relPath
                    elif newStorageLocation == StorageLocation.AbsoluteLink:
                        info.filePath = absPath
                    else:
                        assert False, "Unknown storage location setting."
                op.Dataset.setValue( info )
        self._error_fields.discard('Storage Location')
        return True

    def _handleClearRangeButton(self):
        self.rangeMinSpinBox.setValue( self.rangeMinSpinBox.minimum() )
        self.rangeMaxSpinBox.setValue( self.rangeMaxSpinBox.minimum() )


