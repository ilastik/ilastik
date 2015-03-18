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
import os

from PyQt4 import uic
from PyQt4.QtGui import QVBoxLayout, QSpacerItem, QSizePolicy

from volumina.widgets.thresholdingWidget import ThresholdingWidget
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

class ThresholdMaskingGui(LayerViewerGui):
    """
    Simple example of an applet tha  
    """
    
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################

    def appletDrawer(self):
        return self._drawer

    # (Other methods already provided by our base class)

    ###########################################
    ###########################################
    
    def __init__(self, parentApplet, topLevelOperatorView):
        """
        """
        self.topLevelOperatorView = topLevelOperatorView
        super(ThresholdMaskingGui, self).__init__(parentApplet, self.topLevelOperatorView)
            
    def initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")

        # Init threshold widget        
        self.thresholdWidget = ThresholdingWidget(self)
        self.thresholdWidget.valueChanged.connect( self.apply_gui_settings_to_operator )

        # Add widget to a layout
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget( self.thresholdWidget )
        layout.addSpacerItem( QSpacerItem(0,0,vPolicy=QSizePolicy.Expanding) )

        # Apply layout to the drawer
        self._drawer.setLayout( layout )

        # Initialize the gui with the operator's current values
        self.apply_operator_settings_to_gui()

    def apply_operator_settings_to_gui(self):
        minValue, maxValue = (0,255)

        if self.topLevelOperatorView.MinValue.ready():
            minValue = self.topLevelOperatorView.MinValue.value
        if self.topLevelOperatorView.MaxValue.ready():
            maxValue = self.topLevelOperatorView.MaxValue.value

        self.thresholdWidget.setValue(minValue, maxValue)

    def apply_gui_settings_to_operator(self, minVal, maxVal):
        self.topLevelOperatorView.MinValue.setValue(minVal)
        self.topLevelOperatorView.MaxValue.setValue(maxVal)
    
    def setupLayers(self):
        """
        Overridden from LayerViewerGui.
        Create a list of all layer objects that should be displayed.
        """
        layers = []

        # Show the thresholded data
        outputImageSlot = self.topLevelOperatorView.Output
        if outputImageSlot.ready():
            outputLayer = self.createStandardLayerFromSlot( outputImageSlot )
            outputLayer.name = "min <= x <= max"
            outputLayer.visible = True
            outputLayer.opacity = 0.75
            layers.append(outputLayer)
        
        # Show the  data
        invertedOutputSlot = self.topLevelOperatorView.InvertedOutput
        if invertedOutputSlot.ready():
            invertedLayer = self.createStandardLayerFromSlot( invertedOutputSlot )
            invertedLayer.name = "(x < min) U (x > max)"
            invertedLayer.visible = True
            invertedLayer.opacity = 0.25
            layers.append(invertedLayer)
        
        # Show the raw input data
        inputImageSlot = self.topLevelOperatorView.InputImage
        if inputImageSlot.ready():
            inputLayer = self.createStandardLayerFromSlot( inputImageSlot )
            inputLayer.name = "Raw Input"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append(inputLayer)

        return layers
