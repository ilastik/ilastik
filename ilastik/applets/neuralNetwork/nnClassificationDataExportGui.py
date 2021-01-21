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
# 		   http://ilastik.org/license.html
###############################################################################

from lazyflow.operators.generic import OpMultiArraySlicer2
from volumina.api import LazyflowSource, AlphaModulatedLayer, ColortableLayer
from ilastik.utility import bind
from ilastik.applets.dataExport.dataExportGui import DataExportGui, DataExportLayerViewerGui

from PyQt5.QtGui import QColor


class NNClassificationDataExportGui(DataExportGui):
    """
    A subclass of the generic data export gui that creates custom layer viewers.
    """

    def createLayerViewer(self, opLane):
        return NNClassificationResultsViewer(self.parentApplet, opLane)


class NNClassificationResultsViewer(DataExportLayerViewerGui):
    """
    SubClass for the DataExport viewerGui to show the layers correctly
    """

    def __init__(self, *args, **kwargs):
        super(NNClassificationResultsViewer, self).__init__(*args, **kwargs)
        self.topLevelOperatorView.PmapColors.notifyDirty(bind(self.updateAllLayers))
        self.topLevelOperatorView.LabelNames.notifyDirty(bind(self.updateAllLayers))

    def setupLayers(self):
        layers = []
        opLane = self.topLevelOperatorView

        # This code depends on a specific order for the export slots.
        # If those change, update this function!
        selection_names = opLane.SelectionNames.value

        # see comment above
        for name, expected in zip(selection_names[0:1], ["Probabilities", "Labels"]):
            assert name.startswith(expected), "The Selection Names don't match the expected selection names."

        selection = selection_names[opLane.InputSelection.value]

        if selection.startswith("Probabilities"):
            exportedLayers = self._initPredictionLayers(opLane.ImageToExport)
            for layer in exportedLayers:
                layer.visible = True
                layer.name = layer.name + "- Exported"
            layers += exportedLayers
        elif selection.startswith("Labels"):
            exportedLayer = self._initColortablelayer(opLane.ImageOnDisk)
            if exportedLayer:
                exportedLayer.visible = True
                exportedLayer.name = selection + " - Exported"
                layers.append(exportedLayer)

            previewLayer = self._initColortablelayer(opLane.ImageToExport)
            if previewLayer:
                previewLayer.visible = False
                previewLayer.name = selection + " - Preview"
                layers.append(previewLayer)

        # If available, also show the raw data layer
        rawSlot = opLane.FormattedRawData
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot(rawSlot)
            rawLayer.name = "Raw Data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append(rawLayer)

        return layers

    def _initColortablelayer(self, labelSlot):
        """
        Used to export labels
        """
        if not labelSlot.ready():
            return None

        opLane = self.topLevelOperatorView
        colors = opLane.PmapColors.value
        colortable = []
        colortable.append(QColor(0, 0, 0, 0).rgba())  # transparent
        for color in colors:
            colortable.append(QColor(*color).rgba())
        labelsrc = LazyflowSource(labelSlot)
        labellayer = ColortableLayer(labelsrc, colortable)
        return labellayer

    def _initPredictionLayers(self, predictionSlot):
        opLane = self.topLevelOperatorView
        if not opLane.LabelNames.ready() or not opLane.PmapColors.ready():
            return []

        layers = []
        colors = opLane.PmapColors.value
        names = opLane.LabelNames.value

        if predictionSlot.ready():
            if "c" in predictionSlot.meta.getAxisKeys():
                num_channels = predictionSlot.meta.getTaggedShape()["c"]
            else:
                num_channels = 1
            if num_channels != len(names) or num_channels != len(colors):
                names = ["Label {}".format(n) for n in range(1, num_channels + 1)]
                colors = num_channels * [(0, 0, 0)]  # it doesn't matter, if the pmaps color is not known,
                # we are either initializing and it will be rewritten or
                # something is very wrong elsewhere

        # Use a slicer to provide a separate slot for each channel layer
        opSlicer = OpMultiArraySlicer2(parent=opLane.viewed_operator().parent)
        opSlicer.Input.connect(predictionSlot)
        opSlicer.AxisFlag.setValue("c")

        for channel, channelSlot in enumerate(opSlicer.Slices):
            if channelSlot.ready() and channel < len(colors) and channel < len(names):
                drange = channelSlot.meta.drange or (0.0, 1.0)
                predictsrc = LazyflowSource(channelSlot)
                predictLayer = AlphaModulatedLayer(predictsrc, tintColor=QColor(*colors[channel]), normalize=drange)
                predictLayer.opacity = 0.25
                predictLayer.visible = True
                predictLayer.name = names[channel]
                layers.append(predictLayer)

        return layers
