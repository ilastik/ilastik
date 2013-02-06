from PyQt4.QtGui import QColor, QPixmap, QIcon, QItemSelectionModel, QPainter, QPen, QImage
from PyQt4.QtCore import QObject, QAbstractTableModel, Qt, QModelIndex, pyqtSignal

import logging
logger = logging.getLogger(__name__)

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
            logger.debug("Label '%s' has new brush color %r" % (self._brushColor, c))
            self._brushColor = c
            self.colorChanged.emit(c)
            
    def pmapColor(self):
        return self._pmapColor
    def setPmapColor(self, c):
        if self._pmapColor != c:
            logger.debug("Label '%s' has new pmapColor %r" % (self._pmapColor, c))
            self._pmapColor = c
            self.pmapColorChanged.emit(c)
    
    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, n):
        if self._name != n:
            logger.debug("Label '%s' has new name '%s'" % (self._name, n))
            self._name = n
            self.nameChanged.emit(n)
    
    def __repr__(self):
        return "<Label name=%s, color=%r>" % (self.name, self._brushColor)

class LabelListModel(QAbstractTableModel):
    orderChanged = pyqtSignal()
    labelSelected = pyqtSignal(int)
    
    def __init__(self, labels = [], parent = None):
        QAbstractTableModel.__init__(self, parent)
        self._labels = list(labels)
        self._selectionModel = QItemSelectionModel(self)
        
        def onSelectionChanged(selected, deselected):
            if selected:
                self.labelSelected.emit(selected[0].indexes()[0].row())
        self._selectionModel.selectionChanged.connect(onSelectionChanged)
        
        self._allowRemove = True
        self._toolTipSuffixes = {}
    
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
        """
        This class can be used to make each row look like a separate widget with its own tooltip.
        In this case, the "tooltip" is the suffix appended to the tooltip of the middle column.
        """
        def __init__(self, table, row):
            self._row = row
            self._table = table
        def toolTip(self):
            return self._table._getToolTipSuffix(self._row)
        def setToolTip(self, text):
            self._table._setToolTipSuffix(self._row, text)

    def data(self, index, role):
        if role == Qt.EditRole and index.column() == 0:
            return (self._labels[index.row()].color, self._labels[index.row()].pmapColor)
        if role == Qt.EditRole and index.column() == 1:
            return self._labels[index.row()].name
        
        if role == Qt.ToolTipRole and index.column() == 0:
            return "Hex code : " + self._labels[index.row()].color.name() + "\n DoubleClick to change"
        if role == Qt.ToolTipRole and index.column() == 1:
            suffix = self._getToolTipSuffix(index.row())
            return self._labels[index.row()].name + "\n DoubleClick to rename" + suffix
        if role == Qt.ToolTipRole and index.column() == 2:
            return "Delete " + self._labels[index.row()].name
        
        if role == Qt.DecorationRole and index.column() == 0:
            row = index.row()
            value = self._labels[row]
            if(value.brushColor == value.pmapColor):
                pixmap = QPixmap(26, 26)
                pixmap.fill(value.brushColor)
            else:
                a = value.brushColor().rgba()
                b = value.pmapColor().rgba()
                img = QImage(26,26, QImage.Format_RGB32)
                for i in range(26):
                    for j in range(0,26-i):
                        img.setPixel(i,j, a)
                for i in range(26):
                    for j in range(26-i,26):
                        img.setPixel(i,j, b)
                pixmap = QPixmap.fromImage(img)
            icon = QIcon(pixmap)
            return icon
        
        if role == Qt.DecorationRole and index.column() == 2:
            row = index.row()
            pixmap = QPixmap(26, 26)
            pixmap.fill(Qt.transparent)
            painter = QPainter()
            painter.begin(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor("red"))
            painter.drawEllipse(1, 1, 24, 24)
            pen = QPen(QColor("black"))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(8,8, 18,18)
            painter.drawLine(18,8, 8,18)
            
            painter.end()
            icon = QIcon(pixmap)
            return icon
        
        if role == Qt.DisplayRole and index.column() == 1:
            row = index.row()
            value = self._labels[row]
            return value.name

    def flags(self, index):
        if  index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        elif  index.column() == 1:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        elif  index.column() == 2:
            if self._allowRemove:
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable
            else:
                return Qt.NoItemFlags
        
    def setData(self, index, value, role = Qt.EditRole):
        if role == Qt.EditRole  and index.column() == 0:
            row = index.row()
            brushColor = QColor(value[0])
            pmapColor = QColor(value[1])
            if brushColor.isValid() and pmapColor.isValid():
                print "setData: brushColor = %r, pmapColor = %r" % (brushColor.name(), pmapColor.name())
                print "  self._labels[row] has type ", type(self._labels[row])
                self._labels[row].setBrushColor(brushColor)
                self._labels[row].setPmapColor(pmapColor)
                print "  self._labels[row].brushColor = ", self._labels[row].brushColor().name()
                print "  self._labels[row].pmapColor  = ", self._labels[row].pmapColor().name()
                self.dataChanged.emit(index, index)
                return True
            
        if role == Qt.EditRole  and index.column() == 1:
            row = index.row()
            name = value
            self._labels[row].name = str(name.toString())
            self.dataChanged.emit(index, index)
            return True
        
        return False

    def insertRow(self, position, object, parent = QModelIndex()):
        self.beginInsertRows(parent, position, position)
        self._labels.insert(position, object)
        self.endInsertRows()
        return True

    def removeRow(self, position, parent = QModelIndex()):
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
        self.dataChanged.emit(self.createIndex(0, 2), self.createIndex(self.rowCount(), 2))

    def select(self, row):
        self._selectionModel.clear()
        self._selectionModel.select(self.index(row, 0), QItemSelectionModel.Select)
        self._selectionModel.select(self.index(row, 1), QItemSelectionModel.Select)
        
    
    
