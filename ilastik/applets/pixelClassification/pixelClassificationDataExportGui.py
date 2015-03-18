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

from volumina.api import LazyflowSource, AlphaModulatedLayer, ColortableLayer

from ilastik.utility import bind
from ilastik.applets.dataExport.dataExportGui import DataExportGui, DataExportLayerViewerGui

class PixelClassificationDataExportGui( DataExportGui ):
    """
    A subclass of the generic data export gui that creates custom layer viewers.
    """
    def createLayerViewer(self, opLane):
        return PixelClassificationResultsViewer(self.parentApplet, opLane)
        
class PixelClassificationResultsViewer(DataExportLayerViewerGui):
    
    def __init__(self, *args, **kwargs):
        super(PixelClassificationResultsViewer, self).__init__(*args, **kwargs)
        self.topLevelOperatorView.PmapColors.notifyDirty( bind( self.updateAllLayers ) )
        self.topLevelOperatorView.LabelNames.notifyDirty( bind( self.updateAllLayers ) )
    
    def setupLayers(self):
        layers = []
        opLane = self.topLevelOperatorView

        # This code depends on a specific order for the export slots.
        # If those change, update this function!
        selection_names = opLane.SelectionNames.value
        assert selection_names == ['Probabilities', 'Simple Segmentation', 'Uncertainty', 'Features'] # see comment above
        
        selection = selection_names[ opLane.InputSelection.value ]

        if selection == 'Probabilities':
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
        elif selection == "Simple Segmentation":
            exportedLayer = self._initSegmentationlayer(opLane.ImageOnDisk)
            if exportedLayer:
                exportedLayer.visible = True
                exportedLayer.name = exportedLayer.name + " - Exported"
                layers.append( exportedLayer )

            previewLayer = self._initSegmentationlayer(opLane.ImageToExport)
            if previewLayer:
                previewLayer.visible = False
                previewLayer.name = previewLayer.name + " - Preview"
                layers.append( previewLayer )
        elif selection == "Uncertainty":
            if opLane.ImageToExport.ready():
                previewUncertaintySource = LazyflowSource(opLane.ImageToExport)
                previewLayer = AlphaModulatedLayer( previewUncertaintySource,
                                                    tintColor=QColor(0,255,255), # cyan
                                                    range=(0.0, 1.0),
                                                    normalize=(0.0,1.0) )
                previewLayer.opacity = 0.5
                previewLayer.visible = False
                previewLayer.name = "Uncertainty - Preview"
                layers.append(previewLayer)
            if opLane.ImageOnDisk.ready():
                exportedUncertaintySource = LazyflowSource(opLane.ImageOnDisk)
                exportedLayer = AlphaModulatedLayer( exportedUncertaintySource,
                                                     tintColor=QColor(0,255,255), # cyan
                                                     range=(0.0, 1.0),
                                                     normalize=(0.0,1.0) )
                exportedLayer.opacity = 0.5
                exportedLayer.visible = True
                exportedLayer.name = "Uncertainty - Exported"
                layers.append(exportedLayer)
        elif selection == "Features":
            if opLane.ImageToExport.ready():
                previewLayer = self.createStandardLayerFromSlot( opLane.ImageToExport )
                previewLayer.visible = False
                previewLayer.name = "Features - Preview"
                previewLayer.set_normalize( 0, None )
                layers.append(previewLayer)
            if opLane.ImageOnDisk.ready():
                exportedLayer = self.createStandardLayerFromSlot( opLane.ImageOnDisk )
                exportedLayer.visible = True
                exportedLayer.name = "Features - Exported"
                exportedLayer.set_normalize( 0, None )
                layers.append(exportedLayer)

        # If available, also show the raw data layer
        rawSlot = opLane.FormattedRawData
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot( rawSlot )
            rawLayer.name = "Raw Data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append( rawLayer )

        return layers 

    def _initSegmentationlayer(self, segSlot):
        if not segSlot.ready():
            return None
        opLane = self.topLevelOperatorView
        colors = opLane.PmapColors.value
        colortable = []
        colortable.append( QColor(0,0,0).rgba() )
        for color in colors:
            colortable.append( QColor(*color).rgba() )
        segsrc = LazyflowSource( segSlot )
        seglayer = ColortableLayer( segsrc, colortable )
        seglayer.name = "Simple Segmentation"
        return seglayer

    def _initPredictionLayers(self, predictionSlot):
        opLane = self.topLevelOperatorView
        if not opLane.LabelNames.ready() or not opLane.PmapColors.ready():
            return []

        layers = []
        colors = opLane.PmapColors.value
        names = opLane.LabelNames.value

        # Use a slicer to provide a separate slot for each channel layer
        opSlicer = OpMultiArraySlicer2( parent=opLane.viewed_operator().parent )
        opSlicer.Input.connect( predictionSlot )
        opSlicer.AxisFlag.setValue('c')

        for channel, channelSlot in enumerate(opSlicer.Slices):
            if channelSlot.ready() and channel < len(colors) and channel < len(names):
                drange = channelSlot.meta.drange or (0.0, 1.0)
                predictsrc = LazyflowSource(channelSlot)
                predictLayer = AlphaModulatedLayer( predictsrc,
                                                    tintColor=QColor(*colors[channel]),
                                                    # FIXME: This is weird.  Why are range and normalize both set to the same thing?
                                                    range=drange,
                                                    normalize=drange )
                predictLayer.opacity = 0.25
                predictLayer.visible = True
                predictLayer.name = names[channel]
                layers.append(predictLayer)

        return layers