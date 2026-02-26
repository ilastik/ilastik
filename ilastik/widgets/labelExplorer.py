###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2026, the ilastik developers
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
from abc import ABCMeta
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable

from qtpy.QtCore import Qt, QTimer, Signal
from qtpy.QtGui import QPaintEvent, QShowEvent
from qtpy.QtWidgets import QAbstractItemView, QStyledItemDelegate, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from volumina.utility import qabc
from volumina.utility.qabc import QABCMeta

from ilastik.utility.gui import silent_qobject
from lazyflow.base import Axiskey

logger = logging.getLogger(__name__)


class LookupDelegate(QStyledItemDelegate):
    def __init__(self, parent, lookup_func):
        super().__init__(parent)
        self._lookup_fun = lookup_func

    def displayText(self, value, locale):
        return self._lookup_fun(value)


@dataclass(frozen=True)
class AnnotationAnchor:
    label: int
    position: dict[Axiskey, float]


class LabelExplorerBase(QWidget, metaclass=QABCMeta):
    """
    Widget used with `LabelingGui`: shows table of annotations from the label output slot

    Clicking on an item in the table emits a `positionRequested` event.

    The ui is expected to be lazy. Calculations are only done if this widget is shown.
    If changes to the label slot are detected without the ui being visible, `_table_initialized`
    is set to False and a complete recalculation will happen the next time the widget is shown.
    (This could be in principle optimized by keeping track of the dirty rois.)

    Subclasses are responsible for updates to the table, e.g. on slot dirtyness.

    See ilastik.applets.labeling.pixelLabelExplorer and
    ilastik.applets.objectClassification.objectLabelExplorer for concrete implementations.
    """

    # Should emit the position as a "tagged position"
    positionRequested = Signal(dict)

    @qabc.abstractmethod
    def initialize_table(self):
        """
        Do full processing in the beginning to initialize the table
        should set self._table_initialized = True in the end.
        """
        ...

    @qabc.abstractmethod
    def _populate_table(self, *args) -> list[AnnotationAnchor]:
        """
        Should update state according to it's args and return a full
        list of annotations. Should usually not directly be called but via
        populate_table.
        """
        ...

    def __init__(self, axiskeys: list[Axiskey], parent=None) -> None:
        super().__init__(parent)
        self._axiskeys = axiskeys
        self._display_axiskeys = [x for x in self._axiskeys if x != "c"]
        self._table_initialized: bool = False
        self._shown: bool = False
        # lookup label identifier to label display name, e.g. "0" -> "Foreground"
        self._lookup_table: dict[str, str] = {}
        self._item_flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren
        self._unsubscribe_fns: list[Callable[..., Any]] = []

    def add_unsubscribe_fn(self, fn: Callable[..., Any]):
        """Functions to call before once gui is scheduled to be removed

        e.g. unsubscribe from slot signals
        """
        self._unsubscribe_fns.append(fn)

    def _setupUi(self):
        """
        Create initial QTableWidget

        sub-classes want to call this (super()._setupUi) in their own _setupUi method
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.tableWidget = QTableWidget()
        layout.addWidget(self.tableWidget)
        self.tableWidget.setColumnCount(len(self._display_axiskeys) + 1)
        self.tableWidget.setHorizontalHeaderLabels(self._display_axiskeys + ["label"])
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.setSortingEnabled(True)
        self.tableWidget.setItemDelegateForColumn(
            len(self._display_axiskeys), LookupDelegate(self.tableWidget, self._item_lookup)
        )
        self.setLayout(layout)

        def _sync_viewer_position(currentRow, _currentColumn, _previousRow, _previousColumn):
            position = self.tableWidget.item(currentRow, 0).data(Qt.UserRole)
            self.positionRequested.emit(position)

        self.tableWidget.currentCellChanged.connect(_sync_viewer_position)

    def _item_lookup(self, item: str):
        return self._lookup_table.get(item, "NOT FOUND")

    def setLookupTable(self, lookup_table: dict[str, str]):
        """Set dict to go from label id (usually a number) to label name"""
        self._lookup_table = lookup_table

    def paintEvent(self, a0: QPaintEvent) -> None:
        # Hack: Initialize new widget after lane removal
        # need to trigger initialization manually - while the widget is on the
        # not on the screen
        if not self._table_initialized:
            QTimer.singleShot(0, self.sync_state)
        super().paintEvent(a0)

    @contextmanager
    def _ensure_no_sort(self):
        """
        Turn off sorting during table update, otherwise rows will get resorted
        after cell gets inserted into sort-by column - before row is completely filled
        """
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
        for fn in self._unsubscribe_fns:
            fn()

    def resize_columns_to_contents(self):
        for column in range(self.tableWidget.columnCount() - 1):
            self.tableWidget.resizeColumnToContents(column)

    def _update_table_data(self, annotation_anchors: list[AnnotationAnchor]):
        with silent_qobject(self.tableWidget), self._ensure_no_sort():
            self.tableWidget.setRowCount(len(annotation_anchors))
            for row, anchor in enumerate(annotation_anchors):
                roi_center = anchor.position
                for i, at in enumerate(self._display_axiskeys):
                    position_item = QTableWidgetItem()
                    position_item.setFlags(self._item_flags)
                    position_item.setData(Qt.DisplayRole, int(roi_center[at]))
                    position_item.setData(Qt.UserRole, roi_center)
                    self.tableWidget.setItem(row, i, position_item)

                label_item = QTableWidgetItem(str(anchor.label))
                label_item.setFlags(self._item_flags)
                self.tableWidget.setItem(row, len(self._display_axiskeys), label_item)

    def populate_table(self, *args):
        if not self._shown:
            # No need to update the table if not shown
            # but mark to redo the table again if shown
            self._table_initialized = False
            return

        anchors = self._populate_table(*args)
        self._update_table_data(anchors)
