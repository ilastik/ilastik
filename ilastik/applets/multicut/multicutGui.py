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

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPen, QIcon
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QDoubleSpinBox,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QPushButton,
)

from ilastik.utility.gui import threadRouted
from volumina.api import createDataSource
from volumina.layer import SegmentationEdgesLayer
from volumina.utility import ShortcutManager

from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.applets.multicut.opMulticut import OpMulticutAgglomerator, AVAILABLE_SOLVER_NAMES, DEFAULT_SOLVER_NAME

from lazyflow.request import Request

import logging

logger = logging.getLogger(__name__)

# This is a mixin that can be added to any LayerViewerGui subclass
# See MulticutGui (bottom of this file) for the standalone version.
class MulticutGuiMixin(object):

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################

    def stopAndCleanUp(self):
        # Unsubscribe to all signals
        for fn in self.__cleanup_fns:
            fn()

        super(MulticutGuiMixin, self).stopAndCleanUp()

    ###########################################
    ###########################################

    def __init__(self, parentApplet, topLevelOperatorView):
        self.__cleanup_fns = []
        self.__topLevelOperatorView = topLevelOperatorView
        self.superpixel_edge_layer = None
        self.disagreement_layer = None
        super(MulticutGuiMixin, self).__init__(parentApplet, topLevelOperatorView)
        self.__init_probability_colortable()
        self.__init_disagreement_label_colortable()

    def _after_init(self):
        pass

    def createDrawerControls(self):
        """
        This is a separate function from initAppletDrawer() so that it can be
        called and used within another applet (this class is a mixin).
        """
        op = self.__topLevelOperatorView

        def configure_update_handlers(qt_signal, op_slot):
            qt_signal.connect(self.configure_operator_from_gui)
            op_slot.notifyDirty(self.configure_gui_from_operator)
            self.__cleanup_fns.append(partial(op_slot.unregisterDirty, self.configure_gui_from_operator))

        def control_layout(label_text, widget):
            row_layout = QHBoxLayout()
            row_layout.addWidget(QLabel(label_text))
            row_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Expanding))
            row_layout.addWidget(widget)
            return row_layout

        drawer_layout = QVBoxLayout()
        drawer_layout.setSpacing(1)

        # Beta
        beta_box = QDoubleSpinBox(
            decimals=2,
            minimum=0.01,
            maximum=0.99,
            singleStep=0.1,
            toolTip="Bias parameter for the multicut optimization.",
        )
        configure_update_handlers(beta_box.valueChanged, op.Beta)
        beta_layout = control_layout("Beta", beta_box)
        drawer_layout.addLayout(beta_layout)
        self.beta_box = beta_box

        # Solver
        solver_name_combo = QComboBox(
            toolTip="Multicut optimization technique. Available solvers depend on which optimizer library you have installed."
        )
        for solver_name in AVAILABLE_SOLVER_NAMES:
            solver_name_combo.addItem(solver_name)
        configure_update_handlers(solver_name_combo.currentIndexChanged, op.SolverName)
        drawer_layout.addLayout(control_layout("Solver", solver_name_combo))
        self.solver_name_combo = solver_name_combo

        button_layout = QHBoxLayout()

        # Live Multicut Button
        live_multicut_button = QPushButton(text="Live Multicut", checkable=True, icon=QIcon(ilastikIcons.Play))
        configure_update_handlers(live_multicut_button.toggled, op.FreezeCache)

        # Extra: Auto-show the multicut edges if necessary.
        def auto_show_multicut_layer(checked):
            if checked:
                self.getLayerByName("Multicut Edges").visible = True

        live_multicut_button.toggled.connect(auto_show_multicut_layer)

        button_layout.addWidget(live_multicut_button)
        self.live_multicut_button = live_multicut_button

        # Update Button
        update_button = QPushButton(
            text="Update Now", icon=QIcon(ilastikIcons.Play), clicked=self._handle_multicut_update_clicked
        )
        button_layout.addWidget(update_button)
        self.update_button = update_button

        drawer_layout.addLayout(button_layout)

        # Layout
        drawer_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Finally, the whole drawer widget
        drawer = QWidget(parent=self)
        drawer.setLayout(drawer_layout)

        # Widget Shortcuts
        mgr = ShortcutManager()
        ActionInfo = ShortcutManager.ActionInfo
        shortcut_group = "Multicut"
        mgr.register(
            "u",
            ActionInfo(
                shortcut_group,
                "UpdateMulticut",
                "Run the multicut optimization using the current edge probabilities",
                update_button.click,
                update_button,
                update_button,
            ),
        )

        return drawer

    def __init_probability_colortable(self):
        self.probability_colortable = []
        for v in np.linspace(0.0, 1.0, num=101):
            self.probability_colortable.append(QColor(255 * (v), 255 * (1.0 - v), 0))

        self.probability_pen_table = []
        for color in self.probability_colortable:
            pen = QPen(SegmentationEdgesLayer.DEFAULT_PEN)
            pen.setColor(color)
            self.probability_pen_table.append(pen)

        # When the edge probabilities are dirty, update the probability edge layer pens
        op = self.__topLevelOperatorView
        op.EdgeProbabilitiesDict.notifyDirty(self.__update_probability_edges)
        self.__cleanup_fns.append(partial(op.EdgeProbabilitiesDict.unregisterDirty, self.__update_probability_edges))

    # Configure the handler for updated probability maps
    # FIXME: Should we make a new Layer subclass that handles this colortable mapping for us?  Yes.
    def __update_probability_edges(self, *args):
        def _impl():
            op = self.__topLevelOperatorView
            if not self.superpixel_edge_layer:
                return
            edge_probs = op.EdgeProbabilitiesDict.value
            new_pens = {}
            for id_pair, probability in list(edge_probs.items()):
                new_pens[id_pair] = self.probability_pen_table[int(probability * 100)]
            self.__apply_new_probability_edges(new_pens)

        # submit the worklaod in a request and return immediately
        Request(_impl).submit()

    @threadRouted
    def __apply_new_probability_edges(self, new_pens):
        # This function is threadRouted because you can't
        # touch the layer colortable outside the main thread.
        self.superpixel_edge_layer.pen_table.update(new_pens)

    def __init_disagreement_label_colortable(self):
        self.disagreement_colortable = [QColor(255, 0, 255, 255), QColor(0, 255, 255, 255)]  # magenta  # cyan

        self.disagreement_pen_table = []
        for color in self.disagreement_colortable:
            pen = QPen(SegmentationEdgesLayer.DEFAULT_PEN)
            pen.setColor(color)
            pen.setWidth(3)
            self.disagreement_pen_table.append(pen)

        op = self.topLevelOperatorView
        op.EdgeLabelDisagreementDict.notifyReady(self.__update_disagreement_edges)
        self.__cleanup_fns.append(
            partial(op.EdgeLabelDisagreementDict.unregisterReady, self.__update_disagreement_edges)
        )
        op.EdgeLabelDisagreementDict.notifyDirty(self.__update_disagreement_edges)
        self.__cleanup_fns.append(
            partial(op.EdgeLabelDisagreementDict.unregisterDirty, self.__update_disagreement_edges)
        )

    def __update_disagreement_edges(self, *args):
        self.__init_disagreement_label_colortable()

        def _impl():
            op = self.__topLevelOperatorView
            if not self.disagreement_layer:
                return

            edge_disagreements = op.EdgeLabelDisagreementDict.value
            new_pens = {}
            for id_pair, disagreement_label in list(edge_disagreements.items()):
                new_pens[id_pair] = self.disagreement_pen_table[disagreement_label]
            self.__apply_disagreement_edges(new_pens)

        # submit the worklaod in a request and return immediately
        Request(_impl).submit()

    @threadRouted
    def __apply_disagreement_edges(self, new_pens):
        # This function is threadRouted because you can't
        # touch the layer colortable outside the main thread.
        if self.disagreement_layer:
            self.disagreement_layer.pen_table.overwrite(new_pens)

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
            op = self.__topLevelOperatorView
            self.update_button.setEnabled(op.FreezeCache.value)
            self.live_multicut_button.setChecked(not op.FreezeCache.value)
            if op.FreezeCache.value:
                self.live_multicut_button.setIcon(QIcon(ilastikIcons.Play))
            else:
                self.live_multicut_button.setIcon(QIcon(ilastikIcons.Pause))
            self.beta_box.setValue(op.Beta.value)

            solver_name = op.SolverName.value
            try:
                solver_index = AVAILABLE_SOLVER_NAMES.index(solver_name)
            except ValueError:
                # If the solver name is unknown to us, then
                # this project file must have been created on a different machine,
                # where we had access to different solvers.
                # Override the solver name with the default.
                solver_index = AVAILABLE_SOLVER_NAMES.index(DEFAULT_SOLVER_NAME)
                op.SolverName.setValue(DEFAULT_SOLVER_NAME)
            self.solver_name_combo.setCurrentIndex(solver_index)

    def configure_operator_from_gui(self):
        if self._currently_updating:
            return False
        with self.set_updating():
            op = self.__topLevelOperatorView
            op.Beta.setValue(self.beta_box.value())
            op.SolverName.setValue(str(self.solver_name_combo.currentText()))
            op.FreezeCache.setValue(not self.live_multicut_button.isChecked())

        # The GUI may need to respond to some changes in the operator outputs
        # (e.g. the FreezeCache setting).
        self.configure_gui_from_operator()

    def _handle_multicut_update_clicked(self):
        def updateThread():
            """
            Temporarily unfreeze the cache and freeze it again after the views are finished rendering.
            """
            with self.set_updating():
                self.topLevelOperatorView.FreezeCache.setValue(False)
                self.topLevelOperatorView.FreezeClassifier.setValue(False)
                self.update_button.setEnabled(False)
                self.live_multicut_button.setEnabled(False)

                # This is hacky, but for now it's the only way to do it.
                # We need to make sure the rendering thread has actually seen that the cache
                # has been updated before we ask it to wait for all views to be 100% rendered.
                # If we don't wait, it might complete too soon (with the old data).
                ndim = len(self.topLevelOperatorView.Output.meta.shape)
                self.topLevelOperatorView.Output((0,) * ndim, (1,) * ndim).wait()

                # Wait for the image to be rendered into all three image views
                for imgView in self.editor.imageViews:
                    if imgView.isVisible():
                        imgView.scene().joinRenderingAllTiles()
                self.topLevelOperatorView.FreezeCache.setValue(True)
                self.topLevelOperatorView.FreezeClassifier.setValue(True)
                self.update_button.setEnabled(True)
                self.live_multicut_button.setEnabled(True)

        self.getLayerByName("Multicut Edges").visible = True
        # self.getLayerByName("Multicut Segmentation").visible = True
        th = threading.Thread(target=updateThread)
        th.start()

    def create_multicut_disagreement_layer(self):
        ActionInfo = ShortcutManager.ActionInfo
        op = self.__topLevelOperatorView
        if not op.Output.ready():
            return None

        # Final segmentation -- Edges
        default_pen = QPen(SegmentationEdgesLayer.DEFAULT_PEN)
        default_pen.setColor(Qt.transparent)
        layer = SegmentationEdgesLayer(createDataSource(op.Superpixels), default_pen)
        layer.name = "Multicut Disagreements"
        layer.visible = False  # Off by default...
        layer.opacity = 1.0
        self.disagreement_layer = layer
        self.__update_disagreement_edges()  # Initialize

        layer.shortcutRegistration = (
            "d",
            ActionInfo(
                "Multicut",
                "MulticutDisagrementVisibility",
                "Show/Hide Multicut Disagreement Edges",
                layer.toggleVisible,
                self.viewerControlWidget(),
                layer,
            ),
        )

        return layer

    def create_multicut_edge_layer(self):
        ActionInfo = ShortcutManager.ActionInfo
        op = self.__topLevelOperatorView
        if not op.Output.ready():
            return None

        # Final segmentation -- Edges
        default_pen = QPen(SegmentationEdgesLayer.DEFAULT_PEN)
        default_pen.setColor(Qt.blue)
        layer = SegmentationEdgesLayer(createDataSource(op.Output), default_pen)
        layer.name = "Multicut Edges"
        layer.visible = False  # Off by default...
        layer.opacity = 1.0

        layer.shortcutRegistration = (
            "m",
            ActionInfo(
                "Multicut",
                "MulticutEdgesVisibility",
                "Show/Hide Multicut Edges",
                layer.toggleVisible,
                self.viewerControlWidget(),
                layer,
            ),
        )

        return layer

    def create_multicut_segmentation_layer(self):
        op = self.__topLevelOperatorView
        # Final segmentation -- Label Image
        if not op.Output.ready():
            return None

        layer = self.createStandardLayerFromSlot(op.Output)
        layer.name = "Multicut Segmentation"
        layer.colortableIsRandom = True
        layer.visible = False  # Off by default...
        layer.opacity = 0.5
        return layer

    def setupLayers(self):
        layers = []
        op = self.__topLevelOperatorView

        mc_disagreement_layer = self.create_multicut_disagreement_layer()
        if mc_disagreement_layer:
            layers.append(mc_disagreement_layer)

        mc_edge_layer = self.create_multicut_edge_layer()
        if mc_edge_layer:
            layers.append(mc_edge_layer)

        # Superpixels -- Edge Probabilities
        # We use the RAG's superpixels, which may have different IDs
        self.superpixel_edge_layer = None
        if op.Superpixels.ready() and op.EdgeProbabilitiesDict.ready():
            layer = SegmentationEdgesLayer(createDataSource(op.Superpixels))
            layer.name = "Superpixel Edge Probabilities"
            layer.visible = True
            layer.opacity = 1.0
            self.superpixel_edge_layer = layer
            self.__update_probability_edges()  # Initialize
            layers.append(layer)
            del layer

        # Superpixels -- Edges
        if op.Superpixels.ready():
            default_pen = QPen(SegmentationEdgesLayer.DEFAULT_PEN)
            default_pen.setColor(Qt.yellow)
            layer = SegmentationEdgesLayer(createDataSource(op.Superpixels), default_pen)
            layer.name = "Superpixel Edges"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)
            del layer

        mc_seg_layer = self.create_multicut_segmentation_layer()
        if mc_seg_layer:
            layers.append(mc_seg_layer)

        # Superpixels
        if op.Superpixels.ready():
            layer = self.createStandardLayerFromSlot(op.Superpixels)
            layer.name = "Superpixels"
            layer.visible = False
            layer.opacity = 0.5
            layers.append(layer)
            del layer

        # Raw Data (grayscale)
        if op.RawData.ready():
            layer = self.createStandardLayerFromSlot(op.RawData)
            layer.name = "Raw Data"
            layer.visible = True
            layer.opacity = 1.0
            layers.append(layer)
            layer.shortcutRegistration = (
                "i",
                ActionInfo(
                    "Multicut" "Hide all but Raw",
                    "Hide all but Raw",
                    partial(self.toggle_show_raw, "Raw Data"),
                    self.viewerControlWidget(),
                    layer,
                ),
            )

            del layer

        return layers


class MulticutGui(MulticutGuiMixin, LayerViewerGui):
    def appletDrawer(self):
        return self.__drawer

    def initAppletDrawerUi(self):
        """
        Overridden from base class (LayerViewerGui)
        """
        # Save these members for later use
        self.__drawer = self.createDrawerControls()

        # Initialize everything with the operator's initial values
        self.configure_gui_from_operator()
