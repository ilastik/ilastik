###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2021, the ilastik developers
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
#          http://ilastik.org/license.html
###############################################################################
import logging
import os
from pathlib import Path
import time
import traceback
from functools import partial

import numpy
from PyQt5 import uic
from PyQt5.QtCore import (
    Qt,
    QTimer,
    pyqtSlot,
)
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import (
    QAction,
    QColorDialog,
    QMessageBox,
    QStackedWidget,
    QWidget,
    QToolButton,
    QListWidget,
    QAbstractItemView,
)
from ilastik.applets.neuralNetwork.unetStateControl import busy_cursor
from ilastik.applets.labeling import LABELING_DIR
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.widgets.labelListModel import Label
from volumina.api import AlphaModulatedLayer, LazyflowSource
from volumina.utility import ShortcutManager
from volumina.api import GrayscaleLayer
from volumina import colortables

from ilastik.applets.labeling.labelingGui import Tool
from ilastik.utility.gui import threadRouted

from .tiktorchController import TiktorchUnetController, TiktorchUnetOperatorModel

logger = logging.getLogger(__name__)


class CheckpointWidget(QWidget):
    def __init__(
        self,
        *,
        parent: QWidget,
        add: QToolButton,
        remove: QToolButton,
        load: QToolButton,
        view: QListWidget,
    ):
        super().__init__(parent=parent)
        self._add_btn = add
        self._remove_btn = remove
        self._load_btn = load
        self._list = view
        self._list.setSelectionMode(QAbstractItemView.SingleSelection)

        self._add_btn.clicked.connect(self._on_add)
        self._remove_btn.clicked.connect(self._on_remove)
        self._load_btn.clicked.connect(self._on_load)

    def setup(self, tiktorch_controller: TiktorchUnetController, tiktorch_model: TiktorchUnetOperatorModel):
        self._tiktorch_controller = tiktorch_controller
        self._tiktorch_model = tiktorch_model
        self._checkpoint_dir = self._tiktorch_model.session.unet_config.get_checkpoint_dir()

        assert self._checkpoint_dir.exists()
        self._refresh_checkpoint_list()

    def clear(self):
        self._list.clear()

    def _refresh_checkpoint_list(self):
        self.clear()
        checkpoints = sorted(os.listdir(self._checkpoint_dir))
        for checkpoint in checkpoints:
            if checkpoint.endswith(".pt") or checkpoint.endswith(".pytorch"):
                self._list.addItem(checkpoint)

    def _on_add(self):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        checkpoint_name = f"{timestamp}.pt"
        checkpoint_path = self._checkpoint_dir / checkpoint_name

        try:
            self._save(checkpoint_path)
            QMessageBox.information(self, "Checkpoint Saved", f"Checkpoint saved as '{checkpoint_name}'.")
            self._refresh_checkpoint_list()
        except Exception as e:
            QMessageBox.critical(self, "Error Saving Checkpoint", f"An error occurred: {e}")

    @busy_cursor
    def _save(self, checkpoint_path: Path):
        self._tiktorch_model.session.save_checkpoint(checkpoint_path)

    def _on_remove(self):
        selected_items = self._list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a checkpoint to remove.")
            return

        assert len(selected_items) == 1, "Single selection"
        item = selected_items[0]

        checkpoint_name = item.text()
        checkpoint_path = os.path.join(self._checkpoint_dir, checkpoint_name)

        try:
            os.remove(checkpoint_path)
            QMessageBox.information(self, "Checkpoint Removed", f"Checkpoint '{checkpoint_name}' has been removed.")
        except Exception as e:
            QMessageBox.critical(self, "Error Removing Checkpoint", f"An error occurred: {e}")

        self._refresh_checkpoint_list()

    def _on_load(self):
        selected_items = self._list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a checkpoint to load.")
            return

        assert len(selected_items) == 1, "Single selection"
        item = selected_items[0]

        checkpoint_name = item.text()
        checkpoint_path = self._checkpoint_dir / checkpoint_name

        try:
            self._reload(checkpoint_path)
            QMessageBox.information(self, "Checkpoint Loaded", f"Checkpoint '{checkpoint_name}' has been loaded.")
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Checkpoint", f"An error occurred: {e}")

    @busy_cursor
    def _reload(self, checkpoint_path: Path):
        updated_unet_config = self._tiktorch_model.session.unet_config.resume_with_checkpoint(checkpoint_path)
        self._tiktorch_controller.closeSession()
        self._tiktorch_controller.initTraining(updated_unet_config)


class NNTrainingClassGui(LayerViewerGui):
    """
    LayerViewerGui class for Neural Network Classification

    todo: monitor the state of the training loop (we need to know if for example the training has failed)
    """

    def viewerControlWidget(self):
        """
        Return the widget that controls how the content of the central widget is displayed
        """
        return self._viewerControlUi

    def centralWidget(self):
        """
        Return the widget that will be displayed in the main viewer area.
        """
        return self

    def stopAndCleanUp(self):
        """
        The gui should stop updating all data views and should clean up any resources it created
        """
        super(NNTrainingClassGui, self).stopAndCleanUp()

        logger.info("Closing session.")
        for fn in self.__cleanup_fns:
            fn()

    def menus(self):
        """
        Return a list of QMenu widgets to be shown in the menu bar when this applet is visible
        """
        menus = super(NNTrainingClassGui, self).menus()
        return menus

    def _added(self, snapshot):
        self.topLevelOperatorView.Checkpoints.setValue(list(snapshot))

    def checkpoints_dirty(self, slot, roi):
        self.checkpoint_mng.setData(slot.value)

    def _initCheckpointActions(self):
        self.checkpoint_widget = CheckpointWidget(
            parent=self,
            add=self._drawer.addCheckpoint,
            remove=self._drawer.removeCheckpoint,
            load=self._drawer.loadCheckpoint,
            view=self._drawer.checkpointList,
        )

    def __init__(self, parentApplet, topLevelOperatorView):
        self.parentApplet = parentApplet

        super(NNTrainingClassGui, self).__init__(
            parentApplet,
            topLevelOperatorView,
        )

        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir + "/nnTrainingClass.ui")

        iconsDir = LABELING_DIR / "icons"
        if hasattr(self._drawer, "thresToolButton"):
            thresholdIconPath = str(iconsDir / "threshold.png")
            thresholdIcon = QIcon(thresholdIconPath)
            self._drawer.thresToolButton.setIcon(thresholdIcon)
            self._drawer.thresToolButton.setCheckable(True)
            self._drawer.thresToolButton.clicked.connect(
                lambda checked: self._handleToolButtonClicked(checked, Tool.Threshold)
            )

        if hasattr(self._drawer, "thresToolButton"):
            self.toolButtons = {
                Tool.Navigation: self._drawer.arrowToolButton,
                Tool.Threshold: self._drawer.thresToolButton,
            }
        else:
            self.toolButtons = {Tool.Navigation: self._drawer.arrowToolButton}

        arrowIconPath = str(iconsDir / "arrow.png")
        arrowIcon = QIcon(arrowIconPath)
        self._drawer.arrowToolButton.setIcon(arrowIcon)
        self._drawer.arrowToolButton.setCheckable(True)
        self._drawer.arrowToolButton.clicked.connect(
            lambda checked: self._handleToolButtonClicked(checked, Tool.Navigation)
        )

        self.liveTraining = False
        self.livePrediction = False

        self.__cleanup_fns = []

        self._drawer.unetStateControl.liveTraining.toggled.connect(self.toggleLiveTraining)
        self._drawer.unetStateControl.livePrediction.toggled.connect(self.toggleLivePrediction)
        self._drawer.unetStateControl.setTiktorchController(self.tiktorchController)
        self._drawer.unetStateControl.setTiktorchModel(self.tiktorchModel)
        self._drawer.unetStateControl.start_stop_button.toggled.connect(self._on_start_stop_training)
        # self._drawer.unetStateControl.addCheck(self._check_input_spec_compatible)

        self.initViewerControls()
        self.initViewerControlUi()

        self.__cleanup_fns.append(self.topLevelOperatorView.cleanUp)

        self.invalidatePredictionsTimer = QTimer()
        self.invalidatePredictionsTimer.timeout.connect(self._timer_update)

        self._initCheckpointActions()
        self._has_training_started = False
        self._on_start_stop_training(False)

    def _on_start_stop_training(self, started_training: bool):
        self._drawer.checkpoints.setEnabled(started_training)
        if started_training:
            self.checkpoint_widget.setup(tiktorch_controller=self.tiktorchController, tiktorch_model=self.tiktorchModel)
        else:
            self.checkpoint_widget.clear()

        self._drawer.unetStateControl.export.setEnabled(started_training)

        # disable live predictions by default
        self._drawer.unetStateControl.livePrediction.setEnabled(started_training)
        self._drawer.unetStateControl.livePrediction.setChecked(False)

        # if we start, there is no need to resume
        # if we stop, there is no need to pause
        self._ignore_toggle_training = True
        self._drawer.unetStateControl.liveTraining.setEnabled(started_training)
        self._drawer.unetStateControl.liveTraining.setChecked(started_training)
        self._ignore_toggle_training = False

    def start_timer(self):
        self.invalidatePredictionsTimer.start(60_000)

    def stop_timer(self):
        self.invalidatePredictionsTimer.stop()

    def _timer_update(self):
        self.topLevelOperatorView.ModelSession.setDirty()

    def _check_input_spec_compatible(self, model_info):
        pass

    def _handleToolButtonClicked(self, checked, toolId):
        """
        Called when the user clicks any of the "tool" buttons in the label applet bar GUI.
        """
        if not checked:
            # Users can only *switch between* tools, not turn them off.
            # If they try to turn a button off, re-select it automatically.
            self.toolButtons[toolId].setChecked(True)
        else:
            # If the user is checking a new button
            self._changeInteractionMode(toolId)

    @threadRouted
    def _changeInteractionMode(self, toolId):
        """
        Implement the GUI's response to the user selecting a new tool.
        """
        # Uncheck all the other buttons
        for tool, button in list(self.toolButtons.items()):
            if tool != toolId:
                button.setChecked(False)

        # If we have no editor, we can't do anything yet
        if self.editor is None:
            return

        # The volume editor expects one of two specific names
        if hasattr(self._drawer, "thresToolButton"):
            modeNames = {
                Tool.Navigation: "navigation",
                Tool.Threshold: "thresholding",
            }
        else:
            modeNames = {Tool.Navigation: "navigation"}

        if toolId == Tool.Navigation:
            self._drawer.arrowToolButton.setChecked(True)
        elif toolId == Tool.Threshold:
            self._drawer.thresToolButton.setChecked(True)
            self.setCursor(Qt.ArrowCursor)

        self.editor.setInteractionMode(modeNames[toolId])
        self._toolId = toolId

    @property
    def tiktorchController(self) -> TiktorchUnetController:
        return self.parentApplet.tiktorchController

    @property
    def tiktorchModel(self) -> TiktorchUnetOperatorModel:
        return self.parentApplet.tiktorchOpModel

    def updatePredictions(self):
        logger.info("Invalidating predictions")
        self.topLevelOperatorView.FreezePredictions.setValue(False)
        self.topLevelOperatorView.classifier_cache.Output.setDirty()

    def initViewerControls(self):
        """
        initializing viewerControl
        """
        self._viewerControlWidgetStack = QStackedWidget(parent=self)

    def initViewerControlUi(self):
        """
        Load the viewer controls GUI, which appears below the applet bar.
        In our case, the viewer control GUI consists mainly of a layer list.
        """
        localDir = os.path.split(__file__)[0]
        self._viewerControlUi = uic.loadUi(os.path.join(localDir, "viewerControls.ui"))

        def nextCheckState(checkbox):
            """
            sets the checkbox to the next state
            """
            checkbox.setChecked(not checkbox.isChecked())

        self._viewerControlUi.checkShowPredictions.nextCheckState = partial(
            nextCheckState, self._viewerControlUi.checkShowPredictions
        )
        self._viewerControlUi.checkShowPredictions.clicked.connect(self.handleShowPredictionsClicked)

        model = self.editor.layerStack
        self._viewerControlUi.viewerControls.setupConnections(model)

    def _createPredLayer(self, predictionSlot, ref_label: Label):
        predictionSource = LazyflowSource(predictionSlot)
        predictionLayer = AlphaModulatedLayer(predictionSource, tintColor=ref_label.pmapColor(), normalize=(0.0, 1.0))
        predictionLayer.visible = self._drawer.unetStateControl.livePrediction.isChecked()
        predictionLayer.opacity = 0.5
        predictionLayer.visibleChanged.connect(self.updateShowPredictionCheckbox)

        def setLayerColor(color, layer=predictionLayer, initializing=False):
            if initializing or layer in self.layerstack:
                layer.tintColor = color

        def setPredLayerName(name, layer=predictionLayer, initializing=False):
            if initializing or layer in self.layerstack:
                layer.name = f"Prediction for {name}"

        def changePredLayerColor(ref_label_, _checked):
            new_color = QColorDialog.getColor(ref_label_.pmapColor(), self, "Select Layer Color")
            if new_color.isValid():
                ref_label_.setPmapColor(new_color)

        setPredLayerName(ref_label.name, initializing=True)
        ref_label.pmapColorChanged.connect(setLayerColor)
        ref_label.nameChanged.connect(setPredLayerName)

        predictionLayer.contexts.append(
            QAction("Change color", None, triggered=partial(changePredLayerColor, ref_label))
        )

        return predictionLayer

    def setupLayers(self):
        """
        which layers will be shown in the layerviewergui.
        Triggers the prediction by setting the layer on visible
        """

        layers = self._setupLayers()

        def add_prediction_layers():
            if not self.topLevelOperatorView.NumClasses.ready():
                return

            for channel, predictionSlot in enumerate(self.topLevelOperatorView.PredictionProbabilityChannels):
                logger.info(f"prediction_slot: {predictionSlot}")
                name = f"Label {channel + 1}"
                color = QColor()
                color.setRgba(colortables.default16_new[channel + 1])
                label = Label(name, color)
                if predictionSlot.ready():
                    layers.append(self._createPredLayer(predictionSlot, label))

        add_prediction_layers()

        # Add the overlay second to last
        overlaySlot = self.topLevelOperatorView.OverlayImages
        if overlaySlot.ready():
            overlayLayer = self.createStandardLayerFromSlot(overlaySlot)
            overlayLayer.name = "Overlay"
            overlayLayer.visible = True
            overlayLayer.opacity = 1.0

            layers.append(overlayLayer)

        return layers

    def _setupLayers(self):
        layers = []

        # Raw Input Layer
        input_images = self.topLevelOperatorView.InputImages
        if input_images.ready():
            layer = self.createStandardLayerFromSlot(input_images, name="Raw Input")
            layers.append(layer)

            if isinstance(layer, GrayscaleLayer):
                self._drawer.thresToolButton.show()
            else:
                self._drawer.thresToolButton.hide()

            layer.shortcutRegistration = (
                "i",
                ShortcutManager.ActionInfo(
                    "Prediction Layers",
                    "Bring Input To Top/Bottom",
                    "Bring Input To Top/Bottom",
                    partial(self.layerstack.toggleTopToBottom, layer),
                    self.viewerControlWidget(),
                    layer,
                ),
            )

        return layers

    def toggleLivePrediction(self, checked):
        logger.debug("toggle live prediction mode to %r", checked)

        if checked:
            self.start_timer()
            self.updatePredictions()
            self._viewerControlUi.checkShowPredictions.setChecked(True)
            self.handleShowPredictionsClicked()
        else:
            self.stop_timer()

        self.topLevelOperatorView.FreezePredictions.setValue(not checked)

        # Notify the workflow that some applets may have changed state now.
        # (For example, the downstream pixel classification applet can
        #  be used now that there are features selected)
        self.parentApplet.appletStateUpdateRequested()

    def toggleLiveTraining(self, checked):
        if self._ignore_toggle_training:
            return
        self._toggleLiveTraining(checked)

    @busy_cursor
    def _toggleLiveTraining(self, checked):
        if checked:
            self.tiktorchModel.session.resume_training()
        else:
            self.tiktorchModel.session.pause_training()

    @pyqtSlot()
    def handleShowPredictionsClicked(self):
        """
        sets the layer visibility when showPredicition is clicked
        """
        checked = self._viewerControlUi.checkShowPredictions.isChecked()
        for layer in self.layerstack:
            if "Prediction" in layer.name:
                layer.visible = checked

    @pyqtSlot()
    def updateShowPredictionCheckbox(self):
        """
        updates the showPrediction Checkbox when Predictions were added to the layers
        """
        predictLayerCount = 0
        visibleCount = 0
        for layer in self.layerstack:
            if "Prediction" in layer.name:
                predictLayerCount += 1
                if layer.visible:
                    visibleCount += 1

        if visibleCount == 0:
            self._viewerControlUi.checkShowPredictions.setCheckState(Qt.Unchecked)
        elif predictLayerCount == visibleCount:
            self._viewerControlUi.checkShowPredictions.setCheckState(Qt.Checked)
        else:
            self._viewerControlUi.checkShowPredictions.setCheckState(Qt.PartiallyChecked)

    def cancel(self, *args, **kwargs):
        self.cancel_src.cancel()

    @threadRouted
    def _showErrorMessage(self, exc):
        logger.error("".join(traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)))
        QMessageBox.critical(
            self, "ilastik detected a problem with your model", f"Failed to initialize model:\n {type(exc)} {exc}"
        )

    def _update_rendering(self):
        if not self.render:
            return
        shape = self.topLevelOperatorView.InputImages.meta.shape[1:4]
        if len(shape) != 5:
            # this might be a 2D image, no need for updating any 3D stuff
            return

        time = self.editor.posModel.slicingPos5D[0]
        if not self._renderMgr.ready:
            self._renderMgr.setup(shape)

        layernames = set(layer.name for layer in self.layerstack)
        self._renderedLayers = dict((k, v) for k, v in self._renderedLayers.items() if k in layernames)

        newvolume = numpy.zeros(shape, dtype=numpy.uint8)
        for layer in self.layerstack:
            try:
                label = self._renderedLayers[layer.name]
            except KeyError:
                continue
            for ds in layer.datasources:
                vol = ds.dataSlot.value[time, ..., 0]
                indices = numpy.where(vol != 0)
                newvolume[indices] = label

        self._renderMgr.volume = newvolume
        self._update_colors()
        self._renderMgr.update()
