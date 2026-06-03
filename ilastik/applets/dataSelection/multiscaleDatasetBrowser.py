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
    QFileDialog,
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
)
from requests.exceptions import SSLError, ConnectionError as RequestsConnectionError

from lazyflow.utility import isUrl
from lazyflow.utility.io_util.OMEZarrStore import OMEZarrStore
from lazyflow.utility.io_util.RESTfulPrecomputedChunkedVolume import RESTfulPrecomputedChunkedVolume
from lazyflow.utility.io_util.multiscaleStore import MultiscaleStore
from lazyflow.utility.pathHelpers import uri_to_Path
from volumina.utility import preferences

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
        except (ConnectionError, RequestsConnectionError) as e:
            if isinstance(e, SSLError):
                msg = "SSL error, please check that you are using the correct protocol (http/https)."
            elif isinstance(e, ConnectionError):
                msg = "Connection error, please check that the server is online and the URL is correct."
            msg += f"\n\nMore detail:\n{e}"
            logger.error(e, exc_info=True)
            self.error.emit(msg)
        except Exception as e:
            logger.error(e, exc_info=True)
            msg = f"Couldn't load a multiscale dataset at this address.\n\nMore detail:\n{e}"
            self.error.emit(msg)


class MultiscaleDatasetBrowser(QDialog):

    EXAMPLE_URI = "https://data.ilastik.org/2d_cells_apoptotic_1channel.zarr"
    PREFERENCES_GROUP = "DataSelection"
    PREFERENCES_SETTING = "recent multiscale dir"

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
        self.browse_button = QPushButton(self)
        self.browse_button.setText("Browse...")
        self.browse_button.setToolTip("Choose an OME-Zarr dataset folder from disk.")
        self.browse_button.clicked.connect(self._browse_for_directory)
        self.check_button = QPushButton(self)
        self.check_button.setText("Check")
        self.check_button.clicked.connect(self._validate_text_input)
        self.combo.lineEdit().returnPressed.connect(self.check_button.click)
        combo_layout.addWidget(combo_label, 0, 0)
        combo_layout.addWidget(self.combo, 0, 1)
        combo_layout.addWidget(self.browse_button, 0, 2)
        combo_layout.addWidget(self.check_button, 0, 3)
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

    def _starting_directory_for_folder_picker(self) -> str:
        text = self.combo.currentText().strip()
        pref_path = pathlib.Path(preferences.get(self.PREFERENCES_GROUP, self.PREFERENCES_SETTING, pathlib.Path.home()))
        default_dir = pref_path if pref_path.is_dir() else pref_path.parent

        if not text:
            return str(default_dir)

        try:
            return str(uri_to_Path(text))  # Valid file URI?
        except ValueError:
            pass

        if isUrl(text):
            return str(default_dir)

        path = pathlib.Path(text).expanduser()
        if path.exists():
            return str(path if path.is_dir() else path.parent)
        if path.parent.exists():
            return str(path.parent)

        return str(default_dir)

    def _browse_for_directory(self):
        options = QFileDialog.Options(QFileDialog.ShowDirsOnly)
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select OME-Zarr Dataset Folder",
            self._starting_directory_for_folder_picker(),
            options=options,
        )
        if not directory:
            return

        preferences.set(self.PREFERENCES_GROUP, self.PREFERENCES_SETTING, pathlib.Path(directory).as_posix())
        self.combo.lineEdit().setText(directory)
        self.check_button.click()

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
        known_formats_msg = ""
        if RESTfulPrecomputedChunkedVolume.is_uri_compatible(uri):
            StoreTypeMatchingUri = RESTfulPrecomputedChunkedVolume
            worker = CheckRemoteStoreWorker(self, partial(RESTfulPrecomputedChunkedVolume, volume_url=uri))
        elif OMEZarrStore.is_uri_probable(uri):
            StoreTypeMatchingUri = OMEZarrStore
            worker = CheckRemoteStoreWorker(self, partial(OMEZarrStore, uri))
        else:
            StoreTypeMatchingUri = OMEZarrStore
            worker = CheckRemoteStoreWorker(self, partial(OMEZarrStore, uri))
            store_types = [OMEZarrStore, RESTfulPrecomputedChunkedVolume]
            supported_formats = "\n".join(f"<li>{s.NAME} ({s.URI_HINT})</li>" for s in store_types)
            known_formats_msg = (
                "<p>This address doesn't look like a supported format, but we're trying OME-Zarr anyway.</p>"
                "<p>Supported formats:</p>"
                f"<ul>{supported_formats}</ul>"
            )
        self.result_text_box.setText(
            f"<p>Trying to load {StoreTypeMatchingUri.NAME} at {uri}.</p>"
            f"<p>This could take a while if the server or connection is slow.</p>{known_formats_msg}"
        )
        worker.success.connect(self.display_success)
        worker.error.connect(self.display_error)
        self._worker_start_time = perf_counter()
        worker.start()

    def _set_inputs_enabled(self, enabled):
        self.example_button.setEnabled(enabled)
        self.browse_button.setEnabled(enabled)
        self.check_button.setEnabled(enabled)
        self.combo.setEnabled(enabled)

    def display_error(self, msg):
        self._set_inputs_enabled(True)
        self.result_text_box.setText(msg)
        self.qbuttons.button(QDialogButtonBox.Ok).setEnabled(False)

    def display_success(self, store: MultiscaleStore):
        self._set_inputs_enabled(True)
        self.selected_uri = store.uri
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
