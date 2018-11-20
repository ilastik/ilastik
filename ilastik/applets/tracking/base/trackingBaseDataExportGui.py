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
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QMessageBox
from PyQt5.QtGui import QColor
from ilastik.utility.exportingOperator import ExportingGui
from ilastik.plugins import pluginManager
from ilastik.applets.dataExport.dataExportGui import DataExportGui, DataExportLayerViewerGui
from ilastik.applets.tracking.base.opTrackingBaseDataExport import OpTrackingBaseDataExport
import volumina.colortables as colortables
from volumina.api import LazyflowSource, ColortableLayer


from ilastik.applets.tracking.base.pluginExportOptionsDlg import PluginExportOptionsDlg
from ilastik.applets.dataExport.opDataExport import get_model_op


import logging

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

class TrackingBaseDataExportGui( DataExportGui, ExportingGui ):
    """
    A subclass of the generic data export gui that creates custom layer viewers.
    """

    @property
    def gui_applet(self):
        return self.parentApplet

    def __init__(self, *args, **kwargs):
        super(TrackingBaseDataExportGui, self).__init__(*args, **kwargs)
        self.pluginWasSelected = False
        self._exporting_operator = None
        self._default_export_filename = None

    def get_feature_names(self):
        op = self.get_exporting_operator()
        try:
            slot = op.ComputedFeatureNamesWithDivFeatures
        except AttributeError:
            slot = op.ComputedFeatureNames
        if not slot:
            slot = op.ComputedFeatureNames
        return slot([]).wait()

    def get_exporting_operator(self, lane=0):
        return self._exporting_operator.getLane(lane)

    def set_exporting_operator(self, op):
        self._exporting_operator = op

    def get_export_dialog_title(self):
        return "Export Tracking Data"

    def get_raw_shape(self):
        return self.get_exporting_operator().RawImage.meta.shape

    def createLayerViewer(self, opLane):
        return TrackingBaseResultsViewer(self.parentApplet, opLane)

    def _includePluginOnlyOption(self):
        """
        Append Plugin-Only option to export tracking result using a plugin (without exporting volumes)
        """
        opDataExport = self.topLevelOperator
        names = opDataExport.SelectionNames.value
        if OpTrackingBaseDataExport.PluginOnlyName not in names:
            names.append(OpTrackingBaseDataExport.PluginOnlyName)
            opDataExport.SelectionNames.setValue(names)

    def _getAvailablePlugins(self):
        '''
        Checks whether any plugins are found and whether we use the hytra backend.
        Returns the list of available plugins
        '''
        try:
            import hytra
            # export plugins only available with hytra backend
            exportPlugins = pluginManager.getPluginsOfCategory('TrackingExportFormats')
            availableExportPlugins = [pluginInfo.name for pluginInfo in exportPlugins]

            return availableExportPlugins
        except ImportError:
            return []

    def _chooseSettings(self):
        if self.topLevelOperator.SelectedExportSource.value != OpTrackingBaseDataExport.PluginOnlyName:
            super(TrackingBaseDataExportGui, self)._chooseSettings()
            return
        opExportModelOp, opSubRegion = get_model_op( self.topLevelOperator )
        if opExportModelOp is None:
            QMessageBox.information( self,
                                     "Image not ready for export",
                                     "Export isn't possible yet: No images are ready for export.  "
                                     "Please configure upstream pipeline with valid settings, "
                                     "check that images were specified in the (batch) input applet and try again." )
            return

        settingsDlg = PluginExportOptionsDlg(self)
        if settingsDlg.exec_() == PluginExportOptionsDlg.Accepted:
            # Copy the settings from our 'model op' into the real op
            setting_slots = [ opExportModelOp.RegionStart,
                              opExportModelOp.RegionStop,
                              opExportModelOp.InputMin,
                              opExportModelOp.InputMax,
                              opExportModelOp.ExportMin,
                              opExportModelOp.ExportMax,
                              opExportModelOp.ExportDtype,
                              opExportModelOp.OutputAxisOrder,
                              opExportModelOp.OutputFilenameFormat,
                              opExportModelOp.OutputInternalPath,
                              opExportModelOp.OutputFormat ]

            # Disconnect the special 'transaction' slot to prevent these 
            #  settings from triggering many calls to setupOutputs.
            self.topLevelOperator.TransactionSlot.disconnect()

            for model_slot in setting_slots:
                real_inslot = getattr(self.topLevelOperator, model_slot.name)
                if model_slot.ready():
                    real_inslot.setValue( model_slot.value )
                else:
                    real_inslot.disconnect()

            # Re-connect the 'transaction' slot to apply all settings at once.
            self.topLevelOperator.TransactionSlot.setValue(True)

            # Discard the temporary model op
            opExportModelOp.cleanUp()
            opSubRegion.cleanUp()

            # Update the gui with the new export paths      
            for index, slot in enumerate(self.topLevelOperator.ExportPath):
                self.updateTableForSlot(slot)

    def _initAppletDrawerUic(self):
        # first check whether "Plugins" should be made available
        availableExportPlugins = self._getAvailablePlugins()
        if len(availableExportPlugins) > 0:
            self._includePluginOnlyOption()

        super()._initAppletDrawerUic()

        def _handleDirty(slot, roi):
            sourceName = slot.value
            selectionNames = self.topLevelOperator.SelectionNames.value
            index = selectionNames.index(sourceName)
            self.drawer.inputSelectionCombo.setCurrentIndex(index)

        self.topLevelOperator.SelectedExportSource.notifyDirty(_handleDirty)

        if len(availableExportPlugins) > 0:
            self.topLevelOperator.SelectedPlugin.setValue(availableExportPlugins[0])

            # register the "plugins" option in the parent
            self._includePluginOnlyOption()
        else:
            btn = QPushButton("Configure Table Export for Tracking+Features", clicked=self.configure_table_export)
            self.drawer.exportSettingsGroupBox.layout().addWidget(btn)
            self.topLevelOperator.SelectedPlugin.setValue(None)

    def _handleInputComboSelectionChanged( self, index ):
        '''
        Overrides the inherited method that gets called whenever the export source has changed.
        Only forwards this to the parent GUI class if the user didn't select 'Plugin' because
        then the superclass needs to configure more things.
        '''
        sourceName = self.drawer.inputSelectionCombo.currentText()
        self._onSelectedExportSourceChanged(sourceName)
        if sourceName != OpTrackingBaseDataExport.PluginOnlyName:
            super(TrackingBaseDataExportGui, self)._handleInputComboSelectionChanged(index)

    def _onSelectedExportSourceChanged(self, sourceName):
        self.topLevelOperator.SelectedExportSource.setValue(sourceName)

    def set_default_export_filename(self, filename):
        # TODO: remove once tracking is hytra-only
        self._default_export_filename = filename

    def exportResultsForSlot(self, opLane):
        if self.topLevelOperator.SelectedExportSource.value == OpTrackingBaseDataExport.PluginOnlyName and not self.pluginWasSelected:
            QMessageBox.critical(self, "Choose Export Plugin",
                                 "You did not select any export plugin. \nPlease do so by clicking 'Choose Export Image Settings'")
            return
        else:
            super(TrackingBaseDataExportGui, self).exportResultsForSlot(opLane)

    def exportAllResults(self):
        if self.topLevelOperator.SelectedExportSource.value == OpTrackingBaseDataExport.PluginOnlyName and not self.pluginWasSelected:
            QMessageBox.critical(self, "Choose Export Plugin",
                                 "You did not select any export plugin. \nPlease do so by clicking 'Choose Export Image Settings'")
            return
        else:
            super(TrackingBaseDataExportGui, self).exportAllResults()

class TrackingBaseResultsViewer(DataExportLayerViewerGui):
    
    ct = colortables.create_random_16bit()
    ct[0] = 0

    def setupLayers(self):
        layers = []

        fromDiskSlot = self.topLevelOperatorView.ImageOnDisk
        if fromDiskSlot.ready():
            exportLayer = ColortableLayer( LazyflowSource(fromDiskSlot), colorTable=self.ct )
            exportLayer.name = "Selected Output - Exported"
            exportLayer.visible = True
            layers.append(exportLayer)

        previewSlot = self.topLevelOperatorView.ImageToExport
        if previewSlot.ready():
            previewLayer = ColortableLayer( LazyflowSource(previewSlot), colorTable=self.ct )
            previewLayer.name = "Selected Output - Preview"
            previewLayer.visible = False
            layers.append(previewLayer)

        rawSlot = self.topLevelOperatorView.RawData
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot(rawSlot)
            rawLayer.name = "Raw Data"
            rawLayer.opacity = 1.0
            layers.append(rawLayer)

        return layers 

