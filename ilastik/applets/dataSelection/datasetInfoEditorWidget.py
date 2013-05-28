import os
import traceback
import copy

import h5py
import numpy
import vigra

from PyQt4 import uic
from PyQt4.QtCore import Qt, QEvent, QVariant, QString
from PyQt4.QtGui import QDialog, QMessageBox, QDoubleSpinBox, QApplication

from ilastik.applets.base.applet import DatasetConstraintError
from ilastik.utility import getPathVariants, PathComponents
from opDataSelection import OpDataSelection, DatasetInfo

class StorageLocation(object):
    ProjectFile = 0
    AbsoluteLink = 1
    RelativeLink = 2
    
    NumOptions = 3

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
        self._error_fields = set()

        self.okButton.clicked.connect( self.accept )
        self.cancelButton.clicked.connect( self.reject )

        self._setUpEventFilters()

        self.axesEdit.setEnabled( self._shouldEnableAxesEdit() )

        self._initInternalDatasetNameCombo()
        self.internalDatasetNameComboBox.currentIndexChanged.connect( self._applyInternalPathToTempOps )
        self._updateInternalDatasetSelection()
        
        self._initStorageCombo()
        self.storageComboBox.currentIndexChanged.connect( self._applyStorageComboToTempOps )
        self._updateStorageCombo()
        
        self._initChannelDisplayCombo()
        self.channelDisplayComboBox.currentIndexChanged.connect( self._applyChannelDescriptionToTempOps )
        self._updateChannelDisplayCombo()

        self.rangeMinSpinBox.setSpecialValueText( "--" )
        self.rangeMaxSpinBox.setSpecialValueText( "--" )
        self.rangeMinSpinBox.setValue( self.rangeMinSpinBox.minimum() )
        self.rangeMaxSpinBox.setValue( self.rangeMaxSpinBox.minimum() )
        self.clearRangeButton.clicked.connect( self._handleClearRangeButton )
        
        self._updateShape()
        self._updateDtype()
        self._updateRange()
        self._updateAxes()
        
        self._updateNickname()

    def rangeDisplay(self, box, val):
        drange = self._getCommonMetadataValue("drange")
        if drange is None:
            return QString("")
        return QDoubleSpinBox.textFromValue(box, val)

    def _setUpEventFilters(self):
        # Changes to these widgets are detected via eventFilter()
        self._autoAppliedWidgets = { self.nicknameEdit : self._applyNicknameToTempOps,
                                     self.axesEdit : self._applyAxesToTempOps,
                                     self.rangeMinSpinBox : self._applyRangeToTempOps,
                                     self.rangeMaxSpinBox : self._applyRangeToTempOps }

        for widget in self._autoAppliedWidgets.keys():
            widget.installEventFilter(self)

    def _tearDownEventFilters(self):
        for widget in self._autoAppliedWidgets.keys():
            widget.removeEventFilter(self)

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
        
        if not self._applyTempOpSettingsRealOp():
            return
        else:
            # Success.  Close the dialog.
            self._tearDownEventFilters()
            self._cleanUpTempOperators()
            super( DatasetInfoEditorWidget, self ).accept()

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
            originalInfos[laneIndex] = copy.copy( realSlot.value )

        currentLane = self._laneIndexes[0]
        try:
            for laneIndex, op in self.tempOps.items():
                info = copy.copy( op.Dataset.value )
                realSlot = self._op.DatasetGroup[laneIndex][self._roleIndex]
                realSlot.setValue( info )
            return True
        except Exception as ex:
            if isinstance(ex, DatasetConstraintError):
                msg = "Failed to apply your new settings to the workflow " \
                      "because they violate a constraint of the {} applet.\n\n".format( ex.appletName ) + \
                      ex.message
                QMessageBox.critical( self, "Unacceptable Settings", msg )
            else:
                traceback.print_exc()
                msg = "Failed to apply dialog settings due to an exception:\n"
                msg += "{}".format( ex )
                QMessageBox.critical(self, "Error", msg)
                return False

            # Revert everything back to the previous state
            for laneIndex, info in originalInfos.items():
                realSlot = self._op.DatasetGroup[laneIndex][self._roleIndex]
                realSlot.setValue( info )
                if laneIndex == currentLane:
                    # Only need to revert the lanes we actually changed.
                    # Everything else wasn't touched
                    break

    def _cleanUpTempOperators(self):
        for laneIndex, op in self.tempOps.items():
            op.cleanUp()

    def _updateNickname(self):
        firstOp = self.tempOps.values()[0]
        nickname = firstOp.Dataset.value.nickname
        for op in self.tempOps.values():
            info = op.Dataset.value
            if nickname != info.nickname:
                nickname = None
                break
        if nickname is None:
            self.nicknameEdit.setText("<multiple>")
        else:
            self.nicknameEdit.setText(nickname)

    def _applyNicknameToTempOps(self):
        newNickname = str(self.nicknameEdit.text())
        if "<multiple>" in newNickname:
            return

        try:
            # Remove the event filter while this function executes because we don't 
            #  want to trigger additional calls to this very function.
            self.nicknameEdit.removeEventFilter(self)
            
            # Save a copy of our settings
            oldInfos = {}
            for laneIndex, op in self.tempOps.items():
                oldInfos[laneIndex] = copy.copy( op.Dataset.value )
    
            currentLane = self.tempOps.keys()[0]
            try:
                for laneIndex, op in self.tempOps.items():
                    info = copy.copy( op.Dataset.value )
                    info.nickname = newNickname
                    op.Dataset.setValue( info )
                self._error_fields.discard('Nickname')
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
                msg = "Could not set new nickname due to an exception:\n"
                msg += "{}".format( e )
                QMessageBox.warning(self, "Error", msg)
                self._error_fields += 'Nickname'
                return False

        finally:
            self.nicknameEdit.installEventFilter(self)
            self._updateNickname()


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
    
    def _updateShape(self):
        firstOp = self.tempOps.values()[0]
        shape = firstOp.Image.meta.original_shape
        if shape is None:
            shape = firstOp.Image.meta.shape
        for laneIndex, op in self.tempOps.items():
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

    def _updateAxes(self):
        # If all images have the same axis keys,
        # then display it.  Otherwise, display default text.
        axiskeys = None
        for laneIndex, op in self.tempOps.items():
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
        else:
            self.axesEdit.setText( axiskeys )

    def _shouldEnableAxesEdit(self):
        # Enable IFF all datasets have the same number of axes.
        firstOp = self.tempOps.values()[0]
        original_shape = firstOp.Image.meta.original_shape
        shape = firstOp.Image.meta.shape
        if original_shape is not None:
            numaxes = len(original_shape)
        else:
            numaxes = len(shape)
        for op in self.tempOps.values():
            nextShape = op.Image.meta.original_shape
            if nextShape is None:
                nextShape = op.Image.meta.shape
            if len(nextShape) != numaxes:
                return False
        return True
    
    def _applyAxesToTempOps(self):
        newAxisOrder = str(self.axesEdit.text())
        # Check for errors
        firstOp = self.tempOps.values()[0]
        shape = firstOp.Image.meta.shape
        original_shape = firstOp.Image.meta.original_shape
        if original_shape is not None:
            numaxes = len(original_shape)
        else:
            numaxes = len(shape)

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
            for laneIndex, op in self.tempOps.items():
                oldInfos[laneIndex] = copy.copy( op.Dataset.value )
    
            currentLane = self.tempOps.keys()[0]
            try:
                for laneIndex, op in self.tempOps.items():
                    info = copy.copy( op.Dataset.value )
                    # Use new order, but keep the data from the old axis tags
                    # (for all axes that were kept)
                    newTags = vigra.defaultAxistags(newAxisOrder)
                    for tag in newTags:
                        if tag.key in op.Image.meta.getAxisKeys():
                            newTags[tag.key] = op.Image.meta.axistags[tag.key]
                        
                    info.axistags = newTags
                    op.Dataset.setValue( info )
                self._error_fields.discard('Axis Order')
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
                self._error_fields.add('Axis Order')
                return False

        finally:
            self.axesEdit.installEventFilter(self)
            # Either way, show the axes
            self._updateAxes()

    def _handleClearRangeButton(self):
        self.rangeMinSpinBox.setValue( self.rangeMinSpinBox.minimum() )
        self.rangeMaxSpinBox.setValue( self.rangeMaxSpinBox.minimum() )
        self._applyRangeToTempOps()

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
                for laneIndex, op in self.tempOps.items():
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
            for laneIndex, op in self.tempOps.items():
                oldInfos[laneIndex] = copy.copy( op.Dataset.value )
    
            currentLane = self.tempOps.keys()[0]
            try:
                for laneIndex, op in self.tempOps.items():
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
            datasetInfo = self._op.DatasetGroup[laneIndex][self._roleIndex].value
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
            datasetInfo = self._op.DatasetGroup[laneIndex][self._roleIndex].value
            
            externalPath = PathComponents( datasetInfo.filePath ).externalPath
            absPath, relPath = getPathVariants( externalPath, self._op.WorkingDirectory.value )
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
            datasetInfo = self._op.DatasetGroup[laneIndex][self._roleIndex].value
            
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
        for laneIndex, op in self.tempOps.items():
            oldInfos[laneIndex] = copy.copy( op.Dataset.value )
        
        # Attempt to apply to all temp operators
        currentLane = self.tempOps.keys()[0]
        try:
            for laneIndex, op in self.tempOps.items():
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
            for laneIndex, op in self.tempOps.items():
                op.Dataset.setValue( oldInfos[laneIndex] )
                if laneIndex == currentLane:
                    # Only need to revert the lanes we actually changed.
                    # Everything else wasn't touched
                    break
            
            traceback.print_exc()
            msg = "Could not set new internal path settings due to an exception:\n"
            msg += "{}".format( e )
            QMessageBox.warning(self, "Error", msg)
            self._error_fields.add('Internal Dataset Name')
            return False
        
    def _initStorageCombo(self):
        
        # If there's only one dataset, show the path in the combo
        showpaths = False
        if len( self._laneIndexes ) == 1:
            op = self.tempOps.values()[0]
            info = op.Dataset.value
            cwd = op.WorkingDirectory.value
            filePath = PathComponents(info.filePath).externalPath
            absPath, relPath = getPathVariants(filePath, cwd)
            showpaths = not info.fromstack

        if showpaths:
            self.storageComboBox.addItem( "Copied to Project File", userData=StorageLocation.ProjectFile )
            self.storageComboBox.addItem( "Absolute Link: " + absPath, userData=StorageLocation.AbsoluteLink )
            self.storageComboBox.addItem( "Relative Link: " + relPath, userData=StorageLocation.RelativeLink )
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
                if os.path.isabs(info.filePath):
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
            comboIndex = self.storageComboBox.findData( QVariant(sharedStorageSetting) )
            self.storageComboBox.setCurrentIndex( comboIndex )

        disableLinks = False
        for laneIndex in self._laneIndexes:
            op = self.tempOps[laneIndex]
            info = op.Dataset.value
            
            disableLinks |= info.fromstack
        
        if disableLinks:
            # If any of the files were loaded from a stack, then you can't refer to them via a link.
            absIndex = self.storageComboBox.findData( QVariant(StorageLocation.AbsoluteLink) )
            relIndex = self.storageComboBox.findData( QVariant(StorageLocation.RelativeLink) )

            # http://theworldwideinternet.blogspot.com/2011/01/disabling-qcombobox-items.html
            model = self.storageComboBox.model()
            model.setData( model.index( absIndex, 0 ), 0, Qt.UserRole-1 )
            model.setData( model.index( relIndex, 0 ), 0, Qt.UserRole-1 )

    def _applyStorageComboToTempOps(self, index):
        if index == -1:
            return
        
        newStorageLocation, goodcast = self.storageComboBox.itemData( index ).toInt()
        assert goodcast
        
        # Save a copy of our settings
        oldInfos = {}
        for laneIndex, op in self.tempOps.items():
            oldInfos[laneIndex] = copy.copy( op.Dataset.value )
        
        # Attempt to apply to all temp operators
        currentLane = self.tempOps.keys()[0]
        try:
            for laneIndex, op in self.tempOps.items():
                info = copy.copy( op.Dataset.value )
                
                if info.location == DatasetInfo.Location.ProjectInternal:
                    thisLaneStorage = StorageLocation.ProjectFile
                elif info.location == DatasetInfo.Location.FileSystem:
                    # Determine if the path is relative or absolute
                    if os.path.isabs(info.filePath):
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
                        if newStorageLocation == StorageLocation.AbsoluteLink:
                            info.filePath = absPath
                        elif newStorageLocation == StorageLocation.RelativeLink:
                            info.filePath = relPath
                        else:
                            assert False, "Unknown storage location setting."
                    op.Dataset.setValue( info )
            self._error_fields.discard('Storage Location')
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
            msg = "Could not set new storage location settings due to an exception:\n"
            msg += "{}".format( e )
            QMessageBox.warning(self, "Error", msg)
            self._error_fields.add('Storage Location')
            return False
        
        finally:
            self._updateStorageCombo()
        
    def _initChannelDisplayCombo(self):
        self.channelDisplayComboBox.addItem("Default", userData="default")
        self.channelDisplayComboBox.addItem("Grayscale", userData="grayscale")
        self.channelDisplayComboBox.addItem("RGBA", userData="rgba")

    def _updateChannelDisplayCombo(self):
        channel_description = None
        for laneIndex, op in self.tempOps.items():
            cmp_description = op.Image.meta.axistags['c'].description
            if cmp_description == "":
                cmp_description = "default"
            if channel_description is None:
                channel_description = cmp_description
            elif channel_description != cmp_description:
                channel_description = None
                break

        if channel_description is None:
            self.channelDisplayComboBox.setCurrentIndex(-1)
        else:
            index = self.channelDisplayComboBox.findData( channel_description )
            self.channelDisplayComboBox.setCurrentIndex(index)


    def _applyChannelDescriptionToTempOps(self, index):
        if index == -1:
            return
        
        newChannelDescription = str( self.channelDisplayComboBox.itemData( index ).toString() )
        
        # Save a copy of our settings
        oldInfos = {}
        for laneIndex, op in self.tempOps.items():
            oldInfos[laneIndex] = copy.copy( op.Dataset.value )
        
        # Attempt to apply to all temp operators
        currentLane = self.tempOps.keys()[0]
        try:
            for laneIndex, op in self.tempOps.items():
                info = copy.copy( op.Dataset.value )
                if info.axistags is None or info.axistags['c'].description != newChannelDescription:
                    if info.axistags is None:
                        info.axistags = op.Image.meta.axistags
                    info.axistags['c'].description = newChannelDescription
                    op.Dataset.setValue( info )
            self._error_fields.discard('Channel Display')
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
            msg = "Could not set new channel display settings due to an exception:\n"
            msg += "{}".format( e )
            QMessageBox.warning(self, "Error", msg)
            self._error_fields.add('Channel Display')
            return False
        
        finally:
            self._updateChannelDisplayCombo()
        















