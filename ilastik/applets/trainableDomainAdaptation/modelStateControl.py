import logging

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLabel, QToolButton, QVBoxLayout

from ilastik.applets.neuralNetwork.modelStateControl import ModelStateControl, display_template
from ilastik.utility.gui import ThreadRouter, silent_qobject

logger = logging.getLogger(__file__)


class BioImageModelCombo(QComboBox):
    collections_url = "https://raw.githubusercontent.com/bioimage-io/collection-bioimage-io/gh-pages/collection.json"
    _SELECT_FILE = object()
    _REMOVE_FILE = object()

    modelDeleted = pyqtSignal()
    modelOpenFromFile = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(False)
        self.refresh()
        self.currentIndexChanged.connect(self.onIndexChange)

    def getModelSource(self):
        idx = self.currentIndex()
        data = self.itemData(idx)
        if data == BioImageModelCombo._SELECT_FILE:
            return ""
        if data:
            return data["id"]

    def clear(self):
        super().clear()
        self.setToolTip("")

    def setEmptyState(self):
        self.refresh()
        self.setEnabled(True)

    def setModelInfo(self, model_source, model_info, template=display_template):
        # TODO (k-dominik)
        pass

    def onIndexChange(self, idx):
        item_data = self.itemData(idx)
        if item_data == BioImageModelCombo._REMOVE_FILE:
            logger.debug("model remove requested")
            self.modelDeleted.emit()
        elif item_data == BioImageModelCombo._SELECT_FILE:
            logger.debug("open model from file")
            self.modelOpenFromFile.emit()

    def setModelDataAvailableState(self, model_source, model_info):
        idx = self.findText(model_info.name)
        if idx == -1:
            # from file
            with silent_qobject(self) as silent_self:
                silent_self.insertItem(1, model_info.name, model_info)
        else:
            self.setCurrentText(self.itemText(idx))
        self.setItemText(0, "remove model")
        self.setItemData(0, BioImageModelCombo._REMOVE_FILE)

        self.setEnabled(True)

    def setReadyState(self, model_source, model_info):
        self.setModelDataAvailableState(model_source, model_info)
        self.setEnabled(False)

    def refresh(self):
        # do this in the background, indicate busyness
        from bioimageio.spec.shared import BIOIMAGEIO_COLLECTION, BIOIMAGEIO_COLLECTION_ERROR

        self.clear()

        if BIOIMAGEIO_COLLECTION is None:
            logger.error(f"Error fetching models from bioimage.io: {BIOIMAGEIO_COLLECTION_ERROR}")
            return

        enhancer_models = [m for m in BIOIMAGEIO_COLLECTION["collection"] if "shallow2deep" in m["tags"]]

        self.addItem("choose model..", {})
        for m in enhancer_models:
            self.addItem(m["name"], m)
        self.addItem("select file", BioImageModelCombo._SELECT_FILE)


class EnhancerModelStateControl(ModelStateControl):
    uploadDone = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.modelSourceEdit.modelOpenFromFile.connect(self.onModelInfoRequested)

    def _setup_ui(self):
        self.threadRouter = ThreadRouter(self)
        self._preDownloadChecks = set()

        layout = QVBoxLayout()

        self.modelSourceEdit = BioImageModelCombo(self)
        self.statusLabel = QLabel(self)
        self.statusLabel.setText("status...")
        self.modelControlButton = QToolButton(self)
        self.modelControlButton.setText("...")
        self.modelControlButton.setToolTip("Click here to check model details, initialize, or un-initialize the model")
        self.statusLabel.setVisible(False)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.modelSourceEdit)
        top_layout.addWidget(self.modelControlButton)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.statusLabel)
        bottom_layout.addStretch()

        layout.addLayout(top_layout)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)
