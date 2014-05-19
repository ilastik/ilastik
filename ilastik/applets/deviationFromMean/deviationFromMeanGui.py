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
from PyQt4 import uic

import os
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

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
    
    def __init__(self, parentApplet, topLevelOperatorView):
        """
        """
        self.topLevelOperatorView = topLevelOperatorView
        super(DeviationFromMeanGui, self).__init__(parentApplet, topLevelOperatorView)
            
    def initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")

        # If the user changes a setting the GUI, update the appropriate operator slot.        
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

        # If the operator is changed *outside* the GUI (e.g. the project is loaded),
        #  then update the GUI to match the new operator slot values.            
        self.topLevelOperatorView.ScalingFactor.notifyDirty( bind(updateDrawerFromOperator) )
        self.topLevelOperatorView.Offset.notifyDirty( bind(updateDrawerFromOperator) )
        
        # Initialize the GUI with the operator's initial state.
        updateDrawerFromOperator()

        # Provide defaults if the operator isn't already configured.
        #  (e.g. if it's a blank project, then the operator won't have any setup yet.)
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
        """
        The LayerViewer base class calls this function to obtain the list of layers that 
        should be displayed in the central viewer.
        """
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














