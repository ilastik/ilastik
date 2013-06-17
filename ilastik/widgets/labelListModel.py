from PyQt4.QtGui import QColor, QPixmap, QIcon, QItemSelectionModel, QPainter, QPen, QImage
from PyQt4.QtCore import QObject, QAbstractTableModel, Qt, QModelIndex, pyqtSignal

import logging
logger = logging.getLogger(__name__)

_NPIXELS = 26
_XSTART = 8

class Label(QObject):
    changed      = pyqtSignal()
    colorChanged = pyqtSignal(QColor)
    pmapColorChanged = pyqtSignal(QColor)
    nameChanged  = pyqtSignal(object)

    def __init__(self, name, color, parent = None, pmapColor=None):
        QObject.__init__(self, parent)
        self._name       = name
        self._brushColor = color
        if pmapColor is None:
            self._pmapColor = color
        else:
            self._pmapColor = pmapColor

    def brushColor(self):
        return self._brushColor

    def setBrushColor(self, c):
        if self._brushColor != c:
            logger.debug("Label '{}' has new brush color {}".format(
                self._brushColor, c))
            self._brushColor = c
            self.colorChanged.emit(c)

    def pmapColor(self):
        return self._pmapColor

    def setPmapColor(self, c):
        if self._pmapColor != c:
            logger.debug("Label '{}' has new pmapColor {}".format(
                self._pmapColor, c))
            self._pmapColor = c
            self.pmapColorChanged.emit(c)

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

    def __repr__(self):
        return "<Label name={}, color={}>".format(
            self.name, self._brushColor)




class LabelListModel(QAbstractTableModel):
    orderChanged = pyqtSignal()
    labelSelected = pyqtSignal(int)
    
    
    class ColumnID():
        Color  = 0
        Name   = 1
        Delete = 2

    def __init__(self, labels=None, parent=None):
        QAbstractTableModel.__init__(self, parent)

        if labels is None:
            labels = []
        self._labels = list(labels)
        self._selectionModel = QItemSelectionModel(self)

        def onSelectionChanged(selected, deselected):
            if selected:
                self.labelSelected.emit(selected[0].indexes()[0].row())

        self._selectionModel.selectionChanged.connect(onSelectionChanged)

        self._allowRemove = True
        self._toolTipSuffixes = {}
        
        self.unremovable_rows=[] #rows in this list cannot be removed from the gui, 
                                 # to add to this list call self.makeRowPermanent(int)
                                 # to remove make the self.makeRowRemovable(int)
                                  
    
    def makeRowPermanent(self,rowindex):
        """
        The rowindex cannot be removed from gui
        to remove this index use self.makeRowRemovable
        """
        
        self.unremovable_rows.append(rowindex)
    
    def makeRowRemovable(self,rowindex):
        self.unremovable_rows.pop(rowindex)

    def __len__(self):
        return len(self._labels)

    def __getitem__(self, i):
        return self._labels[i]

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
        return len(self._labels)

    def columnCount(self, parent):
        return 3

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

    def data(self, index, role):
        if role == Qt.EditRole and index.column() == self.ColumnID.Color:
            return (self._labels[index.row()].brushColor(),
                    self._labels[index.row()].pmapColor())

        if role == Qt.EditRole and index.column() == self.ColumnID.Name:
            return self._labels[index.row()].name

        if role == Qt.ToolTipRole and index.column() == self.ColumnID.Color:
            return ("Hex code : {}\nDouble click to change".format(
                self._labels[index.row()].brushColor().name()))

        if role == Qt.ToolTipRole and index.column() == self.ColumnID.Name:
            suffix = self._getToolTipSuffix(index.row())
            return "{}\nDouble click to rename {}".format(
                self._labels[index.row()].name, suffix)

        if role == Qt.ToolTipRole and index.column() == self.ColumnID.Delete:
            return "Delete {}".format(self._labels[index.row()].name)

        if role == Qt.DecorationRole and index.column() == self.ColumnID.Color:
            row = index.row()
            value = self._labels[row]
            if value.brushColor == value.pmapColor():
                pixmap = QPixmap(_NPIXELS, _NPIXELS)
                pixmap.fill(value.brushColor)
            else:
                a = value.brushColor().rgba()
                b = value.pmapColor().rgba()
                img = QImage(_NPIXELS,_NPIXELS, QImage.Format_RGB32)
                for i in range(_NPIXELS):
                    for j in range(0, _NPIXELS - i):
                        img.setPixel(i, j, a)
                for i in range(_NPIXELS):
                    for j in range(_NPIXELS - i, _NPIXELS):
                        img.setPixel(i, j, b)
                pixmap = QPixmap.fromImage(img)
            icon = QIcon(pixmap)
            return icon

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

        if role == Qt.DisplayRole and index.column() == self.ColumnID.Name:
            row = index.row()
            value = self._labels[row]
            return value.name

    def flags(self, index):
        if  index.column() == self.ColumnID.Color:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        elif  index.column() == self.ColumnID.Name:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        elif  index.column() == self.ColumnID.Delete:
            if self._allowRemove:
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable
            else:
                return Qt.NoItemFlags

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole  and index.column() == self.ColumnID.Color:
            row = index.row()
            brushColor = QColor(value[0])
            pmapColor = QColor(value[1])
            if brushColor.isValid() and pmapColor.isValid():
                print "setData: brushColor = {}, pmapColor = {}".format(
                    brushColor.name(), pmapColor.name())
                print "  self._labels[row] has type {}".format(
                    type(self._labels[row]))
                self._labels[row].setBrushColor(brushColor)
                self._labels[row].setPmapColor(pmapColor)
                print "  self._labels[row].brushColor = {}".format(
                    self._labels[row].brushColor().name())
                print "  self._labels[row].pmapColor  = {}".format(
                    self._labels[row].pmapColor().name())
                self.dataChanged.emit(index, index)
                return True

        if role == Qt.EditRole  and index.column() == self.ColumnID.Name:
            row = index.row()
            name = value
            self._labels[row].name = str(name.toString())
            self.dataChanged.emit(index, index)
            return True


        return False

    def insertRow(self, position, object, parent=QModelIndex()):
        self.beginInsertRows(parent, position, position)
        object.changed.connect(self.modelReset)
        self._labels.insert(position, object)
        self.endInsertRows()
        return True

    def removeRow(self, position, parent=QModelIndex()):
        if position in self.unremovable_rows:
            return False
        

        self.beginRemoveRows(parent, position, position)
        value = self._labels[position]
        logger.debug("removing row: " + str(value))
        self._labels.remove(value)
        self.endRemoveRows()
        return True

    def allowRemove(self, check):
        #Allow removing of rows. Needed to be able to disallow it
        #in interactive mode
        self._allowRemove = check
        self.dataChanged.emit(self.createIndex(0, self.ColumnID.Delete),
                              self.createIndex(self.rowCount(), self.ColumnID.Delete))

    def select(self, row):
        self._selectionModel.clear()
        self._selectionModel.select(self.index(row, self.ColumnID.Color),
                                    QItemSelectionModel.Select)
        self._selectionModel.select(self.index(row, self.ColumnID.Name),
                                    QItemSelectionModel.Select)


