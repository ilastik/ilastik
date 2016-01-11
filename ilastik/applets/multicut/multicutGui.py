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
from functools import partial

from PyQt4.QtGui import QWidget, QLabel, QSpinBox, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy

from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

import logging
from PyQt4.Qt import QDoubleSpinBox, QHBoxLayout
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

        # Base class
        super( MulticutGui, self ).stopAndCleanUp()
    
    ###########################################
    ###########################################
    
    def __init__(self, parentApplet, topLevelOperatorView):
        self.__cleanup_fns = []
        self.topLevelOperatorView = topLevelOperatorView
        super(MulticutGui, self).__init__( parentApplet, topLevelOperatorView )

    def initAppletDrawerUi(self):
        """
        Overridden from base class (LayerViewerGui)
        """
        op = self.topLevelOperatorView

        # Beta controls
        beta_label = QLabel(text="Beta:")
        beta_box = QDoubleSpinBox()
        beta_box.setDecimals(2)
        beta_box.setMinimum(0.01)
        beta_box.setMaximum(0.99)
        beta_box.setSingleStep(0.1)
        
        # Keep in sync: operator <--> gui
        beta_box.valueChanged.connect( self.configure_operator_from_gui )
        op.Beta.notifyDirty( self.configure_gui_from_operator )
        self.__cleanup_fns.append( partial( op.Beta.unregisterDirty, self.configure_gui_from_operator ) )
        
        beta_layout = QHBoxLayout()
        beta_layout.addWidget(beta_label)
        beta_layout.addSpacerItem( QSpacerItem(10, 0, QSizePolicy.Expanding) )
        beta_layout.addWidget(beta_box)

        # Layout
        layout = QVBoxLayout()
        layout.addLayout(beta_layout)
        layout.addSpacerItem( QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding) )
        
        # Finally, the whole drawer widget
        drawer = QWidget(parent=self)
        drawer.setLayout(layout)

        # Save these members for later use
        self._drawer = drawer
        self._beta_box = beta_box

        # Initialize everything with the operator's initial values
        self.configure_gui_from_operator()

    def configure_gui_from_operator(self, *args):
        op = self.topLevelOperatorView
        self._beta_box.setValue( op.Beta.value )

    def configure_operator_from_gui(self):
        op = self.topLevelOperatorView
        op.Beta.setValue( self._beta_box.value() )

    def setupLayers(self):
        layers = []
        op = self.topLevelOperatorView
        
        # Final segmentation
        if op.Output.ready():
            layer = self.createStandardLayerFromSlot( op.Output )
            layer.name = "Multicut Segmentation"
            layer.visible = False # Off by default...
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
