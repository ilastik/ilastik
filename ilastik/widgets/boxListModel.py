from PyQt4.QtGui import QColor, QPixmap, QIcon, QItemSelectionModel, QPainter, QPen, QImage, QDialog,QColorDialog
from PyQt4.QtCore import QObject, QAbstractTableModel, Qt, QModelIndex, pyqtSignal,QString
from listModel import ListModel,ListElement,_NPIXELS
#from labelListModel import LabelListModel
import logging
from PyQt4.uic.Compiler.qtproxies import QtGui
from PyQt4 import uic
import os
logger = logging.getLogger(__name__)

#===============================================================================
# Implements the functionality for the dynamic boxes of the counting applet
# This model is fully compatible with the labelListView
#===============================================================================


class BoxLabel(ListElement):
    changed      = pyqtSignal()
    colorChanged = pyqtSignal(QColor)
    densityChanged = pyqtSignal(object)
    isFixedChanged = pyqtSignal(bool)
    
    def __init__(self, name, color, density=0.0, parent = None):
        ListElement.__init__(self, name, parent)
        self._density    = density
        self._color = color
            
        self._fixvalue=self._density # a fixed box should have this set to a particular value
        self._isFixed=False        
        self._register_signals()
    
    def _register_signals(self):
        self.colorChanged.connect(self.changed.emit)
        self.nameChanged.connect(self.changed.emit)
        self.densityChanged.connect(self.changed.emit)
        self.isFixedChanged.connect(self.changed.emit)
        
        self.densityChanged.connect(self._update_fixvalue_display)
    
        
    def _update_fixvalue_display(self):
        if not self._isFixed:
            self.fixvalue=self.density
            self.changed.emit()
    
    def setColor(self, c):
        if self._color != c:
            logger.debug("BoxLabel '{}' has new brush color {}".format(
                self._color, c))
            self._color = c
            self.colorChanged.emit(c)

    def color(self):
        return self._color

    def setPmapColor(self, c):
        if self._color != c:
            logger.debug("BoxLabel '{}' has new pmapColor {}".format(
                self._color, c))
            self._color = c
            self.colorChanged.emit(c)

    @property
    def density(self):
        return self._density
    @density.setter
    def density(self, n):
        if self._density != n:
            logger.debug("BoxLabel '{}' has new density '{}'".format(
                self._density, n))
            self._density = n
            self.densityChanged.emit(n)
            self.changed.emit()
   
    @property
    def fixvalue(self):
        return self._fixvalue
    @fixvalue.setter
    def fixvalue(self, n):
#         if self._density != n:
#             logger.debug("BoxLabel '{}' has new density '{}'".format(
#                 self._density, n))
            self._fixvalue = n
            self.changed.emit()
            
    @property
    def isFixed(self):
        return self._isFixed
    @isFixed.setter
    def isFixed(self, bool):
#         if self._density != n:
#             logger.debug("BoxLabel '{}' has new density '{}'".format(
#                 self._density, n))
            self._isFixed = bool
            self.isFixedChanged.emit(self._isFixed)
            self.changed.emit()   
    def __repr__(self):
        return "<BoxLabel name={}, color={}>".format(
            self.name, self._color)







class BoxListModel(ListModel):
    boxRemoved = pyqtSignal(int)
    
    class ColumnID():
        Color  = 0
        Name   = 1
        Text   = 2
        Fix    = 3
        Delete = 4
        
        ncols=5
        
    
    def __init__(self, elements=None, parent=None):
        super(BoxListModel,self).__init__(elements,parent)
        
    def flags(self, index):
        if  index.column() == self.ColumnID.Color:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        elif  index.column() == self.ColumnID.Name:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
#         elif index.column() == self.ColumnID.Fix:
#             return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        elif index.column() == self.ColumnID.Text:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        
        elif  index.column() == self.ColumnID.Fix:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
#           
        elif  index.column() == self.ColumnID.Delete:
            if self._allowRemove:
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable
            else:
                return Qt.NoItemFlags
    
    def removeRow(self, position, parent=QModelIndex()):
        
        print position,self._elements
        self.boxRemoved.emit(position)
        return super(BoxListModel,self).removeRow(position, parent=parent)
    
    def data(self, index, role):
        if role == Qt.DisplayRole and index.column() == self.ColumnID.Text:
            row = index.row()
            value = self._elements[row]
            return value.density
        
        if role == Qt.DisplayRole and index.column() == self.ColumnID.Fix:
            row = index.row()
            value = self._elements[row]
            return value.fixvalue
        
        if role == Qt.DecorationRole and index.column() == self.ColumnID.Color:
            row = index.row()
            value = self._elements[row]
            pixmap = QPixmap(_NPIXELS, _NPIXELS)
            pixmap.fill(value.color())
            icon = QIcon(pixmap)
            return icon
        
        
        return super(BoxListModel,self).data(index, role)
    
    def setData(self, index, value, role=Qt.EditRole):
        
        if role == Qt.EditRole  and index.column() == self.ColumnID.Color:
            row = index.row()
            color = QColor(value[0])
            if color.isValid():
                self._elements[row].setColor(color)
                self.dataChanged.emit(index, index)
                return True
            
        if index.column()==self.ColumnID.Fix:
            self._elements[index.row()].isFixed=True
            value=float(value.toString())
            row=index.row()
            self._elements[row].fixvalue=QString("%.1f"%value)
            self.dataChanged.emit(index,index)
            return True
            
    def select(self, row):
        self._selectionModel.clear()
        self._selectionModel.select(self.index(row, self.ColumnID.Color),
                                    QItemSelectionModel.Select)        
        self._selectionModel.select(self.index(row, self.ColumnID.Name),
                                    QItemSelectionModel.Select)
        
        
        
