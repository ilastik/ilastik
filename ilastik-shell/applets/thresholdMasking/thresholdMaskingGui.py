from PyQt4.QtGui import *
from PyQt4 import uic

import os

from applets.layerViewer import LayerViewerGui
from volumina.widgets.thresholdingWidget import ThresholdingWidget

class ThresholdMaskingGui(LayerViewerGui):
    """
    """
    
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    
    def appletDrawers(self):
        return [ ("Threshold Mask Viewer", self.getAppletDrawerUi() ) ]

    # (Other methods already provided by our base class)

    ###########################################
    ###########################################
    
    def __init__(self, mainOperator):
        """
        """
        super(ThresholdMaskingGui, self).__init__([mainOperator])
        self.mainOperator = mainOperator
        self.handleThresholdGuiValuesChanged(0, 255)
    
    def initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
        
        layout = QVBoxLayout( self )
        layout.setSpacing(0)
        self._drawer.setLayout( layout )

        thresholdWidget = ThresholdingWidget(self)
        thresholdWidget.valueChanged.connect( self.handleThresholdGuiValuesChanged )
        layout.addWidget( thresholdWidget )
        
        def enableDrawerControls(enabled):
            pass

        # Expose the enable function with the name the shell expects
        self._drawer.enableControls = enableDrawerControls
    
    def handleThresholdGuiValuesChanged(self, minVal, maxVal):
        self.mainOperator.MinValue.setValue(minVal)
        self.mainOperator.MaxValue.setValue(maxVal)
        self.editor.scheduleSlicesRedraw()

    def getAppletDrawerUi(self):
        return self._drawer
    
    def setupLayers(self, currentImageIndex):
        layers = []

        # Show the thresholded data
        outputImageSlot = self.mainOperator.Output[ currentImageIndex ]
        if outputImageSlot.ready():
            outputLayer = self.createStandardLayerFromSlot( outputImageSlot )
            outputLayer.name = "min <= x <= max"
            outputLayer.visible = True
            outputLayer.opacity = 0.75
            layers.append(outputLayer)
        
        # Show the  data
        invertedOutputSlot = self.mainOperator.InvertedOutput[ currentImageIndex ]
        if invertedOutputSlot.ready():
            invertedLayer = self.createStandardLayerFromSlot( invertedOutputSlot )
            invertedLayer.name = "(x < min) U (x > max)"
            invertedLayer.visible = True
            invertedLayer.opacity = 0.25
            layers.append(invertedLayer)
        
        # Show the raw input data
        inputImageSlot = self.mainOperator.InputImage[ currentImageIndex ]
        if inputImageSlot.ready():
            inputLayer = self.createStandardLayerFromSlot( inputImageSlot )
            inputLayer.name = "Raw Input"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append(inputLayer)

        return layers














