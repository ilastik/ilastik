import logging

import sip
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QAction, QCheckBox, QFileDialog, QHBoxLayout, QLabel, QMenu, QPushButton, QToolButton
from volumina.api import AlphaModulatedLayer, LazyflowSource
from volumina.colortables import default16_new

from ilastik.applets.pixelClassification.pixelClassificationGui import PixelClassificationGui
from ilastik.shell.gui.iconMgr import ilastikIcons

from ..neuralNetwork.modelStateControl import EnhancerModelStateControl
from ..neuralNetwork.tiktorchController import TiktorchOperatorModel
from ..pixelClassification.FeatureSelectionDialog import FeatureSelectionDialog

logger = logging.getLogger(__name__)


class PixelClassificationEnhancerGui(PixelClassificationGui):
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
            label_names = self.topLevelOperatorView.LabelNames.value
            for i, label_name in enumerate(label_names):
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

        def _update_channel_selector_txt(slot, roi):
            selected_channels = ", ".join(map(str, slot.value))
            self._channel_selector.setText(selected_channels)

        self.__cleanup_fns.append(self.topLevelOperatorView.SelectedChannels.notifyDirty(_update_channel_selector_txt))
        _update_channel_selector_txt(self.topLevelOperatorView.SelectedChannels, ())

    @classmethod
    def getModelToOpen(cls, parent_window, defaultDirectory):
        """
        opens a QFileDialog for importing files
        """
        return QFileDialog.getOpenFileName(parent_window, "Select Model", defaultDirectory, "Models (*.tmodel *.zip)")[
            0
        ]

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
            self.handleShowNNPredictionsClicked()

        # Notify the workflow that some applets may have changed state now.
        # (For example, the downstream pixel classification applet can
        #  be used now that there are features selected)
        self.parentApplet.appletStateUpdateRequested()

    def onChannelSelectionClicked(self, *args):
        channel_selections = []
        for ch in range(len(self.channel_actions)):
            if self.channel_actions[ch].isChecked():
                channel_selections.append(ch)

        self.topLevelOperatorView.SelectedChannels.setValue(channel_selections)

    def stopAndCleanUp(self):
        for fn in self.__cleanup_fns:
            fn()

        # Base class
        super().stopAndCleanUp()

    def setupLayers(self):

        layers = []
        enhancer_slot = self.topLevelOperatorView.EnhancerInput

        n_layers = len(self.labelListData)
        # NeuralNetwork Predictions
        if enhancer_slot is not None and enhancer_slot.ready():
            for channel, predictionSlot in enumerate(self.topLevelOperatorView.NNPredictionProbabilityChannels):
                logger.info(f"prediction_slot: {predictionSlot}")
                if predictionSlot.ready():
                    predictsrc = LazyflowSource(predictionSlot)
                    predictionLayer = AlphaModulatedLayer(
                        predictsrc, tintColor=QColor(default16_new[n_layers + channel + 1]), normalize=(0.0, 1.0)
                    )
                    predictionLayer.visible = self.labelingDrawerUi.liveUpdateButton.isChecked()
                    predictionLayer.opacity = 0.5
                    predictionLayer.visibleChanged.connect(self.updateShowPredictionCheckbox)

                    predictionLayer.name = f"NN prediction Channel {channel}"

                    # def setLayerColor(c, predictLayer_=predictionLayer):
                    #     new_color = QColorDialog.getColor()
                    #     if new_color:
                    #         predictLayer_.tintColor = new_color

                    # action = QAction("Change prediction color")
                    # action.triggered.connect(setLayerColor)
                    # predictionLayer.contexts.append(action)

                    layers.append(predictionLayer)

        # EnhancerInput
        if enhancer_slot is not None and enhancer_slot.ready():
            layer = self.createStandardLayerFromSlot(enhancer_slot, name="EnhancerInput")
            layer.visible = False
            layers.append(layer)

        layers.extend(super().setupLayers())
        return layers

    def initFeatSelDlg(self):
        thisOpFeatureSelection = (
            self.topLevelOperatorView.parent.featureSelectionApplet.topLevelOperator.innerOperators[0]
        )

        self.featSelDlg = FeatureSelectionDialog(thisOpFeatureSelection, self, self.labelListData)

    @property
    def tiktorchController(self):
        return self.parentApplet.tiktorchController

    @property
    def tiktorchModel(self):
        return self.parentApplet.tiktorchOpModel

    def cc(self, *args, **kwargs):
        self.cancel_src.cancel()

    @pyqtSlot()
    def updateShowNNPredictionCheckbox(self):
        """
        updates the showPrediction Checkbox when Predictions were added to the layers
        """
        predictLayerCount = 0
        visibleCount = 0
        for layer in self.layerstack:
            if "NN prediction" in layer.name:
                predictLayerCount += 1
                if layer.visible:
                    visibleCount += 1
            elif "Prediction" in layer.name:
                predictLayerCount += 1
                if layer.visible:
                    visibleCount += 1

        if visibleCount == 0:
            self.checkShowPredictions.setCheckState(Qt.Unchecked)
        elif predictLayerCount == visibleCount:
            self.checkShowPredictions.setCheckState(Qt.Checked)
        else:
            self.checkShowPredictions.setCheckState(Qt.PartiallyChecked)

    @pyqtSlot()
    def handleShowNNPredictionsClicked(self):
        checked = self._viewerControlUi.checkShowPredictions.isChecked()
        for layer in self.layerstack:
            if "NN prediction" in layer.name:
                layer.visible = checked
            elif "Prediction" in layer.name:
                layer.visible = checked
