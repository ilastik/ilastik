###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
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
from past.utils import old_div
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QUrl, QObject, QEvent, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QTableView,
    QHeaderView,
    QMenu,
    QAction,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QItemDelegate,
    QComboBox,
    QStyledItemDelegate,
    QMessageBox,
)

from .datasetDetailedInfoTableModel import DatasetColumn
from .addFileButton import AddFileButton, FILEPATH

from pathlib import Path
from functools import partial


class RemoveButtonOverlay(QPushButton):
    """
    Overlay used to show "Remove" button in the row under the cursor.
    """

    def __init__(self, parent=None):
        super().__init__(
            QIcon(FILEPATH + "/../../shell/gui/icons/16x16/actions/list-remove.png"),
            "",
            parent,
            clicked=self.removeButtonClicked,
        )
        self.setFixedSize(20, 20)  # size is fixed based on the icon above
        # these are used to compute placement at the right end of the
        # first column
        self.width = 20
        self.height = 20
        self.setVisible(False)

        # space taken by the headers in tableview
        # the coordinate system is for the whole table, we need to
        # skip the headers to draw in the correct place
        # these will be initialized first time placeAtRow is called
        self.xoffset = None
        self.yoffset = None

        self.current_row = -1

    def removeButtonClicked(self):
        """
        Handles the button click by passing the current row to the parent
        handler.
        """
        assert self.current_row > -1
        view = self.parent()
        view.removeButtonClicked(self.current_row)

    def setVisible(self, state):
        """
        Set visibility of the overlay button.

        ``current_row`` is reset when visibility is turned off to make sure
        that we recompute the placement afterwards.
        """
        if state is False:
            self.current_row = -1
        return super().setVisible(state)

    def placeAtRow(self, ind):
        """
        Place the button in the row with index ``ind``.
        """
        if ind == self.current_row:
            return
        view = self.parent()
        model = view.model()
        if ind == -1 or ind >= model.rowCount() - 1 or model.isEmptyRow(ind):
            self.setVisible(False)
            return

        # initialize x and y offset if not done already
        if self.yoffset is None:
            self.yoffset = view.horizontalHeader().sizeHint().height() + 2  # nudge a little lower
        if self.xoffset is None:
            self.xoffset = view.verticalHeader().sizeHint().width()

        # avoid painting over the header
        row_y_offset = view.rowViewportPosition(ind)
        if row_y_offset < 0:
            self.setVisible(False)
            return

        # we're on
        column_width = view.columnWidth(0)
        row_height = view.rowHeight(ind)

        self.setGeometry(
            self.xoffset + column_width - self.width,
            row_y_offset + self.yoffset + old_div((row_height - self.height), 2),
            self.width,
            self.height,
        )
        self.setVisible(True)
        self.current_row = ind


class DisableButtonOverlayOnMouseEnter(QObject):
    """
    Event filter to disable the button overlay if mouse enters the widget.

    This is used on the horizontal and vertical headers of the table
    view to prevent the remove button from being displayed.
    """

    def __init__(self, parent, overlay):
        super(DisableButtonOverlayOnMouseEnter, self).__init__(parent)
        self._overlay = overlay

    def eventFilter(self, object, event):
        if event.type() == QEvent.Enter:
            self._overlay.setVisible(False)
        return False


class InlineAddButtonDelegate(QItemDelegate):
    """
    Displays an "Add..." button on the first column of the table if the
    corresponding row has not been assigned data yet. This is needed when a
    prediction map for a raw data lane needs to be specified for example.
    """

    def __init__(self, parent):
        super().__init__(parent)

    def paint(self, painter, option, index):
        # This method will be called every time a particular cell is in
        # view and that view is changed in some way. We ask the delegates
        # parent (in this case a table view) if the index in question (the
        # table cell) corresponds to an empty row (indicated by '<empty>'
        # in the data field), and create a button if there isn't one
        # already associated with the cell.
        parent_view = self.parent()
        button = parent_view.indexWidget(index)
        if index.row() < parent_view.model().rowCount() - 1 and parent_view.model().isEmptyRow(index.row()):
            if isinstance(button, AddFileButton) and button.index.row() != index.row():
                button.index = index  # Just in case index got out of sync
            if button is None:
                # this is only executed on init, but not on remove, such that row and lane get out of sync
                button = AddFileButton(parent_view, index=index)
                button.addFilesRequested.connect(partial(parent_view.handleCellAddFilesEvent, button))
                button.addStackRequested.connect(partial(parent_view.handleCellAddStackEvent, button))
                button.addPrecomputedVolumeRequested.connect(
                    partial(parent_view.handleCellAddPrecomputedVolumeEvent, button)
                )
                button.addDvidVolumeRequested.connect(partial(parent_view.handleCellAddDvidVolumeEvent, button))
                parent_view.setIndexWidget(index, button)
        elif index.data() != "" and button is not None:
            # If this row has data, we must delete the button.
            # Otherwise, it can steal input events (e.g. mouse clicks) from the cell, even if it is hidden!
            # However, we can't remove it yet, because we are currently running in the context of a signal handler for the button itself!
            # Instead, use a QTimer to delete the button as soon as the eventloop is finished with the current event.
            QTimer.singleShot(750, lambda: parent_view.setIndexWidget(index, None))
        super().paint(painter, option, index)


class ScaleComboBoxDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        self.parent().openPersistentEditor(index)

    def createEditor(self, parent: "DatasetDetailedInfoTableView", option, index):
        model: "DatasetDetailedInfoTableModel" = index.model()
        scales = model.get_scale_options(index.row())
        if not scales:
            return None
        combo = QComboBox(parent)
        for scale_index, scale in enumerate(scales):
            combo.addItem(scale, scale_index)
        combo.currentIndexChanged.connect(partial(self.on_combo_selected, index))
        return combo

    def setEditorData(self, editor, index):
        value = index.data(Qt.DisplayRole)
        current_selected = editor.findText(value)
        if current_selected >= 0:
            editor.setCurrentIndex(current_selected)

    def setModelData(self, editor, model, index, user_triggered=False):
        if not user_triggered:
            # De-focussing the combobox triggers setModelData.
            # We only want to emit when the user actually selects from the combobox.
            return
        self.parent().scaleSelected.emit(index.row(), editor.currentIndex())

    def on_combo_selected(self, index):
        model = index.model()
        if model.is_scale_locked(index.row()):
            message = (
                "You have already continued in the project with this dataset at the selected scale. "
                'To inspect another scale, please use "Add New" and add the same remote source as '
                "another dataset, or create a new project."
            )
            QMessageBox.information(self.parent(), "Scale locked", message)
            # Reset the combobox to the previous value
            editor = self.sender()
            previous_index = editor.findText(index.data(Qt.DisplayRole))
            editor.blockSignals(True)  # To avoid re-triggering on_combo_selected
            editor.setCurrentIndex(previous_index)
            editor.blockSignals(False)
            return
        self.setModelData(self.sender(), None, index, user_triggered=True)
        changed_cell = model.index(index.row(), DatasetColumn.Shape)
        # dataChanged(topLeft, bottomRight); since we're editing one cell, topLeft == bottomRight
        model.dataChanged.emit(changed_cell, changed_cell)


class DatasetDetailedInfoTableView(QTableView):
    dataLaneSelected = pyqtSignal(object)  # Signature: (laneIndex)
    scaleSelected = pyqtSignal(int, int)  # Signature: (lane_index, scale_index)

    replaceWithFileRequested = pyqtSignal(int)  # Signature: (laneIndex), or (-1) to indicate "append requested"
    replaceWithStackRequested = pyqtSignal(int)  # Signature: (laneIndex)
    editRequested = pyqtSignal(object)  # Signature: (lane_index_list)
    resetRequested = pyqtSignal(object)  # Signature: (lane_index_list)

    addFilesRequested = pyqtSignal(int)  # Signature: (lane_index)
    addStackRequested = pyqtSignal(int)  # Signature: (lane_index)
    addPrecomputedVolumeRequested = pyqtSignal(int)  # Signature: (lane_index)
    addDvidVolumeRequested = pyqtSignal(int)  # Signature: (lane_index)
    addFilesRequestedDrop = pyqtSignal(object, int)  # Signature: (filepath_list, lane_index)

    def __init__(self, parent: "DataSelectionGui"):
        super().__init__(parent)
        # this is needed to capture mouse events that are used for
        # the remove button placement
        self.setMouseTracking(True)

        self.selectedLanes = []
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.handleCustomContextMenuRequested)

        self.resizeRowsToContents()
        self.resizeColumnsToContents()
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)

        self.setItemDelegateForColumn(0, InlineAddButtonDelegate(self))
        self.setItemDelegateForColumn(DatasetColumn.Scale, ScaleComboBoxDelegate(self))

        self.setSelectionBehavior(QTableView.SelectRows)

        self.setAcceptDrops(True)

        self.overlay = RemoveButtonOverlay(self)

        event_filter = DisableButtonOverlayOnMouseEnter(self, self.overlay)
        self.horizontalHeader().installEventFilter(event_filter)
        self.verticalHeader().installEventFilter(event_filter)

    @pyqtSlot(int)
    def handleCellAddFilesEvent(self, button):
        self.addFilesRequested.emit(button.index.row())

    @pyqtSlot(int)
    def handleCellAddStackEvent(self, button):
        self.addStackRequested.emit(button.index.row())

    @pyqtSlot(int)
    def handleCellAddDvidVolumeEvent(self, button):
        self.addDvidVolumeRequested.emit(button.index.row())

    @pyqtSlot(int)
    def handleCellAddPrecomputedVolumeEvent(self, button):
        self.addPrecomputedVolumeRequested.emit(button.index.row())

    def wheelEvent(self, event):
        """
        Handle mouse wheel scroll by updating the remove button overlay.
        """
        res = super().wheelEvent(event)
        self.adjustRemoveButton(event.pos())
        return res

    def leaveEvent(self, event):
        """
        Disable the remove button overlay when mouse leaves this widget.
        """
        self.overlay.setVisible(False)
        return super().enterEvent(event)

    def mouseMoveEvent(self, event=None):
        """
        Update the remove button overlay according to the new mouse
        position.
        """
        self.adjustRemoveButton(event.pos())
        return super().mouseMoveEvent(event)

    def adjustRemoveButton(self, pos):
        """
        Move the remove button overlay to the row under the cursor
        position given by ``pos``.
        """
        ind = self.indexAt(pos)
        if ind.column() == -1:
            # disable remove button if not cursor is not over a column
            self.overlay.setVisible(False)
            return

        row_ind = ind.row()
        self.overlay.placeAtRow(row_ind)

    def removeButtonClicked(self, ind):
        """
        Handle remove file events generated by the remove button overlay.
        """
        assert ind <= self.model().rowCount() - 1
        self.resetRequested.emit([ind])
        # redraw the table and disable the overlay
        self.overlay.setVisible(False)
        self.update()

    def setModel(self, model):
        """
        Set model used to store the data. This method adds an extra row
        at the end, which is used to keep the "Add..." button.
        """
        super().setModel(model)

        widget = QWidget()
        layout = QHBoxLayout(widget)
        self._addButton = button = AddFileButton(widget, new=True)
        button.addFilesRequested.connect(partial(self.addFilesRequested.emit, -1))
        button.addStackRequested.connect(partial(self.addStackRequested.emit, -1))
        button.addDvidVolumeRequested.connect(partial(self.addDvidVolumeRequested.emit, -1))
        button.addPrecomputedVolumeRequested.connect(partial(self.addPrecomputedVolumeRequested.emit, -1))
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(button)
        layout.addStretch()
        widget.setLayout(layout)

        lastRow = self.model().rowCount() - 1
        button.index = self.model().index(lastRow, 0)
        self.setIndexWidget(button.index, widget)
        # the "Add..." button spans last row
        self.setSpan(lastRow, 0, 1, model.columnCount())

        self.horizontalHeader().setSectionResizeMode(DatasetColumn.Nickname, QHeaderView.Interactive)
        self.horizontalHeader().setSectionResizeMode(DatasetColumn.Location, QHeaderView.Interactive)
        self.horizontalHeader().setSectionResizeMode(DatasetColumn.InternalID, QHeaderView.Interactive)
        self.horizontalHeader().setSectionResizeMode(DatasetColumn.AxisOrder, QHeaderView.Interactive)

    def setEnabled(self, status):
        """
        Set status of the add button shown on the last row.

        If this view is used for a secondary role, such as importing
        prediction maps, the button is only available if there are more
        raw data lanes than prediction maps.
        """
        self._addButton.setEnabled(status)

    def selectionChanged(self, selected, deselected):
        super().selectionChanged(selected, deselected)
        rows = {index.row() for index in self.selectedIndexes()}
        rows.discard(self.model().rowCount() - 1)  # last row is a button
        self.selectedLanes = sorted(rows)

        self.dataLaneSelected.emit(self.selectedLanes)

    def handleCustomContextMenuRequested(self, pos):
        def _is_position_within_table():
            # last row is a button
            return 0 <= col < self.model().columnCount() and 0 <= row < self.model().rowCount() - 1

        def _is_multilane_selection():
            return row in self.selectedLanes and len(self.selectedLanes) > 1

        col = self.columnAt(pos.x())
        row = self.rowAt(pos.y())

        if not _is_position_within_table():
            return

        menu = QMenu(parent=self)
        editSharedPropertiesAction = QAction("Edit shared properties...", menu)
        editPropertiesAction = QAction("Edit properties...", menu)
        replaceWithFileAction = QAction("Replace with file...", menu)
        replaceWithStackAction = QAction("Replace with stack...", menu)
        removeAction = QAction("Remove", menu)

        if _is_multilane_selection():
            editable = all(self.model().isEditable(lane) for lane in self.selectedLanes)
            menu.addAction(editSharedPropertiesAction)
            editSharedPropertiesAction.setEnabled(editable)
            menu.addAction(removeAction)
        else:
            menu.addAction(editPropertiesAction)
            editPropertiesAction.setEnabled(self.model().isEditable(row))
            menu.addAction(replaceWithFileAction)
            menu.addAction(replaceWithStackAction)
            menu.addAction(removeAction)

        globalPos = self.viewport().mapToGlobal(pos)
        selection = menu.exec_(globalPos)
        if selection is None:
            return
        if selection is editSharedPropertiesAction:
            self.editRequested.emit(self.selectedLanes)
        if selection is editPropertiesAction:
            self.editRequested.emit([row])
        if selection is replaceWithFileAction:
            self.replaceWithFileRequested.emit(row)
        if selection is replaceWithStackAction:
            self.replaceWithStackRequested.emit(row)
        if selection is removeAction:
            self.resetRequested.emit(self.selectedLanes)

    def mouseDoubleClickEvent(self, event):
        row = self.rowAt(event.pos().y())

        # If the user double-clicked an empty table,
        #  we behave as if she clicked the "add file" button.
        if row == self.model().rowCount() - 1 or row == -1:
            # In this case -1 means "append a row"
            self.replaceWithFileRequested.emit(-1)
            return

        if self.model().isEditable(row):
            self.editRequested.emit([row])
        else:
            self.replaceWithFileRequested.emit(row)

    def dragEnterEvent(self, event):
        # Only accept drag-and-drop events that consist of urls to local files.
        if not event.mimeData().hasUrls():
            return
        urls = event.mimeData().urls()
        if all(map(QUrl.isLocalFile, urls)):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        # Must override this or else the QTableView base class steals dropEvents from us.
        pass

    def dropEvent(self, dropEvent):
        filepaths = [Path(QUrl.toLocalFile(url)) for url in dropEvent.mimeData().urls()]
        starting_lane_index = self.rowAt(dropEvent.pos().y())
        # Last row is the button.
        if starting_lane_index == self.model().rowCount() - 1:
            starting_lane_index = -1

        self.addFilesRequestedDrop.emit(filepaths, starting_lane_index)

    def scrollContentsBy(self, dx, dy):
        """
        Overridden from QTableView.
        This forces the table to be redrawn after the user scrolls.
        This is apparently needed on OS X.
        """
        super().scrollContentsBy(dx, dy)

        # Hack: On Mac OS X, there is an issue that causes the row buttons not to be drawn correctly in some cases.
        # We can force a repaint by resizing the column.
        # (Manually calling self.update() here doesn't solve the issue, but this trick does.)
        first_col_width = self.columnWidth(0)
        self.setColumnWidth(0, first_col_width + 1)
        self.setColumnWidth(0, first_col_width)
