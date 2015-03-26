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
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor

from volumina.api import LazyflowSource, ColortableLayer, AlphaModulatedLayer
from ilastik.applets.dataExport.dataExportGui import DataExportGui, DataExportLayerViewerGui
from lazyflow.operators import OpMultiArraySlicer2
from ilastik.utility.exportingOperator import ExportingGui

class ObjectClassificationDataExportGui( DataExportGui, ExportingGui ):
    """
    A subclass of the generic data export gui that creates custom layer viewers.
    """
    def __init__(self, *args, **kwargs):
        super(ObjectClassificationDataExportGui, self).__init__(*args, **kwargs)
        self._exporting_operator = None

    def set_exporting_operator(self, op):
        self._exporting_operator = op

    def get_exporting_operator(self, lane=0):
        return self._exporting_operator.getLane(lane)

    def createLayerViewer(self, opLane):
        return ObjectClassificationResultsViewer(self.parentApplet, opLane)

    def get_export_dialog_title(self):
        return "Export Object Information"

    @property
    def gui_applet(self):
        return self.parentApplet

    def get_raw_shape(self):
        return self.get_exporting_operator().RawImages.meta.shape

    def get_feature_names(self):
        return self.get_exporting_operator().ComputedFeatureNames([]).wait()

    def _initAppletDrawerUic(self):
        super(ObjectClassificationDataExportGui, self)._initAppletDrawerUic()

        from PyQt4.QtGui import QGroupBox, QPushButton, QVBoxLayout
        group = QGroupBox("Export Object Feature Table", self.drawer)
        group.setLayout(QVBoxLayout())
        self.drawer.layout().addWidget(group)

        btn = QPushButton("Configure and export", group)
        btn.clicked.connect(self.show_export_dialog)
        group.layout().addWidget(btn)
        

def _createDefault16ColorColorTable():
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
    colors.append( QColor( Qt.lightGray ) )

    # Additional colors
    colors.append( QColor(255, 105, 180) ) #hot pink
    colors.append( QColor(102, 205, 170) ) #dark aquamarine
    colors.append( QColor(165,  42,  42) ) #brown
    colors.append( QColor(0, 0, 128) )     #navy
    colors.append( QColor(255, 165, 0) )   #orange
    colors.append( QColor(173, 255,  47) ) #green-yellow
    colors.append( QColor(128,0, 128) )    #purple
    colors.append( QColor(240, 230, 140) ) #khaki

#    colors.append( QColor(192, 192, 192) ) #silver
#    colors.append( QColor(69, 69, 69) )    # dark grey
#    colors.append( QColor( Qt.cyan ) )

    assert len(colors) == 16

    return [c.rgba() for c in colors]

class ObjectClassificationResultsViewer(DataExportLayerViewerGui):

    _colorTable16 = _createDefault16ColorColorTable()
    
    def setupLayers(self):
        layers = []

        opLane = self.topLevelOperatorView

        selection_names = opLane.SelectionNames.value
        selection = selection_names[ opLane.InputSelection.value ]

        # This code depends on a specific order for the export slots.
        # If those change, update this function!
        assert selection in ['Object Predictions', 'Object Probabilities', 'Pixel Probabilities']
    
        if selection == "Object Predictions":
            fromDiskSlot = self.topLevelOperatorView.ImageOnDisk
            if fromDiskSlot.ready():
                exportLayer = ColortableLayer( LazyflowSource(fromDiskSlot), colorTable=self._colorTable16 )
                exportLayer.name = "Prediction - Exported"
                exportLayer.visible = True
                layers.append(exportLayer)
    
            previewSlot = self.topLevelOperatorView.ImageToExport
            if previewSlot.ready():
                previewLayer = ColortableLayer( LazyflowSource(previewSlot), colorTable=self._colorTable16 )
                previewLayer.name = "Prediction - Preview"
                previewLayer.visible = False
                layers.append(previewLayer)

        elif selection == "Object Probabilities":
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
        
        elif selection == 'Pixel Probabilities':
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
        opSlicer = OpMultiArraySlicer2( parent=opLane.viewed_operator().parent )
        opSlicer.Input.connect( predictionSlot )
        opSlicer.AxisFlag.setValue('c')

        for channel, channelSlot in enumerate(opSlicer.Slices):
            if channelSlot.ready():
                drange = channelSlot.meta.drange or (0.0, 1.0)
                predictsrc = LazyflowSource(channelSlot)
                predictLayer = AlphaModulatedLayer( predictsrc,
                                                    tintColor=QColor.fromRgba(self._colorTable16[channel+1]),
                                                    # FIXME: This is weird.  Why are range and normalize both set to the same thing?
                                                    range=drange,
                                                    normalize=drange )
                predictLayer.opacity = 1.0
                predictLayer.visible = True
                predictLayer.name = "Probability Channel #{}".format( channel+1 )
                layers.append(predictLayer)

        return layers