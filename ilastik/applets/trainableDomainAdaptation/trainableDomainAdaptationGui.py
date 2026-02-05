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

from qtpy.QtCore import Qt, Signal, Slot
from qtpy.QtGui import QColor
from qtpy.QtWidgets import (
    QAction,
    QActionGroup,
    QColorDialog,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
)
from volumina.api import AlphaModulatedLayer, LazyflowSource
from volumina.colortables import default16_new

from ilastik.applets.neuralNetwork.tiktorchController import TiktorchOperatorModel
from ilastik.applets.pixelClassification.pixelClassificationGui import PixelClassificationGui
from ilastik.applets.pixelClassification.suggestFeaturesDialog import SuggestFeaturesDialog

from .modelStateControl import EnhancerModelStateControl

logger = logging.getLogger(__name__)


class ConfigurableChannelSelector(QPushButton):
    channelSelectionFinalized = Signal(list)

    def __init__(self, options: Sequence[str], *args, required_selections=1, **kwargs):
        super().__init__(*args, **kwargs)

        self._channel_menu = QMenu(self)
        self.setMenu(self._channel_menu)
        self.update_options(options, required_selections)

    def onChannelSelectionClicked(self, a0):
        self._update_channel_selector_txt()
        if self._is_configured() or self._is_empty_selection():
            idx = [i for i, action in enumerate(self._channel_menu.actions()) if action.isChecked()]
            self.channelSelectionFinalized.emit(idx)

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
        if len(selected_actions) == self._required_selections:
            return True

        return False

    def update_options(self, options: Sequence[str], required_selections: int = 1, selection=None):
        self._channel_menu.clear()
        self._action_group = QActionGroup(self)
        if selection is None:
            selection = []
        if required_selections == 1:
            self._action_group.setExclusionPolicy(QActionGroup.ExclusionPolicy.ExclusiveOptional)
        else:
            self._action_group.setExclusionPolicy(QActionGroup.ExclusionPolicy.None_)

        self._required_selections = required_selections

        for label_name in options:
            action = QAction(label_name, self._channel_menu)
            action.setCheckable(True)
            self._channel_menu.addAction(action)
            self._action_group.addAction(action)

        self._action_group.triggered.connect(self.onChannelSelectionClicked)

        self.set_selection(selection)

    def set_selection(self, selection: Sequence[int]):
        """
        Intended for synchronization with slot value
        """
        if selection and max(selection) >= len(self._channel_menu.actions()):
            raise ValueError(
                f"Trying to select channels outside the available range {selection=} {len(self._channel_menu.actions())=}."
            )

        for idx, action in enumerate(self._channel_menu.actions()):
            action.setChecked(idx in selection)

        self._update_channel_selector_txt()


class TrainableDomainAdaptationGui(PixelClassificationGui):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._drawer = self._labelControlUi
        self.liveNNPrediction = False
        self.__cleanup_fns = []
        self._init_tda_ui()

        self.tiktorchModel.registerListener(self._onModelStateChanged)

        self.labelingDrawerUi.liveUpdateButton.toggled.connect(self.toggleLiveNNPrediction)

    def _init_tda_ui(self):
        drawer = self._drawer

        channel_selector = ConfigurableChannelSelector(options=self.topLevelOperatorView.LabelNames.value)

        self._channel_selector = channel_selector
        self._channel_selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        channel_selector.channelSelectionFinalized.connect(self.onChannelSelectionClicked)

        channel_selector.setToolTip("Select Channels for NN input")
        channel_selector.setContentsMargins(0, 0, 0, 0)

        self.addModel = EnhancerModelStateControl()

        self.addModel.setTiktorchController(self.tiktorchController)
        self.addModel.setTiktorchModel(self.tiktorchModel)

        tda_layout = QGridLayout()
        tda_layout.addWidget(self.addModel, 0, 2, 1, 2)
        tda_layout.addWidget(QLabel("Model"), 0, 0)
        tda_layout.addWidget(QLabel("Channels"), 1, 0)
        tda_layout.addWidget(channel_selector, 1, 2, 1, 2)

        box = QGroupBox("Enhancer Settings")
        box.setLayout(tda_layout)
        drawer.verticalLayout.addWidget(box)

        self.__cleanup_fns.append(self.topLevelOperatorView.LabelNames.notifyDirty(self.onLabelNamesChanged))
        self.__cleanup_fns.append(
            self.topLevelOperatorView.SelectedChannels.notifyDirty(self._on_channel_selection_changed)
        )

        self._on_channel_selection_changed()

    def _on_channel_selection_changed(self, *args, **kwargs):
        selection = self.topLevelOperatorView.SelectedChannels.value
        self._channel_selector.set_selection(selection)

    @classmethod
    def getModelToOpen(cls, parent_window, defaultDirectory):
        """
        opens a QFileDialog for importing files
        """
        files = QFileDialog.getOpenFileName(parent_window, "Select Model", defaultDirectory, "Models (*.tmodel *.zip)")
        return files[0]

    def _onModelStateChanged(self, state: TiktorchOperatorModel.State):
        if state == TiktorchOperatorModel.State.Empty:
            self._channel_selector.setEnabled(False)
        else:
            self._channel_selector.setEnabled(True)

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

    def onLabelNamesChanged(self, _slot, _roi):
        label_data = self.labelListData
        n_labels = len(label_data)
        selected_channels = self.topLevelOperatorView.SelectedChannels.value
        try:
            if selected_channels and max(selected_channels) >= n_labels:
                selected_channels = [chan for chan in selected_channels if chan < n_labels]
                self.topLevelOperatorView.SelectedChannels.setValue(selected_channels)
        finally:
            self._channel_selector.update_options([label.name for label in label_data], selection=selected_channels)

    def onChannelSelectionClicked(self, selection=Sequence[int]):
        self.topLevelOperatorView.SelectedChannels.setValue(selection)

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

    @Slot()
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

    @Slot()
    def handleShowPredictionsClicked(self):
        checked = self._viewerControlUi.checkShowPredictions.isChecked()
        for layer in self.layerstack:
            if any(layer.name.lower().startswith(x) for x in ["nn prediction", "prediction"]):
                layer.visible = checked
