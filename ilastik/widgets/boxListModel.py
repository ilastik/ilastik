from __future__ import absolute_import
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
from PyQt5 import uic
from PyQt5.QtGui import QColor, QPixmap, QIcon, QPainter, QPen, QImage
from PyQt5.QtWidgets import QDialog, QColorDialog, QGraphicsTextItem
from PyQt5.QtCore import QObject, QAbstractTableModel, Qt, QModelIndex, pyqtSignal, QItemSelectionModel
from .listModel import ListModel, ListElement, _NPIXELS
#from labelListModel import LabelListModel
import logging
import os
logger = logging.getLogger(__name__)

#===============================================================================
# Implements the functionality for the dynamic boxes of the counting applet
# This model is fully compatible with the labelListView
#===============================================================================


class BoxLabel(ListElement):
    changed      = pyqtSignal()
    existenceChanged = pyqtSignal()
    densityChanged = pyqtSignal(object)
    isFixedChanged = pyqtSignal(bool)

    colorChanged = pyqtSignal(QColor)
    fontSizeChanged =pyqtSignal(int)
    lineWidthChanged = pyqtSignal(int)
    fontColorChanged = pyqtSignal(QColor)




    def __init__(self, name, color, density=0.0, fontsize=12, linewidth=2, fontcolor=QColor(255,255,255), parent = None):
        ListElement.__init__(self, name, parent)
        self._density    = density
        self._color = color

        self._fontsize=fontsize
        self._linewidth=linewidth
        self._fontcolor=fontcolor



        self._fixvalue=self._density # a fixed box should have this set to a particular value
        self._isFixed=False
        self._register_signals()


    def _register_signals(self):
        #self.colorChanged.connect(self.changed.emit)
        #self.nameChanged.connect(self.changed.emit)
        #self.densityChanged.connect(self.changed.emit)
        #self.isFixedChanged.connect(self.changed.emit)



        self.densityChanged.connect(self._update_fixvalue_display)


    def _update_fixvalue_display(self):
        if not self._isFixed:
            self.fixvalue=self.density
            self.changed.emit()

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, c):
        if self._color != c:
            logger.debug("BoxLabel '{}' has new brush color {}".format(
                self._color, c))
            self._color = c
            self.colorChanged.emit(c)

    @property
    def fontsize(self):
        return self._fontsize
    @fontsize.setter
    def fontsize(self, n):
        if self._fontsize != n:
            logger.debug("BoxLabel '{}' has new density '{}'".format(
                self._fontsize, n))
            self._fontsize = n
            self.fontSizeChanged.emit(n)
            self.changed.emit()

    @property
    def linewidth(self):
        return self._linewidth
    @linewidth.setter
    def linewidth(self, n):
        if self._linewidth != n:
            logger.debug("BoxLabel '{}' has new density '{}'".format(
                self._linewidth, n))
            self._linewidth = n
            self.lineWidthChanged.emit(n)
            self.changed.emit()



    @property
    def fontcolor(self):
        return self._fontcolor

    @fontcolor.setter
    def fontcolor(self, n):
        if self._fontcolor != n:
            logger.debug("BoxLabel '{}' has new density '{}'".format(
                self._fontcolor, n))
            self._fontcolor = n
            self.fontColorChanged.emit(n)
            self.changed.emit()


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
            self.isFixedChanged.emit(self._isFixed)
            #self.changed.emit()


    @property
    def isFixed(self):
        return self._isFixed
    @isFixed.setter
    def isFixed(self, bool):
#         if self._density != n:
#             logger.debug("BoxLabel '{}' has new density '{}'".format(
#                 self._density, n))
            self._isFixed = bool
            #self.changed.emit()
            #self.isFixedChanged.emit(self._isFixed)
    def __repr__(self):
        return "<BoxLabel name={}, color={}>".format(
            self.name, self._color)







class BoxListModel(ListModel):
    boxRemoved = pyqtSignal(int)
    signalSaveAllBoxesToCSV = pyqtSignal(str)

    class ColumnID(object):
        Color   = 0
        Name    = 1
        Text    = 2
        FixIcon = 3
        Fix     = 4

        Delete = 5

        ncols=6


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
        elif  index.column() == self.ColumnID.FixIcon:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        elif  index.column() == self.ColumnID.Delete:
            if self._allowRemove:
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable
            else:
                return Qt.NoItemFlags
        else:
            return Qt.NoItemFlags

    def removeRow(self, position, parent=QModelIndex()):
        self.boxRemoved.emit(position)
        return super(BoxListModel,self).removeRow(position, parent=parent)

    def data(self, index, role):

#
        if role == Qt.BackgroundColorRole and (index.column() == self.ColumnID.Fix or index.column() == self.ColumnID.FixIcon):
            row = index.row()
            value = self._elements[row]
            if value.isFixed:
                color=QColor(Qt.red)

                color.setAlphaF(0.5)
                return color

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
            pixmap.fill(value.color)
            icon = QIcon(pixmap)
            return icon

        if role == Qt.DecorationRole and index.column() == self.ColumnID.FixIcon:
            row = index.row()
            value = self._elements[row]

            pixmap = QPixmap(_NPIXELS,_NPIXELS)

            if value.isFixed:
                iconpath=os.path.join(os.path.split(__file__)[0],
                                      'icons/lock-edit-icon-32.png')
            else:
                iconpath=os.path.join(os.path.split(__file__)[0],
                                      'icons/lock_open-32.png')
            pixmap.load(iconpath)
            icon = QIcon(pixmap)

            return icon



        return super(BoxListModel,self).data(index, role)

    def setData(self, index, value, role=Qt.EditRole):

        if role == Qt.EditRole  and index.column() == self.ColumnID.Color:
            row = index.row()
            color = QColor(value["color"][0])
            colorglobal=value["color"][1]

            fontsize,fontsizeglobal = value["fontsize"]
            linewidth,linewidthglobal = value["linewidth"]

            fontcolor = QColor(value["fontcolor"][0])
            fontcolorglobal = value["fontcolor"][1]



            if color.isValid():
                if not colorglobal:
                    self._elements[row].color=color
                    self.dataChanged.emit(index, index)
                else:
                    for row,el in enumerate(self._elements):
                        el.color=color
                        ind=self.createIndex(row, self.ColumnID.Color, object=0)
                        self.dataChanged.emit(ind, ind)


            if fontcolor.isValid():
                if not fontcolorglobal:
                    self._elements[row].fontcolor=fontcolor
                else:
                    for row,el in enumerate(self._elements):
                        el.fontcolor=fontcolor

            if not linewidthglobal:
                self._elements[row].linewidth=linewidth
            else:
                for row,el in enumerate(self._elements):
                    el.linewidth=linewidth



            if not fontsizeglobal:
                self._elements[row].fontsize=fontsize
            else:
                for row,el in enumerate(self._elements):
                    el.fontsize=fontsize

            return True


        if index.column()==self.ColumnID.Fix:
            try:
                value=float(value)
                self._elements[index.row()].isFixed=True
                row=index.row()
                self._elements[row].fixvalue="%.1f"%value
                self.dataChanged.emit(index,index)
                return True
            except:
                return False



    def select(self, row):
        self._selectionModel.clear()
        self._selectionModel.select(self.index(row, self.ColumnID.Color),
                                    QItemSelectionModel.Select)
        self._selectionModel.select(self.index(row, self.ColumnID.Name),
                                    QItemSelectionModel.Select)



