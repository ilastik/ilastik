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

import requests
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QComboBox, QHBoxLayout, QSizePolicy, QToolButton

from ilastik.applets.neuralNetwork.modelStateControl import ModelStateControl, display_template
from ilastik.utility.gui import ThreadRouter, silent_qobject

logger = logging.getLogger(__file__)


class BioImageModelCombo(QComboBox):
    collections_url = "https://uk1s3.embassy.ebi.ac.uk/public-datasets/bioimage.io/collection.json"
    _SELECT_FILE = object()
    _REMOVE_FILE = object()

    modelDeleted = Signal()
    modelOpenFromFile = Signal()

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
            with silent_qobject(self):
                self.setCurrentIndex(0)

            self.modelOpenFromFile.emit()

    def setModelDataAvailableState(self, model_source, model_info):
        idx = self.findText(model_info.name)
        if idx == -1:
            # from file
            with silent_qobject(self) as silent_self:
                silent_self.insertItem(1, model_info.name, model_info)
            idx = 1

        self.setCurrentText(self.itemText(idx))

        model = self.model()
        assert model
        for idx in range(1, self.count()):
            model.item(idx).setEnabled(False)

        self.setItemText(0, "remove model")
        self.setItemData(0, BioImageModelCombo._REMOVE_FILE)

        self.setEnabled(True)

    def setReadyState(self, model_source, model_info):
        self.setModelDataAvailableState(model_source, model_info)
        self.setEnabled(False)

    def refresh(self):
        # do this in the background, indicate busyness
        resp = requests.get(self.collections_url)

        self.clear()

        if resp.status_code != 200:
            self.addItem("error fetching model list", {})
            logger.error(f"Error fetching model list from {self.collections_url}: {resp.status_code=}")
            return

        BIOIMAGEIO_COLLECTION = resp.json()

        self.addItem("choose model..", {})
        self.insertSeparator(1)

        for model in BIOIMAGEIO_COLLECTION["collection"]:
            if "shallow2deep" in model["tags"]:
                self.addItem(model["name"], model)

        self.insertSeparator(self.count())
        self.addItem("select file", BioImageModelCombo._SELECT_FILE)


class EnhancerModelStateControl(ModelStateControl):
    uploadDone = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.modelSourceEdit.modelOpenFromFile.connect(self._open_model_from_dialog)

    def _setup_ui(self):
        self.threadRouter = ThreadRouter(self)
        self._preDownloadChecks = set()

        layout = QHBoxLayout()

        self.modelSourceEdit = BioImageModelCombo(self)
        self.modelSourceEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.modelControlButton = QToolButton(self)
        self.modelControlButton.setText("...")
        self.modelControlButton.setToolTip("Click here to check model details, initialize, or un-initialize the model")

        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.modelSourceEdit)
        layout.addWidget(self.modelControlButton)

        self.setLayout(layout)
