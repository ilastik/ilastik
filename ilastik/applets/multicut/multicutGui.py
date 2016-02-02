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

import numpy as np

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QWidget, QLabel, QDoubleSpinBox, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QColor, QPen

from ilastik.utility.gui import threadRouted
from volumina.pixelpipeline.datasources import LazyflowSource
from volumina.layer import SegmentationEdgesLayer
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

        self._init_probability_colortable()

    def _init_probability_colortable(self):
        self.probability_colortable = []
        for v in np.linspace(0.0, 1.0, num=101):
            self.probability_colortable.append( QColor(255*(v), 255*(1.0-v), 0) )
        
        self.probability_pen_table = []
        for color in self.probability_colortable:
            pen = QPen(SegmentationEdgesLayer.DEFAULT_PEN)
            pen.setColor(color)
            self.probability_pen_table.append(pen)

        # When the edge probabilities are dirty, update the probability edge layer pens
        op = self.topLevelOperatorView
        op.EdgeProbabilitiesDict.notifyDirty( self.update_probability_edges )
        self.__cleanup_fns.append( partial( op.EdgeProbabilitiesDict.unregisterDirty, self.update_probability_edges ) )

    # Configure the handler for updated probability maps
    # FIXME: Should we make a new Layer subclass that handles this colortable mapping for us?  Yes.
    def update_probability_edges(self, *args):
        op = self.topLevelOperatorView
        if not self.superpixel_edge_layer:
            return
        edge_probs = op.EdgeProbabilitiesDict.value
        new_pens = {}
        for id_pair, probability in edge_probs.items():
            new_pens[id_pair] = self.probability_pen_table[int(probability * 100)]
        self.apply_new_probability_edges(new_pens)
    
    @threadRouted
    def apply_new_probability_edges(self, new_pens):
        # This function is threadRouted because you can't 
        # touch the layer colortable outside the main thread.
        self.superpixel_edge_layer.pen_table.update(new_pens)

    def configure_gui_from_operator(self, *args):
        op = self.topLevelOperatorView
        self._beta_box.setValue( op.Beta.value )

    def configure_operator_from_gui(self):
        op = self.topLevelOperatorView
        op.Beta.setValue( self._beta_box.value() )

    def setupLayers(self):
        layers = []
        op = self.topLevelOperatorView

        # Final segmentation -- Edges
        if op.Output.ready():
            default_pen = QPen(SegmentationEdgesLayer.DEFAULT_PEN)
            default_pen.setColor(Qt.blue)
            layer = SegmentationEdgesLayer( LazyflowSource(op.Output), default_pen )
            layer.name = "Multicut Edges"
            layer.visible = False # Off by default...
            layer.opacity = 1.0
            layers.append(layer)
            del layer

        # Superpixels -- Edge Probabilities
        # We use the RAG's superpixels, which may have different IDs
        self.superpixel_edge_layer = None
        if op.RagSuperpixels.ready() and op.EdgeProbabilitiesDict.ready():
            layer = SegmentationEdgesLayer( LazyflowSource(op.RagSuperpixels) )
            layer.name = "Superpixel Edge Probabilities"
            layer.visible = True
            layer.opacity = 1.0
            self.superpixel_edge_layer = layer
            layers.append(layer)
            del layer
                
        # Superpixels -- Edges
        if op.RagSuperpixels.ready():
            default_pen = QPen(SegmentationEdgesLayer.DEFAULT_PEN)
            default_pen.setColor(Qt.yellow)
            layer = SegmentationEdgesLayer( LazyflowSource(op.RagSuperpixels), default_pen )
            layer.name = "Superpixel Edges"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)
            del layer

        # Final segmentation -- Label Image
        if op.Output.ready():
            layer = self.createStandardLayerFromSlot( op.Output )
            layer.name = "Multicut Segmentation"
            layer.visible = False # Off by default...
            layer.opacity = 0.5
            layers.append(layer)
            del layer
 
        # Input Superpixels
        if op.InputSuperpixels.ready():
            layer = self.createStandardLayerFromSlot( op.InputSuperpixels )
            layer.name = "Input Superpixels"
            layer.visible = True
            layer.opacity = 0.5
            layers.append(layer)
            del layer
 
        # Voxel data
        if op.VoxelData.ready():
            layer = self.createStandardLayerFromSlot( op.VoxelData )
            layer.name = "Voxel Data"
            layer.visible = False
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
