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
import os
from PyQt4.QtGui import QColorDialog, QVBoxLayout, QPushButton, QDialog,\
    QColor, QWidget
from PyQt4.QtCore import Qt
from PyQt4 import uic
from labelListModel import LabelListModel, Label
from listView import ListView


class SubModelListView(ListView):

    def __init__(self, parent = None):
        super(SubModelListView, self).__init__(parent=parent)
        
        #self._colorDialog = ColorDialog(self)
        
        self.resetEmptyMessage("No Sub-Models defined.")

        print ",,,,,,,,,,,,,,,,,,,,> __init__ SubModelListView"
    
    #def tableViewCellDoubleClicked(self, modelIndex):
        #if modelIndex.column() == self.model.ColumnID.Color:
        #    self._colorDialog.setBrushColor(self._table.model()[modelIndex.row()].brushColor())
        #    self._colorDialog.setPmapColor (self._table.model()[modelIndex.row()].pmapColor())
        #    self._colorDialog.exec_()
        #    #print "brush color = {}".format(self._colorDialog.brushColor().name())
        #    #print "pmap color  = {}".format(self._colorDialog.pmapColor().name())
        #    self._table.model().setData(modelIndex, (self._colorDialog.brushColor(),
        #                                      self._colorDialog.pmapColor ()))
    
    #def tableViewCellClicked(self, modelIndex):
        #if (modelIndex.column() == self.model.ColumnID.Delete and
        #    not self._table.model().flags(modelIndex) == Qt.NoItemFlags):
        #    self._table.model().removeRow(modelIndex.row())
