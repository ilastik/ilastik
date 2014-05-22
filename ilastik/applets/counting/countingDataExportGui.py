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
from PyQt4.QtGui import QColor

from lazyflow.operators.generic import OpMultiArraySlicer2

from volumina.api import LazyflowSource, ColortableLayer
from volumina import colortables
from countingGui import countingColorTable

from ilastik.utility import bind
from ilastik.applets.dataExport.dataExportGui import DataExportGui, DataExportLayerViewerGui

class CountingDataExportGui( DataExportGui ):
    """
    A subclass of the generic data export gui that creates custom layer viewers.
    """
    def createLayerViewer(self, opLane):
        return CountingResultsViewer(self.parentApplet, opLane)
        
class CountingResultsViewer(DataExportLayerViewerGui):
    
    def __init__(self, *args, **kwargs):
        super(CountingResultsViewer, self).__init__(*args, **kwargs)
        self.topLevelOperatorView.PmapColors.notifyDirty( bind( self.updateAllLayers ) )
        self.topLevelOperatorView.LabelNames.notifyDirty( bind( self.updateAllLayers ) )
        self.topLevelOperatorView.UpperBound.notifyDirty( bind( self.updateAllLayers ) )
    
    def setupLayers(self):
        layers = []
        opLane = self.topLevelOperatorView

        exportedLayers = self._initPredictionLayers(opLane.ImageOnDisk)
        for layer in exportedLayers:
            layer.visible = True
            layer.name = layer.name + "- Exported"
        layers += exportedLayers
        
        previewLayers = self._initPredictionLayers(opLane.ImageToExport)
        for layer in previewLayers:
            layer.visible = False
            layer.name = layer.name + "- Preview"
        layers += previewLayers
        
        # If available, also show the raw data layer
        rawSlot = opLane.FormattedRawData
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot( rawSlot )
            rawLayer.name = "Raw Data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append( rawLayer )

        return layers 

    def _initPredictionLayers(self, predictionSlot):
        layers = []

        opLane = self.topLevelOperatorView
        if predictionSlot.ready() and self.topLevelOperatorView.UpperBound.ready():
            upperBound = self.topLevelOperatorView.UpperBound.value
            layer = ColortableLayer(LazyflowSource(predictionSlot), colorTable = countingColorTable, normalize =
                               (0,upperBound))
            layer.name = "Density"
            layers.append(layer)

    

#    def _initPredictionLayers(self, predictionSlot):
#        layers = []
#
#        opLane = self.topLevelOperatorView
#        colors = opLane.PmapColors.value
#        names = opLane.LabelNames.value
#
#        # Use a slicer to provide a separate slot for each channel layer
#        opSlicer = OpMultiArraySlicer2( parent=opLane.viewed_operator() )
#        opSlicer.Input.connect( predictionSlot )
#        opSlicer.AxisFlag.setValue('c')
#
#        for channel, channelSlot in enumerate(opSlicer.Slices):
#            if channelSlot.ready() and channel < len(colors) and channel < len(names):
#                drange = channelSlot.meta.drange or (0.0, 1.0)
#                predictsrc = LazyflowSource(channelSlot)
#                predictLayer = AlphaModulatedLayer( predictsrc,
#                                                    tintColor=QColor(*colors[channel]),
#                                                    # FIXME: This is weird.  Why are range and normalize both set to the same thing?
#                                                    range=drange,
#                                                    normalize=drange )
#                predictLayer.opacity = 0.25
#                predictLayer.visible = True
#                predictLayer.name = names[channel]
#                layers.append(predictLayer)

        return layers
