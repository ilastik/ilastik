"""
Depending on the demand this might get reworked into a real "browser". Right now
this will only be used to punch in the url and do some validation. Naming of the
file is just to reflect the similar function as dvidDataSelectionBrowser.

Todos:
  - check whether can me somehow merged with dvidDataSelctionBrowser

"""
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
)


from lazyflow.utility.io_util.RESTfulPrecomputedChunkedVolume import RESTfulPrecomputedChunkedVolume

import logging


logger = logging.getLogger(__name__)


class PrecomputedVolumeBrowser(QDialog):
    def __init__(self, history=None, parent=None):
        super().__init__(parent)
        self._history = history or []
        self.selected_url = None

        self.setup_ui()

    def setup_ui(self):
        self.setMinimumSize(800, 200)
        self.setWindowTitle('Precomputed Volume Selection Dialog')
        main_layout = QVBoxLayout()

        # TODO: get history of successful URLs from config:
        self.combo = QComboBox(self)
        self.combo.setEditable(True)
        self.combo.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.combo.addItem("")
        for item in self._history:
            self.combo.addItem(item)

        combo_label = QLabel(parent=self)
        combo_label.setText("Enter volume address: ")
        combo_layout = QHBoxLayout()
        chk_button = QPushButton(self)
        chk_button.setText('Check URL')
        chk_button.clicked.connect(self.handle_chk_button_clicked)
        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(self.combo)
        combo_layout.addWidget(chk_button)

        main_layout.addLayout(combo_layout)

        # add some debug stuff
        debug_label = QLabel(self)
        debug_label.setText('debug: ')
        self.debug_text = QTextBrowser(self)
        debug_layout = QVBoxLayout()
        debug_layout.addWidget(debug_label)
        debug_layout.addWidget(self.debug_text)

        main_layout.addLayout(debug_layout)

        qb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        qb.accepted.connect(self.accept)
        qb.rejected.connect(self.reject)
        main_layout.addWidget(qb)
        self.setLayout(main_layout)

    def handle_chk_button_clicked(self, event):
        self.selected_url = self.combo.currentText()
        logger.debug(f"selected url: {self.selected_url}")
        url = self.selected_url.lstrip('precomputed://')
        try:
            rv = RESTfulPrecomputedChunkedVolume(volume_url=url)
        except Exception as e:
            qm = QMessageBox(self)
            qm.setWindowTitle('An Error Occured')
            qm.setText(f"woops: {e}")
            qm.show()
            return

        self.debug_text.setText(
            f"volume encoding: {rv.get_encoding()}\n"
            f"available scales: {rv.available_scales}\n"
            f"using scale: {rv._use_scale}\n"
            f"data shape: {rv.get_shape()}\n"
        )


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])

    logging.basicConfig(level=logging.INFO)

    pv = PrecomputedVolumeBrowser()
    pv.combo.addItem("test")
    pv.show()
    app.exec_()
    print(pv.result(), pv.selected_url)
