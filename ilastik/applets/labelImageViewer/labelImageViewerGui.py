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
from PyQt5.QtGui import QColor

from lazyflow.operators import OpMultiArraySlicer2
from volumina.api import LazyflowSource, ColortableLayer
from volumina import colortables
from ilastik.utility import bind
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

class LabelImageViewerGui( LayerViewerGui ):
    
    def __init__(self, *args, **kwargs):
        super(LabelImageViewerGui, self).__init__(*args, **kwargs)
        self._colorTable16 = colortables.default16_new
    
    def setupLayers(self):
        layers = []
        opLane = self.topLevelOperatorView

        labelSlot = opLane.LabelImage
        if labelSlot.ready():
            labelImageLayer = ColortableLayer( LazyflowSource(labelSlot),
                                               colorTable=self._colorTable16 )
            labelImageLayer.name = "Label Image"
            labelImageLayer.visible = True
            layers.append(labelImageLayer)
        
        # If available, also show the raw data layer
        rawSlot = opLane.RawImage
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot( rawSlot )
            rawLayer.name = "Raw Data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append( rawLayer )

        return layers

