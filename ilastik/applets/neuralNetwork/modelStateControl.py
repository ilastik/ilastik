import contextlib
import logging
import os
import traceback
from functools import partial
from textwrap import dedent
from typing import Callable, List

import requests
from bioimageio.core import load_raw_resource_description
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSizePolicy,
    QSpacerItem,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from volumina.utility import preferences

from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.utility.gui import ThreadRouter, threadRouted
from ilastik.widgets.progressDialog import BarId, PercentProgressDialog
from lazyflow.cancel_token import CancellationTokenSource

from .bioimageiodl import BioImageDownloader
from .tiktorchController import TiktorchOperatorModel

logger = logging.getLogger(__file__)


class ModelIncompatible(Exception):
    pass


class ModelControlButtons(QWidget):
    remove = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.btnlayout = QHBoxLayout()
        self.btn_remove = QToolButton()
        self.btn_remove.clicked.connect(self.remove)
        self.btn_remove.setToolTip("Clear and remove model")
        self.btn_remove.setIcon(QIcon(ilastikIcons.ProcessStop))
        self.btn_remove.setCheckable(False)

        self.btnlayout.addSpacerItem(QSpacerItem(0, 0, hPolicy=QSizePolicy.Expanding))
        self.btnlayout.addWidget(self.btn_remove)
        v = QVBoxLayout()
        self.setLayout(v)
        v.addLayout(self.btnlayout)
        self.setVisible(False)
        self.setMinimumHeight(50)
        self.setMaximumHeight(50)
        self.setMinimumWidth(50)
        self.setMaximumWidth(50)
        self.setMouseTracking(True)


display_template = dedent(
    """<b>{model_name}</b><br>
    <i>{model_description}</i><br>
    <b>source:</b> {model_source}<br>
    <b>input axes:</b> {fmt_input_shape}<br>
    <b>output axes:</b> {fmt_output_shape}<br>"""
)


class ModelSourceEdit(QTextEdit):
    modelDeleted = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.btn_container = ModelControlButtons(self)
        self.btn_container.remove.connect(self.askClear)

        self.setPlaceholderText(
            "Copy-paste a bioimage.io model doi or nickname, or drag and drop a model.zip file here. Then press on the '+' button below."
        )

        self._model_source = None

    def getModelSource(self) -> str:
        return self._model_source or self.toPlainText()

    def resizeEvent(self, evt):
        own_size = self.size()
        self.btn_container.move(own_size.width() - self.btn_container.size().width(), 0)
        self.btn_container.resize(own_size.width(), self.btn_container.size().height())

        super().resizeEvent(evt)

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Enter, Qt.Key_Return]:
            event.accept()
            return

        super().keyPressEvent(event)

    def enterEvent(self, ev):
        if self.toPlainText():
            self.btn_container.setVisible(True)
        super().enterEvent(ev)

    def leaveEvent(self, ev):
        self.btn_container.setVisible(False)
        super().leaveEvent(ev)

    def setModelInfo(self, model_source, model_info, template=display_template):
        self.setHtml(
            template.format(
                model_source=model_source,
                model_name=getattr(model_info, "name", "n/a"),
                model_description=getattr(model_info, "description", "n/a"),
                fmt_input_shape="".join(model_info.inputs[0].axes),
                fmt_output_shape="".join(model_info.outputs[0].axes),
            )
        )
        self._model_source = model_source

    def dropEvent(self, dropEvent):
        urls = dropEvent.mimeData().urls()
        self.clear()
        self.setPlainText(urls[0].toLocalFile())

    def dragEnterEvent(self, event):
        # Only accept drag-and-drop events that consist of a single local file.
        urls = event.mimeData().urls()
        if len(urls) == 1 and all(url.isLocalFile() for url in urls):
            event.acceptProposedAction()

    def clear(self):
        super().clear()
        self.setEnabled(True)
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.setToolTip(
            "Copy/Paste a bioimage.io model doi or nickname, or\ndrag-and-drop a downloaded bioimage.io model.zip file."
        )
        self._model_source = None

    def askClear(self):
        if (
            QMessageBox.question(self, "Remove model", "Do you want to remove the model from the project file?")
            == QMessageBox.Yes
        ):
            self.clear()
            self.modelDeleted.emit()

    def setModelIncompatibleState(self, model_source, model_info, error_message):
        self.setToolTip(f"Model not compatible with data:\n\n{error_message}")
        self.setModelInfo(model_source, model_info, template=f"<red>{display_template}</red>")

    def setEmptyState(self):
        self.clear()

    def setModelDataAvailableState(self, model_source, model_info):
        self.btn_container.setEnabled(True)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setToolTip("Remove the model by clicking the 'x' in the upper right corner.")
        self.setModelInfo(model_source, model_info)

    def setReadyState(self, model_source, model_info):
        self.btn_container.setEnabled(False)
        self.setToolTip("Stop the model to make changes.")
        self.setModelInfo(model_source, model_info)


class ModelStateControl(QWidget):
    uploadDone = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.threadRouter = ThreadRouter(self)
        self._preDownloadChecks = set()

        layout = QVBoxLayout()

        self.modelInfoWidget = ModelSourceEdit(self)
        self.statusLabel = QLabel(self)
        self.modelControlButton = QToolButton(self)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.statusLabel)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.modelControlButton)
        layout.addWidget(self.modelInfoWidget)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    def setTiktorchController(self, tiktorchController):
        self._tiktorchController = tiktorchController

    def setTiktorchModel(self, tiktorchModel):
        self._tiktorchModel = tiktorchModel
        self._tiktorchModel.registerListener(self._onTiktorchStateChange)
        self.modelInfoWidget.modelDeleted.connect(self._tiktorchModel.clear)

    @threadRouted
    def _onTiktorchStateChange(self, state: TiktorchOperatorModel.State):

        with contextlib.suppress(Exception):
            self.modelControlButton.clicked.disconnect()

        if state is TiktorchOperatorModel.State.Empty:
            self.modelControlButton.setIcon(QIcon(ilastikIcons.GoNext))
            self.modelControlButton.setToolTip("Check and activate the model")
            self.modelControlButton.setEnabled(True)
            self.modelControlButton.clicked.connect(self.onModelInfoRequested)
            self.modelInfoWidget.setEmptyState()

        elif state is TiktorchOperatorModel.State.ModelDataAvailable:
            self.modelControlButton.clicked.connect(self.uploadModelClicked)
            self.modelControlButton.setIcon(QIcon(ilastikIcons.Upload))
            self.modelControlButton.setToolTip("Activate the model")
            self.modelControlButton.setEnabled(True)
            modelData = self._tiktorchModel.modelData
            self.modelInfoWidget.setModelDataAvailableState(modelData.modelUri, modelData.rawDescription)

        elif state is TiktorchOperatorModel.State.Ready:
            self.modelControlButton.setIcon(QIcon(ilastikIcons.ProcessStop))
            self.modelControlButton.setToolTip("Stop and unload the model")
            self.modelControlButton.clicked.connect(self._tiktorchController.closeSession)
            self.modelControlButton.setEnabled(True)
            modelData = self._tiktorchModel.modelData
            self.modelInfoWidget.setReadyState(modelData.modelUri, modelData.rawDescription)

    def _setAndUploadModel(self, modelUri, rawDescription, modelBinary):
        self._setModel(modelUri, rawDescription, modelBinary)
        self._uploadModel()

    def _setModel(self, modelUri, rawDescription, modelBinary):
        self._tiktorchController.setModelData(modelUri, rawDescription, modelBinary)

    def _uploadModel(self):
        cancelSrc = CancellationTokenSource()
        dialog = PercentProgressDialog(self, title="Initializing model")
        dialog.rejected.connect(cancelSrc.cancel)
        dialog.open()

        modelInfo = self._tiktorchController.uploadModel(
            progressCallback=dialog.updateProgress,
            cancelToken=cancelSrc.token,
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

    def uploadModelClicked(self):
        try:
            self._uploadModel()
        except Exception as e:
            self._showErrorMessage(e)

    def onModelInfoRequested(self):
        model_uri = self.modelInfoWidget.getModelSource()
        if model_uri is None:
            logger.debug("No model uri provided")
            return
        model_uri = model_uri.strip()
        if not model_uri:
            # try select file from file chooser
            model_uri = self.getModelToOpen(self)
        if not model_uri:
            return

        model_info = load_raw_resource_description(model_uri)

        self.modelInfoWidget.setModelInfo(model_uri, model_info)
        # check model is broadly compatible with ilastik
        try:
            compatibility_checks = self.checkModelCompatibility(model_info)

            if any(compatibility_checks):
                reasons = "\n".join(r["reason"] for r in compatibility_checks if r)
                QMessageBox.information(
                    self,
                    "Model incompatible",
                    f"Model incompatible, reasons:\n\n{reasons}.\nPlease select a different model.",
                )
                reasons_log = " - ".join(r["reason"] for r in compatibility_checks if r)
                logger.debug(f"Incompatible model from {model_uri}. Reasons: {reasons_log}")
                self.modelInfoWidget.setModelIncompatibleState(model_uri, model_info, reasons)
                return
        except Exception as e:
            self._showErrorMessage(e)
            return

        try:
            downloader = self.resolveModel(model_uri, model_info)
        except Exception as e:
            self._showErrorMessage(e)

    def resolveModel(self, model_uri, model_info) -> BioImageDownloader:
        """Initiate model download"""
        cancelSrc = CancellationTokenSource()
        downloader = BioImageDownloader(model_uri, cancelSrc.token, self)
        dialog = PercentProgressDialog(self, title="Downloading model", secondary_bar=True)
        dialog.rejected.connect(cancelSrc.cancel)
        dialog.show()
        downloader.finished.connect(dialog.accept)
        downloader.error.connect(self._showErrorMessage)
        downloader.progress0.connect(dialog.updateProgress)
        downloader.progress1.connect(partial(dialog.updateProgress, bar=BarId.bar1))
        downloader.currentUri.connect(partial(dialog.updateBarFormat, bar=BarId.bar1))
        downloader.dataAvailable.connect(partial(self._setAndUploadModel, model_uri, model_info))
        downloader.start()
        return downloader

    @staticmethod
    def _check_model_compatible(model_info):
        """General checks whether ilastik will be able to show results of the network"""

        checks = []
        # currently we only support a single input:
        if len(model_info.inputs) != 1:
            checks.append(
                {
                    "reason": f"ilastik supports only models with one input tensor. Model expects {len(model_info.inputs)}"
                }
            )

        if len(model_info.outputs) != 1:
            checks.append(
                {
                    "reason": f"ilastik supports only models with one output tensor. Model expects {len(model_info.inputs)}"
                }
            )

        output_spec = model_info.outputs[0]
        # we need at least twp spacial axes, and a channel axes in the output
        if "c" not in output_spec.axes:
            checks.append(
                {
                    "reason": "ilastik only supports models with a channel axis in the outputs. No channel axis found in output."
                }
            )

        spacial_axes_in_output = [ax for ax in output_spec.axes if ax in "xyz"]
        if len(spacial_axes_in_output) < 2:
            checks.append(
                {
                    "reason": f"ilastik needs at least two spacial (xyz) axes in the output to show an image. Only found {output_spec.axes}."
                }
            )

        return checks

    def _showErrorMessage(self, exc):
        logger.error("".join(traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)))
        QMessageBox.critical(
            self, "ilastik detected a problem with your model", f"Failed to initialize model:\n {type(exc)} {exc}"
        )

    def addCheck(self, fn: Callable[[dict], List[dict]]):
        """Function called after raw model info is retrieved before it's resolved

        Resolving/Downloading can be quite a lengthy process - which we want to
        avoid if model cannot be run in the first place.

        Args:
            fn: callable that takes a single arg: model_info and performs
              compatibility checks. Must return {} if it's all good.
              Must return a dict with at least {"reason": "why it failed"}
              See `ModelStateControl._check_model_compatible` for an example.
        """
        self._preDownloadChecks.add(fn)

    def checkModelCompatibility(self, model_info):
        # first check is for _general_ compatibility with ilastik
        return self._check_model_compatible(model_info) + [
            pre_check(model_info) for pre_check in self._preDownloadChecks
        ]

    @classmethod
    def getModelToOpen(cls, parent_window):
        """
        opens a QFileDialog for importing files
        """
        # open dialog in recent model folder if possible
        folder = preferences.get("DataSelection", "recent model", os.path.expanduser("~"))

        # get folder from user
        return QFileDialog.getOpenFileName(parent_window, "Select Model", folder, "Models (*.tmodel *.zip)")[0]


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

    def setModelInfo(self, model_source, model_info, template=Template(display_template)):
        self.setToolTip(
            template.render(
                model_source=model_source,
                model_name=getattr(model_info, "name", "n/a"),
                model_description=getattr(model_info, "description", "n/a"),
                fmt_input_shape="".join(model_info.inputs[0].axes),
                fmt_output_shape="".join(model_info.outputs[0].axes),
            )
        )

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
            self.insertItem(1, model_source, model_info)
        else:
            self.setCurrentText(self.itemText(idx))
        self.setItemText(0, "remove model")
        self.setItemData(0, BioImageModelCombo._REMOVE_FILE)

    def setReadyState(self, model_source, model_info):
        self.setModelDataAvailableState(model_source, model_info)

    def refresh(self):
        # do this in the background, indicate busyness
        self.clear()
        resp = requests.get(BioImageModelCombo.collections_url)
        if resp.status_code != 200:
            logger.error(f"Error fetching models - status code: {resp.status_code}")
            return

        js = resp.json()

        enhancer_models = [
            m for m in js["collection"] if "enhancer" in m["name"].lower() or "shallow2deep" in m["tags"]
        ]

        self.addItem("choose model..", {})
        for m in enhancer_models:
            self.addItem(m["name"], m)
        self.addItem("select file", BioImageModelCombo._SELECT_FILE)


class EnhancerModelStateControl(ModelStateControl):
    uploadDone = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.modelInfoWidget.modelOpenFromFile.connect(self.onModelInfoRequested)

    def _setup_ui(self):
        self.threadRouter = ThreadRouter(self)
        self._preDownloadChecks = set()

        layout = QVBoxLayout()

        self.modelInfoWidget = BioImageModelCombo(self)
        self.statusLabel = QLabel(self)
        self.statusLabel.setText("status...")
        self.modelControlButton = QToolButton(self)
        self.modelControlButton.setText("...")
        self.modelControlButton.setToolTip("Click here to check model details, initialize, or un-initialize the model")
        self.statusLabel.setVisible(False)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.statusLabel)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.modelControlButton)
        layout.addWidget(self.modelInfoWidget)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)
