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
# 		   http://ilastik.org/license.html
###############################################################################
import logging
import pathlib
from functools import partial
from time import perf_counter
from typing import Type

from qtpy.QtCore import Signal, QThread
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
)
from requests.exceptions import SSLError, ConnectionError

from lazyflow.utility import isUrl
from lazyflow.utility.io_util.OMEZarrStore import OMEZarrStore
from lazyflow.utility.io_util.RESTfulPrecomputedChunkedVolume import RESTfulPrecomputedChunkedVolume
from lazyflow.utility.io_util.multiscaleStore import MultiscaleStore
from lazyflow.utility.pathHelpers import uri_to_Path

logger = logging.getLogger(__name__)


def _validate_uri(text: str) -> str:
    """Make sure the input is a URI, convert if it's a path, ensure path exists if it's a 'file:' URI already.
    Returns a valid URI, or raises ValueError if invalid."""
    if text == "":
        raise ValueError('Please enter a path or URL, then press "Check".')
    if not isUrl(text):
        ospath = pathlib.Path(text)
        if ospath.exists():  # It's a local file path - convert to file: URI
            return ospath.as_uri()
        else:  # Maybe the user typed the address manually and forgot https://?
            raise ValueError('Please enter a URL including protocol ("http(s)://" or "file:").')
    elif isUrl(text) and text.startswith("file:"):
        # Check the file URI points to an existing path
        try:
            exists = uri_to_Path(text).exists()
        except ValueError:  # from uri_to_Path
            raise ValueError("Path is not absolute. Please try copy-pasting the full path.")
        if not exists:
            raise ValueError("Directory does not exist or URL is malformed. Please try copy-pasting the path directly.")
    return text

def generate_nickname(uri: str) -> str:
    """
    Generate a nickname for multiscale dataset:
    Examples:
        https://data.ilastik.org/2d_cells_apoptotic_1channel.zarr -> 2d_cells_apoptotic_1channel
        https://data.ilastik.org/2d_cells_apoptotic_1channel.zarr/s1 -> 2d_cells_apoptotic_1channel-s1
    """
    import os
    from urllib.parse import urlparse, unquote
    parsed = urlparse(uri)
    path_parts = parsed.path.strip("/").split("/")

    container = os.path.splitext(path_parts[0])[0] if path_parts else "dataset"
    internal = path_parts[1] if len(path_parts) > 1 else ""

    if internal.startswith("s") and internal[1:].isdigit():
        nickname = f"{container}-{internal}"
    else:
        nickname = container

    return nickname


class CheckRemoteStoreWorker(QThread):
    success = Signal(object)  # returns MultiscaleStore
    error = Signal(str)  # returns error message

    def __init__(self, parent, store_init: Type[MultiscaleStore.__init__]):
        super().__init__(parent)
        self.store_init = store_init

    def run(self):
        try:
            store = self.store_init()
            self.success.emit(store)
        except Exception as e:
            if isinstance(e, SSLError):
                msg = "SSL error, please check that you are using the correct protocol (http/https)."
            elif isinstance(e, ConnectionError):
                msg = "Connection error, please check that the server is online and the URL is correct."
            else:
                msg = "Couldn't load a multiscale dataset at this address."
            msg += f"\n\nMore detail:\n{e}"
            logger.error(e, exc_info=True)
            self.error.emit(msg)


class MultiscaleDatasetBrowser(QDialog):

    EXAMPLE_URI = "https://data.ilastik.org/2d_cells_apoptotic_1channel.zarr"

    def __init__(self, history=None, parent=None):
        super().__init__(parent)
        self._worker_start_time = 0
        self._history = history or []
        self.selected_uri = None  # Return value read by the caller after the dialog is closed

        self.setup_ui()

    def setup_ui(self):
        self.setMinimumSize(800, 200)
        self.setWindowTitle("Select Multiscale Source")
        main_layout = QVBoxLayout()

        description = QLabel(self)
        description.setText('Enter path or URL and click "Check".')
        main_layout.addWidget(description)

        self.combo = QComboBox(self)
        self.combo.setEditable(True)
        self.combo.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        for item in self._history:
            self.combo.addItem(item, item)

        self.combo.lineEdit().setPlaceholderText("Enter path/URL or choose from history...")
        self.combo.setCurrentIndex(-1)

        combo_label = QLabel(self)
        combo_label.setText("Dataset address: ")

        self.example_button = QPushButton(self)
        self.example_button.setText("Add example")
        self.example_button.setToolTip("Add url to '2d_cells_apoptotic_1channel` example from the ilastik website.")
        self.example_button.pressed.connect(lambda: self.combo.lineEdit().setText(self.EXAMPLE_URI))

        combo_layout = QGridLayout()
        self.check_button = QPushButton(self)
        self.check_button.setText("Check")
        self.check_button.clicked.connect(self._validate_text_input)
        self.combo.lineEdit().returnPressed.connect(self.check_button.click)
        combo_layout.addWidget(combo_label, 0, 0)
        combo_layout.addWidget(self.combo, 0, 1)
        combo_layout.addWidget(self.check_button, 0, 2)
        combo_layout.addWidget(self.example_button, 1, 0)

        main_layout.addLayout(combo_layout)

        result_label = QLabel(self)
        result_label.setText("Metadata found at the given address: ")
        self.result_text_box = QTextBrowser(self)
        result_layout = QVBoxLayout()
        result_layout.addWidget(result_label)
        result_layout.addWidget(self.result_text_box)

        main_layout.addLayout(result_layout)

        self.qbuttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.qbuttons.accepted.connect(self.accept)
        self.qbuttons.rejected.connect(self.reject)
        self.qbuttons.button(QDialogButtonBox.Ok).setText("Add to project")
        self.qbuttons.button(QDialogButtonBox.Ok).setEnabled(False)

        def update_ok_button(current_entered_text):
            if current_entered_text == self.selected_uri:
                self.qbuttons.button(QDialogButtonBox.Ok).setEnabled(True)
            else:
                self.qbuttons.button(QDialogButtonBox.Ok).setEnabled(False)

        self.combo.lineEdit().textChanged.connect(update_ok_button)
        main_layout.addWidget(self.qbuttons)
        self.setLayout(main_layout)

    def _validate_text_input(self, _event):
        self._set_inputs_enabled(False)
        self.selected_uri = None
        text = self.combo.currentText().strip()
        try:
            uri = _validate_uri(text)
        except ValueError as e:
            self.display_error(str(e))
            return
        if uri != text:
            self.combo.lineEdit().setText(uri)
        logger.debug(f"Entered URL: {uri}")
        # Ask each store type if it likes the URL to avoid web requests during instantiation attempts.
        if OMEZarrStore.is_uri_compatible(uri):
            StoreTypeMatchingUri = OMEZarrStore
            worker = CheckRemoteStoreWorker(self, partial(OMEZarrStore, uri))
        elif RESTfulPrecomputedChunkedVolume.is_uri_compatible(uri):
            StoreTypeMatchingUri = RESTfulPrecomputedChunkedVolume
            worker = CheckRemoteStoreWorker(self, partial(RESTfulPrecomputedChunkedVolume, volume_url=uri))
        else:
            store_types = [OMEZarrStore, RESTfulPrecomputedChunkedVolume]
            supported_formats = "\n".join(f"<li>{s.NAME} ({s.URI_HINT})</li>" for s in store_types)
            self.display_error(
                f"<p>Address does not look like any supported format.</p>"
                f"<p>Supported formats:</p>"
                f"<ul>{supported_formats}</ul>"
            )
            return
        self.result_text_box.setText(
            f"Trying to load {StoreTypeMatchingUri.NAME} at {uri}.\nThis could take a while if the server or connection is slow."
        )
        worker.success.connect(self.display_success)
        worker.error.connect(self.display_error)
        self._worker_start_time = perf_counter()
        worker.start()

    def _set_inputs_enabled(self, enabled):
        self.example_button.setEnabled(enabled)
        self.check_button.setEnabled(enabled)
        self.combo.setEnabled(enabled)

    def display_error(self, msg):
        self._set_inputs_enabled(True)
        self.result_text_box.setText(msg)
        self.qbuttons.button(QDialogButtonBox.Ok).setEnabled(False)

    def display_success(self, store: MultiscaleStore):
        self._set_inputs_enabled(True)
        self.selected_uri = store.uri
        nickname = generate_nickname(store.uri)

        time_to_finish = perf_counter() - self._worker_start_time
        time_text = f"Finished check in {time_to_finish:.2f} seconds."
        if time_to_finish > 3:
            time_text += (
                "</p><p>This was <b>very</b> slow. "
                "If you add this dataset to your project, you may experience long delays. "
                "The ilastik documentation contains some performance tips that might be helpful.</p>"
            )
        scale_info_html = "\n".join(
            [f"<li>{scale.to_display_string(name)}</li>" for name, scale in store.multiscale.items()]
        )
        self.result_text_box.setHtml(
            f"<p>{time_text}<br>"
            f"Nickname: <b>{nickname}</b><br>"
            f"URL: {self.selected_uri}<br>"
            f"Data format: {store.NAME}<br>"
            f"Available scales:</p><ol>{scale_info_html}</ol>"
        )
        self.qbuttons.button(QDialogButtonBox.Ok).setEnabled(True)


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication

    app = QApplication([])

    logging.basicConfig(level=logging.INFO)

    pv = MultiscaleDatasetBrowser()
    pv.combo.addItem("test")
    pv.show()
    app.exec_()
    print(pv.result(), pv.selected_uri)
