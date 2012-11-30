from PyQt4.QtGui import *
from PyQt4 import uic

import os

from ilastik.applets.layerViewer import LayerViewerGui
from volumina.widgets.thresholdingWidget import ThresholdingWidget

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)
from lazyflow.tracer import Tracer

from ilastik.utility import bind

class ThresholdMaskingGui(LayerViewerGui):
    """
    """
    
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################

    def appletDrawer(self):
        return self.getAppletDrawerUi()

    # (Other methods already provided by our base class)

    ###########################################
    ###########################################
    
    def __init__(self, mainOperator):
        """
        """
        with Tracer(traceLogger):
            self.mainOperator = mainOperator
            super(ThresholdMaskingGui, self).__init__(self.mainOperator)
            
    def initAppletDrawerUi(self):
        with Tracer(traceLogger):
            # Load the ui file (find it in our own directory)
            localDir = os.path.split(__file__)[0]
            self._drawer = uic.loadUi(localDir+"/drawer.ui")
            
            layout = QVBoxLayout( self )
            layout.setSpacing(0)
            self._drawer.setLayout( layout )
    
            thresholdWidget = ThresholdingWidget(self)
            thresholdWidget.valueChanged.connect( self.handleThresholdGuiValuesChanged )
            layout.addWidget( thresholdWidget )
            
            def updateDrawerFromOperator():
                minValue, maxValue = (0,255)

                if self.mainOperator.MinValue.ready():
                    minValue = self.mainOperator.MinValue.value
                if self.mainOperator.MaxValue.ready():
                    maxValue = self.mainOperator.MaxValue.value

                thresholdWidget.setValue(minValue, maxValue)
                
            self.mainOperator.MinValue.notifyDirty( bind(updateDrawerFromOperator) )
            self.mainOperator.MaxValue.notifyDirty( bind(updateDrawerFromOperator) )
            updateDrawerFromOperator()
            
    def handleThresholdGuiValuesChanged(self, minVal, maxVal):
        with Tracer(traceLogger):
            self.mainOperator.MinValue.setValue(minVal)
            self.mainOperator.MaxValue.setValue(maxVal)
    
    def getAppletDrawerUi(self):
        return self._drawer
    
    def setupLayers(self):
        with Tracer(traceLogger):
            layers = []
    
            # Show the thresholded data
            outputImageSlot = self.mainOperator.Output
            if outputImageSlot.ready():
                outputLayer = self.createStandardLayerFromSlot( outputImageSlot )
                outputLayer.name = "min <= x <= max"
                outputLayer.visible = True
                outputLayer.opacity = 0.75
                layers.append(outputLayer)
            
            # Show the  data
            invertedOutputSlot = self.mainOperator.InvertedOutput
            if invertedOutputSlot.ready():
                invertedLayer = self.createStandardLayerFromSlot( invertedOutputSlot )
                invertedLayer.name = "(x < min) U (x > max)"
                invertedLayer.visible = True
                invertedLayer.opacity = 0.25
                layers.append(invertedLayer)
            
            # Show the raw input data
            inputImageSlot = self.mainOperator.InputImage
            if inputImageSlot.ready():
                inputLayer = self.createStandardLayerFromSlot( inputImageSlot )
                inputLayer.name = "Raw Input"
                inputLayer.visible = True
                inputLayer.opacity = 1.0
                layers.append(inputLayer)
    
            return layers














