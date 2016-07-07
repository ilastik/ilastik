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
from PyQt4.QtGui import QColor, QPixmap, QIcon, QItemSelectionModel, QImage
from PyQt4.QtCore import Qt, pyqtSignal, QModelIndex
from listModel import ListModel,ListElement,_NPIXELS

import logging
logger = logging.getLogger(__name__)

class Crop(ListElement):
    changed      = pyqtSignal()
    colorChanged = pyqtSignal(QColor)
    pmapColorChanged = pyqtSignal(QColor)
    roi_4dChanged = pyqtSignal()

    def __init__(self, name, roi_4d, color, parent = None, pmapColor=None):
        ListElement.__init__(self, name,parent)
        self._brushColor = color
        if pmapColor is None:
            self._pmapColor = color
        else:
            self._pmapColor = pmapColor

        self._roi_4d = roi_4d

    def roi_4d(self):
        return self._roi_4d

    def setRoi_4d(self, roi_4d):
        if self._roi_4d != roi_4d:
            logger.debug("Crop '{}' has new RoI {}".format(
                self._roi_4d, roi_4d))
            self._roi_4d = roi_4d
            self.roi_4dChanged.emit()

    def brushColor(self):
        return self._brushColor

    def setBrushColor(self, c):
        if self._brushColor != c:
            logger.debug("Crop '{}' has new brush color {}".format(
                self._brushColor, c))
            self._brushColor = c
            self.colorChanged.emit(c)

    def pmapColor(self):
        return self._pmapColor

    def setPmapColor(self, c):
        if self._pmapColor != c:
            logger.debug("Crop '{}' has new pmapColor {}".format(
                self._pmapColor, c))
            self._pmapColor = c
            self.pmapColorChanged.emit(c)
            
    def __repr__(self):
        return "<Crop name={}, color={}>".format(
            self.name, self._brushColor)

class CropListModel(ListModel):
    cropSelected = pyqtSignal(int)
    
    icon_cache = {}
        
    class ColumnID():
        Color  = 0
        Name   = 1
        Delete = 2

        ncols=3
    
    def __init__(self, crops=None, parent=None):
        ListModel.__init__(self,crops, parent)


        self._crops=self._elements
        self.elementSelected.connect(self.cropSelected.emit)
        

    def __len__(self):
        return len(self._crops)

    def __getitem__(self, i):
        return self._crops[i]

    def rowCount(self, parent=None):
        return len(self._elements)

    def removeRow(self, position, parent=QModelIndex()):
        if position in self.unremovable_rows:
            return False

        if self.rowCount() <= 1:
            return False

        self.beginRemoveRows(parent, position, position)
        value = self._elements[position]
        logger.debug("removing row: " + str(value))
        self._elements.remove(value)
        self.endRemoveRows()
        return True

    def data(self, index, role):
        if role == Qt.EditRole and index.column() == self.ColumnID.Color:
            return (self._elements[index.row()].brushColor(),
                    self._elements[index.row()].pmapColor())

        elif role == Qt.ToolTipRole and index.column() == self.ColumnID.Color:
            return ("Hex code : {}\nDouble click to change".format(
                self._elements[index.row()].brushColor().name()))


        elif role == Qt.DecorationRole and index.column() == self.ColumnID.Color:
            row = index.row()
            return self.createIconForCrop(row)
        
        else:
            return ListModel.data(self,index,role)
    
    
    def createIconForCrop(self, row):
        value = self._elements[row]
        a = value.brushColor().rgba()
        b = value.pmapColor().rgba()
        try:
            # Return a cached icon if we already generated one.
             return CropListModel.icon_cache[(a,b)]
        except KeyError:
            if a == b:
                pixmap = QPixmap(_NPIXELS, _NPIXELS)
                pixmap.fill(value.brushColor())
            else:
                img = QImage(_NPIXELS,_NPIXELS, QImage.Format_RGB32)
                for i in range(_NPIXELS):
                    for j in range(0, _NPIXELS - i):
                        img.setPixel(i, j, a)
                for i in range(_NPIXELS):
                    for j in range(_NPIXELS - i, _NPIXELS):
                        img.setPixel(i, j, b)
                pixmap = QPixmap.fromImage(img)
            icon = QIcon(pixmap)
            # Cache this icon so we don't have to make it again
            CropListModel.icon_cache[(a,b)] = icon
            return icon
    
    def flags(self, index):
        if  index.column() == self.ColumnID.Color:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return ListModel.flags(self, index)
        
    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole  and index.column() == self.ColumnID.Color:
            row = index.row()
            brushColor = QColor(value[0])
            pmapColor = QColor(value[1])
            if brushColor.isValid() and pmapColor.isValid():
                logger.debug("setData: brushColor = {}, pmapColor = {}"
                             "".format(brushColor.name(), pmapColor.name()))
                logger.debug("  self._elements[row] has type {}"
                             "".format(type(self._elements[row])))
                self._elements[row].setBrushColor(brushColor)
                self._elements[row].setPmapColor(pmapColor)
                logger.debug("  self._elements[row].brushColor = {}"
                             "".format(self._elements[row].brushColor().name()))
                logger.debug("  self._elements[row].pmapColor  = {}"
                             "".format(self._elements[row].pmapColor().name()))
                self.dataChanged.emit(index, index)
                return True

        else:
            return ListModel.setData(self, index, value, role)
        
    def select(self, row):
        self._selectionModel.clear()
        self._selectionModel.select(self.index(row, self.ColumnID.Color),
                                    QItemSelectionModel.Select)
        self._selectionModel.select(self.index(row, self.ColumnID.Name),
                                    QItemSelectionModel.Select)


