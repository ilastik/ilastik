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
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QFrame, QPushButton, QHBoxLayout, QComboBox, QLabel
from ilastik.utility.exportingOperator import ExportingGui
from ilastik.plugins import pluginManager
from ilastik.applets.dataExport.dataExportGui import DataExportGui, DataExportLayerViewerGui

import volumina.colortables as colortables
from volumina.api import LazyflowSource, ColortableLayer

import os
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
        if opDataExport.PluginOnlyName.value not in names:
            names.append(opDataExport.PluginOnlyName.value)
            opDataExport.SelectionNames.setValue(names)
        logger.info("New available names are: {}".format(names))

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

    def _initAppletDrawerUic(self):
        # first check whether "Plugins" should be made available
        availableExportPlugins = self._getAvailablePlugins()
        if len(availableExportPlugins) > 0:
            self._includePluginOnlyOption()

        super(TrackingBaseDataExportGui, self)._initAppletDrawerUic()
        btn = QPushButton("Configure Table Export for Tracking+Features", clicked=self.configure_table_export)
        self.drawer.exportSettingsGroupBox.layout().addWidget(btn)

        if len(availableExportPlugins) > 0:
            self.topLevelOperator.SelectedPlugin.setValue(availableExportPlugins[0])

            # register the "plugins" option in the parent
            self._includePluginOnlyOption()

            frame = QFrame(parent=self)
            horizontalBoxLayout = QHBoxLayout()
            frame.setLayout(horizontalBoxLayout)

            self.label = QLabel("Plugin:")

            self.pluginDropdown = QComboBox()
            self.pluginDropdown.addItems(availableExportPlugins)
            self.pluginDropdown.currentIndexChanged[str].connect(self._onSelectedExportPluginChanged)
            horizontalBoxLayout.addWidget(self.label)
            horizontalBoxLayout.addWidget(self.pluginDropdown)

            # add new widgets to drawer
            self.drawer.exportSettingsGroupBox.layout().addWidget(frame)
            self._onSelectedExportSourceChanged(self.drawer.inputSelectionCombo.currentText())
        else:
            self.topLevelOperator.SelectedPlugin.setValue(None)

    def _handleInputComboSelectionChanged( self, index ):
        sourceName = self.drawer.inputSelectionCombo.currentText()
        self._onSelectedExportSourceChanged(sourceName)
        if sourceName != OpTrackingBaseDataExport.PluginOnlyName:
            super(TrackingBaseDataExportGui, self)._handleInputComboSelectionChanged(index)

    def _onSelectedExportSourceChanged(self, sourceName):
        self.selectedExportSource = sourceName
        if sourceName == 'Plugin':
            self.label.setEnabled(True)
            self.pluginDropdown.setEnabled(True)
        else:
            self.label.setEnabled(False)
            self.pluginDropdown.setEnabled(False)

    def _onSelectedExportPluginChanged(self, pluginText):
        self.topLevelOperator.SelectedPlugin.setValue(pluginText)

    def set_default_export_filename(self, filename):
        self._default_export_filename = filename

    # override this ExportingOperator function so that we can pass the default filename
    def show_export_dialog(self):
        """
        Shows the ExportObjectInfoDialog and calls the operators export_object_data method
        """
        # Late imports here, so we don't accidentally import PyQt during headless mode.
        from ilastik.widgets.exportObjectInfoDialog import ExportObjectInfoDialog
        
        dimensions = self.get_raw_shape()
        feature_names = self.get_feature_names()        

        op = self.get_exporting_operator()
        settings, selected_features = op.get_table_export_settings()
                
        dialog = ExportObjectInfoDialog(dimensions, 
                                        feature_names,
                                        selected_features=selected_features, 
                                        title=self.get_export_dialog_title(), 
                                        filename=self._default_export_filename)
        if not dialog.exec_():
            return (None, None)

        settings = dialog.settings()
        selected_features = list(dialog.checked_features()) # returns a generator, but that's inconvenient because it can't be serialized.
        return settings, selected_features

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

