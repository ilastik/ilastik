from PyQt4 import uic
from PyQt4.QtCore import pyqtSlot

import os
import time
import threading

from ilastik.applets.layerViewer import LayerViewerGui

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)
from lazyflow.tracer import traceLogged

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
    
    @traceLogged(traceLogger)
    def __init__(self, mainOperator):
        """
        """
        super(VigraWatershedViewerGui, self).__init__([mainOperator.InputChannels, mainOperator.Output])
        self.mainOperator = mainOperator
        self.mainOperator.FreezeCache.setValue(True)
    
        self._colortable = []
    
    @traceLogged(traceLogger)
    def initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
        self._drawer.updateWatershedsButton.clicked.connect( self.onUpdateWatershedsButton )
                
    def getAppletDrawerUi(self):
        return self._drawer
    
    @traceLogged(traceLogger)
    def setupLayers(self, currentImageIndex):
        layers = []

        # Show the watershed data
        outputImageSlot = self.mainOperator.Output[ currentImageIndex ]
        if outputImageSlot.ready():
            outputLayer = self.createStandardLayerFromSlot( outputImageSlot, lastChannelIsAlpha=True )
            outputLayer.name = "Watershed (channel 0)"
            outputLayer.visible = True
            outputLayer.opacity = 0.5
            layers.append(outputLayer)
        
        # Show the raw input data
        inputImageSlot = self.mainOperator.InputChannels[ currentImageIndex ]
        if inputImageSlot.ready():
            for channel, slot in enumerate(inputImageSlot):
                inputLayer = self.createStandardLayerFromSlot( slot )
                inputLayer.name = "Raw Input (Ch.{})".format(channel)
                inputLayer.visible = True
                inputLayer.opacity = 1.0
                layers.append(inputLayer)

        return layers

    @pyqtSlot()
    @traceLogged(traceLogger)
    def onUpdateWatershedsButton(self):        
        @traceLogged(traceLogger)
        def updateThread():
            """
            Temporarily unfreeze the cache and freeze it again after the views are finished rendering.
            """
            self.mainOperator.FreezeCache.setValue(False)

            # Force the cache to update.
            self.mainOperator.InputImage[self.imageIndex].setDirty( slice(None) )
            
            # Wait for the image to be rendered into all three image views
            time.sleep(1)
            for imgView in self.editor.imageViews:
                imgView.scene().joinRendering()
            self.mainOperator.FreezeCache.setValue(True)

        if self.imageIndex >= 0:
            th = threading.Thread(target=updateThread)
            th.start()




