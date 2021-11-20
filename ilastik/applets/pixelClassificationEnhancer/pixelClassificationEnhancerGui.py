from ilastik.applets.pixelClassification.pixelClassificationGui import PixelClassificationGui
from ..pixelClassification.FeatureSelectionDialog import FeatureSelectionDialog

from functools import partial

import sip
from PyQt5.QtWidgets import (
    QFileDialog,
    QCheckBox,
    QComboBox,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QMenu,
    QAction,
    QToolButton,
    QColorDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from ilastik.shell.gui.iconMgr import ilastikIcons
from PyQt5.QtGui import QColor, QIcon
from ilastik.widgets.progressDialog import PercentProgressDialog
from volumina.utility import preferences


from lazyflow.cancel_token import CancellationTokenSource
from tiktorch.types import ModelState
from ..neuralNetwork.tiktorchController import TiktorchOperatorModel

from volumina.api import LazyflowSource, AlphaModulatedLayer, GrayscaleLayer
from volumina.colortables import default16_new

import logging

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

    @classmethod
    def getModelToOpen(cls, parent_window, defaultDirectory):
        """
        opens a QFileDialog for importing files
        """
        return QFileDialog.getOpenFileName(parent_window, "Select Model", defaultDirectory, "Models (*.tmodel *.zip)")[
            0
        ]

    def _init_nn_prediction_ui(self):
        drawer = self._drawer
        nn_pred_layout = QHBoxLayout()
        self.liveNNPredictionBtn = QToolButton()
        self.liveNNPredictionBtn.setText("Enhance!")
        self.liveNNPredictionBtn.setCheckable(True)
        self.liveNNPredictionBtn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.set_nn_live_predict_icon(self.liveNNPredictionBtn)
        self.liveNNPredictionBtn.toggled.connect(self.toggleLiveNNPrediction)
        self.checkShowNNPredictions = QCheckBox()
        self.checkShowNNPredictions.setText("Show enhance Predictions")
        nn_pred_layout.addWidget(self.checkShowNNPredictions)

        nn_pred_layout.addWidget(self.liveNNPredictionBtn)

        nn_ctrl_layout = QHBoxLayout()
        self.addModel = QPushButton()
        self.addModel.clicked.connect(self.addModelClicked)
        self.closeModel = QToolButton()
        self.closeModel.setIcon(QIcon(ilastikIcons.ProcessStop))
        self.closeModel.clicked.connect(self.closeModelClicked)

        nn_ctrl_layout.addWidget(self.addModel)
        nn_ctrl_layout.addWidget(self.closeModel)

        drawer.verticalLayout.addLayout(nn_ctrl_layout)
        drawer.verticalLayout.addLayout(nn_pred_layout)

    def _onModelStateChanged(self, state):

        if state is TiktorchOperatorModel.State.Empty:
            self.addModel.setText("Load model")
            self.addModel.setEnabled(True)
            self.closeModel.setEnabled(False)
            self.liveNNPredictionBtn.setEnabled(False)
            self.updateAllLayers()

        elif state is TiktorchOperatorModel.State.ReadFromProjectFile:
            info = self.tiktorchModel.modelInfo

            self.addModel.setText(f"{info.name}")
            self.addModel.setEnabled(True)
            self.closeModel.setEnabled(True)
            self.liveNNPredictionBtn.setEnabled(False)

            self.updateAllLayers()

        elif state is TiktorchOperatorModel.State.Ready:
            info = self.tiktorchModel.modelInfo
            self.addModel.setText(f"{info.name}")
            self.addModel.setEnabled(True)
            self.closeModel.setEnabled(True)
            self.liveNNPredictionBtn.setEnabled(True)
            self.updateAllLayers()

    def updateNNPredictions(self):
        logger.info("Invalidating predictions")
        self.topLevelOperatorView.FreezePredictions.setValue(False)
        self.topLevelOperatorView.classifier_cache.Output.setDirty()

    def toggleLiveNNPrediction(self, checked):

        logger.debug("toggle live prediction mode to %r", checked)
        self.liveNNPredictionBtn.setEnabled(False)

        # If we're changing modes, enable/disable our controls and other applets accordingly
        if self.liveNNPrediction != checked:
            if checked:
                self.updateNNPredictions()

            self.liveNNPrediction = checked
            self.liveNNPredictionBtn.setChecked(checked)
            self.set_nn_live_predict_icon(checked)

        self.topLevelOperatorView.FreezeNNPredictions.setValue(not checked)

        # Auto-set the "show predictions" state according to what the user just clicked.
        if checked:
            self.checkShowNNPredictions.setChecked(True)
            self.handleShowNNPredictionsClicked()

        # Notify the workflow that some applets may have changed state now.
        # (For example, the downstream pixel classification applet can
        #  be used now that there are features selected)
        self.parentApplet.appletStateUpdateRequested()
        self.liveNNPredictionBtn.setEnabled(True)

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

        # NeuralNetwork Predictions
        if enhancer_slot is not None and enhancer_slot.ready():
            for channel, predictionSlot in enumerate(self.topLevelOperatorView.NNPredictionProbabilityChannels):
                logger.info(f"prediction_slot: {predictionSlot}")
                if predictionSlot.ready():
                    predictsrc = LazyflowSource(predictionSlot)
                    predictionLayer = AlphaModulatedLayer(
                        predictsrc, tintColor=QColor(default16_new[channel + 1]), normalize=(0.0, 1.0)
                    )
                    predictionLayer.visible = self.checkShowNNPredictions.isChecked()
                    predictionLayer.opacity = 0.5
                    predictionLayer.visibleChanged.connect(self.updateShowNNPredictionCheckbox)

                    predictionLayer.name = f"NN prediction Channel {channel}"

                    def setLayerColor(c, predictLayer_=predictionLayer):
                        new_color = QColorDialog.getColor()
                        if new_color:
                            predictLayer_.tintColor = new_color

                    action = QAction("Change prediction color")
                    action.triggered.connect(setLayerColor)
                    predictionLayer.contexts.append(action)

                    layers.append(predictionLayer)

        # EnhancerInput
        if enhancer_slot is not None and enhancer_slot.ready():
            layer = self.createStandardLayerFromSlot(enhancer_slot, name="EnhancerInput")
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

    def set_nn_live_predict_icon(self, active: bool):
        if active:
            self.liveNNPredictionBtn.setIcon(QIcon(ilastikIcons.Pause))
        else:
            self.liveNNPredictionBtn.setIcon(QIcon(ilastikIcons.Play))

    def addModelClicked(self):
        """
        When AddModel button is clicked.
        """
        # open dialog in recent model folder if possible
        folder = preferences.get("DataSelection", "recent model")
        if folder is None:
            folder = os.path.expanduser("~")

        # get folder from user
        filename = self.getModelToOpen(self, folder)

        if filename:
            with open(filename, "rb") as modelFile:
                modelBytes = modelFile.read()

            self._uploadModel(modelBytes)

            preferences.set("DataSelection", "recent model", filename)
            self.parentApplet.appletStateUpdateRequested()

    def closeModelClicked(self):
        self.tiktorchController.closeSession()

    def cc(self, *args, **kwargs):
        self.cancel_src.cancel()

    uploadDone = pyqtSignal()

    def _uploadModel(self, modelBytes):
        cancelSrc = CancellationTokenSource()
        dialog = PercentProgressDialog(self, title="Initializing model")
        dialog.rejected.connect(cancelSrc.cancel)
        dialog.open()

        modelInfo = self.tiktorchController.uploadModel(
            modelBytes=modelBytes, progressCallback=dialog.updateProgress, cancelToken=cancelSrc.token
        )

        def _onUploadDone():
            self.uploadDone.disconnect()
            dialog.accept()

        self.uploadDone.connect(_onUploadDone)

        def _onDone(fut):
            self.uploadDone.emit()

            if fut.cancelled():
                return

            if fut.exception():
                self._showErrorMessage(fut.exception())

        modelInfo.add_done_callback(_onDone)

    @pyqtSlot()
    def handleShowNNPredictionsClicked(self):
        """
        sets the layer visibility when showPredicition is clicked
        """
        checked = self.checkShowNNPredictions.isChecked()
        for layer in self.layerstack:
            if "NN prediction" in layer.name:
                layer.visible = checked

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

        if visibleCount == 0:
            self.checkShowNNPredictions.setCheckState(Qt.Unchecked)
        elif predictLayerCount == visibleCount:
            self.checkShowNNPredictions.setCheckState(Qt.Checked)
        else:
            self.checkShowNNPredictions.setCheckState(Qt.PartiallyChecked)
