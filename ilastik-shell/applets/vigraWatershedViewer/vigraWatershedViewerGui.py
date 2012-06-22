from PyQt4.QtGui import *
from PyQt4 import uic

from volumina.api import ColortableLayer, LazyflowSource

import random
import os

from applets.layerViewer import LayerViewerGui
from volumina.widgets.thresholdingWidget import ThresholdingWidget

class VigraWatershedViewerGui(LayerViewerGui):
    """
    """
    
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    
    def appletDrawers(self):
        return [ ("Watershed Viewer", self.getAppletDrawerUi() ) ]

    # (Other methods already provided by our base class)

    ###########################################
    ###########################################
    
    def __init__(self, mainOperator):
        """
        """
        super(VigraWatershedViewerGui, self).__init__([mainOperator])
        self.mainOperator = mainOperator
        #self.mainOperator.PaddingWidth.setValue(10)
    
        self._colortable = []
    
    def initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
        
#        layout = QVBoxLayout( self )
#        layout.setSpacing(0)
#        self._drawer.setLayout( layout )
#
#        thresholdWidget = ThresholdingWidget(self)
#        thresholdWidget.valueChanged.connect( self.handleThresholdGuiValuesChanged )
#        layout.addWidget( thresholdWidget )
        
        def enableDrawerControls(enabled):
            pass

        # Expose the enable function with the name the shell expects
        self._drawer.enableControls = enableDrawerControls
    
#    def handleThresholdGuiValuesChanged(self, minVal, maxVal):
#        self.mainOperator.MinValue.setValue(minVal)
#        self.mainOperator.MaxValue.setValue(maxVal)
#        self.editor.scheduleSlicesRedraw()

    def getAppletDrawerUi(self):
        return self._drawer
    
    def setupLayers(self, currentImageIndex):
        layers = []

        # Show the watershed data
        outputImageSlot = self.mainOperator.Output[ currentImageIndex ]
        if outputImageSlot.ready():
            outputLayer = self.createStandardLayerFromSlot( outputImageSlot )
#            source = LazyflowSource( self.mainOperator.Output[currentImageIndex] )
#            outputLayer = ColortableLayer( source, colorTable = self.getColortable(100000) )
            outputLayer.name = "watershed"
            outputLayer.visible = True
            outputLayer.opacity = 0.5
            layers.append(outputLayer)
        
        # Show the raw input data
        inputImageSlot = self.mainOperator.InputImage[ currentImageIndex ]
        if inputImageSlot.ready():
            inputLayer = self.createStandardLayerFromSlot( inputImageSlot )
            inputLayer.name = "Raw Input"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append(inputLayer)

        return layers

    def getColortable(self, minLength):
        def randChannel():
            return int(random.random() * 256)
        while len(self._colortable) < minLength:
            self._colortable += [ QColor(randChannel(), randChannel(), randChannel()).rgba() ]
        return self._colortable











