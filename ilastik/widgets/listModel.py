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
#		   http://ilastik.org/license.html
###############################################################################
from PyQt5.QtGui import QColor, QPixmap, QIcon, QPainter, QPen, QImage
from PyQt5.QtCore import QObject, QAbstractTableModel, QItemSelectionModel, Qt, QModelIndex, pyqtSignal

import logging
logger = logging.getLogger(__name__)

_NPIXELS = 26
_XSTART = 8

class ListElement(QObject):
    nameChanged  = pyqtSignal(object)

    def __init__(self,name, parent = None):
        QObject.__init__(self, parent)
        self._name       = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, n):
        if self._name != n:
            logger.debug("Label '{}' has new name '{}'".format(
                self._name, n))
            self._name = n
            self.nameChanged.emit(n)



class ListModel(QAbstractTableModel):
    orderChanged = pyqtSignal()
    elementSelected = pyqtSignal(int)


    class ColumnID(object):
        '''
        Define how many column the model holds and their type

        '''
        ncols=2
        Name=0
        Delete=1

    def __init__(self, elements=None, parent=None):
        '''
        Common interface for the labelListModel, the boxListModel, and the cropListModel
        see concrete implementations for details

        :param elements:
        :param parent:
        '''
        QAbstractTableModel.__init__(self, parent)

        if elements is None:
            elements = []
        self._elements = list(elements)
        self._selectionModel = QItemSelectionModel(self)

        def onSelectionChanged(selected, deselected):


            if selected:
                ind = selected[0].indexes()
                if len(ind)>0:
                    self.elementSelected.emit(ind[0].row())

        self._selectionModel.selectionChanged.connect(onSelectionChanged)

        self._allowRemove = True
        self._toolTipSuffixes = {}

        self.unremovable_rows=[] #rows in this list cannot be removed from the gui,
                                 # to add to this list call self.makeRowPermanent(int)
                                 # to remove make the self.makeRowRemovable(int)
    def makeRowPermanent(self, rowIndex):
        """
        The rowindex cannot be removed from gui
        to remove this index use self.makeRowRemovable
        """

        self.unremovable_rows.append(rowIndex)

    def makeRowRemovable(self, rowIndex):
        """
        :param rowIndex: is the index for the label of interest in the current gui setting
        """
        self.unremovable_rows.remove(rowIndex)

    def __len__(self):
        return len(self._elements)

    def __getitem__(self, i):
        return self._elements[i]

    def selectedRow(self):
        selected = self._selectionModel.selectedRows()
        if len(selected) == 1:
            return selected[0].row()
        return -1

    def selectedIndex(self):
        row = self.selectedRow()
        if row >= 0:
            return self.index(self.selectedRow())
        else:
            return QModelIndex()

    def rowCount(self, parent=None):
        return len(self._elements)

    def columnCount(self, parent):
        return self.ColumnID.ncols

    def _getToolTipSuffix(self, row):
        """
        Get the middle column tooltip suffix
        """
        suffix = "; Click to select"
        if row in self._toolTipSuffixes:
            suffix = self._toolTipSuffixes[row]
        return suffix

    def _setToolTipSuffix(self, row, text):
        """
        Set the middle column tooltip suffix
        """
        self._toolTipSuffixes[row] = text
        index = self.createIndex(row, 1)
        self.dataChanged.emit(index, index)

    class EntryToolTipAdapter(object):
        """This class can be used to make each row look like a
        separate widget with its own tooltip.

        In this case, the "tooltip" is the suffix appended to the
        tooltip of the middle column.

        """
        def __init__(self, table, row):
            self._row = row
            self._table = table
        def toolTip(self):
            return self._table._getToolTipSuffix(self._row)
        def setToolTip(self, text):
            self._table._setToolTipSuffix(self._row, text)



    def insertRow(self, position, object, parent=QModelIndex()):
        self.beginInsertRows(parent, position, position)
        object.changed.connect(self.modelReset)
        self._elements.insert(position, object)
        self.endInsertRows()
        return True

    def removeRow(self, position, parent=QModelIndex()):
        if position in self.unremovable_rows:
            return False

        self.beginRemoveRows(parent, position, position)
        value = self._elements[position]
        logger.debug("removing row: " + str(value))
        self._elements.remove(value)
        self.endRemoveRows()
        return True

    def allowRemove(self, check):
        #Allow removing of rows. Needed to be able to disallow it
        #in interactive mode
        self._allowRemove = check
        self.dataChanged.emit(self.createIndex(0, self.ColumnID.Delete),
                              self.createIndex(self.rowCount(), self.ColumnID.Delete))
    def data(self, index, role):
        '''
        Reimplement, see labelListModel or boxListModel for concrete example
        :param index:
        :param role:
        '''

        if role == Qt.EditRole and index.column() == self.ColumnID.Name:
            name = self._elements[index.row()].name
            return name

        elif role == Qt.ToolTipRole and index.column() == self.ColumnID.Delete:
            s = "Delete {}".format(self._elements[index.row()].name)
            return s

        elif role == Qt.ToolTipRole and index.column() == self.ColumnID.Name:
            suffix = self._getToolTipSuffix(index.row())
            s = "{}\nDouble click to rename {}".format(
                self._elements[index.row()].name, suffix)
            return s
        elif role == Qt.DisplayRole and index.column() == self.ColumnID.Name:
            name = self._elements[index.row()].name
            return name

        if role == Qt.DecorationRole and index.column() == self.ColumnID.Delete:
            if index.row() in self.unremovable_rows: return

            row = index.row()
            pixmap = QPixmap(_NPIXELS, _NPIXELS)
            pixmap.fill(Qt.transparent)
            painter = QPainter()
            painter.begin(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor("red"))
            painter.drawEllipse(1, 1, _NPIXELS - 2, _NPIXELS - 2)
            pen = QPen(QColor("black"))
            pen.setWidth(2)
            painter.setPen(pen)

            x = _XSTART
            y = _NPIXELS - x
            painter.drawLine(x, x, y, y)
            painter.drawLine(y, x, x, y)

            painter.end()
            icon = QIcon(pixmap)
            return icon

    def flags(self, index):
        '''
        Reimplement, see labelListModel or boxListModel for concrete example
        :param index:
        '''
        if index.column() == self.ColumnID.Delete:
            if self._allowRemove:
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable
            else:
                return Qt.NoItemFlags
        elif  index.column() == self.ColumnID.Name:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return Qt.NoItemFlags

    def setData(self, index, value, role=Qt.EditRole):
        '''
        Reimplement, see labelListModel or boxListModel for concrete example
        :param index:
        '''
        if role == Qt.EditRole  and index.column() == self.ColumnID.Name:
            row = index.row()
            self._elements[row].name = value
            self.dataChanged.emit(index, index)
            return True

        return False

    def select(self, row):
        '''
        Reimplement, see labelListModel or boxListModel for concrete example
        :param row
        '''
        self._selectionModel.clear()
        self._selectionModel.select(self.index(row, self.ColumnID.Name),
                                    QItemSelectionModel.Select)

    def clearSelectionModel(self):
        self._selectionModel.clear()

