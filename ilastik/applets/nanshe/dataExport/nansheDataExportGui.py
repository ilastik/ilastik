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
        colors.append(QColor(0,0,0,0))

        # ilastik v0.5 colors
        colors.append( QColor( Qt.red ) )
        colors.append( QColor( Qt.green ) )
        colors.append( QColor( Qt.yellow ) )
        colors.append( QColor( Qt.blue ) )
        colors.append( QColor( Qt.magenta ) )
        colors.append( QColor( Qt.darkYellow ) )

        # Additional colors
        colors.append( QColor(255, 105, 180) ) #hot pink
        colors.append( QColor(102, 205, 170) ) #dark aquamarine
        colors.append( QColor(165,  42,  42) ) #brown
        colors.append( QColor(0, 0, 128) )     #navy
        colors.append( QColor(255, 165, 0) )   #orange
        colors.append( QColor(173, 255,  47) ) #green-yellow
        colors.append( QColor(128,0, 128) )    #purple
        colors.append( QColor(240, 230, 140) ) #khaki

        colors.append( QColor( Qt.cyan ) )

        colors = [c.rgba() for c in colors]

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
        exportedDataSlot = opLane.ImageOnDisk
        if exportedDataSlot.ready():
            # exportLayer = self.createStandardLayerFromSlot( exportedDataSlot )
            exportLayer = ColortableLayer( LazyflowSource(exportedDataSlot), colorTable=NansheDataExportLayerViewerGui.colorTableList() )
            exportLayer.name = "Exported Image (from disk)"
            exportLayer.visible = True
            exportLayer.opacity = 1.0
            layers.append(exportLayer)

        # Show the (live-updated) data we're exporting
        previewSlot = opLane.ImageToExport
        if previewSlot.ready():
            previewLayer = ColortableLayer( LazyflowSource(previewSlot), colorTable=NansheDataExportLayerViewerGui.colorTableList() )
            previewLayer.name = "Live Preview"
            previewLayer.visible = False # off by default
            previewLayer.opacity = 1.0
            layers.append(previewLayer)

        rawSlot = opLane.FormattedRawData
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot( rawSlot )
            rawLayer.name = "Raw Data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append(rawLayer)

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

        return layers
