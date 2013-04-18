import os
import sys
import traceback
import copy

import numpy

from PyQt4 import uic
from PyQt4.QtCore import Qt, QEvent
from PyQt4.QtGui import QDialog, QMessageBox

from opDataSelection import OpDataSelection, DatasetInfo

class DatasetInfoEditorWidget(QDialog):
    
    def __init__(self, parent, topLevelOperator, roleIndex, laneIndexes):
        super( DatasetInfoEditorWidget, self ).__init__(parent)
        self._op = topLevelOperator
        self._roleIndex = roleIndex
        self._laneIndexes = laneIndexes

        assert len(laneIndexes) > 0

        # We instantiate our own temporary operator for every input,
        # which we will use to experiment with the user's selections
        # This way, we can read e.g. the image shape without touching the "real"
        # operator until the user hits "OK".
        self.tempOps = {}
        for laneIndex in laneIndexes:
            origOp = self._op.innerOperators[laneIndex]._opDatasets[roleIndex]
            tmpOp = OpDataSelection(graph=origOp.graph)
            tmpOp.ProjectFile.setValue( origOp.ProjectFile.value )
            tmpOp.ProjectDataGroup.setValue( origOp.ProjectDataGroup.value )
            tmpOp.WorkingDirectory.setValue( origOp.WorkingDirectory.value )
            # Assumes that the original operator already has a dataset info.
            assert origOp.Dataset.ready(), "Can't edit dataset info for lanes that aren't initialized yet."
            tmpOp.Dataset.setValue( copy.copy( origOp.Dataset.value ) )
            
            self.tempOps[laneIndex] = tmpOp
                
        self._initUi()

    def _initUi(self):
        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        uiFilePath = os.path.join( localDir, 'datasetInfoEditorWidget.ui' )
        uic.loadUi(uiFilePath, self)

        self.okButton.clicked.connect( self.accept )
        self.cancelButton.clicked.connect( self.reject )

        self._autoAppliedWidgets = { self.axesEdit : self._applyAxesToTempOps,
                                     self.rangeMinSpinBox : self._applyRangeToTempOps,
                                     self.rangeMaxSpinBox : self._applyRangeToTempOps }
        self._setUpEventFilters()

        self.axesEdit.setEnabled( self._shouldEnableAxesEdit() )
        self.internalDatasetNameComboBox.setEnabled( self._shouldEnableInternalDatasetNameComboBox() )

        self._showShape()
        self._showDtype()
        self._showRange()
        self._showAxes()

    def _setUpEventFilters(self):
        for widget in self._autoAppliedWidgets.keys():
            widget.installEventFilter(self)

    def _tearDownEventFilters(self):
        for widget in self._autoAppliedWidgets.keys():
            widget.removeEventFilter(self)

#    def event(self, event):
#        if ( event.type() == QEvent.KeyPress ): # and event.key() == Qt.Key_Enter ):
#            print "got event: {}, key: {}".format( event, event.key() )
#            return True
#        return super( DatasetInfoEditorWidget, self ).event( event )
    
    def eventFilter(self, watched, event):
        if watched in self._autoAppliedWidgets:
            if ( event.type() == QEvent.KeyPress \
                and ( event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return) ):
                self._autoAppliedWidgets[watched]()
                return True
            if ( event.type() == QEvent.FocusOut ):
                self._autoAppliedWidgets[watched]()
                return False
        return False
    
    def accept(self):
        self._tearDownEventFilters()
        super( DatasetInfoEditorWidget, self ).accept()

    def reject(self):
        self._tearDownEventFilters()
        super( DatasetInfoEditorWidget, self ).reject()

    def _getCommonMetadataValue(self, attr):
        # If this metadata attribute is common across all images,
        # return it.  Otherwise, return None.
        firstOp = self.tempOps.values()[0]
        val = firstOp.Image.meta[attr]
        for laneIndex, op in self.tempOps.items():
            if val != op.Image.meta[attr]:
                val = None
                break
        return val
    
    def _showShape(self):
        shape = self._getCommonMetadataValue("shape")
        if shape is None:
            self.shapeLabel.setText( "" )
        else:
            self.shapeLabel.setText( str(shape) )

    def _showDtype(self):
        dtype = self._getCommonMetadataValue("dtype")
        if dtype is None:
            self.dtypeLabel.setText( "" )
            return
        if isinstance(dtype, numpy.dtype):
            dtype = dtype.type
        self.dtypeLabel.setText( dtype.__name__ )

    def _showRange(self):
        drange = self._getCommonMetadataValue("drange")
        if drange is None:
            # TODO: Override QSpinBox.textFromValue() to make a special display for invalid ranges
            self.rangeMinSpinBox.setValue( 0.0 )
            self.rangeMaxSpinBox.setValue( 0.0 )
        else:
            self.rangeMinSpinBox.setValue( drange[0] )
            self.rangeMaxSpinBox.setValue( drange[1] )

    def _showAxes(self):
        # If all images have the same axis keys,
        # then display it.  Otherwise, display default text.
        axiskeys = None
        for laneIndex, op in self.tempOps.items():
            cmpkeys = "".join(op.Image.meta.getAxisKeys())
            if axiskeys is None:
                axiskeys = cmpkeys
            elif axiskeys != cmpkeys:
                axiskeys = None
                break
        if axiskeys is None:
            self.axesEdit.setText( "<multiple>" )
        else:
            self.axesEdit.setText( axiskeys )

    def _shouldEnableAxesEdit(self):
        # Enable IFF all datasets have the same number of axes.
        firstOp = self.tempOps.values()[0]
        numaxes = len(firstOp.Image.meta.shape)
        for op in self.tempOps.values():
            if len(op.Image.meta.shape) != numaxes:
                return False
        return True

    def _shouldEnableInternalDatasetNameComboBox(self):
        # Enable IFF all datasets have at least one common internal dataset
        return False
    
    def _applyAxesToTempOps(self):
        newAxisOrder = str(self.axesEdit.text())
        # Check for errors
        firstOp = self.tempOps.values()[0]
        numaxes = len(firstOp.Image.meta.shape)

        try:
            # Remove the event filter while this function executes because we don't 
            #  want to trigger additional calls to this very function.
            self.axesEdit.removeEventFilter(self)
            
            if numaxes != len( newAxisOrder ):
                QMessageBox.warning(self, "Error", "Can't use those axes: wrong number.")
                return False
            
            for c in newAxisOrder:
                if c not in 'txyzc':
                    QMessageBox.warning(self, "Error", "Can't use those axes: Don't understand axis ''.".format(c))
                    return False
    
            if len(set(newAxisOrder)) != len(newAxisOrder):
                QMessageBox.warning(self, "Error", "Axis order has repeated axes.")
                return False
    
            # Save a copy of our settings
            oldInfos = {}
            for laneIndex, op in self.tempOps.items():
                oldInfos[laneIndex] = copy.copy( op.Dataset.value )
    
            currentLane = self.tempOps.keys()[0]
            try:
                for laneIndex, op in self.tempOps.items():
                    info = copy.copy( op.Dataset.value )
                    info.axisorder = newAxisOrder
                    op.Dataset.setValue( info )
                return True
            except Exception as e:
                # Revert everything back to the previous state
                for laneIndex, op in self.tempOps.items():
                    op.Dataset.setValue( oldInfos[laneIndex] )
                    if laneIndex == currentLane:
                        # Only need to revert the lanes we actually changed.
                        # Everything else wasn't touched
                        break
                
                traceback.print_exc()
                msg = "Could not apply axis settings due to an exception:\n"
                msg += "{}".format( e )
                QMessageBox.warning(self, "Error", msg)
                return False

        finally:
            self.axesEdit.installEventFilter(self)
            # Either way, show the axes
            self._showAxes()

    def _applyRangeToTempOps(self):
        new_drange = ( self.rangeMinSpinBox.value(), self.rangeMaxSpinBox.value() )

        try:
            # Remove the event filter while this function executes because we don't 
            #  want to trigger additional calls to this very function.
            self.rangeMinSpinBox.removeEventFilter(self)
            self.rangeMaxSpinBox.removeEventFilter(self)
            
            if new_drange[0] >= new_drange[1]:
                QMessageBox.warning(self, "Error", "Can't apply data range values: Data range MAX must be greater than MIN.")
                return False

            # Make sure the new bounds don't exceed the dtype range
            for laneIndex, op in self.tempOps.items():
                dtype_info = numpy.iinfo(op.Image.meta.dtype)
                if new_drange[0] < dtype_info.min or new_drange[1] > dtype_info.max:
                    QMessageBox.warning(self, "Error",
                        "Can't apply data range values:\n"
                        "Range {} is outside the allowed range for the data type of lane {}.\n"
                        "(Full range of {} is [{}, {}].)".format( new_drange, laneIndex, dtype_info.dtype.name, dtype_info.min, dtype_info.max ) )
                    return False
            
            # Save a copy of our settings
            oldInfos = {}
            for laneIndex, op in self.tempOps.items():
                oldInfos[laneIndex] = copy.copy( op.Dataset.value )
    
            currentLane = self.tempOps.keys()[0]
            try:
                for laneIndex, op in self.tempOps.items():
                    info = copy.copy( op.Dataset.value )
                    dtype_info = numpy.iinfo(op.Image.meta.dtype)
                    dtype = dtype_info.dtype.type
                    info.drange = ( dtype(new_drange[0]), dtype(new_drange[1]) )
                    op.Dataset.setValue( info )
                return True
            except Exception as e:
                # Revert everything back to the previous state
                for laneIndex, op in self.tempOps.items():
                    op.Dataset.setValue( oldInfos[laneIndex] )
                    if laneIndex == currentLane:
                        # Only need to revert the lanes we actually changed.
                        # Everything else wasn't touched
                        break
                
                traceback.print_exc()
                msg = "Could not apply data range settings due to an exception:\n"
                msg += "{}".format( e )
                QMessageBox.warning(self, "Error", msg)
                return False

        finally:
            self.rangeMinSpinBox.installEventFilter(self)
            self.rangeMaxSpinBox.installEventFilter(self)
            # Either way, show the current data range
            self._showRange()






