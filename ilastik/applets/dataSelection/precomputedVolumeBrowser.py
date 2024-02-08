"""
Depending on the demand this might get reworked into a real "browser". Right now
this will only be used to punch in the url and do some validation. Naming of the
file is just to reflect the similar function as dvidDataSelectionBrowser.

Todos:
  - check whether can me somehow merged with dvidDataSelctionBrowser

"""
import logging

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
)

from lazyflow.utility.io_util.RESTfulPrecomputedChunkedVolume import RESTfulPrecomputedChunkedVolume

logger = logging.getLogger(__name__)


class PrecomputedVolumeBrowser(QDialog):
    def __init__(self, history=None, parent=None):
        super().__init__(parent)
        self._history = history or []
        self.selected_url = None

        self.setup_ui()

    def setup_ui(self):
        self.setMinimumSize(800, 200)
        self.setWindowTitle("Select Precomputed Volume")
        main_layout = QVBoxLayout()

        description = QLabel(self)
        description.setText('Enter URL (with or without "precomputed://") and click "Check URL".')
        main_layout.addWidget(description)

        self.combo = QComboBox(self)
        self.combo.setEditable(True)
        self.combo.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.combo.addItem("")
        for item in self._history:
            self.combo.addItem(item)

        combo_label = QLabel(self)
        combo_label.setText("Dataset address: ")
        combo_layout = QHBoxLayout()
        chk_button = QPushButton(self)
        chk_button.setText("Check URL")
        chk_button.clicked.connect(self.handle_chk_button_clicked)
        self.combo.lineEdit().returnPressed.connect(chk_button.click)
        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(self.combo)
        combo_layout.addWidget(chk_button)

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
        main_layout.addWidget(self.qbuttons)
        self.setLayout(main_layout)

    def handle_chk_button_clicked(self, event):
        url = self.combo.currentText().strip().lstrip("precomputed://")
        if url == "":
            return
        logger.debug(f"Entered URL: {url}")
        try:
            rv = RESTfulPrecomputedChunkedVolume(volume_url=url)
        except Exception as e:
            self.qbuttons.button(QDialogButtonBox.Ok).setEnabled(False)
            msg = f"Could not connect to a Precomputed dataset at this address. Full error message:\n\n{e}"
            self.result_text_box.setText(msg)
            return

        self.selected_url = f"precomputed://{url}"
        self.result_text_box.setText(
            f"Full URL: {self.selected_url}\n"
            f"Dataset encoding: {rv.get_encoding()}\n"
            f"Number of scales: {len(rv.scales)}\n"
            f"Raw dataset shape: {rv.get_shape(rv.highest_resolution_key)}\n"
            f"Lowest scale shape: {rv.get_shape(rv.lowest_resolution_key)}\n"
        )
        # This check-button might have been triggered by pressing Enter.
        # The timer prevents triggering the now enabled OK button by the same keypress.
        QTimer.singleShot(0, lambda: self.qbuttons.button(QDialogButtonBox.Ok).setEnabled(True))


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    logging.basicConfig(level=logging.INFO)

    pv = PrecomputedVolumeBrowser()
    pv.combo.addItem("test")
    pv.show()
    app.exec_()
    print(pv.result(), pv.selected_url)
