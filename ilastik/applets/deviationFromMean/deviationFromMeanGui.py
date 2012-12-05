from PyQt4.QtGui import QWidget, QVBoxLayout
from PyQt4 import uic

import os
from ilastik.applets.layerViewer import LayerViewerGui

from ilastik.utility import bind

class DeviationFromMeanGui(LayerViewerGui):
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
    
    def __init__(self, topLevelOperatorView):
        """
        """
        self.topLevelOperatorView = topLevelOperatorView
        super(DeviationFromMeanGui, self).__init__(topLevelOperatorView)
            
    def initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
        
        self._drawer.scalingFactorSpinBox.valueChanged.connect(self.updateOperatorScalingFactor)
        self._drawer.offsetSpinBox.valueChanged.connect(self.updateOperatorOffset)

        def updateDrawerFromOperator():
            scalingFactor, offset = (0,0)

            if self.topLevelOperatorView.ScalingFactor.ready():
                scalingFactor = self.topLevelOperatorView.ScalingFactor.value
            if self.topLevelOperatorView.Offset.ready():
                offset = self.topLevelOperatorView.Offset.value

            self._drawer.scalingFactorSpinBox.setValue(scalingFactor)
            self._drawer.offsetSpinBox.setValue(offset)
            
        self.topLevelOperatorView.ScalingFactor.notifyDirty( bind(updateDrawerFromOperator) )
        self.topLevelOperatorView.Offset.notifyDirty( bind(updateDrawerFromOperator) )
        updateDrawerFromOperator()

        # Provide defaults if the operator isn't already configured..
        if not self.topLevelOperatorView.ScalingFactor.ready():
            self.updateOperatorScalingFactor(1)
        if not self.topLevelOperatorView.Offset.ready():
            self.updateOperatorOffset(0)
        
    def updateOperatorScalingFactor(self, scalingFactor):
        self.topLevelOperatorView.ScalingFactor.setValue(scalingFactor)
    
    def updateOperatorOffset(self, offset):
        self.topLevelOperatorView.Offset.setValue(offset)
    
    def getAppletDrawerUi(self):
        return self._drawer
    
    def setupLayers(self):
        layers = []

        # Show the Output data
        outputImageSlot = self.topLevelOperatorView.Output
        if outputImageSlot.ready():
            outputLayer = self.createStandardLayerFromSlot( outputImageSlot )
            outputLayer.name = "Deviation From Mean"
            outputLayer.visible = True
            outputLayer.opacity = 1.0
            layers.append(outputLayer)

        # Show the mean image
        meanImageSlot = self.topLevelOperatorView.Mean
        if meanImageSlot.ready():
            meanLayer = self.createStandardLayerFromSlot(meanImageSlot)
            meanLayer.name = "Mean"
            meanLayer.visible = True
            meanLayer.opacity = 1.0
            layers.append(meanLayer)
        
        # Show the raw input data as a convenience for the user
        inputImageSlot = self.topLevelOperatorView.Input
        if inputImageSlot.ready():
            inputLayer = self.createStandardLayerFromSlot( inputImageSlot )
            inputLayer.name = "Input"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append(inputLayer)

        return layers














