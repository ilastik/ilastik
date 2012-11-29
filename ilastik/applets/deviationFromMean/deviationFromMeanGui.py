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

    @classmethod
    def appletDrawerName(self):
        return "Deviation From Mean"

    # (Other methods already provided by our base class)

    ###########################################
    ###########################################
    
    def __init__(self, mainOperator):
        """
        """
        self.mainOperator = mainOperator
        super(DeviationFromMeanGui, self).__init__(mainOperator)
            
    def initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
        
        layout = QVBoxLayout( self )
        layout.setSpacing(0)
        self._drawer.setLayout( layout )

        self._drawer.scalingFactorSpinBox.valueChanged.connect(self.updateOperatorScalingFactor)
        self._drawer.offsetSpinBox.valueChanged.connect(self.updateOperatorOffset)

        def updateDrawerFromOperator():
            scalingFactor, offset = (0,0)

            if self.mainOperator.ScalingFactor.ready():
                scalingFactor = self.mainOperator.ScalingFactor.value
            if self.mainOperator.Offset.ready():
                offset = self.mainOperator.Offset.value

            self._drawer.scalingFactorSpinBox.setValue(scalingFactor)
            self._drawer.offsetSpinBox.setValue(offset)
            
        self.mainOperator.ScalingFactor.notifyDirty( bind(updateDrawerFromOperator) )
        self.mainOperator.Offset.notifyDirty( bind(updateDrawerFromOperator) )
        updateDrawerFromOperator()

        # Provide defaults if the operator isn't already configured..
        if not self.mainOperator.ScalingFactor.ready():
            self.updateOperatorScalingFactor(1)
        if not self.mainOperator.Offset.ready():
            self.updateOperatorOffset(0)
        
    def updateOperatorScalingFactor(self, scalingFactor):
        self.mainOperator.ScalingFactor.setValue(scalingFactor)
    
    def updateOperatorOffset(self, offset):
        self.mainOperator.Offset.setValue(offset)
    
    def getAppletDrawerUi(self):
        return self._drawer
    
    def setupLayers(self):
        layers = []

        # Show the Output data
        outputImageSlot = self.mainOperator.Output
        if outputImageSlot.ready():
            outputLayer = self.createStandardLayerFromSlot( outputImageSlot )
            outputLayer.name = "Deviation From Mean"
            outputLayer.visible = True
            outputLayer.opacity = 1.0
            layers.append(outputLayer)

        # Show the mean image
        meanImageSlot = self.mainOperator.Mean
        if meanImageSlot.ready():
            meanLayer = self.createStandardLayerFromSlot(meanImageSlot)
            meanLayer.name = "Mean"
            meanLayer.visible = True
            meanLayer.opacity = 1.0
            layers.append(meanLayer)
        
        # Show the raw input data as a convenience for the user
        inputImageSlot = self.mainOperator.Input
        if inputImageSlot.ready():
            inputLayer = self.createStandardLayerFromSlot( inputImageSlot )
            inputLayer.name = "Input"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append(inputLayer)

        return layers














