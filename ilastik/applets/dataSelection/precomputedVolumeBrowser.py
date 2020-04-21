"""
Depending on the demand this might get reworked into a real "browser". Right now
this will only be used to punch in the url and do some validation. Naming of the
file is just to reflect the similar function as dvidDataSelectionBrowser.

Todos:
  - check whether can me somehow merged with dvidDataSelctionBrowser

"""
from typing import List, Optional
from urllib.parse import urljoin
from pathlib import Path
import os
import json
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
from ilastik.filesystem import get_filesystem_for
from ndstructs.datasource.PrecomputedChunksDataSource import PrecomputedChunksInfo

import logging


logger = logging.getLogger(__name__)


class PrecomputedVolumeBrowser(QDialog):
    def __init__(self, history=None, parent=None):
        super().__init__(parent)
        self._history = history or []
        self.base_url = None

        self.setMinimumSize(800, 200)
        self.setWindowTitle("Precomputed Volume Selection Dialog")
        main_layout = QVBoxLayout()

        description = QLabel(self)
        description.setText(
            'enter base URL of volume starting with "precomputed://http..."'
            'hit the "check URL" button to validate the entered address.'
        )
        main_layout.addWidget(description)

        self.combo = QComboBox(self)
        self.combo.setEditable(True)
        self.combo.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.combo.currentTextChanged.connect(self.resetVolume)
        self.combo.addItem("")
        for item in self._history:
            self.combo.addItem(item)

        combo_label = QLabel(parent=self)
        combo_label.setText("Enter volume address: ")
        combo_layout = QHBoxLayout()
        chk_button = QPushButton(self)
        chk_button.setText("Check URL")
        chk_button.clicked.connect(self.handle_chk_button_clicked)
        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(self.combo)
        combo_layout.addWidget(chk_button)

        main_layout.addLayout(combo_layout)

        scale_layout = QHBoxLayout()
        scale_label = QLabel(self)
        scale_label.setText("scale: ")
        scale_layout.addWidget(scale_label)
        self.scale_combo = QComboBox(self)
        self.scale_combo.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        scale_layout.addWidget(self.scale_combo)
        main_layout.addLayout(scale_layout)

        # add some debug stuff
        debug_label = QLabel(self)
        debug_label.setText("debug: ")
        self.debug_text = QTextBrowser(self)
        debug_layout = QVBoxLayout()
        debug_layout.addWidget(debug_label)
        debug_layout.addWidget(self.debug_text)

        main_layout.addLayout(debug_layout)

        self.qbuttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.qbuttons.accepted.connect(self.accept)
        self.qbuttons.rejected.connect(self.reject)
        self.qbuttons.button(QDialogButtonBox.Ok).setEnabled(False)
        main_layout.addWidget(self.qbuttons)
        self.setLayout(main_layout)

    def resetVolume(self):
        self.qbuttons.button(QDialogButtonBox.Ok).setEnabled(False)
        self.debug_text.setText("")
        self.scale_combo.clear()
        self.base_url = None

    @property
    def selected_url(self) -> Optional[str]:
        if not self.base_url:
            return None
        url = urljoin(self.base_url + "/", self.scale_combo.currentText())
        if url.startswith("precomputed://"):
            return url
        else:
            return "precomputed://" + url

    def handle_chk_button_clicked(self, event):
        try:
            filesystem, path = get_filesystem_for(url=self.combo.currentText())
            if 'info' in path.parts:
                info_idx = path.parts.index('info')
                path = Path(os.path.join(*path.parts[:info_idx + 1]))
            else:
                path = path / "info"
            info = PrecomputedChunksInfo.load(path=path, filesystem=filesystem)
            self.base_url = filesystem.geturl(path.parent.as_posix())
            for scale in info.scales:
                self.scale_combo.addItem(scale.key)
            self.scale_combo.setCurrentIndex(0)
            scale_display_infos : List[str] = [json.dumps(scale.to_json_data(), indent=4) for scale in info.scales]
            self.debug_text.setText("\n".join(scale_display_infos))
            self.qbuttons.button(QDialogButtonBox.Ok).setEnabled(True)
        except Exception as e:
            self.qbuttons.button(QDialogButtonBox.Ok).setEnabled(False)
            self.resetVolume()
            qm = QMessageBox(self)
            qm.setWindowTitle("An Error Occured!")
            qm.setText(f"woops: {e}")
            qm.show()
            return



if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    logging.basicConfig(level=logging.INFO)

    pv = PrecomputedVolumeBrowser()
    pv.combo.addItem("test")
    pv.show()
    app.exec_()
    print(pv.result(), pv.selected_url)
