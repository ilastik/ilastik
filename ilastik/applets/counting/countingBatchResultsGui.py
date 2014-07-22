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
from ilastik.applets.dataExport.dataExportGui import DataExportGui, DataExportLayerViewerGui
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

from ilastik.utility import bind

from lazyflow.operators import OpMultiArraySlicer2

from volumina.api import LazyflowSource,ColortableLayer 

class CountingBatchResultsGui( DataExportGui ):
    """
    A subclass of the generic Batch gui that creates custom layer viewers.
    """
    def createLayerViewer(self, opLane):
        return CountingResultsViewer(self.parentApplet, opLane)
        
class CountingResultsViewer(LayerViewerGui):
    
    def __init__(self, *args, **kwargs):
        super(CountingResultsViewer, self).__init__(*args, **kwargs)
        self.topLevelOperatorView.PmapColors.notifyDirty( bind( self.updateAllLayers ) )
        self.topLevelOperatorView.LabelNames.notifyDirty( bind( self.updateAllLayers ) )
    
    def setupLayers(self):
        layers = []
        opLane = self.topLevelOperatorView

        exportedLayers = self._initPredictionLayers(opLane.ExportedImage)
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
        rawSlot = opLane.RawImage
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
        colors = opLane.PmapColors.value
        names = opLane.LabelNames.value

        # Use a slicer to provide a separate slot for each channel layer
        #opSlicer = OpMultiArraySlicer2( parent=opLane.viewed_operator() )
        #opSlicer.Input.connect( predictionSlot )
        #opSlicer.AxisFlag.setValue('c')

        if predictionSlot.ready() :
            from volumina import colortables
            predictLayer = ColortableLayer(LazyflowSource(predictionSlot), colorTable = colortables.jet(), normalize = 'auto')
            #predictLayer = AlphaModulatedLayer( predictsrc,
            #                                    tintColor=QColor(*colors[channel]),
            #                                    range=(0.0, 1.0),
            #                                    normalize=(0.0, 1.0) )
            predictLayer.opacity = 0.25
            predictLayer.visible = True
            predictLayer.name = "Prediction"
            layers.append(predictLayer)

        return layers
