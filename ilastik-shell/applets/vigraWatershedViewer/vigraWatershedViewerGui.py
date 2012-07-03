from PyQt4.QtGui import *
from PyQt4 import uic

from volumina.api import ColortableLayer, LazyflowSource

import random
import os

from applets.layerViewer import LayerViewerGui
from volumina.widgets.thresholdingWidget import ThresholdingWidget

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)
from lazyflow.tracer import Tracer

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
        with Tracer(traceLogger):
            super(VigraWatershedViewerGui, self).__init__([mainOperator.InputImage, mainOperator.Output])
            self.mainOperator = mainOperator
            self.mainOperator.FreezeCache.setValue(True)
        
            self._colortable = []
    
    def initAppletDrawerUi(self):
        with Tracer(traceLogger):
            # Load the ui file (find it in our own directory)
            localDir = os.path.split(__file__)[0]
            self._drawer = uic.loadUi(localDir+"/drawer.ui")
                
    def getAppletDrawerUi(self):
        return self._drawer
    
    def setupLayers(self, currentImageIndex):
        with Tracer(traceLogger):
            layers = []
    
            # Show the watershed data
            outputImageSlot = self.mainOperator.Output[ currentImageIndex ]
            if outputImageSlot.ready():
                outputLayer = self.createStandardLayerFromSlot( outputImageSlot )
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
        with Tracer(traceLogger):
            def randChannel():
                return int(random.random() * 256)
            while len(self._colortable) < minLength:
                self._colortable += [ QColor(randChannel(), randChannel(), randChannel()).rgba() ]
            return self._colortable

    def showEvent(self, e):
        # Update while we're visible
        self.mainOperator.FreezeCache.setValue(False)

    def hideEvent(self, e):
        # Don't update while we're not visible
        self.mainOperator.FreezeCache.setValue(True)











