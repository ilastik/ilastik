##############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2023, the ilastik developers
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
#          http://ilastik.org/license.html
###############################################################################

from volumina.api import AlphaModulatedLayer, ColortableLayer, LazyflowSource

from ilastik.applets.dataExport.dataExportGui import DataExportGui, DataExportLayerViewerGui
from ilastik.applets.neuralNetwork.nnClassificationDataExportGui import (
    NNClassificationDataExportGui,
    NNClassificationResultsViewer,
)
from ilastik.utility import bind
from ilastik.workflows.trainableDomainAdaptation import LocalTrainableDomainAdaptationWorkflow
from lazyflow.operators.generic import OpMultiArraySlicer2


class TdaDataExportGui(NNClassificationDataExportGui):
    """
    A subclass of the generic data export gui that creates custom layer viewers.
    """

    def createLayerViewer(self, opLane):
        return TdaResultsViewer(self.parentApplet, opLane)


class TdaResultsViewer(NNClassificationResultsViewer):
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

        export_names = LocalTrainableDomainAdaptationWorkflow.ExportNames

        # see comment above
        for name, expected in zip(selection_names[0:1], export_names.asDisplayNameList()):
            assert name.startswith(expected), "The Selection Names don't match the expected selection names."

        selection = selection_names[opLane.InputSelection.value]

        if selection.startswith(export_names.NN_PROBABILITIES.displayName) or selection.startswith(
            export_names.PROBABILITIES.displayName
        ):
            exportedLayers = self._initPredictionLayers(opLane.ImageToExport)
            for i, layer in enumerate(exportedLayers):
                layer.visible = False
                layer.name = f"{selection} {i} - Exported"
            layers += exportedLayers
        elif selection.startswith("Labels"):
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
