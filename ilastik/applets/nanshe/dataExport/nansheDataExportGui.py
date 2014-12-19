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
__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Nov 12, 2014 13:41:31 EST$"



import PyQt4
from PyQt4 import uic, QtCore
from PyQt4.QtGui import QColor
from PyQt4.QtCore import Qt

from ilastik.applets.dataExport.dataExportGui import DataExportGui, DataExportLayerViewerGui

from volumina.api import LazyflowSource, ColortableLayer

import matplotlib
import matplotlib.colors
import matplotlib.cm

import nanshe
import nanshe.additional_generators


class NansheDataExportGui(DataExportGui):
    def createLayerViewer(self, opLane):
        return NansheDataExportLayerViewerGui(self.parentApplet, opLane)


class NansheDataExportLayerViewerGui(DataExportLayerViewerGui):
    """
    Subclass the default LayerViewerGui implementation so we can provide a custom layer order.
    """

    @staticmethod
    def colorTableList():
        colors = []

        # Transparent for the zero label
        colors.append((0,0,0,0))

        rgba_color_values = list(nanshe.additional_generators.splitting_xrange(256))

        for _ in rgba_color_values:
            a_rgba_color = tuple()
            for __ in matplotlib.colors.ColorConverter().to_rgba(matplotlib.cm.gist_rainbow(_)):
                 a_rgba_color += ( int(round(255*__)), )

            colors.append(a_rgba_color)

        colors = [QColor(*c).rgba() for c in colors]

        return(colors)

    def determineDatashape(self):
        """Overridden from DataExportGui"""

        shape = None
        if self.topLevelOperatorView.RawData.ready():
            shape = self.getVoluminaShapeForSlot(self.topLevelOperatorView.RawData)

        return shape

    def setupLayers(self):
        layers = []

        # Show the exported data on disk
        opLane = self.topLevelOperatorView
        exportedDataSlot = opLane.ImageOnDiskColorized
        if exportedDataSlot.ready():
            exportLayer = self.createStandardLayerFromSlot( exportedDataSlot, lastChannelIsAlpha=True )
            exportLayer.name = "Exported Image (from disk)"
            exportLayer.visible = True
            exportLayer.opacity = 1.0
            layers.append(exportLayer)

        # Show the (live-updated) data we're exporting
        previewSlot = opLane.ImageToExportColorized
        if previewSlot.ready():
            previewLayer = self.createStandardLayerFromSlot( previewSlot, lastChannelIsAlpha=True )
            previewLayer.name = "Live Preview"
            previewLayer.visible = False # off by default
            previewLayer.opacity = 1.0
            layers.append(previewLayer)

        maxSlot = opLane.FormattedMaxProjection
        if maxSlot.ready():
            maxLayer = self.createStandardLayerFromSlot( maxSlot )
            maxLayer.name = "Raw Data Max"
            maxLayer.visible = True
            maxLayer.opacity = 1.0
            layers.append(maxLayer)

        meanSlot = opLane.FormattedMeanProjection
        if meanSlot.ready():
            meanLayer = self.createStandardLayerFromSlot( meanSlot )
            meanLayer.name = "Raw Data Mean"
            meanLayer.visible = True
            meanLayer.opacity = 1.0
            layers.append(meanLayer)

        rawSlot = opLane.RawData
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot( rawSlot )
            rawLayer.name = "Raw Data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append(rawLayer)

        return layers
