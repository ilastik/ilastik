from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os.path
import re


class ExportToKnimeDialog(QDialog):

    REQ_MSG = " (REQUIRED)"
    RAW_LAYER_SIZE_LIMIT = 0
    ALLOWED_EXTENSIONS = ["hd5", "csv"]
    RE_EXT = r"\.[a-zA-Z0-9]+$"

    def __init__(self, layerstack, raw_index, feature_table, req_features=None, image_per_object=True,
                 image_per_time=True, parent=None):
        super(ExportToKnimeDialog, self).__init__(parent)
        ui_class, widget_class = uic.loadUiType(os.path.split(__file__)[0] + "/exportToKnimeDialog.ui")
        self.ui = ui_class()
        self.ui.setupUi(self)

        self.raw_index = raw_index
        self._setup_stack(layerstack)

        raw = layerstack[raw_index]
        print "Channels: ", raw.numberOfChannels
        print "DataSource: ", raw.datasources
        print dir(raw.datasources)

        if req_features is None:
            req_features = []
        req_features.extend(["Coord<Minimum>", "Coord<Maximum>"])
        self._setup_features(feature_table, req_features)
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
                item.setCheckState(0, state)

    def _setup_stack(self, layerstack):
        for i in xrange(len(layerstack)):
            if i != self.raw_index:
                layer = layerstack[i]
                item = QListWidgetItem(self.ui.objLayerView)
                item.setText(layer.name)
                item.setCheckState(Qt.Unchecked)

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
            if ext == [] or ext[0] not in ExportToKnimeDialog.ALLOWED_EXTENSIONS:
                title = "Warning"
                text = "No file extension or invalid file extension\nAllowed: *.hd5 and *.csv"
                QMessageBox.information(self.parent(), title, text)

        if len(list(self.checked_layers())) == 0:
            title = "Warning"
            text = "Select some layers to export!"
            QMessageBox.warning(self.parent(), title, text)
            self.ui.toolBox.setCurrentIndex(1)  # Layers Page
            return
        if self.ui.includeRaw.checkState == Qt.Checked and False:  # FIXME: change to "if size to large"
            title = "Warning"
            text = "Raw layer is very large (%d%s). Do you really want to export it?"
            buttons = QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            button = QMessageBox.question(self.parent(), title, text, buttons)
            if button == QMessageBox.No:
                self.ui.includeRaw.checkState = Qt.Unchecked
            elif button == QMessageBox.Cancel:
                return

        self.accept()

    # slot is called from button.click
    def choose_path(self):
        extensions = "HDF 5 (*.hd5);;Excel (*.csv);;Both (*.hd5 *.csv);;Any (*.*)"
        path = QFileDialog.getSaveFileName(self.parent(), "Save File", "", extensions)
        if path != "":
            self.ui.exportPath.setText(path)

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

    # the file format the user wants to export
    # hd5 or csv
    def file_format(self):
        return re.findall(ExportToKnimeDialog.RE_EXT, self.ui.exportPath.text())[0]