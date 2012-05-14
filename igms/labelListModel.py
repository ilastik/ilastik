from PyQt4.QtGui import QColor, QPixmap, QIcon, QItemSelectionModel, QPainter, QPen
from PyQt4.QtCore import QObject, QAbstractTableModel, Qt, QModelIndex, pyqtSignal

class Label(QObject):
    changed      = pyqtSignal()
    colorChanged = pyqtSignal(QColor)
    nameChanged  = pyqtSignal(object)
    
    def __init__(self, name, color, parent = None):
        QObject.__init__(self, parent)
        self._name = name
        self._color = color
    
    @property
    def color(self):
        return self._color
    @color.setter
    def color(self, c):
        if self._color != c:
            print "Label '%s' has new color %r" % (self._name, c)
            self._color = c
            self.colorChanged.emit(c)
    
    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, n):
        if self._name != n:
            print "Label '%s' has new name '%s'" % (self._name, n)
            self._name = n
            self.nameChanged.emit(n)
    
    def __repr__(self):
        return "<Label name=%s, color=%r>" % (self.name, self.color)

class LabelListModel(QAbstractTableModel):
    orderChanged = pyqtSignal()
    labelSelected = pyqtSignal(int)
    
    def __init__(self, labels = [], parent = None):
        QAbstractTableModel.__init__(self, parent)
        self._labels = labels
        self._selectionModel = QItemSelectionModel(self)
        
        def onSelectionChanged(selected, deselected):
            if selected:
                self.labelSelected.emit(selected[0].indexes()[0].row())
        self._selectionModel.selectionChanged.connect(onSelectionChanged)
        
        self._allowRemove = True
    
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

    def data(self, index, role):
        if role == Qt.EditRole and index.column() == 0:
            return self._labels[index.row()].color
        if role == Qt.EditRole and index.column() == 1:
            return self._labels[index.row()].name
        
        if role == Qt.ToolTipRole and index.column() == 0:
            return "Hex code : " + self._labels[index.row()].color.name() + "\n DoubleClick to change"
        if role == Qt.ToolTipRole and index.column() == 1:
            return self._labels[index.row()].name + "\n DoubleClick to rename"
        if role == Qt.ToolTipRole and index.column() == 2:
            return "Delete " + self._labels[index.row()].name
        
        if role == Qt.DecorationRole and index.column() == 0:
            row = index.row()
            value = self._labels[row]
            pixmap = QPixmap(26, 26)
            pixmap.fill(value.color)
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
            color = QColor(value)
            if color.isValid():
                self._labels[row].color = color
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
        print "removing row: ", value
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
        
    
    
