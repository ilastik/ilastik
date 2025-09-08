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
#          http://ilastik.org/license.html
###############################################################################
from contextlib import contextmanager
import logging
from functools import partial
from typing import Dict, List, Tuple

import vigra
from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QPaintEvent, QShowEvent
from qtpy.QtWidgets import QAbstractItemView, QStyledItemDelegate, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from qtpy.QtCore import QTimer

from ilastik.utility.gui import silent_qobject
from lazyflow.request.request import Request, RequestPool
from lazyflow.roi import getIntersectingBlocks, roiToSlice
from lazyflow.slot import OutputSlot
from lazyflow.utility.io_util.write_ome_zarr import SPATIAL_AXES
from lazyflow.utility.timer import timeLogged

from .connectBlockedLabels import Block, Neighbourhood, SpatialAxesKeys, connect_regions, extract_annotations

logger = logging.getLogger(__name__)


class LookupDelegate(QStyledItemDelegate):
    def __init__(self, parent, lookup_func):
        super().__init__(parent)
        self._lookup_fun = lookup_func

    def displayText(self, value, locale):
        return self._lookup_fun(value)


class LabelExplorerWidget(QWidget):
    """
    Widget used with `LabelingGui`: shows table of annotations from the label output slot

    Clicking on an item in the table emits a `positionRequested` event.

    Has 2 modes of operation:
      * if `label_slot.meta.is_blocked_cache` is True it is assumed to be connected to a blocked cache
        (as in Pixel Classification and derived workflows).
        `label_slot.meta.ideal_blockshape` must be set and should correspond to the block size signaled
        through `nonzero_block_slot`.
      * if `label_slot.meta.is_blocked_cache` is not True it indicates a non-blocked cache - as used in
        Carving and Counting. In this case it is assumed that any update will require update of the
        whole label array.

    The ui is lazy. Calculations are only done if this widget is shown. If changes to the
    label slot are detected without the ui being visible, `_table_initialized` is set to
    False and a complete recalculation will happen the next time the widget is shown.
    (This could be in principle optimized by keeping track of the dirty rois.)
    """

    positionRequested = Signal(dict)

    display_text = "Label Explorer"

    def __init__(
        self,
        nonzero_blocks_slot: OutputSlot,
        label_slot: OutputSlot,
        parent=None,
    ):
        super().__init__(parent)
        self._table_initialized: bool = False
        self._shown: bool = False
        self._lookup_table: dict[str, str] = {}
        self._nonzero_blocks_slot = nonzero_blocks_slot
        self._axistags = label_slot.meta.getAxisKeys()
        self._display_axistags = [x for x in self._axistags if x != "c"]
        self._item_flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren
        self._label_slot = label_slot
        self._block_cache: Dict[Tuple[int, ...], Block] = {}
        self._neighbourhood = (
            Neighbourhood.SINGLE if getattr(self._label_slot.meta, "is_blocked_cache", False) else Neighbourhood.NONE
        )

        self._setupUi()

        self.unsubscribe_fns = []
        self.unsubscribe_fns.append(label_slot.notifyDirty(self.update_table))

        def _sync_viewer_position(currentRow, _currentColumn, _previousRow, _previousColumn):
            position = self.tableWidget.item(currentRow, 0).data(Qt.UserRole)
            self.positionRequested.emit(position)

        self.tableWidget.currentCellChanged.connect(_sync_viewer_position)

    def _clear_blocking(self):
        self._block_cache = {}

    def _item_lookup(self, item):
        return self._lookup_table.get(item, "NOT FOUND")

    def paintEvent(self, a0: QPaintEvent) -> None:
        # Hack: Initialize new widget after lane removal
        # need to trigger initialization manually - while the widget is on the
        # not on the screen
        if not self._table_initialized:
            QTimer.singleShot(0, self.sync_state)
        super().paintEvent(a0)

    def _setupUi(self):
        layout = QVBoxLayout()
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(len(self._display_axistags) + 1)
        self.tableWidget.setHorizontalHeaderLabels(self._display_axistags + ["label"])
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.setSortingEnabled(True)
        self.tableWidget.setItemDelegateForColumn(
            len(self._display_axistags), LookupDelegate(self.tableWidget, self._item_lookup)
        )
        layout.addWidget(self.tableWidget)
        self.setLayout(layout)

    def initialize_table(self):
        """
        Do a full recalculation of annotations from the connected label cache slot
        """
        if self._table_initialized:
            return

        self._clear_blocking()

        non_zero_slicings: List[Tuple[slice, ...]] = self._nonzero_blocks_slot.value
        self.populate_table(non_zero_slicings)
        self._table_initialized = True
        for column in range(self.tableWidget.columnCount() - 1):
            self.tableWidget.resizeColumnToContents(column)

    def update_table(self, slot, roi, **kwargs):
        """
        Request updated label blocks and recalculate connected labels

        as reaction to dirty notification from output slot.
        """
        if self._neighbourhood is Neighbourhood.NONE:
            self._clear_blocking()
            non_zero_slicings: List[Tuple[slice, ...]] = self._nonzero_blocks_slot.value
            self.populate_table(non_zero_slicings)
        else:
            blockShape = self._label_slot.meta.ideal_blockshape
            block_starts = getIntersectingBlocks(blockshape=blockShape, roi=(roi.start, roi.stop))
            block_rois = [(bl, bl + blockShape) for bl in block_starts]
            block_slicings = [roiToSlice(*br) for br in block_rois]
            self.populate_table(block_slicings)

    def _update_blocks(self, block_slicings):
        """Request data from label slot and save them in `self._block_cache`"""

        def extract_single(roi):
            labels_data = vigra.taggedView(self._label_slot[roi].wait(), "".join(self._axistags))

            spatial_axes = [SpatialAxesKeys(x) for x in self._axistags if x in SPATIAL_AXES]

            labels_data = labels_data.withAxes("".join(spatial_axes))
            block_regions = extract_annotations(labels_data)

            block = Block(
                axistags="".join(self._axistags), slices=roi, regions=block_regions, neigbourhood=self._neighbourhood
            )

            if block_regions:
                self._block_cache[block.block_start] = block
            else:
                if block.block_start in self._block_cache:
                    del self._block_cache[block.block_start]

        # only go through the overhead of a requestpool if there are many blocks to request
        if len(block_slicings) > 1:
            pool = RequestPool()
            for roi in block_slicings:
                pool.add(Request(partial(extract_single, roi)))

            pool.wait()
            pool.clean()
        elif len(block_slicings) == 1:
            extract_single(block_slicings[0])

    def populate_table(self, block_slicings):
        if not self._shown:
            # No need to update the table if not shown
            # but mark to redo the table again if shown
            self._table_initialized = False
            return

        self._populate_table(block_slicings)

    @timeLogged(logger, logging.INFO, "_populate_table")
    def _populate_table(self, block_slicings):
        self._update_blocks(block_slicings)
        self._regions_dict = connect_regions(self._block_cache)
        self._update_table_data()

    def _update_table_data(self):
        annotation_anchors: List[Tuple[Dict[str, float], int]] = []
        for k, v in self._regions_dict.items():
            if k == v:
                annotation_anchors.append((k.tagged_center, k.label))

        at_non_c = [x for x in self._axistags if x != "c"]

        with silent_qobject(self.tableWidget), self._ensure_no_sort():

            self.tableWidget.setRowCount(len(annotation_anchors))
            for row, (roi, label) in enumerate(annotation_anchors):
                roi_center = roi
                for i, at in enumerate(at_non_c):
                    position_item = QTableWidgetItem()
                    position_item.setFlags(self._item_flags)
                    position_item.setData(Qt.DisplayRole, int(roi_center[at]))
                    position_item.setData(Qt.UserRole, roi_center)
                    self.tableWidget.setItem(row, i, position_item)

                label_item = QTableWidgetItem(str(label))
                label_item.setFlags(self._item_flags)
                self.tableWidget.setItem(row, len(at_non_c), label_item)

    @contextmanager
    def _ensure_no_sort(self):
        self.tableWidget.setSortingEnabled(False)
        try:
            yield
        finally:
            self.tableWidget.setSortingEnabled(True)

    def sync_state(self, _a0=None):
        """Update internal "ready" state on gui events

        This widget is shown in a splitter and we want to know if the widget is currently
        visible or not. If not, we don't need to do any updates.
        """
        shown_before = self._shown
        self._shown = not self.visibleRegion().isEmpty()
        if self._shown and not shown_before:
            self.initialize_table()
        self.tableWidget.viewport().update()

    def showEvent(self, a0: QShowEvent) -> None:
        super().showEvent(a0)
        if not self._table_initialized:
            self.sync_state()

    def cleanup(self):
        for fn in self.unsubscribe_fns:
            fn()
