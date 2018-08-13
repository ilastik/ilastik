###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2016, the ilastik developers
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
#                  http://ilastik.org/license.html
###############################################################################
from __future__ import division
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import os.path
import re
from operator import mul
from functools import reduce

FILE_TYPES = ["h5", "csv"]
REQ_MSG = " (REQUIRED)"
RAW_LAYER_SIZE_LIMIT = 1000000
ALLOWED_EXTENSIONS = ["hdf5", "hd5", "h5", "csv"]
DEFAULT_REQUIRED_FEATURES = ["Count", "Coord<Minimum>", "Coord<Maximum>", "RegionCenter", ]
DIALOG_FILTERS = {
    "h5": "HDF 5 (*.h5 *.hd5 *.hdf5)",
    "csv": "CSV (*.csv)",
    "any": "Any (*.*)",
}


class ExportObjectInfoDialog(QDialog):
    """
    This is a QDialog that asks for the settings for
    the exportObjectInfo operator
    :param dimensions: the dimensions of the raw image [t, x, y, z, c]
    :type dimensions: list
    :param feature_table: nested dict of the computed feature names
    :type feature_table: dict
    :param req_features: list of the features that must be exported. None for default
    :type req_features: list or None
    :param parent: the parent QWidget for this dialog
    :type parent: QWidget or None
    :param initial_settings: The initial_settings to use as default
    :type initial_settings: dict, or None
    """
    def __init__(
            self,
            dimensions,
            feature_table,
            req_features=None,
            selected_features=None,
            title=None,
            parent=None,
            initial_settings=None):
        super(ExportObjectInfoDialog, self).__init__(parent)

        ui_class, widget_class = uic.loadUiType(os.path.split(__file__)[0] + "/exportObjectInfoDialog.ui")
        self.ui = ui_class()
        self.ui.setupUi(self)

        self.setWindowTitle(title)

        self.raw_size = reduce(mul, dimensions, 1)

        if req_features is None:
            req_features = []
        req_features.extend(DEFAULT_REQUIRED_FEATURES)
        
        if selected_features is None:
            selected_features = []

        self._setup_features(feature_table, req_features, selected_features)
        self._setup_settings(initial_settings or {})
        self.ui.featureView.setHeaderLabels(("Select Features",))
        self.ui.featureView.expandAll()
            
        self.ui.exportPath.dropEvent = self._drop_event
        # self.ui.forceUniqueIds.setEnabled(dimensions[0] > 1)
        self.ui.compressFrame.setVisible(False)

    def _get_file_type_index_from_filename(self, filename):
        extension = filename.rsplit(".", 1)[1].lower()
        idx = ALLOWED_EXTENSIONS.index(extension)
        if idx < 3:
            return 0 # file type "h5"
        return 1 # file type "csv"

    def checked_features(self):
        """
        :returns: iterator for all features (names) to export
        :rtype: generator object
        """
        flags = QTreeWidgetItemIterator.Checked
        it = QTreeWidgetItemIterator(self.ui.featureView, flags)
        while it.value():
            feature_id = it.value().feature_id
            yield feature_id
            it += 1

    def settings(self):
        """
        file type: the export format (h5 or csv)
        file path: location of the exported file
        compression: dict that contains compression information for h5py
        normalize: make the labeling rois binary
        margin: the margin that should be added around the rois
        include raw: if True include the whole raw image instead of separate rois
        :returns: all settings that can be changed inside the dialog
        :rtype: dict
        """
        s = {
            "file type": FILE_TYPES[self.ui.fileFormat.currentIndex()],
            "file path": str(self.ui.exportPath.text()),
            "compression": {}
        }

        if s["file type"] == "h5":
            s.update({
                "normalize": True,  # self.ui.normalizeLabeling.checkState() == Qt.Checked,
                "margin": self.ui.addMargin.value(),
                "compression": self._compression_settings(),
                "include raw": self.ui.includeRaw.checkState() == Qt.Checked,
            })
        return s

    def _drop_event(self, event):
        data = event.mimeData()
        if data.hasText():
            pattern = r"([^/]+)\://(.*)"
            match = re.findall(pattern, data.text())
            if match:
                text = str(match[0][1]).strip()
            else:
                text = data.text()
            self.ui.exportPath.setText(text)

    def _setup_settings(self, initial_settings):
        """Load previously active settinitial_settingsings.

        Args:
            initial_settings (dict): Dictionary with settings values, see
                ExportObjectInfoDialog.settings for structure
        """
        file_type = initial_settings.get('file type', None)
        if file_type is not None:
            assert file_type in ['csv', 'h5']
            index = FILE_TYPES.index(file_type)
            self.ui.fileFormat.setCurrentIndex(index)

        file_path = initial_settings.get('file path', None)
        if file_path is not None and self.is_valid_path(file_path):
            self.ui.exportPath.setText(file_path)
            self.ui.fileFormat.setCurrentIndex(self._get_file_type_index_from_filename(file_path))
        else:
            self.ui.exportPath.setText(os.path.expanduser("~") + "/exported_data.h5")

        if file_type == 'h5':
            # TODO: what about normalize?
            margin = initial_settings.get('margin', None)
            if margin is not None:
                self.ui.addMargin.setValue(margin)
            include_raw = initial_settings.get('include raw', None)
            if include_raw is not None:
                self.ui.includeRaw.setChecked(include_raw)
            # different compression settings are not working and hidden in the
            # UI. We will, however, always set these settings as they come from
            # the config (so in future, it will just work)
            compression_settings = initial_settings.get('compression', None)
            if compression_settings is not None:
                compression_type = compression_settings.get('compression', None)
                if compression_type is not None:
                    index = self.ui.compressionType.findText(compression_type)
                    if index != -1:
                        self.ui.compressionType.setCurrentIndex(index)
                shuffle = compression_settings.get('shuffle', None)
                if shuffle is not None:
                    self.ui.enableShuffling.setChecked(shuffle)
                    if compression_type == 'gzip':
                        compression_rate = compression_settings.get('compression_opts', None)
                        if compression_rate is not None:
                            assert compression_rate >= 1 and compression_rate <= 9
                            self.ui.gzipRate.setValue(compression_rate)
                        else:
                            # set to maximum per default
                            self.ui.gzipRate.setValue(9)

    def _setup_features(self, features, req_features, selected_features, max_depth=2, parent=None):
        if max_depth == 2 and not features:
            item = QTreeWidgetItem(parent)
            item.setText(0, "All Default Features will be exported.")
            self.ui.selectAllFeatures.setEnabled(False)
            self.ui.selectNoFeatures.setEnabled(False)
            return
        if max_depth == 0:
            return
        if parent is None:
            parent = self.ui.featureView
        for entry, child in features.items():
            item = QTreeWidgetItem(parent)
            try:
                #if it's the feature name, show the human version of the text
                item.setText(0, child["displaytext"])
            except KeyError:
                item.setText(0, entry)
            self._setup_features(child, req_features, selected_features, max_depth-1, item)
            if child == {} or max_depth == 1:  # no children
                state = Qt.Unchecked
                if entry in selected_features:
                    state = Qt.Checked
                if entry in req_features:
                    state = Qt.Checked
                    item.setDisabled(True)
                    item.setText(0, "%s%s" % (item.text(0), REQ_MSG))
                item.setCheckState(0, state)
                item.feature_id = entry

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
    def validate_before_exit(self):
        if self.ui.exportPath.text() == "":
            title = "Warning"
            text = "Please enter a file name!"
            # noinspection PyArgumentList
            QMessageBox.information(self.parent(), title, text)
            self.ui.toolBox.setCurrentIndex(0)
            return
        else:
            path = str(self.ui.exportPath.text())
            if not self.is_valid_path(path):
                title = "Warning"
                text = "No file extension or invalid file extension ( %s )\nAllowed: %s"
                match = path.rsplit(".", 1)
                if len(match) == 1:
                    ext = "<none>"
                else:
                    ext = match[1]
                text %= (ext, ", ".join(ALLOWED_EXTENSIONS))
                # noinspection PyArgumentList
                QMessageBox.information(self.parent(), title, text)
                return

        self.accept()

    def is_valid_path(self, path):
        match = path.rsplit(".", 1)
        if len(match) == 1 or match[1] not in ALLOWED_EXTENSIONS:
            return False
        return True

    # slot is called from button.click
    def choose_path(self):
        filters = ";;".join(list(DIALOG_FILTERS.values()))
        current_extension = FILE_TYPES[self.ui.fileFormat.currentIndex()]
        current_filter = DIALOG_FILTERS[current_extension]
        path, _filter = QFileDialog.getSaveFileName(self.parent(), "Save File", self.ui.exportPath.text(), filters,
                                           current_filter)
        path = str(path)
        if path != "":
            match = path.rsplit(".", 1)
            if len(match) == 1:
                path = "%s.%s" % (path, current_extension)
            self.ui.exportPath.setText(path)

    # slot is called from checkBox.change
    def include_raw_changed(self, state):
        if state == Qt.Checked\
                and self.raw_size >= RAW_LAYER_SIZE_LIMIT:
            title = "Warning"
            text = "Raw layer is very large (%d%s). Do you really want to include it?"
            text %= (self.raw_size // 3, " Pixel")
            buttons = QMessageBox.Yes | QMessageBox.No
            button = QMessageBox.question(self.parent(), title, text, buttons)
            if button == QMessageBox.No:
                self.ui.includeRaw.setCheckState(Qt.Unchecked)

    # slot is called from comboBox.change
    def change_compression(self, qstring):
        hidden = str(qstring) != "gzip"
        self.ui.gzipRate.setHidden(hidden)
        self.ui.rateLabel.setHidden(hidden)

    # slot is called from combobox.indexchanged
    def file_format_changed(self, index):
        path = str(self.ui.exportPath.text())
        match = path.rsplit(".", 1)
        path = "%s.%s" % (match[0], FILE_TYPES[index])
        self.ui.exportPath.setText(path)

        for widget in (self.ui.includeRaw, self.ui.marginLabel, self.ui.addMargin):
            widget.setEnabled(FILE_TYPES[index] != "csv")

    # TODO: check whether this is implemented at all
    def _compression_settings(self):
        settings = {}
        if self.ui.enableCompression.checkState() == Qt.Checked:
            settings["compression"] = str(self.ui.compressionType.currentText())
            settings["shuffle"] = str(self.ui.enableShuffling.checkState() == Qt.Checked)
            if settings["compression"] == "gzip":
                settings["compression_opts"] = self.ui.gzipRate.value()
        return settings
