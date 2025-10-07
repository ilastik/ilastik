###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2015, the ilastik developers
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

# Python
from builtins import range
import collections
import os
from typing import TYPE_CHECKING
import numpy
import vigra

import logging

if TYPE_CHECKING:
    from ilastik.applets.labeling.labelingGui import LabelingSlots

logger = logging.getLogger(__name__)

# Qt
from qtpy import uic
from qtpy.QtCore import Qt, QEvent
from qtpy.QtGui import QValidator, QCloseEvent
from qtpy.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QCheckBox,
    QSpinBox,
    QLabel,
    QProgressDialog,
    QApplication,
)

# lazyflow
import lazyflow
from lazyflow.utility import chunked_bincount
from lazyflow.roi import roiToSlice, roiFromShape
from lazyflow.operators.ioOperators import OpInputDataReader
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.operators.valueProviders import OpMetadataInjector

# ilastik
from ilastik.widgets.ImageFileDialog import ImageFileDialog


def import_labeling_layer(labelingSlots: "LabelingSlots", parent_widget=None):
    """
    Prompt the user for layer import settings, and perform the layer import.
    """
    writeSeeds = labelingSlots.labelInput
    assert isinstance(writeSeeds, lazyflow.graph.Slot), "slot is of type %r" % (type(writeSeeds))
    opLabels = writeSeeds.operator
    assert isinstance(opLabels, lazyflow.graph.Operator), "slot's operator is of type %r" % (type(opLabels))

    fileNames = ImageFileDialog(
        parent_widget, preferences_group="labeling", preferences_setting="recently imported"
    ).getSelectedPaths()
    fileNames = list(map(str, fileNames))

    if not fileNames:
        return

    try:
        # Initialize operators
        opImport = OpInputDataReader(parent=opLabels.parent)
        opCache = OpBlockedArrayCache(parent=opLabels.parent)
        opMetadataInjector = OpMetadataInjector(parent=opLabels.parent)
        opReorderAxes = OpReorderAxes(parent=opLabels.parent)

        # Set up the pipeline as follows:
        #
        #   opImport --> (opCache) --> opMetadataInjector --------> opReorderAxes --(inject via setInSlot)--> labelInput
        #                             /                            /
        #     User-specified axisorder    labelInput.meta.axistags
        opImport.FilePath.setValue(fileNames[0] if len(fileNames) == 1 else os.path.pathsep.join(fileNames))
        assert opImport.Output.ready()

        maxLabels = len(labelingSlots.labelNames.value)

        # We don't bother with counting the label pixels
        # (and caching the data) if it's big (1 GB)
        if numpy.prod(opImport.Output.meta.shape) > 1e9:
            reading_slot = opImport.Output

            # For huge data, we don't go through and search for the pixel values,
            # because that takes an annoyingly long amount of time.
            # Instead, we make the reasonable assumption that the input labels are already 1,2,3..N
            # and we don't tell the user what the label pixel counts are.
            unique_read_labels = numpy.array(list(range(maxLabels + 1)))
            readLabelCounts = numpy.array([-1] * (maxLabels + 1))
            labelInfo = (maxLabels, (unique_read_labels, readLabelCounts))
        else:
            opCache.Input.connect(opImport.Output)
            opCache.CompressionEnabled.setValue(True)
            assert opCache.Output.ready()
            reading_slot = opCache.Output

            # We'll show a little window with a busy indicator while the data is loading
            busy_dlg = QProgressDialog(parent=parent_widget)
            busy_dlg.setLabelText("Scanning Label Data...")
            busy_dlg.setCancelButton(None)
            busy_dlg.setMinimum(100)
            busy_dlg.setMaximum(100)

            def close_busy_dlg(*args):
                QApplication.postEvent(busy_dlg, QCloseEvent())

            # Load the data from file into our cache
            # When it's done loading, close the progress dialog.
            req = reading_slot[:]
            req.notify_finished(close_busy_dlg)
            req.notify_failed(close_busy_dlg)
            req.submit()
            busy_dlg.exec_()

            readData = req.result

            # Can't use return_counts feature because that requires numpy >= 1.9
            # unique_read_labels, readLabelCounts = numpy.unique(readData, return_counts=True)

            # This does the same as the above, albeit slower, and probably with more ram.
            bincounts = chunked_bincount(readData)
            unique_read_labels = bincounts.nonzero()[0].astype(readData.dtype, copy=False)
            readLabelCounts = bincounts[unique_read_labels]

            labelInfo = (maxLabels, (unique_read_labels, readLabelCounts))
            del readData

        opMetadataInjector.Input.connect(reading_slot)
        metadata = reading_slot.meta.copy()
        opMetadataInjector.Metadata.setValue(metadata)
        opReorderAxes.Input.connect(opMetadataInjector.Output)

        # Transpose the axes for assignment to the labeling operator.
        opReorderAxes.AxisOrder.setValue(writeSeeds.meta.getAxisKeys())

        # Ask the user how to interpret the data.
        settingsDlg = LabelImportOptionsDlg(
            parent_widget, fileNames, opMetadataInjector.Output, labelingSlots.labelInput, labelInfo
        )

        def handle_updated_axes():
            # The user is specifying a new interpretation of the file's axes
            updated_axisorder = str(settingsDlg.axesEdit.text())
            metadata = opMetadataInjector.Metadata.value.copy()
            metadata.axistags = vigra.defaultAxistags(updated_axisorder)
            opMetadataInjector.Metadata.setValue(metadata)

            if opReorderAxes._invalid_axes:
                settingsDlg.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
                # Red background
                settingsDlg.axesEdit.setStyleSheet(
                    "QLineEdit { background: rgb(255, 128, 128); selection-background-color: rgb(128, 128, 255); }"
                )

        settingsDlg.axesEdit.editingFinished.connect(handle_updated_axes)

        # Initialize
        handle_updated_axes()

        dlg_result = settingsDlg.exec_()
        if dlg_result != LabelImportOptionsDlg.Accepted:
            return

        # Get user's chosen label mapping from dlg
        labelMapping = settingsDlg.labelMapping

        # Get user's chosen offsets, ordered by the 'write seeds' slot
        axes_5d = opReorderAxes.Output.meta.getAxisKeys()
        tagged_offsets = collections.OrderedDict(list(zip(axes_5d, [0] * len(axes_5d))))
        tagged_offsets.update(dict(list(zip(opReorderAxes.Output.meta.getAxisKeys(), settingsDlg.imageOffsets))))
        imageOffsets = list(tagged_offsets.values())

        # Optimization if mapping is identity
        if list(labelMapping.keys()) == list(labelMapping.values()):
            labelMapping = None

        # If the data was already cached, this will be fast.
        label_data = opReorderAxes.Output[:].wait()

        # Map input labels to output labels
        if labelMapping:
            # There are other ways to do a relabeling (e.g skimage.segmentation.relabel_sequential)
            # But this supports potentially huge values of unique_read_labels (in the billions),
            # without needing GB of RAM.
            mapping_indexes = numpy.searchsorted(unique_read_labels, label_data)
            new_labels = numpy.array([labelMapping[x] for x in unique_read_labels])
            label_data[:] = new_labels[mapping_indexes]

        label_roi = numpy.array(roiFromShape(opReorderAxes.Output.meta.shape))
        label_roi += imageOffsets
        label_slice = roiToSlice(*label_roi)
        writeSeeds[label_slice] = label_data

    finally:
        opReorderAxes.cleanUp()
        opMetadataInjector.cleanUp()
        opCache.cleanUp()
        opImport.cleanUp()


# **************************************************************************
# LabelImportOptionsDlg
# **************************************************************************
class LabelImportOptionsDlg(QDialog):
    def __init__(self, parent, srcInputFiles, dataInputSlot, writeSeedsSlot, labelInfo):
        """
        Constructor.

        :param parent: The parent widget
        :param srcInputFiles: A list of source file names.
        :param dataInputSlot: Slot with imported data
        :param writeSeedsSlot: Slot for writing data into
        :param labelInfo: information about (max_labels, (read_labels, read_label_counts))
        """
        super(LabelImportOptionsDlg, self).__init__(parent)

        localDir = os.path.split(__file__)[0]
        uic.loadUi(os.path.join(localDir, "dataImportOptionsDlg.ui"), self)

        # TODO:
        self._dataInputSlot = dataInputSlot
        self._srcInputFiles = srcInputFiles
        self._writeSeedsSlot = writeSeedsSlot
        self._labelInfo = labelInfo

        self._insert_position_boxes = collections.OrderedDict()
        self._insert_mapping_boxes = collections.OrderedDict()

        write_seeds_tagged_shape = writeSeedsSlot.meta.getTaggedShape()
        label_data_tagged_shape = dataInputSlot.meta.getTaggedShape()

        axisRanges = ()
        for k in list(write_seeds_tagged_shape.keys()):
            try:
                axisRanges += (write_seeds_tagged_shape[k] - label_data_tagged_shape[k],)
            except KeyError:
                axisRanges += (0,)

        self.imageOffsets = LabelImportOptionsDlg._defaultImageOffsets(axisRanges, srcInputFiles, dataInputSlot)
        self.labelMapping = LabelImportOptionsDlg._defaultLabelMapping(labelInfo)

        # Init child widgets
        self._initAxesEdit()
        self._initMetaInfoWidgets()
        self._initInsertPositionMappingWidgets()
        self._initWarningLabel()

        # See self.eventFilter()
        self.installEventFilter(self)

        self._dataInputSlot.notifyMetaChanged(self._initInsertPositionMappingWidgets)
        self._dataInputSlot.notifyMetaChanged(self._initWarningLabel)

    def closeEvent(self, e):
        # Clean-up
        self._dataInputSlot.unregisterMetaChanged(self._initInsertPositionMappingWidgets)
        self._dataInputSlot.unregisterMetaChanged(self._initWarningLabel)
        self.inputMetaInfoWidget.initSlot(None)
        self.labelMetaInfoWidget.initSlot(None)

    @staticmethod
    def _defaultImageOffsets(axisRanges, srcInputFiles, dataInputSlot):
        img_offset = [0] * len(axisRanges)

        # Note: Convenience setting of starting 'z' offset; assumes that filenames are
        # numbered from 0, and they contain only a single number representing their index
        inputAxes = dataInputSlot.meta.getAxisKeys()
        if srcInputFiles is not None and "z" in inputAxes:
            z_idx = inputAxes.index("z")
            filename_digits = "".join(x for x in filter(str.isdigit, os.path.basename(srcInputFiles[0])))
            idx = int(filename_digits) if filename_digits else 0
            img_offset[z_idx] = max(0, min(idx, axisRanges[z_idx]))

        return img_offset

    @staticmethod
    def _defaultLabelMapping(labelInfo):
        max_labels, read_labels_info = labelInfo
        labels, _label_counts = read_labels_info
        label_idx = max_labels

        if 0 not in labels:
            labels = [0] + list(labels)

        label_mapping = collections.defaultdict(int, list(zip(labels, list(range(max_labels + 1)))))
        return label_mapping

    def eventFilter(self, watched, event):
        # Ignore 'enter' keypress events, since the user may just be entering settings.
        # The user must manually click the 'OK' button to close the dialog.
        if (
            watched == self
            and event.type() == QEvent.KeyPress
            and (event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return)
        ):
            return True
        return False

    def _initAxesEdit(self):
        expected_length = len(self._dataInputSlot.meta.getAxisKeys())

        self.axesEdit.setText("".join(self._dataInputSlot.meta.getAxisKeys()))
        self.axesEdit.setValidator(self._QAxesValidator(expected_length, self))

        self.axesEdit.textChanged.connect(self._handleAxesEditChanged)

    def _handleAxesEditChanged(self):
        state, _, _ = self.axesEdit.validator().validate(self.axesEdit.text(), 0)
        self.labelMetaInfoWidget.setEnabled(state == QValidator.Acceptable)
        self.positionWidget.setEnabled(state == QValidator.Acceptable)
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(state == QValidator.Acceptable)

        if state == QValidator.Acceptable:
            # White background
            self.axesEdit.setStyleSheet(
                "QLineEdit { background: rgb(255, 255, 255); selection-background-color: rgb(128, 128, 128); }"
            )
        elif state == QValidator.Intermediate:
            # Yellow background
            self.axesEdit.setStyleSheet(
                "QLineEdit { background: rgb(255, 255, 0); selection-background-color: rgb(128, 128, 128); }"
            )
        else:
            # Red background
            self.axesEdit.setStyleSheet(
                "QLineEdit { background: rgb(255, 128, 128); selection-background-color: rgb(128, 128, 255); }"
            )

    class _QAxesValidator(QValidator):
        def __init__(self, expected_length, parent=None):
            super(LabelImportOptionsDlg._QAxesValidator, self).__init__(parent)
            self.exepected_length = expected_length

        def validate(self, text, pos):
            text = str(text)

            # Remove repeats
            seen = set()
            uniqued_text = "".join([x for x in text if not (x in seen or seen.add(x))])
            if uniqued_text != text:
                return QValidator.Invalid, min(pos, len(uniqued_text))

            # Only valid axis keys allowed
            filtered_keys = [k for k in text if k in "txyzc"]
            filtered_text = "".join(filtered_keys)
            if text != filtered_text:
                return QValidator.Invalid, text, min(pos, len(filtered_text))

            # Must not be longer than the dimensions in the image
            if len(text) > self.exepected_length:
                return QValidator.Invalid, text, pos

            # Not ready until all axes specified
            if len(text) < self.exepected_length:
                return QValidator.Intermediate, text, pos

            # No problems.
            return QValidator.Acceptable, text, pos

    # **************************************************************************
    # Input/Output Meta-info (display only)
    # **************************************************************************
    def _initMetaInfoWidgets(self, *args):
        ## Input/output meta-info display widgets
        dataInputSlot = self._dataInputSlot
        writeSeedsSlot = self._writeSeedsSlot

        self.inputMetaInfoWidget.initSlot(dataInputSlot)
        self.labelMetaInfoWidget.initSlot(writeSeedsSlot)

        self._initSourceFilesList()

    def _initSourceFilesList(self):
        for f in map(os.path.basename, self._srcInputFiles):
            self.inputFilesComboBox.addItem(f)

    # **************************************************************************
    # Insertion Position / Mapping
    # **************************************************************************
    def _initInsertPositionMappingWidgets(self, *args):
        state, _, _ = self.axesEdit.validator().validate(self.axesEdit.text(), 0)
        self.positionWidget.setEnabled(state == QValidator.Acceptable)
        if state != QValidator.Acceptable:
            return

        if not self._dataInputSlot.ready():
            return

        write_seeds_tagged_shape = self._writeSeedsSlot.meta.getTaggedShape()
        label_data_tagged_shape = self._dataInputSlot.meta.getTaggedShape()
        axisRanges = ()
        for k in list(write_seeds_tagged_shape.keys()):
            try:
                axisRanges += (write_seeds_tagged_shape[k] - label_data_tagged_shape[k],)
            except KeyError:
                axisRanges += (write_seeds_tagged_shape[k],)

        # Handle the 'c' axis separately
        inputAxes = self._writeSeedsSlot.meta.getAxisKeys()
        try:
            c_idx = inputAxes.index("c")
        except ValueError:
            inputAxes_noC = inputAxes
            maxValues_noC = axisRanges
        else:
            inputAxes_noC = inputAxes[:c_idx] + inputAxes[c_idx + 1 :]  # del(list(inputAxes)[c_idx])
            maxValues_noC = axisRanges[:c_idx] + axisRanges[c_idx + 1 :]  # del(list(maxValues)[c_idx])

        self._initInsertPositionTableWithExtents(inputAxes_noC, maxValues_noC)
        self._initLabelMappingTableWithExtents()

        if (numpy.asarray(axisRanges) < 0).any():
            self.positionWidget.setEnabled(False)

        # The OK button should have the same status as the positionWidget
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(self.positionWidget.isEnabled())

    def _initInsertPositionTableWithExtents(self, axes, mx):
        positionTbl = self.positionWidget

        tblHeaders = ["insert at", "max"]

        positionTbl.setColumnCount(len(tblHeaders))
        positionTbl.setHorizontalHeaderLabels(tblHeaders)
        positionTbl.resizeColumnsToContents()

        tagged_insert = collections.OrderedDict(list(zip(axes, self.imageOffsets)))
        tagged_max = collections.OrderedDict(list(zip(axes, mx)))
        self._tagged_insert = tagged_insert

        positionTbl.setRowCount(len(tagged_insert))
        positionTbl.setVerticalHeaderLabels(list(tagged_insert.keys()))

        self._insert_position_boxes.clear()

        for row, (axis_key, extent) in enumerate(tagged_max.items()):
            # Init min/max spinboxes
            default_insert = tagged_insert[axis_key] or 0
            default_max = tagged_max[axis_key] or extent

            insertBox = QSpinBox(self)
            maxBox = QLabel(str(default_max), self)

            insertBox.setValue(0)
            insertBox.setMinimum(0)
            insertBox.setMaximum(extent)
            insertBox.setEnabled(tagged_insert[axis_key] is not None)
            if insertBox.isEnabled():
                insertBox.setValue(default_insert)

            # TODO: maxBox shouldn't be in tab list (but it still is)
            maxBox.setTextInteractionFlags(Qt.NoTextInteraction)
            maxBox.setFocusPolicy(Qt.NoFocus)
            maxBox.setEnabled(False)

            insertBox.valueChanged.connect(self._updatePosition)

            positionTbl.setCellWidget(row, 0, insertBox)
            positionTbl.setCellWidget(row, 1, maxBox)

            self._insert_position_boxes[axis_key] = (insertBox, maxBox)

        positionTbl.resizeColumnsToContents()

    def _initLabelMappingTableWithExtents(self):
        mappingTbl = self.mappingWidget
        max_labels, read_labels_info = self._labelInfo
        labels, label_counts = read_labels_info
        label_mapping = self.labelMapping

        mappings = list(zip(labels, [label_mapping[i] for i in labels], label_counts))

        tblHeaders = ["map", "to", "px count"]
        mappingTbl.setColumnCount(len(tblHeaders))
        mappingTbl.setHorizontalHeaderLabels(tblHeaders)
        mappingTbl.resizeColumnsToContents()

        mappingTbl.setRowCount(len(labels))
        mappingTbl.setVerticalHeaderLabels([str(x) for x in labels])

        self._insert_mapping_boxes.clear()

        for row, (label_from, label_to, px_cnt) in enumerate(mappings):
            enabledBox = QCheckBox(self)
            mapToBox = QSpinBox(self)
            pxCountBox = QLabel(str(px_cnt), self)

            enabledBox.setChecked(label_to > 0)

            mapToBox.setMinimum(1 if label_to else 0)
            mapToBox.setMaximum(max_labels if label_to else 0)
            mapToBox.setValue(label_to)
            mapToBox.setEnabled(label_to > 0)

            enabledBox.stateChanged.connect(self._updateMappingEnabled)
            mapToBox.valueChanged.connect(self._updateMapping)

            # TODO: pxCountBox shouldn't be in tab list (but it still is)
            pxCountBox.setTextInteractionFlags(Qt.NoTextInteraction)
            pxCountBox.setFocusPolicy(Qt.NoFocus)
            pxCountBox.setEnabled(False)

            mappingTbl.setCellWidget(row, 0, enabledBox)
            mappingTbl.setCellWidget(row, 1, mapToBox)
            mappingTbl.setCellWidget(row, 2, pxCountBox)

            self._insert_mapping_boxes[label_from] = (enabledBox, mapToBox)

        mappingTbl.resizeColumnsToContents()

    def _initWarningLabel(self, *args):
        self.warningLabel.setText(
            '<html><head/><body><p><span style=" color:#ff0000;">'
            "Warning: Imported X/Y dimensions do not match your original dataset."
            "</span></p></body></html>"
        )

        if not self._dataInputSlot.ready():
            return
        tagged_import_dimensions = self._dataInputSlot.meta.getTaggedShape()
        tagged_destination_dimensions = self._writeSeedsSlot.meta.getTaggedShape()
        show_warning = (
            tagged_import_dimensions["x"] != tagged_destination_dimensions["x"]
            or tagged_import_dimensions["y"] != tagged_destination_dimensions["y"]
        )
        self.warningLabel.setVisible(show_warning)

    # **************************************************************************
    # Update Position / Mapping
    # **************************************************************************
    def _updatePosition(self):
        writeAxes = self._writeSeedsSlot.meta.getAxisKeys()

        for k, v in list(self._insert_position_boxes.items()):
            insertBox, _ = v
            self.imageOffsets[writeAxes.index(k)] = insertBox.value()

    def _updateMappingEnabled(self):
        max_labels, _ = self._labelInfo

        for k, v in list(self._insert_mapping_boxes.items()):
            enabledBox, mapToBox = v
            enabled = enabledBox.isChecked()
            if enabled:
                label_to = mapToBox.value()
                label_to = min(max(1, k if not label_to else label_to), max_labels)
            else:
                label_to = 0

            self.labelMapping[k] = label_to

            mapToBox.setMinimum(1 if label_to else 0)
            mapToBox.setMaximum(max_labels if label_to else 0)
            mapToBox.setValue(label_to)
            mapToBox.setEnabled(label_to > 0)

        enabledBoxes, _ = list(zip(*list(self._insert_mapping_boxes.values())))
        enableOk = any(map(QCheckBox.isChecked, enabledBoxes))

        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enableOk)

    def _updateMapping(self):
        for k, v in list(self._insert_mapping_boxes.items()):
            _, mapToBox = v
            self.labelMapping[k] = mapToBox.value()
