from PyQt4.QtGui import QColor, QPixmap, QIcon, QItemSelectionModel, QPainter, QPen, QImage, QDialog,QColorDialog
from PyQt4.QtCore import QObject, QAbstractTableModel, Qt, QModelIndex, pyqtSignal,QString
from labelListModel import *
import logging
from PyQt4.uic.Compiler.qtproxies import QtGui
from PyQt4 import uic
import os
logger = logging.getLogger(__name__)

#===============================================================================
# Implements the functionality for the dynamic boxes of the counting applet
# This model is fully compatible with the labelListView
#===============================================================================

class BoxLabel(QObject):
    changed      = pyqtSignal()
    colorChanged = pyqtSignal(QColor)
    nameChanged  = pyqtSignal(object)
    densityChanged = pyqtSignal(object)
    isFixedChanged = pyqtSignal(bool)
    
    def __init__(self, name, color, density=0.0, parent = None):
        QObject.__init__(self, parent)
        self._name       = name
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
    def name(self):
        return self._name
    

    @name.setter
    def name(self, n):
        if self._name != n:
            logger.debug("BoxLabel '{}' has new name '{}'".format(
                self._name, n))
            self._name = n
            self.nameChanged.emit(n)

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




_NPIXELS = 26
_XSTART = 8


class BoxListModel(LabelListModel):
    boxRemoved = pyqtSignal(int)
    
    class ColumnID():
        Color  = 0
        Name   = 1
        Text   = 2
        Fix    = 3
        Delete = 4
        
        ncols=5
        
    
    def __init__(self, labels=None, parent=None):
        LabelListModel.__init__(self,labels,parent)
        
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
    
    def select(self, row):
        LabelListModel.select(self, row)
    
    def columnCount(self,parent):
        return self.ColumnID.ncols
    
    def removeRow(self, position, parent=QModelIndex()):
        self.boxRemoved.emit(position)
        return LabelListModel.removeRow(self, position, parent=parent)
    
    def data(self, index, role):
        if role == Qt.DisplayRole and index.column() == self.ColumnID.Text:
            row = index.row()
            value = self._labels[row]
            return value.density
        
        if role == Qt.DisplayRole and index.column() == self.ColumnID.Fix:
            row = index.row()
            value = self._labels[row]
            return value.fixvalue
        
        if role == Qt.DecorationRole and index.column() == self.ColumnID.Color:
            row = index.row()
            value = self._labels[row]
            pixmap = QPixmap(_NPIXELS, _NPIXELS)
            pixmap.fill(value.color())
            icon = QIcon(pixmap)
            return icon
        
        
        return LabelListModel.data(self, index, role)
    
    def setData(self, index, value, role=Qt.EditRole):
        
        if role == Qt.EditRole  and index.column() == self.ColumnID.Color:
            row = index.row()
            color = QColor(value[0])
            if color.isValid():
                self._labels[row].setColor(color)
                self.dataChanged.emit(index, index)
                return True
            
        if index.column()==self.ColumnID.Fix:
            self._labels[index.row()].isFixed=True
            value=float(value.toString())
            row=index.row()
            self._labels[row].fixvalue=QString("%.1f"%value)
            self.dataChanged.emit(index,index)        
