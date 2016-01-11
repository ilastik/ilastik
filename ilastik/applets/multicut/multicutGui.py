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
#           http://ilastik.org/license.html
##############################################################################
from PyQt4.QtGui import QWidget
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

import logging
logger = logging.getLogger(__name__)

class MulticutGui(LayerViewerGui):

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    
    def appletDrawer(self):
        return self._drawer

    def stopAndCleanUp(self):
        # Unsubscribe to all signals
        for fn in self.__cleanup_fns:
            fn()
    
    ###########################################
    ###########################################
    
    def __init__(self, parentApplet, topLevelOperatorView):
        super(MulticutGui, self).__init__( parentApplet, topLevelOperatorView )
        self.topLevelOperatorView = topLevelOperatorView

        # Remember to unsubscribe during shutdown
        self.__cleanup_fns = []

    def initAppletDrawerUi(self):
        self._drawer = QWidget(parent=self)

    def setupLayers(self):
        layers = []
        op = self.topLevelOperatorView
        
        # Final segmentation
        if op.Output.ready():
            layer = self.createStandardLayerFromSlot( op.Output )
            layer.name = "Multicut Segmentation"
            layer.visible = True
            layer.opacity = 0.5
            layers.append(layer)
            del layer

        # Superpixels
        if op.Superpixels.ready():
            layer = self.createStandardLayerFromSlot( op.Superpixels )
            layer.name = "Superpixels"
            layer.visible = True
            layer.opacity = 0.5
            layers.append(layer)
            del layer

        # Probabilities
        if op.Probabilities.ready():
            layer = self.createStandardLayerFromSlot( op.Probabilities )
            layer.name = "Probabilities"
            layer.visible = True
            layer.opacity = 1.0
            layers.append(layer)
            del layer

        # Raw Data (grayscale)
        if op.RawData.ready():
            layer = self.createStandardLayerFromSlot( op.RawData )
            layer.name = "Raw Data"
            layer.visible = True
            layer.opacity = 1.0
            layers.append(layer)
            del layer

        return layers
