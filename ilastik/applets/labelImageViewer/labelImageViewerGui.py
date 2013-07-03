from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor

from lazyflow.operators import OpMultiArraySlicer2
from volumina.api import LazyflowSource, ColortableLayer
from ilastik.utility import bind
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

class LabelImageViewerGui( LayerViewerGui ):
    
    def __init__(self, *args, **kwargs):
        super(LabelImageViewerGui, self).__init__(*args, **kwargs)
        self._colorTable16 = self._createDefault16ColorColorTable()
    
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

    def _createDefault16ColorColorTable(self):
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

#        colors.append( QColor(192, 192, 192) ) #silver
#        colors.append( QColor(69, 69, 69) )    # dark grey
#        colors.append( QColor( Qt.cyan ) )

        assert len(colors) == 16

        #return [c.rgba() for c in colors]
        return colors

