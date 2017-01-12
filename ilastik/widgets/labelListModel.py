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
from PyQt4.QtCore import Qt, pyqtSignal
from listModel import ListModel,ListElement,_NPIXELS, ListElementWithNumber

#for the LabelListModelWithNumber
from volumina.utility import encode_from_qstring, decode_to_qstring

import logging
logger = logging.getLogger(__name__)

class Label(ListElement):
    changed      = pyqtSignal()
    colorChanged = pyqtSignal(QColor)
    pmapColorChanged = pyqtSignal(QColor)

    def __init__(self, name, color, parent = None, pmapColor=None):
        ListElement.__init__(self, name,parent)
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
            
    def __repr__(self):
        return "<Label name={}, color={}>".format(
            self.name, self._brushColor)


class LabelWithNumber(Label, ListElementWithNumber):
    """
    used in watershedLabelingGui.py
    to see the value/number of the label, with which the label will be drawn
    """
    def __init__(self, number, name, color, parent = None, pmapColor=None):
        #ListElementWithNumber: see widgets->listModel.py
        ListElementWithNumber.__init__(self, number, name, parent)
        self._brushColor = color
        if pmapColor is None:
            self._pmapColor = color
        else:
            self._pmapColor = pmapColor


class LabelListModel(ListModel):
    labelSelected = pyqtSignal(int)
    
    icon_cache = {}
        
    class ColumnID():
        Color  = 0
        Name   = 1
        Delete = 2
        
        ncols=3
    
    def __init__(self, labels=None, parent=None):
        ListModel.__init__(self, labels, parent)


        self._labels = self._elements
        self.elementSelected.connect(self.labelSelected.emit)


    def __len__(self):
        return len(self._labels)

    def __getitem__(self, i):
        return self._labels[i]

    def data(self, index, role):
        if role == Qt.EditRole and index.column() == self.ColumnID.Color:
            return (self._elements[index.row()].brushColor(),
                    self._elements[index.row()].pmapColor())

        elif role == Qt.ToolTipRole and index.column() == self.ColumnID.Color:
            return ("Hex code : {}\nDouble click to change".format(
                self._elements[index.row()].brushColor().name()))


        elif role == Qt.DecorationRole and index.column() == self.ColumnID.Color:
            row = index.row()
            return self.createIconForLabel(row)
        
        else:
            return ListModel.data(self,index,role)
    
    
    def createIconForLabel(self, row):
        value = self._elements[row]
        a = value.brushColor().rgba()
        b = value.pmapColor().rgba()
        try:
            # Return a cached icon if we already generated one.
            return LabelListModel.icon_cache[(a,b)]
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
            LabelListModel.icon_cache[(a,b)] = icon            
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


from PyQt4.QtCore import QModelIndex, pyqtSignal
class LabelListModelWithNumber(LabelListModel, ListModel):
    """ 
    expand the LabelListModel by displaying a number which this label has
    this number could be used for drawing with the value of this number
    """
    labelValueToBeDeleted = pyqtSignal(int)
    class ColumnID():
        Number = 0
        Color  = 1
        Name   = 2
        Delete = 3
        
        ncols  = 4


    def data(self, index, role):
        #handle the case of the Number
        #for everything else, use the Model 'data' of LabelListModel (which uses listModel internally)

        #for hover of the element and see some text
        if role == Qt.ToolTipRole and index.column() == self.ColumnID.Number:
            suffix = self._getToolTipSuffix(index.row())
            s = "value: {}\n".format(
                str(self._elements[index.row()].number))
            return decode_to_qstring(s, 'utf-8')
        #show the data
        elif role == Qt.DisplayRole and index.column() == self.ColumnID.Number:
            #number = str(self._elements[index.row()].number)
            number = self._elements[index.row()].number
            # say how many leading zeros there should be, so that all numbers can see seen, 
            # and not just 1-9, 10-99, and afterwards ... instead of a number
            number = "{:04d}".format(number)
            return decode_to_qstring(number, 'utf-8')
        
        else:
            return LabelListModel.data(self,index,role)

    def flags(self, index):
        if  index.column() == self.ColumnID.Number:
            #return Qt.ItemIsEnabled | Qt.ItemIsSelectable
            return Qt.NoItemFlags
        else:
            return LabelListModel.flags(self, index)



    '''
    '''
    def removeRow(self, position, parent=QModelIndex()):
        """
        reimplemented the removeRow from superclass,
        to emit a signal with the value of the label deleted
        """
        #emit signal with the value of the row, otherwise you can't get this value anymore
        value = self._elements[position].number
        self.labelValueToBeDeleted.emit(value)
        #print value

        super(LabelListModelWithNumber, self).removeRow(position, parent)

