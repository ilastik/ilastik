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
from functools import partial
import numpy

from PyQt5.QtGui import QColor

from volumina.api import createDataSource
from volumina.layer import ColortableLayer
from volumina.utility import ShortcutManager

# ilastik
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui


class PreprocessingViewerGui(LayerViewerGui):
    def __init__(self, *args, **kwargs):
        super(PreprocessingViewerGui, self).__init__(*args, **kwargs)

    def setupLayers(self):
        layers = []
        opLane = self.topLevelOperatorView

        # Supervoxels
        watershedSlot = opLane.WatershedImage
        if watershedSlot.ready():
            colortable = []
            for i in range(256):
                r, g, b = numpy.random.randint(0, 255), numpy.random.randint(0, 255), numpy.random.randint(0, 255)
                colortable.append(QColor(r, g, b).rgba())
            watershedLayer = ColortableLayer(createDataSource(watershedSlot), colortable)
            watershedLayer.name = "Watershed"
            watershedLayer.visible = False

            watershedLayer.opacity = 0.5
            watershedLayer.colortableIsRandom = True

            layers.append(watershedLayer)

        filteredSlot = opLane.FilteredImage
        if filteredSlot.ready():
            filteredLayer = self.createStandardLayerFromSlot(filteredSlot)
            filteredLayer.name = "Filtered Data"
            filteredLayer.visible = False
            filteredLayer.opacity = 1.0
            layers.append(filteredLayer)

        overlaySlot = opLane.OverlayData
        if overlaySlot.ready():
            inputLayer = self.createStandardLayerFromSlot(overlaySlot)
            inputLayer.name = "Overlay Image"
            inputLayer.visible = False
            inputLayer.opacity = 1.0
            layers.append(inputLayer)

        inputSlot = opLane.InputData
        if inputSlot.ready():
            inputLayer = self.createStandardLayerFromSlot(inputSlot)
            inputLayer.name = "Input Data"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append(inputLayer)

            inputLayer.shortcutRegistration = (
                "i",
                ShortcutManager.ActionInfo(
                    "Preprocessing Layers",
                    "Bring Input To Top/Bottom",
                    "Bring Input To Top/Bottom",
                    partial(self.layerstack.toggleTopToBottom, inputLayer),
                    self.viewerControlWidget(),
                    inputLayer,
                ),
            )

        return layers
