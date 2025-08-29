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
from builtins import range
from qtpy.QtWidgets import QTableView, QAbstractItemView, QHeaderView, QStackedWidget, QLabel, QSizePolicy
from qtpy.QtCore import Qt

import logging

logger = logging.getLogger(__name__)

# ===============================================================================
# Common base class that can be used by the labelListView and the boxListView
# ===============================================================================


class ListView(QStackedWidget):
    PAGE_EMPTY = 0
    PAGE_LISTVIEW = 1

    def __init__(self, parent=None):

        super(ListView, self).__init__(parent=parent)

        self.emptyMessage = QLabel("no elements defined yet")
        self.emptyMessage.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.emptyMessage.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.addWidget(self.emptyMessage)

        self._table = QTableView()
        self.addWidget(self._table)
        self._table.clicked.connect(self.tableViewCellClicked)
        self._table.doubleClicked.connect(self.tableViewCellDoubleClicked)
        self._table.verticalHeader().sectionMoved.connect(self.rowMovedTest)
        self._table.setShowGrid(False)

    def resetEmptyMessage(self, pystring):
        self.emptyMessage.setText(pystring)

    def tableViewCellClicked(self, modelIndex):
        """
        Reimplemt this function to get interaction when double click
        :param modelIndex:
        """

    def tableViewCellDoubleClicked(self, modelIndex):
        """
        Reimplement this function to get interaction when single click
        :param modelIndex:
        """

    def rowMovedTest(self, logicalIndex, oldVisualIndex, newVisualIndex):
        logger.debug("{} {} {}".format(logicalIndex, oldVisualIndex, newVisualIndex))

    def _setListViewLook(self):
        if self.model.columnCount() < 3:
            raise NotImplementedError("_setListViewLook can only be used for label tables with >=3 columns")
        table = self._table
        table.setStyleSheet(
            """
            QTableView { padding-left: 3px; }
            QTableView::item { padding: 4px; }
            """
        )  # item.padding does not affect all four sides of table cells
        table.setAcceptDrops(True)
        table.setFocusPolicy(Qt.NoFocus)
        table.setShowGrid(False)
        table.horizontalHeader().hide()
        table.verticalHeader().hide()
        table.horizontalHeader().setMinimumSectionSize(1)
        sectionResizeModes = {
            self.model.ColumnID.Color: QHeaderView.ResizeToContents,
            self.model.ColumnID.Name: QHeaderView.Stretch,
            self.model.ColumnID.Delete: QHeaderView.ResizeToContents,
        }
        for column, mode in sectionResizeModes.items():
            table.horizontalHeader().setSectionResizeMode(column, mode)

        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)

    def selectRow(self, *args, **kwargs):
        self._table.selectRow(*args, **kwargs)

    def _onRowsChanged(self, parent, start, end):
        model = self._table.model()
        if model and model.rowCount() > 0:
            self.setCurrentIndex(self.PAGE_LISTVIEW)
        else:
            self.setCurrentIndex(self.PAGE_EMPTY)
        if self.parent() != None:
            self.parent().updateGeometry()

    def setModel(self, model):
        QTableView.setModel(self._table, model)
        self._table.setSelectionModel(model._selectionModel)

        if model.rowCount() > 0:
            self.setCurrentIndex(self.PAGE_LISTVIEW)
        else:
            self.setCurrentIndex(self.PAGE_EMPTY)

        model.rowsInserted.connect(self._onRowsChanged)
        model.rowsRemoved.connect(self._onRowsChanged)
        self.model = model

        self._setListViewLook()

    @property
    def allowDelete(self):
        return not self._table.isColumnHidden(self.model.ColumnID.Delete)

    @allowDelete.setter
    def allowDelete(self, allow):
        self._table.setColumnHidden(self.model.ColumnID.Delete, not allow)

    def minimumSizeHint(self):
        # http://www.qtcentre.org/threads/14764-QTableView-sizeHint%28%29-issues
        t = self._table
        vHeader = t.verticalHeader()
        hHeader = t.horizontalHeader()
        doubleFrame = 2 * t.frameWidth()
        w = hHeader.length() + vHeader.width() + doubleFrame

        contentH = 0
        if self._table.model():
            for i in range(self._table.model().rowCount()):
                contentH += self._table.rowHeight(i)
        contentH = max(90, contentH)

        h = hHeader.height() + contentH + doubleFrame
        from qtpy.QtCore import QSize

        return QSize(w, h)

    def sizeHint(self):
        return self.minimumSizeHint()

    def shrinkToMinimum(self):
        """
        shrink the view around the
        labels which are currently there
        """
        t = self._table
        hHeader = t.horizontalHeader()
        doubleFrame = 2 * t.frameWidth()
        contentH = 0
        if self._table.model():
            for i in range(self._table.model().rowCount()):
                contentH += self._table.rowHeight(i)
        h = contentH + 2
        self.setFixedHeight(h)
