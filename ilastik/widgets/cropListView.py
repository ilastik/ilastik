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
# 		   http://ilastik.org/license.html
###############################################################################
import os
from qtpy.QtWidgets import QColorDialog, QVBoxLayout, QPushButton, QDialog, QWidget
from qtpy.QtGui import QColor
from qtpy.QtCore import Qt, Signal, QObject, QModelIndex
from qtpy import uic
from .cropListModel import CropListModel, Crop
from .listView import ListView


class ColorDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self._brushColor = None
        self._pmapColor = None
        self.ui = uic.loadUi(os.path.join(os.path.split(__file__)[0], "color_dialog.ui"), self)
        self.ui.brushColorButton.clicked.connect(self.onBrushColor)
        self.ui.pmapColorButton.clicked.connect(self.onPmapColor)

    def setBrushColor(self, c):
        self._brushColor = c
        self.ui.brushColorButton.setStyleSheet("background-color: {}".format(c.name()))

    def onBrushColor(self):
        self.setBrushColor(QColorDialog().getColor())

    def brushColor(self):
        return self._brushColor

    def setPmapColor(self, c):
        self._pmapColor = c
        self.ui.pmapColorButton.setStyleSheet("background-color: {}".format(c.name()))

    def onPmapColor(self):
        self.setPmapColor(QColorDialog().getColor())

    def pmapColor(self):
        return self._pmapColor


class CropListView(ListView):

    deleteCrop = Signal(int)
    colorsChanged = Signal(QModelIndex)

    def __init__(self, parent=None):
        super(CropListView, self).__init__(parent=parent)

        self._colorDialog = ColorDialog(self)

        self.resetEmptyMessage("No crops defined.")

    @property
    def allowDelete(self):
        return not self._table.isColumnHidden(self.model.ColumnID.Delete)

    @allowDelete.setter
    def allowDelete(self, allow):
        self._table.setColumnHidden(self.model.ColumnID.Delete, not allow)

    def tableViewCellDoubleClicked(self, modelIndex):
        if modelIndex.column() == self.model.ColumnID.Color:
            self._colorDialog.setBrushColor(self._table.model()[modelIndex.row()].brushColor())
            self._colorDialog.setPmapColor(self._table.model()[modelIndex.row()].pmapColor())
            self._colorDialog.exec_()
            self._table.model().setData(modelIndex, (self._colorDialog.brushColor(), self._colorDialog.pmapColor()))
            self.colorsChanged.emit(modelIndex)

    def tableViewCellClicked(self, modelIndex):

        if (
            modelIndex.column() == self.model.ColumnID.Delete
            and not self._table.model().flags(modelIndex) == Qt.NoItemFlags
        ):
            self.deleteCrop.emit(modelIndex.row())
            self._table.model().removeRow(modelIndex.row())
