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
from PyQt4.QtGui import QWidget, QLabel, QDoubleSpinBox, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QColor, QPen, QPushButton

from ilastikrag.gui import FeatureSelectionDialog

from ilastik.utility.gui import threadRouted
from volumina.pixelpipeline.datasources import LazyflowSource
from volumina.layer import SegmentationEdgesLayer, LabelableSegmentationEdgesLayer
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

from lazyflow.request import Request

import logging
logger = logging.getLogger(__name__)

class EdgeTrainingGui(LayerViewerGui):

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
        super( EdgeTrainingGui, self ).stopAndCleanUp()
    
    ###########################################
    ###########################################
    
    def __init__(self, parentApplet, topLevelOperatorView):
        self.__cleanup_fns = []
        self.parentApplet = parentApplet
        self.topLevelOperatorView = topLevelOperatorView
        super(EdgeTrainingGui, self).__init__( parentApplet, topLevelOperatorView )

    def initAppletDrawerUi(self):
        """
        Overridden from base class (LayerViewerGui)
        """
        op = self.topLevelOperatorView

        # Controls
        feature_selection_button = QPushButton("Select Features", clicked=self._open_feature_selection_dlg)
        self.train_from_gt_button = QPushButton("Train from Groundtruth", clicked=self._handle_train_from_gt_clicked)
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(feature_selection_button)
        layout.addWidget(self.train_from_gt_button)
        layout.addSpacerItem( QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding) )
        
        # Finally, the whole drawer widget
        drawer = QWidget(parent=self)
        drawer.setLayout(layout)

        # Save these members for later use
        self._drawer = drawer

        # Initialize everything with the operator's initial values
        self.configure_gui_from_operator()

        self._init_edge_label_colortable()
        self._init_probability_colortable()
        
        op.GroundtruthSegmentation.notifyReady( self.configure_gui_from_operator )


    def _open_feature_selection_dlg(self):
        rag = self.topLevelOperatorView.Rag.value
        feature_names = rag.supported_features()
        channel_names = self.topLevelOperatorView.VoxelData.meta.channel_names
        default_selections = self.topLevelOperatorView.FeatureNames.value

        dlg = FeatureSelectionDialog(channel_names, feature_names, default_selections, parent=self)
        dlg_result = dlg.exec_()
        if dlg_result != dlg.Accepted:
            return
        
        selections = dlg.selections()
        self.topLevelOperatorView.FeatureNames.setValue(selections)

    # Configure the handler for updated edge label maps
    def _init_edge_label_colortable(self):
        self.edge_label_colortable = [ QColor(  0,  0,  0,   0),  # transparent
                                       QColor(  0, 255, 0, 255),  # green 
                                       QColor(255,   0, 0, 255) ] # red
        
        self.edge_label_pen_table = []
        for color in self.edge_label_colortable:
            pen = QPen(SegmentationEdgesLayer.DEFAULT_PEN)
            pen.setColor(color)
            pen.setWidth(5)
            self.edge_label_pen_table.append(pen)

        # When the edge labels are dirty, update the edge label layer pens
        op = self.topLevelOperatorView
        op.EdgeLabelsDict.notifyDirty( self.update_labeled_edges )
        self.__cleanup_fns.append( partial( op.EdgeLabelsDict.unregisterDirty, self.update_labeled_edges ) )        

    def update_labeled_edges(self, *args):
        def _impl():
            op = self.topLevelOperatorView
            if not self.getLayerByName("Edge Labels"):
                return
            edge_labels = op.EdgeLabelsDict.value
            new_pens = {}
            for id_pair, label in edge_labels.items():
                new_pens[id_pair] = self.edge_label_pen_table[label]
            self.apply_new_labeled_edges(new_pens)

        # submit the worklaod in a request and return immediately
        Request(_impl).submit()
    
    @threadRouted
    def apply_new_labeled_edges(self, new_pens):
        # This function is threadRouted because you can't 
        # touch the layer colortable outside the main thread.
        superpixel_edge_layer = self.getLayerByName("Edge Labels")
        if superpixel_edge_layer:
            superpixel_edge_layer.pen_table.update(new_pens)

    def _handle_edge_label_clicked(self, sp_id_pair, new_label):
        """
        The user clicked an edge label.
        Update the operator with the new values.
        """
        print "Edge Label clicked"
        op = self.topLevelOperatorView
        edge_labels = op.EdgeLabelsDict.value
        new_labels = dict( edge_labels )
        new_labels[sp_id_pair] = new_label
        if new_label == 0:
            del new_labels[sp_id_pair]
        op.EdgeLabelsDict.setValue( new_labels )

    # Configure the handler for updated probability maps
    # FIXME: Should we make a new Layer subclass that handles this colortable mapping for us?  Yes.

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

    def update_probability_edges(self, *args):
        def _impl():
            op = self.topLevelOperatorView
            if not self.getLayerByName("Edge Probabilities"):
                return
            edge_probs = op.EdgeProbabilitiesDict.value
            new_pens = {}
            for id_pair, probability in edge_probs.items():
                new_pens[id_pair] = self.probability_pen_table[int(probability * 100)]
            self.apply_new_probability_edges(new_pens)

        # submit the worklaod in a request and return immediately
        Request(_impl).submit()

    @threadRouted
    def apply_new_probability_edges(self, new_pens):
        # This function is threadRouted because you can't 
        # touch the layer colortable outside the main thread.
        superpixel_edge_layer = self.getLayerByName("Edge Probabilities")
        if superpixel_edge_layer:
            superpixel_edge_layer.pen_table.update(new_pens)

    def configure_gui_from_operator(self, *args):
        op = self.topLevelOperatorView
        self.train_from_gt_button.setEnabled( op.GroundtruthSegmentation.ready() )

    def configure_operator_from_gui(self):
        op = self.topLevelOperatorView

    def _handle_train_from_gt_clicked(self):
        op = self.topLevelOperatorView
        op.trainFromGroundtruth()
        self.update_probability_edges()
        
        # Now that we've trained the classifier, the workflow may wish to enable downstream applets.
        self.parentApplet.appletStateUpdateRequested.emit()

    def setupLayers(self):
        layers = []
        op = self.topLevelOperatorView

        # Superpixels -- Edge Labels 
        if op.Superpixels.ready() and op.EdgeLabelsDict.ready():
            edge_labels = op.EdgeLabelsDict.value
            layer = LabelableSegmentationEdgesLayer( LazyflowSource(op.Superpixels), self.edge_label_pen_table, edge_labels )
            layer.name = "Edge Labels"
            layer.visible = True
            layer.opacity = 1.0

            self.update_labeled_edges() # Initialize
            layer.labelChanged.connect( self._handle_edge_label_clicked )
            
            layers.append(layer)
            del layer

        # Superpixels -- Edge Probabilities
        if op.Superpixels.ready() and op.EdgeProbabilitiesDict.ready():
            layer = SegmentationEdgesLayer( LazyflowSource(op.Superpixels) )
            layer.name = "Edge Probabilities" # Name is hard-coded in multiple places: grep before changing.
            layer.visible = True
            layer.opacity = 1.0
            self.update_probability_edges() # Initialize
            layers.append(layer)
            del layer
                
        # Superpixels -- Edges
        if op.Superpixels.ready():
            default_pen = QPen(SegmentationEdgesLayer.DEFAULT_PEN)
            default_pen.setColor(Qt.yellow)
            layer = SegmentationEdgesLayer( LazyflowSource(op.Superpixels), default_pen )
            layer.name = "Superpixel Edges"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)
            del layer
 
        # Naive Segmentation
        if op.NaiveSegmentation.ready():
            layer = self.createStandardLayerFromSlot( op.NaiveSegmentation )
            layer.name = "Naive Segmentation"
            layer.visible = False
            layer.opacity = 0.5
            layers.append(layer)
            del layer
         
        # Groundtruth
        if op.GroundtruthSegmentation.ready():
            layer = self.createStandardLayerFromSlot( op.GroundtruthSegmentation )
            layer.name = "Groundtruth"
            layer.visible = True
            layer.opacity = 0.5
            layers.append(layer)
            del layer
 
        # Voxel data
        if op.VoxelData.ready():
            layer = self._create_grayscale_layer_from_slot( op.VoxelData,
                                                            op.VoxelData.meta.getTaggedShape()['c'] )
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
