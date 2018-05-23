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
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
)

from PyQt5.QtCore import Qt

import json

from lazyflow.utility.io_util.RESTfulPrecomputedChunkedVolume import RESTfulPrecomputedChunkedVolume


import logging


logger = logging.getLogger(__name__)


class PrecomputedVolumeBrowser(QDialog):
    def __init__(self, history=None, parent=None):
        super().__init__(parent)
        self._history = history or []
        self.selected_url = None
        self.viewer_state = None
        self.rv = None
        self.selected_scale = None

        self.setup_ui()

    def setup_ui(self):
        self.setMinimumSize(800, 200)
        self.setWindowTitle('Precomputed Volume Selection Dialog')
        main_layout = QVBoxLayout()

        description = QLabel(self)
        description.setText(
            'enter base URL of volume starting with "precomputed://http..."'
            'hit the "check URL" button to validate the entered address.')
        main_layout.addWidget(description)

        self.combo = QComboBox(self)
        self.combo.setEditable(True)
        self.combo.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.combo.addItem("")
        for item in self._history:
            self.combo.addItem(item)

        self.combo.editTextChanged.connect(self.check_url)

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

        # add the subvolume selection stuff (hidden)
        self.subvolume_frame = QFrame()
        subvolume_layout = QHBoxLayout()
        subvolume_label = QLabel(parent=self)
        subvolume_label.setText("Select volume: ")
        self.combo_subvolume = QComboBox(self)
        self.combo_subvolume.setEditable(False)
        subvolume_layout.addWidget(subvolume_label)
        subvolume_layout.addWidget(self.combo_subvolume)
        subvolume_layout.setAlignment(Qt.AlignLeft)

        self.subvolume_frame.setLayout(subvolume_layout)
        self.subvolume_frame.hide()

        main_layout.addWidget(self.subvolume_frame)

        subvolume_scale_layout = QHBoxLayout()
        subvolume_scale_label = QLabel(parent=self)
        subvolume_scale_label.setText("Select scale: ")
        self.combo_subvolume_scale = QComboBox(self)
        self.combo_subvolume_scale.setEditable(False)
        subvolume_scale_layout.addWidget(subvolume_scale_label)
        subvolume_scale_layout.addWidget(self.combo_subvolume_scale)
        subvolume_scale_layout.setAlignment(Qt.AlignLeft)
        self.combo_subvolume_scale.setEnabled(False)
        self.combo_subvolume_scale.currentIndexChanged.connect(self.update_volume_info)

        main_layout.addLayout(subvolume_scale_layout)

        # add some debug stuff
        debug_label = QLabel(self)
        debug_label.setText('debug: ')
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

    def clearall(self):
        self.selected_url = None
        self.viewer_state = None
        self.rv = None
        self.selected_scale = None

        self.combo_subvolume.clear()
        self.combo_subvolume_scale.clear()

        self.subvolume_frame.hide()
        self.combo_subvolume_scale.setEnabled(False)
        self.debug_text.setText("")

    def update_subvolume_list(self):
        self.combo_subvolume.clear()

        if self.viewer_state is None:
            return

        if 'layers' not in self.viewer_state:
            return

        for layer in self.viewer_state['layers']:
            self.combo_subvolume.addItem(layer)

    def check_url(self, event):
        current_combo_val = self.combo.currentText()
        self.clearall()
        try:
            url_components = RESTfulPrecomputedChunkedVolume.check_url(current_combo_val)
        except json.JSONDecodeError:
            # do what is necessary,

            return

        if isinstance(url_components, str):
            self.selected_url = url_components

        if isinstance(url_components, dict):
            self.viewer_state = url_components
            self.update_subvolume_list()
            self.subvolume_frame.show()

    def handle_chk_button_clicked(self, event):
        if self.viewer_state is None:
            self.selected_url = self.combo.currentText()
            logger.debug(f"selected url: {self.selected_url}")

        else:
            selected_dataset = self.combo_subvolume.currentText()
            self.selected_url = self.viewer_state['layers'][selected_dataset]['source']
            logger.debug(f"selected url: {self.selected_url}")

        self.init_volume_info()
        self.update_scales()
        self.update_volume_info()
        self.qbuttons.button(QDialogButtonBox.Ok).setEnabled(True)

    def init_volume_info(self):
        url = self.selected_url.lstrip('precomputed://')
        try:
            self.rv = RESTfulPrecomputedChunkedVolume(volume_url=url)
        except Exception as e:
            # :<
            self.qbuttons.button(QDialogButtonBox.Ok).setEnabled(False)
            self.debug_text.setText("")
            qm = QMessageBox(self)
            qm.setWindowTitle('An Error Occured!')
            qm.setText(f"woops: {e}")
            qm.show()
            return

    def update_volume_info(self, event=None):
        if self.rv is None:
            return
        self.selected_scale = self.combo_subvolume_scale.currentText()
        if self.selected_scale in self.rv.available_scales:
            self.rv._use_scale = self.selected_scale

        self.debug_text.setText(
            f"volume encoding: {self.rv.get_encoding()}\n"
            f"available scales: {self.rv.available_scales}\n"
            f"using scale: {self.selected_scale}\n"
            f"data shape: {self.rv.get_shape()}\n"
        )

    def update_scales(self):
        combo = self.combo_subvolume_scale
        combo.clear()
        for scale in self.rv.available_scales:
            combo.addItem(scale)

        combo.setEnabled(True)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])

    logging.basicConfig(level=logging.INFO)

    pv = PrecomputedVolumeBrowser()
    test_string = (
        "https://bigbrain.humanbrainproject.org/"
        "#!{'layers':{"
        "'%20grey%20value:%20':{"
        "'type':'image'_"
        "'source':'precomputed://https://neuroglancer.humanbrainproject.org/precomputed/BigBrainRelease.2015/8bit'_"
        "'transform':[[1_0_0_-70677184]_[0_1_0_-70010000]_[0_0_1_-58788284]_[0_0_0_1]]}_"
        "'%20tissue%20type:%20':{"
        "'type':'segmentation'_"
        "'source':'precomputed://https://neuroglancer.humanbrainproject.org/precomputed/BigBrainRelease.2015/classif'_"
        "'selectedAlpha':0_'transform':[[1_0_0_-70766600]_[0_1_0_-73010000]_[0_0_1_-58877700]_[0_0_0_1]]}}_"
        "'navigation':{"
        "'pose':{"
        "'position':{"
        "'voxelSize':[21166.666015625_20000_21166.666015625]_"
        "'voxelCoordinates':[-21.8844051361084_16.288618087768555_28.418994903564453]}}_"
        "'zoomFactor':28070.863049307816}_"
        "'perspectiveOrientation':[0.3140767216682434_-0.7418519854545593_0.4988985061645508_-0.3195493221282959]_"
        "'perspectiveZoom':1922235.5293810747}"
    )

    pv.combo.addItem("test")
    pv.combo.addItem(test_string)
    pv.show()
    app.exec_()
    print(pv.result(), pv.selected_url, pv.selected_scale)
