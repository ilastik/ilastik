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
import collections

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

class StorageLocation(object):
    ProjectFile = 0
    AbsoluteLink = 1
    RelativeLink = 2
    
    NumOptions = 3

class DatasetInfoEditorWidget(QDialog):
    """
    This dialog allows the user to edit the settings of one **OR MORE** datasets for a given role.
    
    It starts by copying the OpDataSelection operators for all selected lanes.  These temporary operators 
    are NOT connected to the rest of the graph, so we are free to change their settings in 
    response to user actions while this dialog is open.
    
    When the user clicks OK, the slot values from the temporary operators are copied to the 'real' 
    OpDataSelection operators, which are connected to the rest of the graph.  If a downstream applet 
    rejects one of the new settings, we'll see the exception it threw, and the dialog will not 
    accept the user's new settings.
    """
    def __init__(self, parent, topLevelOperator, roleIndex, laneIndexes, defaultInfos={}, show_axis_details=False):
        """
        :param topLevelOperator: The applet's OpMultiLaneDataSelectionGroup instance
        :param roleIndex: The role of the dataset(s) we're editing
        :param laneIndexes: A list of lanes this dialog will apply settings to. (Same role for each lane.)
        :param defaultInfos: If the dialog should be initialized with the info for a dataset that hasn't 
                             been applied to the top-level operator yet, add that dataset to this dict.
                             This is useful for 'repairing' dataset properties that prevented the dataset 
                             from being successfully applied to the original operator.
        """
        assert len(laneIndexes) > 0
        super( DatasetInfoEditorWidget, self ).__init__(parent)
        self._op = topLevelOperator
        self._roleIndex = roleIndex
        self._laneIndexes = laneIndexes
        self.show_axis_details = show_axis_details
        self.encountered_exception = None

        # We instantiate our own temporary operator for every input,
        # which we will use to experiment with the user's selections
        # This way, we can read e.g. the image shape without touching the "real"
        # operator until the user hits "OK".
        self.tempOps = collections.OrderedDict()
        for laneIndex in laneIndexes:
            tmpOp = OpDataSelection(parent=topLevelOperator.parent)
            origOp = self._op.innerOperators[laneIndex]._opDatasets[roleIndex]
            
            if laneIndex in defaultInfos:
                tmpOp.Dataset.setValue( copy.copy(defaultInfos[laneIndex]) )
            else:
                # Assumes that the original operator already has a dataset info.
                assert origOp.Dataset.ready(), "Can't edit dataset info for lanes that aren't initialized yet."
                tmpOp.Dataset.setValue( copy.copy( origOp.Dataset.value ) )

            tmpOp.ProjectFile.setValue( topLevelOperator.ProjectFile.value )
            tmpOp.ProjectDataGroup.setValue( topLevelOperator.ProjectDataGroup.value )
            tmpOp.WorkingDirectory.setValue( topLevelOperator.WorkingDirectory.value )
            
            self.tempOps[laneIndex] = tmpOp
                
        self._initUi()

    def _initUi(self):
        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        uiFilePath = os.path.join( localDir, 'datasetInfoEditorWidget.ui' )
        uic.loadUi(uiFilePath, self)
        self.setObjectName("DatasetInfoEditorWidget_Role_{}".format(self._roleIndex))
        self._error_fields = set()

        self.okButton.clicked.connect( self.accept )
        self.cancelButton.clicked.connect( self.reject )

        self._setUpEventFilters()

        self.axesEdit.setEnabled( self._shouldEnableAxesEdit() )
        self.axistagsEditorWidget.axistagsUpdated.connect( self._applyAxesToTempOps )
        
        self._initNormalizeDisplayCombo()
        self.normalizeDisplayComboBox.currentIndexChanged.connect( self._applyNormalizeDisplayToTempOps )
        self._updateNormalizeDisplay()
        
        self._initInternalDatasetNameCombo()
        self.internalDatasetNameComboBox.currentIndexChanged.connect( self._applyInternalPathToTempOps )
        self._updateInternalDatasetSelection()
        
        self._initStorageCombo()
        self.storageComboBox.currentIndexChanged.connect( self._applyStorageComboToTempOps )
        self._updateStorageCombo()
        
        self._initDisplayModeCombo()
        self.displayModeComboBox.currentIndexChanged.connect( self._applyDisplayModeToTempOps )
        self._updateDisplayModeCombo()
        
        self.rangeMinSpinBox.setSpecialValueText( "--" )
        self.rangeMaxSpinBox.setSpecialValueText( "--" )
        self.rangeMinSpinBox.setValue( self.rangeMinSpinBox.minimum() )
        self.rangeMaxSpinBox.setValue( self.rangeMaxSpinBox.minimum() )
        self.clearRangeButton.clicked.connect( self._handleClearRangeButton )
        
        self._updateShape()
        self._updateDtype()
        self._updateNormalizeDisplay()
        self._updateRange()
        self._updateAxes()
        
        self._updateNickname()
        
        self.adjustSize()

    def rangeDisplay(self, box, val):
        drange = self._getCommonMetadataValue("drange")
        if drange is None:
            return ""
        return QDoubleSpinBox.textFromValue(box, val)

    def _setUpEventFilters(self):
        # Changes to these widgets are detected via eventFilter()
        self._autoAppliedWidgets = { self.nicknameEdit : self._applyNicknameToTempOps,
                                     self.axesEdit : self._applyAxesToTempOps,
                                     self.rangeMinSpinBox : self._applyRangeToTempOps,
                                     self.rangeMaxSpinBox : self._applyRangeToTempOps }

        for widget in list(self._autoAppliedWidgets.keys()):
            widget.installEventFilter(self)

    def _tearDownEventFilters(self):
        for widget in list(self._autoAppliedWidgets.keys()):
            widget.removeEventFilter(self)

    def eventFilter(self, watched, event):
        if watched in self._autoAppliedWidgets:
            if ( event.type() == QEvent.KeyPress \
                and ( event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return) ):
                if self._autoAppliedWidgets[watched]():
                    self.accept()
                return True
            if ( event.type() == QEvent.FocusOut ):
                self._autoAppliedWidgets[watched]()
                return False
        return False
    
    def accept(self):
        # Un-focus the currently focused widget to ensure that it's data validators were checked.
        focusWidget = QApplication.focusWidget()
        if focusWidget is not None:
            focusWidget.clearFocus()            
        
        # Can't accept if there are errors.
        if len(self._error_fields) > 0:
            msg = "Error: Invalid data in the following fields:\n"
            for field in self._error_fields:
                msg += field + '\n'
            QMessageBox.warning(self, "Error", msg)
            return

        # Inspect the user's changes to see if we need to warn about anything.
        closing_messages = self._getClosingMessages()
        self.encountered_exception = self._applyTempOpSettingsRealOp()

        # Close the dialog.
        for title, msg in closing_messages:
            QMessageBox.information(self, title, msg)
        self._tearDownEventFilters()
        self._cleanUpTempOperators()
        super(DatasetInfoEditorWidget, self).accept()

    def exec_(self):
        ret = super().exec_()
        return ret, self.encountered_exception

    def _getClosingMessages(self):
        closing_msgs = []
        
        ## Storage option warning.
        need_message_about_storage = False
        for laneIndex in self._laneIndexes:
            if not self._op.DatasetGroup[laneIndex][self._roleIndex].ready():
                # "real" slot may not be ready yet if this dialog was opened automatically to correct an error
                # (for example, if the user's data has the wrong axes)
                continue
            old_storage = self._op.DatasetGroup[laneIndex][self._roleIndex].value.location
            new_storage = self.tempOps[laneIndex].Dataset.value.location
            
            if old_storage != new_storage and new_storage == DatasetInfo.Location.ProjectInternal:
                need_message_about_storage = True
                break
        if need_message_about_storage:
            msg = "Your dataset will be copied to your project file when your project is saved.\n"\
                  "Please save your project now."
            closing_msgs.append( ("Storage Option Changed", msg) )

        return closing_msgs

    def reject(self):
        self._tearDownEventFilters()
        self._cleanUpTempOperators()
        super( DatasetInfoEditorWidget, self ).reject()

    def _applyTempOpSettingsRealOp(self):
        """
        Apply the settings from our temporary operators to the real operators.
        """
        # Save a copy of our settings
        originalInfos = {}
        for laneIndex in self._laneIndexes:
            realSlot = self._op.DatasetGroup[laneIndex][self._roleIndex]
            if realSlot.ready():
                originalInfos[laneIndex] = copy.copy( realSlot.value )
            else:
                originalInfos[laneIndex] = None

        ret = None
        try:
            for laneIndex, op in list(self.tempOps.items()):
                info = copy.copy(op.Dataset.value)
                realSlot = self._op.DatasetGroup[laneIndex][self._roleIndex]
                realSlot.setValue(info)
        except DatasetConstraintError as ex:
            ret = ex
            if hasattr(ex, 'fixing_dialogs') and ex.fixing_dialogs:
                msg = (
                    f"Can't use given properties for current dataset, because it violates a constraint of "
                    f"the {ex.appletName} component.\n\n{ex.message}\n\nIf possible, fix this problem by adjusting "
                    f"the applet settings in the next window(s).")
                QMessageBox.warning(self, "Applet Settings Need Correction", msg)
                for dlg in ex.fixing_dialogs:
                    dlg()
                try:
                    for laneIndex, op in list(self.tempOps.items()):
                        info = copy.copy(op.Dataset.value)
                        realSlot = self._op.DatasetGroup[laneIndex][self._roleIndex]
                        realSlot.setValue(info)

                    # fixed DatasetConstraintError and there are no other errors
                    ret = None
                except Exception as ex:
                    # Maybe we fixed DatasetConstraintError, but there is still an(other) Exception
                    ret = ex

            if ret is not None:
                # Try to revert everything back to the previous state
                try:
                    for laneIndex, info in list(originalInfos.items()):
                        realSlot = self._op.DatasetGroup[laneIndex][self._roleIndex]
                        if realSlot is not None:
                            realSlot.setValue(info)
                except Exception:
                    pass
            # msg = "Failed to apply your new settings to the workflow " \
            #       "because they violate a constraint of the {} applet.\n\n".format( ex.appletName ) + \
            #       ex.message
            # log_exception(logger, msg, level=logging.INFO)
            # QMessageBox.warning(self, "Unacceptable Settings", msg)
        except Exception as ex:
            ret = ex
            msg = "Failed to apply dialog settings due to an exception:\n"
            msg += "{}".format(ex)
            log_exception(logger, msg)
            QMessageBox.critical(self, "Error", msg)

        return ret

    def _cleanUpTempOperators(self):
        for laneIndex, op in list(self.tempOps.items()):
            op.cleanUp()

    def _updateNickname(self):
        firstOp = list(self.tempOps.values())[0]
        nickname = firstOp.Dataset.value.nickname
        for op in list(self.tempOps.values()):
            info = op.Dataset.value
            if nickname != info.nickname:
                nickname = None
                break
        if nickname is None:
            self.nicknameEdit.setText("<multiple>")
        else:
            self.nicknameEdit.setText( nickname )

    def _applyNicknameToTempOps(self):
        newNickname = self.nicknameEdit.text()
        if "<multiple>" in newNickname:
            return

        try:
            # Remove the event filter while this function executes because we don't 
            #  want to trigger additional calls to this very function.
            self.nicknameEdit.removeEventFilter(self)
            
            # Save a copy of our settings
            oldInfos = {}
            for laneIndex, op in list(self.tempOps.items()):
                oldInfos[laneIndex] = copy.copy( op.Dataset.value )
    
            try:
                for laneIndex, op in list(self.tempOps.items()):
                    info = copy.copy( op.Dataset.value )
                    info.nickname = newNickname
                    op.Dataset.setValue( info )
                self._error_fields.discard('Nickname')
                return True
            except Exception as e:
                # Revert everything back to the previous state
                for laneIndex, op in list(self.tempOps.items()):
                    op.Dataset.setValue( oldInfos[laneIndex] )
                
                msg = "Could not set new nickname due to an exception:\n"
                msg += "{}".format( e )
                QMessageBox.warning(self, "Error", msg)
                log_exception( logger, msg )
                self._error_fields += 'Nickname'
                return False

        finally:
            self.nicknameEdit.installEventFilter(self)
            self._updateNickname()


    def _getCommonMetadataValue(self, attr):
        # If this metadata attribute is common across all images,
        # return it.  Otherwise, return None.
        firstOp = list(self.tempOps.values())[0]
        val = firstOp.Image.meta[attr]
        for laneIndex, op in list(self.tempOps.items()):
            if val != op.Image.meta[attr]:
                val = None
                break
        return val
    
    def _updateShape(self):
        firstOp = list(self.tempOps.values())[0]
        shape = firstOp.Image.meta.original_shape
        if shape is None:
            shape = firstOp.Image.meta.shape
        for laneIndex, op in list(self.tempOps.items()):
            nextShape = op.Image.meta.original_shape
            if nextShape is None:
                nextShape = op.Image.meta.shape
            
            if nextShape != shape:
                shape = None
                break

        if shape is None:
            self.shapeLabel.setText( "" )
        else:
            self.shapeLabel.setText( str(shape) )
    
    def _updateDtype(self):
        dtype = self._getCommonMetadataValue("dtype")
        if dtype is None:
            self.dtypeLabel.setText( "" )
            return
        if isinstance(dtype, numpy.dtype):
            dtype = dtype.type
        self.dtypeLabel.setText( dtype.__name__ )

    def _updateRange(self):
        drange = self._getCommonMetadataValue("drange")
        if drange is not None:
            self.rangeMinSpinBox.setValue( drange[0] )
            self.rangeMaxSpinBox.setValue( drange[1] )
    
    def _updateNormalizeDisplay(self):
        norm = self._getCommonMetadataValue("normalizeDisplay")
        if norm is True:
            self.normalizeDisplayComboBox.setCurrentIndex(1)
        elif norm is False:
            self.normalizeDisplayComboBox.setCurrentIndex(2)
        else:
            self.normalizeDisplayComboBox.setCurrentIndex(1)
            
    def _updateAxes(self):
        # If all images have the same axis keys,
        # then display it.  Otherwise, display default text.
        axiskeys = None
        for laneIndex, op in list(self.tempOps.items()):
            tags = op.Image.meta.original_axistags
            if tags is None:
                tags = op.Image.meta.axistags
            cmpkeys = "".join([ tag.key for tag in tags ])
            if axiskeys is None:
                axiskeys = cmpkeys
            elif axiskeys != cmpkeys:
                axiskeys = None
                break

        if axiskeys is None:
            self.axesEdit.setText( "<multiple>" )
            self.axistagsEditorWidget.setVisible(False)
            self.axesDetailsLabel.setVisible(False)
        else:
            self.axesEdit.setText( axiskeys )
            if self.axistagsEditorWidget.axistags is None:
                self.axistagsEditorWidget.init(tags)
            else:
                self.axistagsEditorWidget.change_axis_order(axiskeys)

        if not self.show_axis_details:
            self.axistagsEditorWidget.setVisible(False)
            self.axesDetailsLabel.setVisible(False)

    def _shouldEnableAxesEdit(self):
        # Enable IFF all datasets have the same number of axes.
        firstOp = list(self.tempOps.values())[0]
        original_shape = firstOp.Image.meta.original_shape
        shape = firstOp.Image.meta.shape
        if original_shape is not None:
            numaxes = len(original_shape)
        else:
            numaxes = len(shape)
        for op in list(self.tempOps.values()):
            nextShape = op.Image.meta.original_shape
            if nextShape is None:
                nextShape = op.Image.meta.shape
            if len(nextShape) != numaxes:
                return False
        return True
    
    def _applyAxesToTempOps(self):
        newAxisOrder = str(self.axesEdit.text())
        # Check for errors
        firstOp = list(self.tempOps.values())[0]

        # This portion was added in order to handle the OpDataSelection adding
        # a channel axis when encountering data without one.
        # check if channel was added and not present in original:
        axistags = firstOp._NonTransposedImage.meta.getOriginalAxisKeys()
        numaxes = len(axistags)

        if 'c' not in axistags and len(newAxisOrder) == numaxes + 1:
            newAxisOrder = newAxisOrder.replace('c', '')

        try:
            # Remove the event filter while this function executes because we don't 
            #  want to trigger additional calls to this very function.
            self.axesEdit.removeEventFilter(self)
            
            if numaxes != len( newAxisOrder ):
                QMessageBox.warning(self, "Error", "Can't use those axes: wrong number.")
                self._error_fields.add('Axis Order')
                return False
            
            for c in newAxisOrder:
                if c not in 'txyzc':
                    QMessageBox.warning(self, "Error", "Can't use those axes: Don't understand axis '{}'.".format(c))
                    self._error_fields.add('Axis Order')
                    return False
    
            if len(set(newAxisOrder)) != len(newAxisOrder):
                QMessageBox.warning(self, "Error", "Axis order has repeated axes.")
                return False
    
            # Save a copy of our settings
            oldInfos = {}
            for laneIndex, op in list(self.tempOps.items()):
                oldInfos[laneIndex] = copy.copy( op.Dataset.value )
    
            try:
                for laneIndex, op in list(self.tempOps.items()):
                    info = copy.copy( op.Dataset.value )
                    # Use new order, but keep the data from the old axis tags
                    # (for all axes that were kept)
                    #newTags = vigra.defaultAxistags(newAxisOrder)
                    self.axistagsEditorWidget.change_axis_order(newAxisOrder)
                    newTags = self.axistagsEditorWidget.axistags
                    info.axistags = newTags
                    op.Dataset.setValue( info )
                self._error_fields.discard('Axis Order')
                return True
            except Exception as e:
                # Revert everything back to the previous state
                for laneIndex, op in list(self.tempOps.items()):
                    op.Dataset.setValue( oldInfos[laneIndex] )
                
                msg = "Could not apply axis settings due to an exception:\n"
                msg += "{}".format( e )
                log_exception( logger, msg )
                QMessageBox.warning(self, "Error", msg)
                self._error_fields.add('Axis Order')
                return False

        finally:
            self.axesEdit.installEventFilter(self)
            # Either way, show the axes
            self._updateAxes()
            self._updateDisplayModeCombo()

    def _handleClearRangeButton(self):
        self.rangeMinSpinBox.setValue( self.rangeMinSpinBox.minimum() )
        self.rangeMaxSpinBox.setValue( self.rangeMaxSpinBox.minimum() )
        self._applyRangeToTempOps()
    
    def _applyNormalizeDisplayToTempOps(self):
        # Save a copy of our settings
        oldInfos = {}
        new_norm = {"True":True,"False":False,"Default":None}[str(self.normalizeDisplayComboBox.currentText())]        
        
        new_drange = ( self.rangeMinSpinBox.value(), self.rangeMaxSpinBox.value() )
        if new_norm is False and (new_drange[0] == self.rangeMinSpinBox.minimum() \
        or new_drange[1] == self.rangeMaxSpinBox.minimum()):
            # no drange given, autonormalization cannot be switched off !
            QMessageBox.warning(None, "Warning", "Normalization cannot be switched off without specifying the data range !")
            self.normalizeDisplayComboBox.setCurrentIndex(1)
            return 
        
        for laneIndex, op in list(self.tempOps.items()):
            oldInfos[laneIndex] = copy.copy( op.Dataset.value )

        try:
            for laneIndex, op in list(self.tempOps.items()):
                info = copy.copy( op.Dataset.value )
                info.normalizeDisplay = new_norm
                op.Dataset.setValue( info )
            self._error_fields.discard('Normalize Display')
            return True
        except Exception as e:
            # Revert everything back to the previous state
            for laneIndex, op in list(self.tempOps.items()):
                op.Dataset.setValue( oldInfos[laneIndex] )
            
            msg = "Could not apply normalization settings due to an exception:\n"
            msg += "{}".format( e )
            log_exception( logger, msg )
            QMessageBox.warning(self, "Error", msg)
            self._error_fields.add('Normalize Display')
            return False
    
    def _applyRangeToTempOps(self):
        new_drange = ( self.rangeMinSpinBox.value(), self.rangeMaxSpinBox.value() )

        if new_drange[0] == self.rangeMinSpinBox.minimum() \
        or new_drange[1] == self.rangeMaxSpinBox.minimum():
            new_drange = None

        def get_dtype_info(dtype):
            try:
                return numpy.iinfo(dtype)
            except ValueError:
                return numpy.finfo(dtype)

        try:
            # Remove the event filter while this function executes because we don't 
            #  want to trigger additional calls to this very function.
            self.rangeMinSpinBox.removeEventFilter(self)
            self.rangeMaxSpinBox.removeEventFilter(self)

            if new_drange is not None:
                if new_drange[0] >= new_drange[1]:
                    QMessageBox.warning(self, "Error", "Can't apply data range values: Data range MAX must be greater than MIN.")
                    self._error_fields.add('Data Range')
                    return False
    
                # Make sure the new bounds don't exceed the dtype range
                for laneIndex, op in list(self.tempOps.items()):
                    dtype_info = get_dtype_info(op.Image.meta.dtype)
                        
                    if new_drange[0] < dtype_info.min or new_drange[1] > dtype_info.max:
                        QMessageBox.warning(self, "Error",
                            "Can't apply data range values:\n"
                            "Range {} is outside the allowed range for the data type of lane {}.\n"
                            "(Full range of {} is [{}, {}].)".format( new_drange, laneIndex, dtype_info.dtype.name, dtype_info.min, dtype_info.max ) )
                        self._error_fields.add('Data Range')
                        return False
            
            # Save a copy of our settings
            oldInfos = {}
            for laneIndex, op in list(self.tempOps.items()):
                oldInfos[laneIndex] = copy.copy( op.Dataset.value )
    
            try:
                for laneIndex, op in list(self.tempOps.items()):
                    info = copy.copy( op.Dataset.value )
                    dtype_info = get_dtype_info(op.Image.meta.dtype)
                    dtype = dtype_info.dtype.type
                    info.drange = None
                    if new_drange is not None:
                        info.drange = ( dtype(new_drange[0]), dtype(new_drange[1]) )
                    op.Dataset.setValue( info )
                self._error_fields.discard('Data Range')
                return True
            except Exception as e:
                # Revert everything back to the previous state
                for laneIndex, op in list(self.tempOps.items()):
                    op.Dataset.setValue( oldInfos[laneIndex] )
                
                msg = "Could not apply data range settings due to an exception:\n"
                msg += "{}".format( e )
                log_exception( logger, msg )
                QMessageBox.warning(self, "Error", msg)
                self._error_fields.add('Data Range')
                return False

        finally:
            self.rangeMinSpinBox.installEventFilter(self)
            self.rangeMaxSpinBox.installEventFilter(self)
            # Either way, show the current data range
            self._updateRange()

    def _initInternalDatasetNameCombo(self):
        # If any dataset is either (1) not hdf5 or (2) project-internal, then we can't change the internal path.
        h5Exts = ['.ilp', '.h5', '.hdf5']
        for laneIndex in self._laneIndexes:
            tmpOp = self.tempOps[laneIndex]
            datasetInfo = tmpOp.Dataset.value
            externalPath = PathComponents( datasetInfo.filePath ).externalPath
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
        # Open the file as a read-only so we can get a list of the internal paths
        with h5py.File(absPath, 'r') as f:
            # Define a closure to collect all of the dataset names in the file.
            def accumulateDatasetPaths(name, val):
                if type(val) == h5py._hl.dataset.Dataset and 3 <= len(val.shape) <= 5:
                    datasetNames.append( '/' + name )
            # Visit every group/dataset in the file
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
        if index == -1:
            return
        
        newInternalPath = str( self.internalDatasetNameComboBox.currentText() )
        
        # Save a copy of our settings
        oldInfos = {}
        for laneIndex, op in list(self.tempOps.items()):
            oldInfos[laneIndex] = copy.copy( op.Dataset.value )
        
        # Attempt to apply to all temp operators
        try:
            for laneIndex, op in list(self.tempOps.items()):
                info = copy.copy( op.Dataset.value )
                pathComponents = PathComponents(info.filePath)
                if pathComponents.internalPath != newInternalPath:
                    pathComponents.internalPath = newInternalPath
                    info.filePath = pathComponents.totalPath()
                    op.Dataset.setValue( info )
            self._error_fields.discard('Internal Dataset Name')
            return True
        except Exception as e:
            # Revert everything back to the previous state
            for laneIndex, op in list(self.tempOps.items()):
                op.Dataset.setValue( oldInfos[laneIndex] )
            
            msg = "Could not set new internal path settings due to an exception:\n"
            msg += "{}".format( e )
            log_exception( logger, msg )
            QMessageBox.warning(self, "Error", msg)
            self._error_fields.add('Internal Dataset Name')
            return False
        
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
        if index == -1:
            return
        
        newStorageLocation = self.storageComboBox.itemData( index )
        
        # Save a copy of our settings
        oldInfos = {}
        for laneIndex, op in list(self.tempOps.items()):
            oldInfos[laneIndex] = copy.copy( op.Dataset.value )
        
        # Attempt to apply to all temp operators
        try:
            for laneIndex, op in list(self.tempOps.items()):
                info = copy.copy( op.Dataset.value )
                
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
        
        except Exception as e:
            # Revert everything back to the previous state
            for laneIndex, op in list(self.tempOps.items()):
                op.Dataset.setValue( oldInfos[laneIndex] )
            
            msg = "Could not set new storage location settings due to an exception:\n"
            msg += "{}".format( e )
            log_exception( logger, msg )
            QMessageBox.warning(self, "Error", msg)
            self._error_fields.add('Storage Location')
            return False
        
        finally:
            self._updateStorageCombo()
        
    def _initDisplayModeCombo(self):
        self.displayModeComboBox.addItem("Default", userData="default")
        self.displayModeComboBox.addItem("Grayscale", userData="grayscale")
        self.displayModeComboBox.addItem("RGBA", userData="rgba")
        self.displayModeComboBox.addItem("Random Colortable", userData="random-colortable")
        self.displayModeComboBox.addItem("Alpha Modulated", userData="alpha-modulated")
        self.displayModeComboBox.addItem("Binary Mask", userData="binary-mask")
    
    def _initNormalizeDisplayCombo(self):
        self.normalizeDisplayComboBox.addItem("Default", userData="default")
        self.normalizeDisplayComboBox.addItem("True", userData="True")
        self.normalizeDisplayComboBox.addItem("False", userData="False")
        self.normalizeDisplayComboBox.setCurrentIndex(1)
        
    def _updateDisplayModeCombo(self):
        # If all lanes have the same mode, then show it.
        # Otherwise, show nothing.
        mode = None
        for laneIndex, op in list(self.tempOps.items()):
            cmp_mode = op.Image.meta.display_mode or "default"
            mode = mode or cmp_mode
            if mode != cmp_mode:
                # Mismatch.  No common mode for all lanes.
                mode = None
                break

        if mode is None:
            self.displayModeComboBox.setCurrentIndex(-1)
        else:
            index = self.displayModeComboBox.findData( mode )
            self.displayModeComboBox.setCurrentIndex(index)


    def _applyDisplayModeToTempOps(self, index):
        if index == -1:
            return
        
        newDisplayMode = str( self.displayModeComboBox.itemData( index ) )
        
        # Save a copy of our settings
        oldInfos = {}
        for laneIndex, op in list(self.tempOps.items()):
            oldInfos[laneIndex] = copy.copy( op.Dataset.value )
        
        # Attempt to apply to all temp operators
        try:
            for laneIndex, op in list(self.tempOps.items()):
                info = copy.copy( op.Dataset.value )
                if info.display_mode != newDisplayMode:
                    info.display_mode = newDisplayMode
                    op.Dataset.setValue( info )
            self._error_fields.discard('Channel Display')
            return True
        
        except Exception as e:
            # Revert everything back to the previous state
            for laneIndex, op in list(self.tempOps.items()):
                op.Dataset.setValue( oldInfos[laneIndex] )
            
            msg = "Could not set new channel display settings due to an exception:\n"
            msg += "{}".format( e )
            log_exception( logger, msg )
            QMessageBox.warning(self, "Error", msg)
            self._error_fields.add('Channel Display')
            return False
        
        finally:
            self._updateDisplayModeCombo()
        

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    # Create a test data file.
    test_data_path = '/tmp/testfile.h5'
    test_project_path = '/tmp/tmp_project.ilp'
    
    def create_test_files():
        tags = vigra.defaultAxistags("zyxc")
        tags['x'].resolution = 1.0
        tags['y'].resolution = 1.0
        tags['z'].resolution = 45.0
        tags['c'].description = 'intensity'
        with h5py.File(test_data_path, 'w') as f:
            f['zeros'] = numpy.zeros( (10, 100, 200, 1), dtype=numpy.uint8 )
            f['zeros'].attrs['axistags'] = tags.toJSON()
        
        import ilastik_main
        parsed_args, workflow_cmdline_args = ilastik_main.parser.parse_known_args()
        parsed_args.new_project = test_project_path
        parsed_args.workflow = "Pixel Classification"
        parsed_args.headless = True
    
        shell = ilastik_main.main(parsed_args, workflow_cmdline_args)    
        data_selection_applet = shell.workflow.dataSelectionApplet
        
        # To configure data selection, start with empty cmdline args and manually fill them in
        data_selection_args, _ = data_selection_applet.parse_known_cmdline_args([])
        data_selection_args.raw_data = [test_data_path + '/zeros']
        
        # Configure 
        data_selection_applet.configure_operator_with_parsed_args(data_selection_args)
        
        shell.projectManager.saveProject()        
        return data_selection_applet

    def open_test_files():
        import ilastik_main
        parsed_args, workflow_cmdline_args = ilastik_main.parser.parse_known_args()
        parsed_args.project = test_project_path
        parsed_args.headless = True
    
        shell = ilastik_main.main(parsed_args, workflow_cmdline_args)    
        return shell.workflow.dataSelectionApplet

    FORCE_CREATE = False
    if not FORCE_CREATE and os.path.exists(test_data_path) and os.path.exists(test_project_path):
        data_selection_applet = open_test_files()
    else:
        data_selection_applet = create_test_files()

    app = QApplication([])
    
    dlg = DatasetInfoEditorWidget(None, data_selection_applet.topLevelOperator, 0, [0], show_axis_details=True)
    dlg.show()
    dlg.raise_()    
    app.exec_()
