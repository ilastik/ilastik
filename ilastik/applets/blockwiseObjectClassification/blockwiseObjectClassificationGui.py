# Built-in
import os
import logging
from functools import partial

# Qt
from PyQt4 import uic
from PyQt4.QtCore import Qt, QEvent
from PyQt4.QtGui import QColor

from lazyflow.utility import traceLogged
from volumina.api import LazyflowSource, ColortableLayer
from ilastik.applets.layerViewer import LayerViewerGui

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)

class BlockwiseObjectClassificationGui( LayerViewerGui ):
    
    def __init__(self, *args, **kwargs):
        super( self.__class__, self ).__init__(*args, **kwargs)
        self._colorTable16 = self._createDefault16ColorColorTable()
    
        # Subscribe to future changes (from serializer or whatever)
        self.topLevelOperatorView.BlockShape3dDict.notifyDirty( self._updateGuiFromOperator )
        self.topLevelOperatorView.HaloPadding3dDict.notifyDirty( self._updateGuiFromOperator )

        # Update with initial values
        self._updateGuiFromOperator()
        
    def initAppletDrawerUi(self):
        """
        Reimplemented from LayerViewerGui base class.
        """
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
        
        self._drawer.applyButton.clicked.connect( self._onApplyButtonPressed )

        self._blockSpinBoxes = { 'x' : self._drawer.blockSpinBox_X,
                                 'y' : self._drawer.blockSpinBox_Y,
                                 'z' : self._drawer.blockSpinBox_Z }

        self._haloSpinBoxes = { 'x' : self._drawer.haloSpinBox_X,
                                'y' : self._drawer.haloSpinBox_Y,
                                'z' : self._drawer.haloSpinBox_Z }

        blockShapeSlot = self.topLevelOperatorView.BlockShape3dDict
        if blockShapeSlot.ready():
            block_shape_dict = blockShapeSlot.value
            self._drawer.blockSpinBox_X.setValue( block_shape_dict['x'] )

        for spinBoxes in ( self._blockSpinBoxes, self._haloSpinBoxes ):
            for spinBox in spinBoxes.values():
                # Any time a spinbox changes, enable the "Apply" button.
                spinBox.valueChanged.connect( partial( self._drawer.applyButton.setEnabled, True ) )
                
                # If the user pressed enter inside a spinbox, auto-click "Apply"
                spinBox.installEventFilter( self )

    @traceLogged(traceLogger)
    def setupLayers(self):
        layers = []
        
        predictionSlot = self.topLevelOperatorView.PredictionImage
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

        binarySlot = self.topLevelOperatorView.BinaryImage
        if binarySlot.ready():
            ct_binary = [QColor(0, 0, 0, 0).rgba(),
                         QColor(255, 255, 255, 255).rgba()]
            binaryLayer = ColortableLayer(LazyflowSource(binarySlot), ct_binary)
            binaryLayer.name = "Binary Image"
            layers.append(binaryLayer)

        return layers

    def eventFilter(self, watched, event):
        """
        If the user pressed 'enter' within a spinbox, auto-click the "apply" button.
        """
        if watched in self._blockSpinBoxes.values() or self._haloSpinBoxes.values():
            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Enter:
                self._drawer.applyButton.click()
                return True
        return False

    def _onApplyButtonPressed(self):
        blockShapeSlot = self.topLevelOperatorView.BlockShape3dDict
        block_shape_dict = dict( blockShapeSlot.value )
        block_shape_dict['x'] = self._drawer.blockSpinBox_X.value()
        block_shape_dict['y'] = self._drawer.blockSpinBox_Y.value()
        block_shape_dict['z'] = self._drawer.blockSpinBox_Z.value()
        blockShapeSlot.setValue( block_shape_dict )

        haloPaddingSlot = self.topLevelOperatorView.HaloPadding3dDict
        halo_padding_dict = dict(self.topLevelOperatorView.HaloPadding3dDict.value)
        halo_padding_dict['x'] = self._drawer.haloSpinBox_X.value()
        halo_padding_dict['y'] = self._drawer.haloSpinBox_Y.value()
        halo_padding_dict['z'] = self._drawer.haloSpinBox_Z.value()
        haloPaddingSlot.setValue( halo_padding_dict )
        
        self._drawer.applyButton.setEnabled( False )

    def _updateGuiFromOperator(self, *args):
        blockShapeDict = self.topLevelOperatorView.BlockShape3dDict.value
        for axiskey, spinBox in self._blockSpinBoxes.items():
            spinBox.setValue( blockShapeDict[axiskey] )

        haloPaddingDict = self.topLevelOperatorView.HaloPadding3dDict.value
        for axiskey, spinBox in self._haloSpinBoxes.items():
            spinBox.setValue( haloPaddingDict[axiskey] )

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
