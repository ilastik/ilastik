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
# Built-in
import os
import logging
from functools import partial

# Qt
from PyQt5 import uic
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QColor

from ilastik.utility.gui import threadRouted
from volumina.api import LazyflowSource, ColortableLayer
from volumina import colortables
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

logger = logging.getLogger(__name__)

class BlockwiseObjectClassificationGui( LayerViewerGui ):
    
    def __init__(self, *args, **kwargs):
        super( self.__class__, self ).__init__(*args, **kwargs)
        self._colorTable16 = colortables.default16_new
    
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

        for spinBoxes in ( self._blockSpinBoxes, self._haloSpinBoxes ):
            for spinBox in list(spinBoxes.values()):
                # Any time a spinbox changes, enable the "Apply" button.
                spinBox.valueChanged.connect( partial( self._drawer.applyButton.setEnabled, True ) )
                
                # If the user pressed enter inside a spinbox, auto-click "Apply"
                spinBox.installEventFilter( self )
        
        #FIXME: we are relying on z being there because of the OpReorderAxes
        zIndex = self.topLevelOperatorView.RawImage.meta.axistags.index('z')
        nz = self.topLevelOperatorView.RawImage.meta.shape[zIndex]
        if nz==1:
            #it's a 2d image, hide z spin boxes
            self._drawer.blockSpinBox_Z.setVisible(False)
            self._drawer.haloSpinBox_Z.setVisible(False)
            

    def setupLayers(self):
        layers = []
        
        predictionSlot = self.topLevelOperatorView.PredictionImage
        if predictionSlot.ready():
            
            predictLayer = ColortableLayer( LazyflowSource(predictionSlot),
                                                 colorTable=self._colorTable16 )
            predictLayer.name = "Blockwise prediction"
            predictLayer.visible = False
            
            layers.append(predictLayer)

        
        binarySlot = self.topLevelOperatorView.BinaryImage
        if binarySlot.ready():
            ct_binary = [QColor(0, 0, 0, 0).rgba(),
                         QColor(255, 255, 255, 255).rgba()]
            binaryLayer = ColortableLayer(LazyflowSource(binarySlot), ct_binary)
            binaryLayer.name = "Binary Image"
            layers.append(binaryLayer)
            
        rawSlot = self.topLevelOperatorView.RawImage
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot(rawSlot)
            rawLayer.name = "Raw data"
            layers.append(rawLayer)


        return layers

    def eventFilter(self, watched, event):
        """
        If the user pressed 'enter' within a spinbox, auto-click the "apply" button.
        """
        if watched in list(self._blockSpinBoxes.values()) or list(self._haloSpinBoxes.values()):
            if  event.type() == QEvent.KeyPress and\
              ( event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return):
                self._drawer.applyButton.click()
                return True
        return False

    def _onApplyButtonPressed(self):
        blockShapeSlot = self.topLevelOperatorView.BlockShape3dDict
        block_shape_dict = dict( blockShapeSlot.value )
        block_shape_dict['x'] = self._drawer.blockSpinBox_X.value()
        block_shape_dict['y'] = self._drawer.blockSpinBox_Y.value()
        block_shape_dict['z'] = self._drawer.blockSpinBox_Z.value()

        haloPaddingSlot = self.topLevelOperatorView.HaloPadding3dDict
        halo_padding_dict = dict(self.topLevelOperatorView.HaloPadding3dDict.value)
        halo_padding_dict['x'] = self._drawer.haloSpinBox_X.value()
        halo_padding_dict['y'] = self._drawer.haloSpinBox_Y.value()
        halo_padding_dict['z'] = self._drawer.haloSpinBox_Z.value()

        blockShapeSlot.setValue( block_shape_dict )
        haloPaddingSlot.setValue( halo_padding_dict )
        #make final output visible
        for layer in self.layerstack:
            if "prediction" in layer.name:
                layer.visible = True

    @threadRouted
    def _updateGuiFromOperator(self, *args):
        blockShapeDict = self.topLevelOperatorView.BlockShape3dDict.value
        for axiskey, spinBox in list(self._blockSpinBoxes.items()):
            spinBox.setValue( blockShapeDict[axiskey] )

        haloPaddingDict = self.topLevelOperatorView.HaloPadding3dDict.value
        for axiskey, spinBox in list(self._haloSpinBoxes.items()):
            spinBox.setValue( haloPaddingDict[axiskey] )
