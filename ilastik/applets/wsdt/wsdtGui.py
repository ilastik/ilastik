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
from contextlib import contextmanager
import threading

import numpy as np

import sip
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QWidget, QLabel, QSpinBox, QDoubleSpinBox, QVBoxLayout, QMenu, QAction, \
                        QHBoxLayout, QSpacerItem, QSizePolicy, QColor, QPen, QComboBox, QPushButton

from ilastik.utility.gui import threadRouted
from volumina.pixelpipeline.datasources import LazyflowSource, ArraySource
from volumina.layer import GrayscaleLayer, ColortableLayer, generateRandomColors
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

from lazyflow.request import Request
from lazyflow.utility import TransposedView

import logging
from PyQt4.Qt import QCheckBox
logger = logging.getLogger(__name__)

class WsdtGui(LayerViewerGui):

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
        super( WsdtGui, self ).stopAndCleanUp()
    
    ###########################################
    ###########################################
    
    def __init__(self, parentApplet, topLevelOperatorView):
        self.__cleanup_fns = []
        self._currently_updating = False
        self.topLevelOperatorView = topLevelOperatorView
        super(WsdtGui, self).__init__( parentApplet, topLevelOperatorView )
        
        self._sp_colortable = generateRandomColors(256, clamp={'v': 1.0, 's' : 0.5}, zeroIsTransparent=True)
        
        self._threshold_colortable = [ QColor(0, 0, 0, 0).rgba(),      # transparent
                                       QColor(0, 255, 0, 255).rgba() ] # green

        # Any time watershed is re-computed, re-update the layer set, in case the set of debug layers has changed.
        self.topLevelOperatorView.watershed_completed.subscribe( self.updateAllLayers )

    def initAppletDrawerUi(self):
        """
        Overridden from base class (LayerViewerGui)
        """
        op = self.topLevelOperatorView
        
        def configure_update_handlers( qt_signal, op_slot ):
            qt_signal.connect( self.configure_operator_from_gui )
            op_slot.notifyDirty( self.configure_gui_from_operator )
            self.__cleanup_fns.append( partial( op_slot.unregisterDirty, self.configure_gui_from_operator ) )

        def control_layout( label_text, widget ):
            row_layout = QHBoxLayout()
            row_layout.addWidget( QLabel(label_text) )
            row_layout.addSpacerItem( QSpacerItem(10, 0, QSizePolicy.Expanding) )
            row_layout.addWidget(widget)
            return row_layout

        drawer_layout = QVBoxLayout()

        channel_button = QPushButton()
        self.channel_menu = QMenu(self) # Must retain menus (in self) or else they get deleted.
        channel_button.setMenu(self.channel_menu)
        channel_button.clicked.connect(channel_button.showMenu)
        def populate_channel_menu(*args):
            if sip.isdeleted(channel_button):
                return
            self.channel_menu.clear()
            self.channel_actions = []
            for ch in range(op.Input.meta.getTaggedShape()['c']):
                action = QAction("Channel {}".format(ch), self.channel_menu)
                action.setCheckable(True)
                self.channel_menu.addAction(action)
                self.channel_actions.append(action)
                configure_update_handlers( action.toggled, op.ChannelSelections )
        populate_channel_menu()
        op.Input.notifyMetaChanged( populate_channel_menu )
        self.__cleanup_fns.append( partial( op.Input.unregisterMetaChanged, populate_channel_menu ) )
        drawer_layout.addLayout( control_layout( "Input Channel", channel_button ) )
        self.channel_button = channel_button

        threshold_box = QDoubleSpinBox()
        threshold_box.setDecimals(2)
        threshold_box.setMinimum(0.00)
        threshold_box.setMaximum(1.0)
        threshold_box.setSingleStep(0.1)
        configure_update_handlers( threshold_box.valueChanged, op.Pmin )
        drawer_layout.addLayout( control_layout( "Threshold", threshold_box ) )
        self.threshold_box = threshold_box

        membrane_size_box = QSpinBox()
        membrane_size_box.setMinimum(0)
        membrane_size_box.setMaximum(1000000)
        configure_update_handlers( membrane_size_box.valueChanged, op.MinMembraneSize )
        drawer_layout.addLayout( control_layout( "Min Membrane Size", membrane_size_box ) )
        self.membrane_size_box = membrane_size_box

        seed_presmoothing_box = QDoubleSpinBox()
        seed_presmoothing_box.setDecimals(1)
        seed_presmoothing_box.setMinimum(0.0)
        seed_presmoothing_box.setMaximum(10.0)
        seed_presmoothing_box.setSingleStep(0.1)
        configure_update_handlers( seed_presmoothing_box.valueChanged, op.SigmaMinima )
        drawer_layout.addLayout( control_layout( "Presmooth before seeds", seed_presmoothing_box ) )
        self.seed_presmoothing_box = seed_presmoothing_box

        seed_method_combo = QComboBox()
        seed_method_combo.addItem("Connected")
        seed_method_combo.addItem("Clustered")
        configure_update_handlers( seed_method_combo.currentIndexChanged, op.GroupSeeds )
        drawer_layout.addLayout( control_layout( "Seed Labeling", seed_method_combo ) )
        self.seed_method_combo = seed_method_combo
        
        watershed_presmoothing_box = QDoubleSpinBox()
        watershed_presmoothing_box.setDecimals(1)
        watershed_presmoothing_box.setMinimum(0.0)
        watershed_presmoothing_box.setMaximum(10.0)
        watershed_presmoothing_box.setSingleStep(0.1)
        configure_update_handlers( watershed_presmoothing_box.valueChanged, op.SigmaWeights )
        drawer_layout.addLayout( control_layout( "Presmooth before watershed", watershed_presmoothing_box ) )
        self.watershed_presmoothing_box = watershed_presmoothing_box

        superpixel_size_box = QSpinBox()
        superpixel_size_box.setMinimum(0)
        superpixel_size_box.setMaximum(1000000)
        configure_update_handlers( superpixel_size_box.valueChanged, op.MinSegmentSize )
        drawer_layout.addLayout( control_layout( "Min Superpixel Size", superpixel_size_box ) )
        self.superpixel_size_box = superpixel_size_box

        preserve_pmaps_box = QCheckBox()
        configure_update_handlers( preserve_pmaps_box.toggled, op.PreserveMembranePmaps )
        drawer_layout.addLayout( control_layout( "Preserve membrane probabilities", preserve_pmaps_box ) )
        self.preserve_pmaps_box = preserve_pmaps_box

        enable_debug_box = QCheckBox()
        configure_update_handlers( enable_debug_box.toggled, op.EnableDebugOutputs )
        drawer_layout.addLayout( control_layout( "Show Debug Layers", enable_debug_box ) )
        self.enable_debug_box = enable_debug_box

        op.Superpixels.notifyReady(self.configure_gui_from_operator)
        op.Superpixels.notifyUnready(self.configure_gui_from_operator)
        self.__cleanup_fns.append( partial( op.Superpixels.unregisterReady, self.configure_gui_from_operator ) )
        self.__cleanup_fns.append( partial( op.Superpixels.unregisterUnready, self.configure_gui_from_operator ) )

        self.update_ws_button = QPushButton("Update Watershed", clicked=self.onUpdateWatershedsButton)
        drawer_layout.addWidget( self.update_ws_button )

        drawer_layout.setSpacing(0)
        drawer_layout.addSpacerItem( QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding) )
        
        # Finally, the whole drawer widget
        drawer = QWidget(parent=self)
        drawer.setLayout(drawer_layout)

        # Save these members for later use
        self._drawer = drawer

        # Initialize everything with the operator's initial values
        self.configure_gui_from_operator()

    @contextmanager
    def set_updating(self):
        assert not self._currently_updating
        self._currently_updating = True
        yield
        self._currently_updating = False

    def configure_gui_from_operator(self, *args):
        if self._currently_updating:
            return False
        with self.set_updating():
            op = self.topLevelOperatorView
            
            channel_selections = op.ChannelSelections.value
            for ch in range(op.Input.meta.shape[-1]):
                self.channel_actions[ch].setChecked(ch in channel_selections)

            if len(channel_selections) == 0:
                self.channel_button.setText("Please Select")
            else:
                self.channel_button.setText(",".join(map(str, channel_selections)))
            
            self.threshold_box.setValue( op.Pmin.value )
            self.membrane_size_box.setValue( op.MinMembraneSize.value )
            self.superpixel_size_box.setValue( op.MinSegmentSize.value )
            self.seed_presmoothing_box.setValue( op.SigmaMinima.value )
            self.watershed_presmoothing_box.setValue( op.SigmaWeights.value )
            self.seed_method_combo.setCurrentIndex( int(op.GroupSeeds.value) )
            self.preserve_pmaps_box.setChecked( op.PreserveMembranePmaps.value )
            self.enable_debug_box.setChecked( op.EnableDebugOutputs.value )
            
            self.update_ws_button.setEnabled( op.Superpixels.ready() )

    def configure_operator_from_gui(self):
        if self._currently_updating:
            return False
        with self.set_updating():
            op = self.topLevelOperatorView
            
            channel_selections = []
            for ch in range(len(self.channel_actions)):
                if self.channel_actions[ch].isChecked():
                    channel_selections.append(ch)

            op.ChannelSelections.setValue( channel_selections )
            op.Pmin.setValue( self.threshold_box.value() )
            op.MinMembraneSize.setValue( self.membrane_size_box.value() )
            op.MinSegmentSize.setValue( self.superpixel_size_box.value() )
            op.SigmaMinima.setValue( self.seed_presmoothing_box.value() )
            op.SigmaWeights.setValue( self.watershed_presmoothing_box.value() )
            op.GroupSeeds.setValue( bool(self.seed_method_combo.currentIndex()) )
            op.PreserveMembranePmaps.setValue( self.preserve_pmaps_box.isChecked() )
            op.EnableDebugOutputs.setValue( self.enable_debug_box.isChecked() )

        # The GUI may need to respond to some changes in the operator outputs.
        self.configure_gui_from_operator()

    def onUpdateWatershedsButton(self):
        def updateThread():
            """
            Temporarily unfreeze the cache and freeze it again after the views are finished rendering.
            """
            self.topLevelOperatorView.FreezeCache.setValue(False)
            
            # This is hacky, but for now it's the only way to do it.
            # We need to make sure the rendering thread has actually seen that the cache
            # has been updated before we ask it to wait for all views to be 100% rendered.
            # If we don't wait, it might complete too soon (with the old data).
            ndim = len(self.topLevelOperatorView.Superpixels.meta.shape)
            self.topLevelOperatorView.Superpixels((0,)*ndim, (1,)*ndim).wait()

            # Wait for the image to be rendered into all three image views
            for imgView in self.editor.imageViews:
                if imgView.isVisible():
                    imgView.scene().joinRenderingAllTiles()
            self.topLevelOperatorView.FreezeCache.setValue(True)

        self.getLayerByName("Superpixels").visible = True
        th = threading.Thread(target=updateThread)
        th.start()

    def setupLayers(self):
        layers = []
        op = self.topLevelOperatorView

        # Superpixels
        if op.Superpixels.ready():
            layer = ColortableLayer( LazyflowSource(op.Superpixels), self._sp_colortable )
            layer.colortableIsRandom = True
            layer.name = "Superpixels"
            layer.visible = True
            layer.opacity = 0.5
            layers.append(layer)
            del layer

        # Debug layers
        if op.debug_results:
            for name, compressed_array in op.debug_results.items():
                axiskeys = op.Superpixels.meta.getAxisKeys()[:-1] # debug images don't have a channel axis
                permutation = map(lambda key: axiskeys.index(key) if key in axiskeys else None, 'txyzc')
                arraysource = ArraySource( TransposedView(compressed_array, permutation) )
                if compressed_array.dtype == np.uint32:
                    layer = ColortableLayer(arraysource, self._sp_colortable)
                else:
                    layer = GrayscaleLayer(arraysource)
                    # TODO: Normalize? Maybe the drange should be included with the debug image.
                layer.name = name
                layer.visible = False
                layer.opacity = 1.0
                layers.append(layer)
                del layer

        # Threshold
        if op.ThresholdedInput.ready():
            layer = ColortableLayer( LazyflowSource(op.ThresholdedInput), self._threshold_colortable )
            layer.name = "Thresholded Input"
            layer.visible = True
            layer.opacity = 1.0
            layers.append(layer)
            del layer

        # Raw Data (grayscale)
        if op.Input.ready():
            layer = self._create_grayscale_layer_from_slot( op.Input, op.Input.meta.getTaggedShape()['c'] )
            layer.name = "Input"
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
