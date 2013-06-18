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
    pmapColorChanged = pyqtSignal(QColor)
    nameChanged  = pyqtSignal(object)
    densityChanged = pyqtSignal(object)
    isFixedChanged = pyqtSignal(bool)
    
    def __init__(self, name, color, density=0.0, parent = None, pmapColor=None):
        QObject.__init__(self, parent)
        self._name       = name
        self._density    = density
        self._brushColor = color
        if pmapColor is None:
            self._pmapColor = color
        else:
            self._pmapColor = pmapColor
            
        self._fixvalue=self._density # a fixed box should have this set to a particular value
        self._isFixed=False
        
        self.densityChanged.connect(self._update_fixvalue_display)
    
    def _update_fixvalue_display(self):
        if not self._isFixed:
            self.fixvalue=self.density
            self.changed.emit()
    
    def brushColor(self):
        return self._brushColor

    def setBrushColor(self, c):
        if self._brushColor != c:
            logger.debug("BoxLabel '{}' has new brush color {}".format(
                self._brushColor, c))
            self._brushColor = c
            self.colorChanged.emit(c)

    def pmapColor(self):
        return self._pmapColor

    def setPmapColor(self, c):
        if self._pmapColor != c:
            logger.debug("BoxLabel '{}' has new pmapColor {}".format(
                self._pmapColor, c))
            self._pmapColor = c
            self.pmapColorChanged.emit(c)

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
            self.name, self._brushColor)




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
        
        
        return LabelListModel.data(self, index, role)
    
    def setData(self, index, value, role=Qt.EditRole):
        
#         if index.colum()==self.CoulmunID.Text:
#             row=index.row()
#             self._labels[row].density=QString("%.1f"%value)
#             self.dataChanged.emit(index,index)
        
        if index.column()==self.ColumnID.Fix:
            self._labels[index.row()].isFixed=True
            value=float(value.toString())
            row=index.row()
            self._labels[row].fixvalue=QString("%.1f"%value)
            self.dataChanged.emit(index,index)        
        return LabelListModel.setData(self, index, value, role=role)    
#     def selectedRow(self):
#         return LabelListModel.selectedRow(self)

    

class BoxDialog(QDialog):
    #FIXME:
    #This is an hack to the functionality of the old ColorDialog
    
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self._brushColor = None
        self._pmapColor  = None
        self.ui = uic.loadUi(os.path.join(os.path.split(__file__)[0],
                                          'box_dialog.ui'),
                             self)
        self.ui.brushColorButton.clicked.connect(self.onBrushColor)

    def setBrushColor(self, c):
        self._brushColor = c
        self.ui.brushColorButton.setStyleSheet("background-color: {}".format(c.name()))

    def onBrushColor(self):
        color=QColorDialog().getColor()
        self.setBrushColor(color)
        self.setPmapColor(color)
        
    def brushColor(self):
        return self._brushColor

    def setPmapColor(self, c):
        self._pmapColor = c
        #self.ui.pmapColorButton.setStyleSheet("background-color: {}".format(c.name()))

    def pmapColor(self):
        return self._pmapColor
    

if __name__=="__main__":
    from labelListView import *
    import numpy
    import sys
    from PyQt4.QtGui import QApplication

    app = QApplication(sys.argv)

    red   = QColor(255,0,0)
    green = QColor(0,255,0)
    blue  = QColor(0,0,255)
    #model = LabelListModel([Label("Label 1", red),
    #                        Label("Label 2", green),
    #                        Label("Label 3", blue)])
    model = BoxListModel()

    l = QVBoxLayout()
    w = QWidget(None)
    w.setLayout(l)
    addButton = QPushButton("Add random label")
    l.addWidget(addButton)


    
    def addRandomLabel():
        import numpy as np
        dens=QString("%.1f"%np.random.rand())
        ll= BoxLabel("BoxLabel {}".format(model.rowCount() + 1),
                              QColor(numpy.random.randint(0, 255),
                                     numpy.random.randint(0, 255),
                                     numpy.random.randint(0, 255)),
                     dens
                     )
        model.insertRow(model.rowCount(),ll)
        
        print "added ",ll
        return ll
    addButton.clicked.connect(addRandomLabel)
    
    ll=addRandomLabel()
    ll=addRandomLabel()
    ll=addRandomLabel()
    
    
    w.show()
    w.raise_()

    tableView = LabelListView()
    tableView._colorDialog=BoxDialog()
    l.addWidget(tableView)
    tableView.setModel(model)
    
    tableView2 = LabelListView()

    tableView2.setModel(model)
    tableView2._table.setShowGrid(True)
    l.addWidget(tableView2)

    ll.density=125
    sys.exit(app.exec_())
