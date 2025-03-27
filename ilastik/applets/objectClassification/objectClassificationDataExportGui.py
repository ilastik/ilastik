###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2025, the ilastik developers
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
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QColor
import os
from PyQt5.QtWidgets import QFileDialog


from ilastik.applets.objectClassification.opObjectClassification import TableExporter
from volumina.api import createDataSource, ColortableLayer, AlphaModulatedLayer
from volumina import colortables
from ilastik.applets.dataExport.dataExportGui import DataExportGui, DataExportLayerViewerGui
from lazyflow.operators import OpMultiArraySlicer2
from ilastik.utility.exportingOperator import ExportingGui


class ObjectClassificationDataExportGui(DataExportGui, ExportingGui):
    """
    A subclass of the generic data export gui that creates custom layer viewers.
    """

    def __init__(self, *args, table_exporter: TableExporter, **kwargs):
        super(ObjectClassificationDataExportGui, self).__init__(*args, **kwargs)
        self._exporting_operator: TableExporter = table_exporter

    def get_exporting_operator(self, lane: int = 0):
        return self._exporting_operator

    def createLayerViewer(self, opLane):
        return ObjectClassificationResultsViewer(self.parentApplet, opLane)

    def get_export_dialog_title(self):
        return "Export Object Information"

    def get_gui_applet(self):
        return self.parentApplet

    def get_table_export_settings(self):
        return self._exporting_operator.get_table_export_settings()

    def get_raw_shape(self):
        return self._exporting_operator.get_raw_shape()

    def get_feature_names(self):
        return self._exporting_operator.get_feature_names()

    def _initAppletDrawerUic(self):
        super(ObjectClassificationDataExportGui, self)._initAppletDrawerUic()
        btn = QPushButton("Configure Feature Table Export", clicked=self.configure_table_export)
        self.drawer.exportSettingsGroupBox.layout().addWidget(btn)
    


    def configure_table_export(self):
        try:
            input_path = self.topLevelOperatorView.InputImageName.value
            base, ext = os.path.splitext(input_path)
            default_filename = f"{base}_features{ext}"
        except Exception:
            default_filename = ""

        file_path, _filter = QFileDialog.getSaveFileName(
            parent=self,
            caption="Export Feature Table",
            directory=default_filename,
        )

        if file_path:
            self._exporting_operator.OutputFilenameFormat.setValue(file_path)



class ObjectClassificationResultsViewer(DataExportLayerViewerGui):

    _colorTable16 = colortables.default16_new

    def setupLayers(self):
        layers = []

        opLane = self.topLevelOperatorView

        selection_names = opLane.SelectionNames.value
        selection = selection_names[opLane.InputSelection.value]

        # This code is written to handle the specific output cases we know about.
        # If those change, update this function!
        assert selection in [
            "Object Predictions",
            "Object Probabilities",
            "Blockwise Object Predictions",
            "Blockwise Object Probabilities",
            "Object Identities",
            "Pixel Probabilities",  # for Pixel + Object Classification Workflow
            "Simple Segmentation",  # for Pixel + Object Classification Workflow
        ]

        if selection in ("Object Predictions", "Blockwise Object Predictions", "Simple Segmentation"):
            previewSlot = self.topLevelOperatorView.ImageToExport
            if previewSlot.ready():
                previewLayer = ColortableLayer(createDataSource(previewSlot), colorTable=self._colorTable16)
                previewLayer.name = selection + "- Preview"
                previewLayer.visible = False
                layers.append(previewLayer)

        elif selection in ("Object Probabilities", "Blockwise Object Probabilities"):
            previewLayers = self._initPredictionLayers(opLane.ImageToExport)
            for layer in previewLayers:
                layer.visible = False
                layer.name = layer.name + "- Preview"
            layers += previewLayers

        elif selection == "Pixel Probabilities":
            previewLayers = self._initPredictionLayers(opLane.ImageToExport)
            for layer in previewLayers:
                layer.visible = False
                layer.name = layer.name + "- Preview"
            layers += previewLayers
        elif selection == "Object Identities":
            previewSlot = self.topLevelOperatorView.ImageToExport
            layer = self._initColortableLayer(previewSlot)
            layers.append(layer)
        else:
            assert False, "Unknown selection."

        rawSlot = self.topLevelOperatorView.RawData
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot(rawSlot)
            rawLayer.name = "Raw Data"
            rawLayer.opacity = 1.0
            layers.append(rawLayer)

        return layers

    def _initPredictionLayers(self, predictionSlot):
        layers = []
        opLane = self.topLevelOperatorView

        # Use a slicer to provide a separate slot for each channel layer
        opSlicer = OpMultiArraySlicer2(parent=opLane.viewed_operator().parent)
        opSlicer.Input.connect(predictionSlot)
        opSlicer.AxisFlag.setValue("c")

        for channel, channelSlot in enumerate(opSlicer.Slices):
            if channelSlot.ready():
                drange = channelSlot.meta.drange or (0.0, 1.0)
                predictsrc = createDataSource(channelSlot)
                predictLayer = AlphaModulatedLayer(
                    predictsrc,
                    tintColor=QColor.fromRgba(self._colorTable16[channel + 1]),
                    normalize=drange,
                )
                predictLayer.opacity = 1.0
                predictLayer.visible = True
                predictLayer.name = "Probability Channel #{}".format(channel + 1)
                layers.append(predictLayer)

        return layers

    def _initColortableLayer(self, labelSlot):
        objectssrc = createDataSource(labelSlot)
        objectssrc.setObjectName("LabelImage LazyflowSrc")
        ct = colortables.create_default_16bit()
        ct[0] = QColor(0, 0, 0, 0).rgba()  # make 0 transparent
        layer = ColortableLayer(objectssrc, ct)
        layer.name = "Object Identities - Preview"
        layer.setToolTip("Segmented objects, shown in different colors")
        layer.visible = False
        layer.opacity = 0.5
        layer.colortableIsRandom = True
        return layer
