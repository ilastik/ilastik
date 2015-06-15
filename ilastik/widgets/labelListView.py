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
from functools import partial

from PyQt4 import uic
from PyQt4.QtCore import Qt, pyqtSignal
from PyQt4.QtGui import QColorDialog, QVBoxLayout, QPushButton, QDialog, \
                        QColor, QWidget, QMenu

from labelListModel import LabelListModel, Label
from listView import ListView


class ColorDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self._brushColor = None
        self._pmapColor  = None
        self.ui = uic.loadUi(os.path.join(os.path.split(__file__)[0],
                                          'color_dialog.ui'),
                             self)
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


class LabelListView(ListView):
    mergeRequested = pyqtSignal( int, str, int, str ) # from_row, from_name, to_row, to_name

    def __init__(self, parent = None):
        super(LabelListView, self).__init__(parent=parent)
        self.support_merges = False        
        self._colorDialog = ColorDialog(self)        
        self.resetEmptyMessage("no labels defined yet")

    def tableViewCellDoubleClicked(self, modelIndex):
        if modelIndex.column() == self.model.ColumnID.Color:
            self._colorDialog.setBrushColor(self._table.model()[modelIndex.row()].brushColor())
            self._colorDialog.setPmapColor (self._table.model()[modelIndex.row()].pmapColor())
            self._colorDialog.exec_()
            #print "brush color = {}".format(self._colorDialog.brushColor().name())
            self.model.setData(modelIndex, (self._colorDialog.brushColor(),
            #print "pmap color  = {}".format(self._colorDialog.pmapColor().name())
                                              self._colorDialog.pmapColor ()))
    
    def tableViewCellClicked(self, modelIndex):
        if (modelIndex.column() == self.model.ColumnID.Delete and
            not self.model.flags(modelIndex) == Qt.NoItemFlags):
            self.model.removeRow(modelIndex.row())
        

    def contextMenuEvent(self, event):
        if not self.support_merges or not self.allowDelete:
            return

        from_index = self._table.indexAt(event.pos())
        if not (0 <= from_index.row() < self.model.rowCount()):
            return

        from_name = self.model.data(from_index, Qt.DisplayRole)
        menu = QMenu(parent=self)
        for to_row in range(self.model.rowCount()):
            to_index = self.model.index(to_row, LabelListModel.ColumnID.Name)
            to_name = self.model.data(to_index, Qt.DisplayRole)
            action = menu.addAction( "Merge {} into {}".format( from_name, to_name ),
                                     partial( self.mergeRequested.emit, from_index.row(), str(from_name),
                                                                        to_row,           str(to_name)) )
            if to_row == from_index.row():
                action.setEnabled(False)

        menu.exec_( self.mapToGlobal(event.pos()) )

if __name__ == '__main__':
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
    model = LabelListModel()

    l = QVBoxLayout()
    w = QWidget(None)
    w.setLayout(l)
    addButton = QPushButton("Add random label\n note: \n the first added is permanent")
    l.addWidget(addButton)
    
    def addRandomLabel():
        model.insertRow(model.rowCount(),
                        Label("Label {}".format(model.rowCount() + 1),
                              QColor(numpy.random.randint(0, 255),
                                     numpy.random.randint(0, 255),
                                     numpy.random.randint(0, 255))))
    
    addButton.clicked.connect(addRandomLabel)
    
    model.makeRowPermanent(0)
    
    w.show()
    w.raise_()

    tableView = LabelListView()
    l.addWidget(tableView)
    tableView.setModel(model)

    tableView2 = LabelListView()
    tableView2.setModel(model)
    tableView2._table.setShowGrid(True)
    l.addWidget(tableView2)
    

    sys.exit(app.exec_())
