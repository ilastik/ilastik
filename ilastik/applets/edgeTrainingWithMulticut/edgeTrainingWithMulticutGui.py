###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2019, the ilastik developers
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
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QIcon

from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.applets.edgeTraining.edgeTrainingGui import EdgeTrainingGui
from ilastik.applets.multicut.multicutGui import MulticutGuiMixin
import ilastik.utility.gui as guiutil


class EdgeTrainingWithMulticutGui(MulticutGuiMixin, EdgeTrainingGui):
    def __init__(self, parentApplet, topLevelOperatorView):
        self.__cleanup_fns = []
        self.topLevelOperatorView = topLevelOperatorView
        MulticutGuiMixin.__init__(self, parentApplet, topLevelOperatorView)
        EdgeTrainingGui.__init__(self, parentApplet, topLevelOperatorView)

    def enable_live_update_on_edges_available(self, *args, **kwargs):
        op = self.topLevelOperatorView
        lane_dicts_ready = [(bool(dct.value) and dct.ready()) for dct in op.viewed_operator().EdgeLabelsDict]
        have_edges = any(lane_dicts_ready)
        if not have_edges:
            self.live_multicut_button.setChecked(False)
            self.live_update_button.setChecked(False)
            self.live_multicut_button.setIcon(QIcon(ilastikIcons.Play))
            self.live_update_button.setIcon(QIcon(ilastikIcons.Play))
        self.live_update_button.setEnabled(have_edges)
        self.configure_operator_from_gui()
        return have_edges

    def _after_init(self):
        def syncLiveUpdate():
            if self.live_multicut_button.isChecked():
                self.live_update_button.setChecked(True)
                self.live_update_button.setIcon(QIcon(ilastikIcons.Pause))

        self.live_multicut_button.toggled.connect(syncLiveUpdate)
        self.live_update_button.toggled.connect(syncLiveUpdate)
        EdgeTrainingGui._after_init(self)
        MulticutGuiMixin._after_init(self)

    def initAppletDrawerUi(self):
        training_controls = EdgeTrainingGui.createDrawerControls(self)
        training_controls.layout().setContentsMargins(5, 0, 5, 0)
        training_layout = QVBoxLayout()
        training_layout.addWidget(training_controls)
        training_layout.setContentsMargins(0, 15, 0, 0)
        training_box = QGroupBox("Training", parent=self)
        training_box.setLayout(training_layout)
        training_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        multicut_controls = MulticutGuiMixin.createDrawerControls(self)
        multicut_controls.layout().setContentsMargins(5, 0, 5, 0)
        multicut_layout = QVBoxLayout()
        multicut_layout.addWidget(multicut_controls)
        multicut_layout.setContentsMargins(0, 15, 0, 0)
        multicut_box = QGroupBox("Multicut", parent=self)
        multicut_box.setLayout(multicut_layout)
        multicut_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        multicut_box.setEnabled(False)

        op = self.topLevelOperatorView
        multicut_required_slots = (op.Superpixels, op.Rag, op.EdgeProbabilities, op.EdgeProbabilitiesDict)
        self.__cleanup_fns.append(guiutil.enable_when_ready(multicut_box, multicut_required_slots))

        drawer_layout = QVBoxLayout()
        drawer_layout.addWidget(training_box)
        drawer_layout.addWidget(multicut_box)
        drawer_layout.setSpacing(2)
        drawer_layout.setContentsMargins(5, 5, 5, 5)
        drawer_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self._drawer = QWidget(parent=self)
        self._drawer.setLayout(drawer_layout)

        # GUI will be initialized in _after_init()
        # self.configure_gui_from_operator()

    def appletDrawer(self):
        return self._drawer

    def stopAndCleanUp(self):
        # Unsubscribe to all signals
        for fn in self.__cleanup_fns:
            fn()

        # Base classes
        EdgeTrainingGui.stopAndCleanUp(self)
        MulticutGuiMixin.stopAndCleanUp(self)

    def setupLayers(self):
        layers = []
        edgeTrainingLayers = EdgeTrainingGui.setupLayers(self)

        mc_disagreement_layer = MulticutGuiMixin.create_multicut_disagreement_layer(self)
        if mc_disagreement_layer:
            layers.append(mc_disagreement_layer)

        mc_edge_layer = MulticutGuiMixin.create_multicut_edge_layer(self)
        if mc_edge_layer:
            layers.append(mc_edge_layer)

        mc_seg_layer = MulticutGuiMixin.create_multicut_segmentation_layer(self)
        if mc_seg_layer:
            layers.append(mc_seg_layer)

        layers += edgeTrainingLayers
        return layers

    def configure_gui_from_operator(self, *args):
        EdgeTrainingGui.configure_gui_from_operator(self)
        MulticutGuiMixin.configure_gui_from_operator(self)

    def configure_operator_from_gui(self):
        EdgeTrainingGui.configure_operator_from_gui(self)
        MulticutGuiMixin.configure_operator_from_gui(self)
        self.configure_gui_from_operator()

