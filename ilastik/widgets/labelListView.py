import os
from PyQt4.QtGui import QColorDialog, QVBoxLayout, QPushButton, QDialog,\
    QColor, QWidget
from PyQt4.QtCore import Qt
from PyQt4 import uic
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

    def __init__(self, parent = None):
        super(LabelListView, self).__init__(parent=parent)
        
        self.resetEmptyMessage("no labels defined yet")
        
    
    def tableViewCellDoubleClicked(self, modelIndex):
        if modelIndex.column() == self.model.ColumnID.Color:
            self._colorDialog.setBrushColor(self._table.model()[modelIndex.row()].brushColor())
            self._colorDialog.setPmapColor (self._table.model()[modelIndex.row()].pmapColor())
            self._colorDialog.exec_()
            #print "brush color = {}".format(self._colorDialog.brushColor().name())
            #print "pmap color  = {}".format(self._colorDialog.pmapColor().name())
            self._table.model().setData(modelIndex, (self._colorDialog.brushColor(),
                                              self._colorDialog.pmapColor ()))
    
    def tableViewCellClicked(self, modelIndex):
        if (modelIndex.column() == self.model.ColumnID.Delete and
            not self._table.model().flags(modelIndex) == Qt.NoItemFlags):
            self._table.model().removeRow(modelIndex.row())
        
        

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
