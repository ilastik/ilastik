from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor

from volumina.api import ColortableLayer, LazyflowSource

from ilastik.applets.batchIo.batchIoGui import BatchIoGui
from ilastik.applets.layerViewer import LayerViewerGui

class BlockwiseObjectClassificationBatchGui( BatchIoGui ):
    """
    A subclass of the generic Batch gui that creates custom layer viewers.
    """
    def createLayerViewer(self, opLane):
        return BlockwiseObjectClassificationResultsViewer(opLane)

class BlockwiseObjectClassificationResultsViewer(LayerViewerGui):
    
    def __init__(self, *args, **kwargs):
        super( self.__class__, self ).__init__(*args, **kwargs)
        self._colorTable16 = self._createDefault16ColorColorTable()
    
    def setupLayers(self):
        layers = []
        
        predictionSlot = self.topLevelOperatorView.ImageToExport
        if predictionSlot.ready():
            predictlayer = ColortableLayer( LazyflowSource(predictionSlot),
                                                 colorTable=self._colorTable16 )
            predictlayer.name = "Prediction"
            predictlayer.visible = True
            layers.append(predictlayer)

        rawSlot = self.topLevelOperatorView.RawImage
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot(rawSlot)
            rawLayer.name = "Raw data"
            layers.append(rawLayer)

#        binarySlot = self.topLevelOperatorView.BinaryImage
#        if binarySlot.ready():
#            ct_binary = [QColor(0, 0, 0, 0).rgba(),
#                         QColor(255, 255, 255, 255).rgba()]
#            binaryLayer = ColortableLayer(LazyflowSource(binarySlot), ct_binary)
#            binaryLayer.name = "Binary Image"
#            layers.append(binaryLayer)

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

        return [c.rgba() for c in colors]
