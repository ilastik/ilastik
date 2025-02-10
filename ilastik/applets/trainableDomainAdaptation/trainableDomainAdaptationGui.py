###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2025, the ilastik developers
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
from functools import partial
from typing import Sequence

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QAction, QColorDialog, QFileDialog, QHBoxLayout, QLabel, QMenu, QPushButton, QActionGroup
from volumina.api import AlphaModulatedLayer, LazyflowSource
from volumina.colortables import default16_new
import sip

from ilastik.applets.pixelClassification.pixelClassificationGui import PixelClassificationGui

from ilastik.applets.pixelClassification.suggestFeaturesDialog import SuggestFeaturesDialog
from .modelStateControl import EnhancerModelStateControl

logger = logging.getLogger(__name__)


class ConfigurableChannelSelector(QPushButton):
    channelSelectionFinalized = pyqtSignal(list)

    def __init__(self, options: Sequence[str], *args, n_options=1, **kwargs):
        super().__init__(*args, **kwargs)

        self._channel_menu = QMenu(self)
        self._channel_menu.installEventFilter(self)
        self.setMenu(self._channel_menu)
        self.update_options(options, n_options)

    def onChannelSelectionClicked(self, a0):
        self._update_channel_selector_txt()

    def _update_channel_selector_txt(self):
        selected_actions = [action for action in self._channel_menu.actions() if action.isChecked()]
        if len(selected_actions) == 0:
            txt = "Select a channel..."
        elif len(selected_actions) == 1:
            txt = selected_actions[0].text()
        else:
            txt = ", ".join(action.text() for action in selected_actions)

        self.setText(txt)

    def _is_empty_selection(self):
        if any(action.isChecked() for action in self._channel_menu.actions()):
            return False

        return True

    def _is_configured(self):
        selected_actions = [action for action in self._channel_menu.actions() if action.isChecked()]
        if len(selected_actions) == self._n_options:
            return True

        return False

    def _emit_updated(self):
        if self._is_configured() or self._is_empty_selection():
            idx = [i for i, action in enumerate(self._channel_actions) if action.isChecked()]
            self.channelSelectionFinalized.emit(idx)

    def update_options(self, options: Sequence[str], n_options: int = 1):
        assert n_options <= len(options)
        self._channel_menu.clear()
        self._action_group = QActionGroup(self)
        if n_options == 1:
            self._action_group.setExclusionPolicy(QActionGroup.ExclusionPolicy.ExclusiveOptional)
        else:
            self._action_group.setExclusionPolicy(QActionGroup.ExclusionPolicy.None_)

        self._action_group.triggered.connect(self.onChannelSelectionClicked)
        self._action_group.triggered.connect(self._emit_updated)

        self._channel_actions = []
        self._n_options = n_options

        for label_name in options:
            action = QAction(label_name, self._channel_menu)
            action.setCheckable(True)
            self._channel_menu.addAction(action)
            self._channel_actions.append(action)
            self._action_group.addAction(action)

        self._update_channel_selector_txt()
        self._emit_updated()


class TrainableDomainAdaptationGui(PixelClassificationGui):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._drawer = self._labelControlUi
        self.liveNNPrediction = False
        self.__cleanup_fns = []
        self._init_channel_selector_ui()
        self._init_nn_prediction_ui()

        self.invalidatePredictionsTimer = QTimer()
        self.invalidatePredictionsTimer.timeout.connect(self.updateNNPredictions)
        self.tiktorchModel.registerListener(self._onModelStateChanged)

        self.labelingDrawerUi.liveUpdateButton.toggled.connect(self.toggleLiveNNPrediction)

    def _init_channel_selector_ui(self):
        drawer = self._drawer

        channel_selector = QPushButton()
        self.channel_menu = QMenu(self)  # Must retain menus (in self) or else they get deleted.
        channel_selector.setMenu(self.channel_menu)
        channel_selector.clicked.connect(channel_selector.showMenu)

        def populate_channel_menu(*args):
            if sip.isdeleted(channel_selector):
                return
            self.channel_menu.clear()
            self.channel_actions = []
            for label_name in self.topLevelOperatorView.LabelNames.value:
                action = QAction(label_name, self.channel_menu)
                action.setCheckable(True)
                self.channel_menu.addAction(action)
                self.channel_actions.append(action)
                action.toggled.connect(self.onChannelSelectionClicked)

        populate_channel_menu()
        self.__cleanup_fns.append(self.topLevelOperatorView.LabelNames.notifyDirty(populate_channel_menu))

        channel_selector.setToolTip("Select Channels for NN input")
        channel_selection_layout = QHBoxLayout()
        channel_selection_layout.addWidget(QLabel("Select Channels"))
        channel_selection_layout.addWidget(channel_selector)
        drawer.verticalLayout.addLayout(channel_selection_layout)
        self._channel_selector = channel_selector

        def _update_channel_selector_txt(_slot, _roi):
            label_data = self.labelListData
            selected_idx = self.topLevelOperatorView.SelectedChannels.value
            selected_channels = ", ".join(label_data[i].name for i in selected_idx)
            self._channel_selector.setText(selected_channels)

        self.__cleanup_fns.append(self.topLevelOperatorView.LabelNames.notifyDirty(_update_channel_selector_txt))
        self.__cleanup_fns.append(self.topLevelOperatorView.SelectedChannels.notifyDirty(_update_channel_selector_txt))
        _update_channel_selector_txt(self.topLevelOperatorView.SelectedChannels, ())

    @classmethod
    def getModelToOpen(cls, parent_window, defaultDirectory):
        """
        opens a QFileDialog for importing files
        """
        files = QFileDialog.getOpenFileName(parent_window, "Select Model", defaultDirectory, "Models (*.tmodel *.zip)")
        return files[0]

    def _init_nn_prediction_ui(self):
        # add new stuff here
        drawer = self._drawer

        nn_ctrl_layout = QHBoxLayout()
        self.addModel = EnhancerModelStateControl()

        self.addModel.setTiktorchController(self.tiktorchController)
        self.addModel.setTiktorchModel(self.tiktorchModel)

        nn_ctrl_layout.addWidget(self.addModel)

        drawer.verticalLayout.addLayout(nn_ctrl_layout)

    def _onModelStateChanged(self, state):
        self.updateAllLayers()

    def updateNNPredictions(self):
        logger.info("Invalidating predictions")
        self.topLevelOperatorView.FreezePredictions.setValue(False)
        self.topLevelOperatorView.classifier_cache.Output.setDirty()

    def toggleLiveNNPrediction(self, checked):
        logger.debug("toggle live prediction mode to %r", checked)
        checked = checked if checked is not None else self.isLiveUpdateEnabled()
        # If we're changing modes, enable/disable our controls and other applets accordingly
        if checked:
            self.updateNNPredictions()

        self.topLevelOperatorView.FreezeNNPredictions.setValue(not checked)

        # Auto-set the "show predictions" state according to what the user just clicked.
        if checked:
            self.handleShowPredictionsClicked()

        # Notify the workflow that some applets may have changed state now.
        # (For example, the downstream pixel classification applet can
        #  be used now that there are features selected)
        self.parentApplet.appletStateUpdateRequested()

    def onChannelSelectionClicked(self, *args):
        channel_selections = [i for i, ch in enumerate(self.channel_actions) if ch.isChecked()]
        self.topLevelOperatorView.SelectedChannels.setValue(channel_selections)

    def stopAndCleanUp(self):
        for fn in self.__cleanup_fns:
            fn()

        # Base class
        super().stopAndCleanUp()

    def setupLayers(self):
        layers = []
        enhancer_slot = self.topLevelOperatorView.EnhancerNetworkInput

        n_layers = len(self.labelListData)
        # NeuralNetwork Predictions
        if enhancer_slot is not None and enhancer_slot.ready():
            for channel, predictionSlot in enumerate(self.topLevelOperatorView.NNPredictionProbabilityChannels):
                if predictionSlot.ready():
                    predictsrc = LazyflowSource(predictionSlot)
                    predictionLayer = AlphaModulatedLayer(
                        predictsrc, tintColor=QColor(default16_new[n_layers + channel + 1]), normalize=(0.0, 1.0)
                    )
                    predictionLayer.visible = self.labelingDrawerUi.liveUpdateButton.isChecked()
                    predictionLayer.opacity = 0.5
                    predictionLayer.visibleChanged.connect(self.updateShowPredictionCheckbox)

                    predictionLayer.name = f"NN prediction Channel {channel}"

                    def changePredLayerColor(ref_layer, _checked):
                        new_color = QColorDialog.getColor(ref_layer.tintColor, self, "Select Layer Color")
                        if new_color.isValid():
                            ref_layer.tintColor = new_color

                    predictionLayer.contexts.append(
                        QAction("Change color", None, triggered=partial(changePredLayerColor, predictionLayer))
                    )

                    layers.append(predictionLayer)

            # EnhancerInput
            layer = self.createStandardLayerFromSlot(enhancer_slot, name="EnhancerInput")
            layer.visible = False
            layers.append(layer)

        layers.extend(super().setupLayers())
        return layers

    def initSuggestFeaturesDialog(self):
        thisOpFeatureSelection = (
            self.topLevelOperatorView.parent.featureSelectionApplet.topLevelOperator.innerOperators[0]
        )

        return SuggestFeaturesDialog(thisOpFeatureSelection, self, self.labelListData, self)

    @property
    def tiktorchController(self):
        return self.parentApplet.tiktorchController

    @property
    def tiktorchModel(self):
        return self.parentApplet.tiktorchOpModel

    def cancel(self, *args, **kwargs):
        self.cancel_src.cancel()

    @pyqtSlot()
    def updateShowPredictionCheckbox(self):
        """
        updates the showPrediction Checkbox when Predictions were added to the layers
        """
        state = Qt.Unchecked
        for layer in self.layerstack:
            if any(layer.name.lower().startswith(x) for x in ["nn prediction", "prediction"]):
                state = Qt.Checked
                if not layer.visible:
                    state = Qt.PartiallyChecked
                    break
        self._viewerControlUi.checkShowPredictions.setCheckState(state)

    @pyqtSlot()
    def handleShowPredictionsClicked(self):
        checked = self._viewerControlUi.checkShowPredictions.isChecked()
        for layer in self.layerstack:
            if any(layer.name.lower().startswith(x) for x in ["nn prediction", "prediction"]):
                layer.visible = checked
