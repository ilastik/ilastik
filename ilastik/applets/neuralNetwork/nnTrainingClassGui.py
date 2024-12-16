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
import traceback
from functools import partial

import numpy
import yaml
from PyQt5 import uic
from PyQt5.QtCore import (
    QModelIndex,
    QPersistentModelIndex,
    QStringListModel,
    Qt,
    QTimer,
    pyqtSignal,
    pyqtSlot,
)
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import (
    QAction,
    QColorDialog,
    QComboBox,
    QDesktopWidget,
    QDialog,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
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


def _listReplace(old, new):
    if len(old) > len(new):
        return new + old[len(new) :]
    else:
        return new


class ParameterDlg(QDialog):
    """
    simple window for setting parameters
    """

    def __init__(self, parent):
        self.hparams = None

        super(QDialog, self).__init__(parent=parent)

        self.optimizer_combo = QComboBox(self)
        self.optimizer_combo.addItem("Adam")
        self.optimizer_kwargs_textbox = QLineEdit()
        self.optimizer_kwargs_textbox.setPlaceholderText(
            "e.g. for Adam: {'lr': 0.0003, 'weight_decay':0.0001, amsgrad: True}"
        )

        self.criterion_combo = QComboBox(self)
        self.criterion_combo.addItem("BCEWithLogitsLoss")
        self.criterion_kwargs_textbox = QLineEdit()
        self.criterion_kwargs_textbox.setPlaceholderText("e.g.: {'reduce': False}")

        self.batch_size_textbox = QLineEdit()
        self.batch_size_textbox.setPlaceholderText("default: 1")

        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(QLabel("Optimizer"), 1, 0)
        grid.addWidget(self.optimizer_combo, 1, 1)

        grid.addWidget(QLabel("Optimizer keyword arguments"), 2, 0)
        grid.addWidget(self.optimizer_kwargs_textbox, 2, 1)

        grid.addWidget(QLabel("Criterion"), 3, 0)
        grid.addWidget(self.criterion_combo, 3, 1)

        grid.addWidget(QLabel("Criterion keyword arguments"), 4, 0)
        grid.addWidget(self.criterion_kwargs_textbox, 4, 1)

        grid.addWidget(QLabel("Batch size"), 5, 0)
        grid.addWidget(self.batch_size_textbox, 5, 1)

        okButton = QPushButton("OK")
        okButton.clicked.connect(self.readParameters)
        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.close)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(okButton)
        hbox.addWidget(cancelButton)

        vbox = QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

        # self.resize(480, 200)
        self.setFixedSize(600, 200)
        self.center()

        self.setWindowTitle("Hyperparameter Settings")
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)

        self.move(qr.topLeft())

    def readParameters(self):
        optimizer = self.optimizer_combo.currentText()
        optimizer_kwargs = yaml.load(self.optimizer_kwargs_textbox.text())
        if optimizer_kwargs is None:
            optimizer_kwargs = dict(lr=0.0003, weight_decay=0.0001, amsgrad=True)
            optimizer = "Adam"
        criterion = self.criterion_combo.currentText()
        criterion_kwargs = yaml.load(self.criterion_kwargs_textbox.text())
        if criterion_kwargs is None:
            criterion_kwargs = dict(reduce=False)
            criterion = "BCEWithLogitsLoss"
        batch_size = int(self.batch_size_textbox.text()) if len(self.batch_size_textbox.text()) > 0 else 1

        self.hparams = dict(
            optimizer_kwargs=optimizer_kwargs,
            optimizer_name=optimizer,
            criterion_kwargs=criterion_kwargs,
            criterion_name=criterion,
            batch_size=batch_size,
        )

        self.close()


class ValidationDlg(QDialog):
    """
    Settings for choosing the validation set
    """

    def __init__(self, parent):
        self.valid_params = None

        super(QDialog, self).__init__(parent=parent)

        self.validation_size = QComboBox(self)
        self.validation_size.addItem("10%")
        self.validation_size.addItem("20%")
        self.validation_size.addItem("30%")
        self.validation_size.addItem("40%")

        self.orientation = QComboBox(self)
        self.orientation.addItem("Top - Left")
        self.orientation.addItem("Top - Right")
        self.orientation.addItem("Top - Mid")
        self.orientation.addItem("Mid - Left")
        self.orientation.addItem("Mid - Right")
        self.orientation.addItem("Mid - Mid")
        self.orientation.addItem("Bottom - Left")
        self.orientation.addItem("Bottom - Right")
        self.orientation.addItem("Bottom - Mid")

        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(QLabel("Validation Set Size"), 1, 0)
        grid.addWidget(self.validation_size, 1, 1)

        grid.addWidget(QLabel("Orientation"), 2, 0)
        grid.addWidget(self.orientation, 2, 1)

        okButton = QPushButton("OK")
        okButton.clicked.connect(self.readParameters)
        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.close)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(okButton)
        hbox.addWidget(cancelButton)

        vbox = QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

        self.center()

        self.setWindowTitle("Validation Set Settings")
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)

        self.move(qr.topLeft())

    def readParameters(self):
        percentage = self.validation_size.currentText()[:-1]
        orientation = self.orientation.currentText()
        self.valid_params = dict(percentage=percentage, orientation=orientation)

        self.close()


class CheckpointManager:
    def __init__(self, widget, get_state, load_state, added, data):
        self._checkpoint_by_idx = {}

        self._get_state = get_state
        self._load_state = load_state
        self._added = added

        self._widget = widget
        self._widget.add_clicked.connect(self._add)
        self._widget.remove_clicked.connect(self._remove)
        self._widget.load_clicked.connect(self._load)

        self._load_data(data)
        self._count = 0

    def setData(self, data):
        self._load_data(data)

    def _load_data(self, data):
        self._widget.clear()
        self._checkpoint_by_idx = {}
        for entry in data:
            idx = self._widget.add_item(entry["name"])
            self._checkpoint_by_idx[idx] = entry

    def _add(self):
        state = self._get_state()
        self._count += 1
        name = f"{self._count}: Epoch: {state.epoch}. Loss: {state.loss}"

        idx = self._widget.add_item(name)
        self._checkpoint_by_idx[idx] = {"name": name, "state": state}
        self._added(self._checkpoint_by_idx.values())

    def _remove(self, removed_idx):
        del self._checkpoint_by_idx[removed_idx]
        self._widget.remove_item(removed_idx)

    def _load(self, load_idx):
        if load_idx.isValid():
            val = self._checkpoint_by_idx[load_idx]
            self._load_state(val["state"])


class CheckpointWidget(QWidget):
    add_clicked = pyqtSignal()
    remove_clicked = pyqtSignal(QPersistentModelIndex)
    load_clicked = pyqtSignal(QPersistentModelIndex)

    def __init__(self, *, parent, add, remove, load, view):
        super().__init__(parent=parent)

        self._add_btn = add
        self._remove_btn = remove
        self._load_btn = load
        self._view = view

        self._model = QStringListModel()
        self._view.setModel(self._model)

        self._add_btn.clicked.connect(self.add_clicked)
        self._remove_btn.clicked.connect(self._remove_click)
        self._load_btn.clicked.connect(self._load_click)

    def clear(self):
        self._model.setStringList([])

    def add_item(self, name: str) -> QPersistentModelIndex:
        self._model.insertRow(0)
        m_idx = self._model.index(0)
        self._model.setData(m_idx, name)
        return QPersistentModelIndex(m_idx)

    def remove_item(self, idx: QModelIndex):
        if idx.isValid():
            self._model.removeRow(idx.row())

    def _remove_click(self):
        idx = self._view.selectionModel().currentIndex()
        if idx.isValid():
            self.remove_clicked.emit(QPersistentModelIndex(idx))

    def _load_click(self):
        idx = self._view.selectionModel().currentIndex()
        if idx.isValid():
            self.load_clicked.emit(QPersistentModelIndex(idx))


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
        self.topLevelOperatorView.Checkpoints.notifyDirty(self.checkpoints_dirty)
        self.checkpoint_mng = CheckpointManager(
            self.checkpoint_widget,
            self._get_model_state,
            self._load_checkpoint,
            self._added,
            data=self.topLevelOperatorView.Checkpoints.value,
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

        self._initCheckpointActions()

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

        self._has_training_started = False
        self._on_start_stop_training(False)

    def _on_start_stop_training(self, started_training: bool):
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


    def _load_checkpoint(self, model_state: ModelState):
        self.topLevelOperatorView.set_model_state(model_state)

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
