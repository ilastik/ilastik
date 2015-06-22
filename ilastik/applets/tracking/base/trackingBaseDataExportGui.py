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
from PyQt4.QtGui import QColor
from ilastik.utility.exportingOperator import ExportingGui
import volumina.colortables as colortables

from volumina.api import LazyflowSource, ColortableLayer
from ilastik.applets.dataExport.dataExportGui import DataExportGui, DataExportLayerViewerGui


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

    def get_feature_names(self):
        op = self.get_exporting_operator()
        try:
            slot = op.ComputedFeatureNamesWithDivFeatures
        except AttributeError:
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

    def _initAppletDrawerUic(self):
        super(TrackingBaseDataExportGui, self)._initAppletDrawerUic()

        from PyQt4.QtGui import QGroupBox, QPushButton, QVBoxLayout
        group = QGroupBox("Export Object Feature and Tracking Table", self.drawer)
        group.setLayout(QVBoxLayout())
        self.drawer.layout().addWidget(group)

        btn = QPushButton("Configure and export", group)
        btn.clicked.connect(self.show_export_dialog)
        group.layout().addWidget(btn)
        

class TrackingBaseResultsViewer(DataExportLayerViewerGui):
    
    ct = colortables.create_random_16bit()
    ct[0] = QColor(0,0,0,255)
    
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

