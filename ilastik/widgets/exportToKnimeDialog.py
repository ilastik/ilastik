from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os.path
import re

class ExportToKnimeDialog(QDialog):

    REQ_MSG = " (REQUIRED)"
    RAW_LAYER_SIZE_LIMIT = 100000
    ALLOWED_EXTENSIONS = [".hdf5", ".hd5", ".h5", ".csv"]
    RE_EXT = r"\.[a-zA-Z0-9]+$"
    RE_FNAME = r"/'"

    def __init__(self, layerstack, dimensions, feature_table, req_features=None, parent=None):
        super(ExportToKnimeDialog, self).__init__(parent)
        ui_class, widget_class = uic.loadUiType(os.path.split(__file__)[0] + "/exportToKnimeDialog.ui")
        self.ui = ui_class()
        self.ui.setupUi(self)

        self.raw_size = dimensions[0] * dimensions[1] * dimensions[2]

        self._setup_stack(layerstack)

        if req_features is None:
            req_features = []
        req_features.extend(["Coord<Minimum>", "Coord<Maximum>"])
        self._setup_features(feature_table, req_features)
        self.ui.featureView.setHeaderLabels(("Select Features",))
        self.ui.exportPath.setText(os.path.expanduser("~") + "/a.h5")
        self.ui.featureView.expandAll()

    def _setup_features(self, features, reqs, max_depth=2, parent=None):
        if max_depth == 0:
            return
        if parent is None:
            parent = self.ui.featureView
        for entry, child in features.iteritems():
            item = QTreeWidgetItem(parent)
            item.setText(0, entry)
            self._setup_features(child, reqs, max_depth-1, item)
            if child == {} or max_depth == 1:  # no children
                state = Qt.Unchecked
                if entry in reqs:
                    state = Qt.Checked
                    item.setDisabled(True)
                    item.setText(0, item.text(0) + ExportToKnimeDialog.REQ_MSG)
                item.setCheckState(0, state)

    def _setup_stack(self, layerstack):
        reqs = [
            layerstack.findMatchingIndex(lambda x: x.name == "Raw data"),
            layerstack.findMatchingIndex(lambda x: x.name == "Labels")
        ]
        for i in xrange(len(layerstack)):
            layer = layerstack[i]
            item = QListWidgetItem(self.ui.objLayerView)
            item.setText(layer.name)
            state = Qt.Unchecked
            if i in reqs:
                state = Qt.Checked
                flags = item.flags() & ~Qt.ItemIsEnabled
                item.setFlags(flags)
                item.setText(item.text() + ExportToKnimeDialog.REQ_MSG)
            item.setCheckState(state)

    # slot is called from button.click
    def select_all_features(self):
        flags = QTreeWidgetItemIterator.Enabled | \
            QTreeWidgetItemIterator.NoChildren | \
            QTreeWidgetItemIterator.NotChecked
        it = QTreeWidgetItemIterator(self.ui.featureView, flags)
        while it.value():
            it.value().setCheckState(0, Qt.Checked)
            it += 1

    # slot is called from button.click
    def select_no_features(self):
        flags = QTreeWidgetItemIterator.Enabled | \
            QTreeWidgetItemIterator.NoChildren | \
            QTreeWidgetItemIterator.Checked
        it = QTreeWidgetItemIterator(self.ui.featureView, flags)
        while it.value():
            it.value().setCheckState(0, Qt.Unchecked)
            it += 1

    # slot is called from buttonBox.accept
    # noinspection PyArgumentList
    def validate_before_exit(self):
        if self.ui.exportPath.text() == "":
            title = "Warning"
            text = "Please enter a file name!"
            QMessageBox.information(self.parent(), title, text)
            self.ui.toolBox.setCurrentIndex(0)
            return
        else:
            ext = re.findall(ExportToKnimeDialog.RE_EXT, self.ui.exportPath.text())
            if not ext or ext[0] not in ExportToKnimeDialog.ALLOWED_EXTENSIONS:
                title = "Warning"
                text = "No file extension or invalid file extension ( %s )\nAllowed: *.h[d[f]]5 and *.csv"
                if not ext:
                    ext = "<none>"
                else:
                    ext = ext[0]
                text %= ext
                QMessageBox.information(self.parent(), title, text)
                return

        if False and len(list(self.checked_layers())) == 0:  # TODO: enable again?
            title = "Warning"
            text = "Select some layers to export!"
            QMessageBox.warning(self.parent(), title, text)
            self.ui.toolBox.setCurrentIndex(1)  # Layers Page
            return

        self.accept()

    # slot is called from button.click
    def choose_path(self):
        extensions = "HDF 5 (*.h5 *.hd5 *.hdf5);;CSV (*.csv);;Both (*.h5 *.hd5 *.hdf5 *.csv);;Any (*.*)"
        path = QFileDialog.getSaveFileName(self.parent(), "Save File", self.ui.exportPath.text(), extensions)
        if path != "":
            match = re.findall("\..+", path)
            if not match:
                path += ".h5"
            self.ui.exportPath.setText(path)

    # slot is called from checkBox.change
    def include_raw_changed(self, state):
        if state == Qt.Checked\
                and self.raw_size >= ExportToKnimeDialog.RAW_LAYER_SIZE_LIMIT:
            title = "Warning"
            text = "Raw layer is very large (%d%s). Do you really want to include it?"
            text %= (self.raw_size / 3, " Pixel")
            buttons = QMessageBox.Yes | QMessageBox.No
            button = QMessageBox.question(self.parent(), title, text, buttons)
            if button == QMessageBox.No:
                self.ui.includeRaw.setCheckState(Qt.Unchecked)

    # iterator for all features to export
    def checked_features(self):
        flags = QTreeWidgetItemIterator.Checked
        it = QTreeWidgetItemIterator(self.ui.featureView, flags)
        while it.value():
            yield str(it.value().text(0))
            it += 1

    # iterator for all layers to export
    def checked_layers(self):
        for i in xrange(self.ui.objLayerView.count()):
            item = self.ui.objLayerView.item(i)
            if item.checkState() == Qt.Checked:
                yield str(item.text())

    # should the raw layer be exported
    def include_raw_layer(self):
        return self.ui.includeRaw.checkState()

    def advanced_settings(self):
        return  {
            "normalize": self.ui.normalizeLabeling.checkState() == Qt.Checked,
            "margin": self.ui.addMargin.value()
        }

    # the file format the user wants to export
    # hd5 or csv
    def file_format(self):
        return re.findall(ExportToKnimeDialog.RE_EXT, self.ui.exportPath.text())[0]

    # the file path
    def file_path(self):
        return self.ui.exportPath.text()