import os
from PyQt4.QtGui import QTableView, QColorDialog, QAbstractItemView, QVBoxLayout, QPushButton, QColor, QWidget, \
                        QHeaderView, QDialog
from PyQt4.QtCore import Qt
from PyQt4 import uic
from labelListModel import LabelListModel, Label

class ColorDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self._brushColor = None
        self._pmapColor  = None
        self.ui = uic.loadUi(os.path.split(__file__)[0] + '/color_dialog.ui', self)
        self.ui.brushColorButton.clicked.connect(self.onBrushColor)
        self.ui.pmapColorButton.clicked.connect(self.onPmapColor)
        
    def setBrushColor(self, c):
        self._brushColor = c
        self.ui.brushColorButton.setStyleSheet("background-color: "+c.name())
    def onBrushColor(self):
        self.setBrushColor(QColorDialog().getColor())
    def brushColor(self):
        return self._brushColor
        
    def setPmapColor(self, c):
        self._pmapColor = c
        self.ui.pmapColorButton.setStyleSheet("background-color: "+c.name())
    def onPmapColor(self):
        self.setPmapColor(QColorDialog().getColor())
    def pmapColor(self):
        return self._pmapColor

class LabelListView(QTableView):

    class ColumnID():
        Color  = 0
        Name   = 1
        Delete = 2
      
    def __init__(self, parent = None):
        QTableView.__init__(self, parent)
        self.clicked.connect(self.tableViewCellClicked)
        self.doubleClicked.connect(self.tableViewCellDoubleClicked)
        self.verticalHeader().sectionMoved.connect(self.rowMovedTest)
        self.setShowGrid(False)
        
        self._colorDialog = ColorDialog() 
        
    def tableViewCellDoubleClicked(self, modelIndex):
        if modelIndex.column() == LabelListView.ColumnID.Color:
            self._colorDialog.setBrushColor( self.model()[modelIndex.row()].brushColor() )
            self._colorDialog.setPmapColor ( self.model()[modelIndex.row()].pmapColor()  )
            self._colorDialog.exec_()
            
            print "brush color = ", self._colorDialog.brushColor().name()
            print "pmap color  = ", self._colorDialog.pmapColor().name()
            
            self.model().setData(modelIndex, (self._colorDialog.brushColor(),
                                              self._colorDialog.pmapColor ()) )
        
    def rowMovedTest(self, logicalIndex, oldVisualIndex, newVisualIndex):
        print logicalIndex, " ", oldVisualIndex, " ", newVisualIndex
        
    def _setListViewLook(self):
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setShowGrid(False)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.resizeColumnToContents(LabelListView.ColumnID.Color)
        self.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        self.resizeColumnToContents(LabelListView.ColumnID.Delete)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
    
    def setModel(self, model):
        QTableView.setModel(self, model)
        self.setSelectionModel(model._selectionModel)
        self._setListViewLook()
            
    def tableViewCellClicked(self, modelIndex):
        if modelIndex.column() == LabelListView.ColumnID.Delete and not self.model().flags(modelIndex) == Qt.NoItemFlags:
            self.model().removeRow(modelIndex.row())
    
    @property
    def allowDelete(self):
        return not self.isColumnHidden(LabelListView.ColumnID.Delete)
    
    @allowDelete.setter
    def allowDelete(self, allow):
        self.setColumnHidden(LabelListView.ColumnID.Delete, not allow)
        
    def minimumSizeHint(self):
        #http://www.qtcentre.org/threads/14764-QTableView-sizeHint%28%29-issues
        vHeader = self.verticalHeader()
        hHeader = self.horizontalHeader()    
        doubleFrame = 2*self.frameWidth()
        w = hHeader.length() + vHeader.width() + doubleFrame;
        h = vHeader.length() + hHeader.height() + doubleFrame;
        from PyQt4.QtCore import QSize
        return QSize(w,h)
    def sizeHint(self):
        return self.minimumSizeHint()

if __name__ == '__main__':
    import numpy
    import sys
    from PyQt4.QtGui import QApplication
    
    app = QApplication(sys.argv)

    red   = QColor(255,0,0)
    green = QColor(0,255,0)
    blue  = QColor(0,0,255)
    model = LabelListModel([Label("Label 1", red), Label("Label 2", green), Label("Label 3", blue)])

    l = QVBoxLayout()
    w = QWidget(None)
    w.setLayout(l)
    addButton = QPushButton("Add random label")
    l.addWidget(addButton)
    
    def addRandomLabel():
        model.insertRow(model.rowCount(), Label("Label %d" % (model.rowCount() + 1), QColor(numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255))))
    addButton.clicked.connect(addRandomLabel)
    
    w.show()
    w.raise_()

    tableView = LabelListView()
    l.addWidget(tableView)
    tableView.setModel(model)
    
    tableView2 = LabelListView()
    tableView2.setModel(model)
    tableView2.setShowGrid(True)
    l.addWidget(tableView2)
    
    sys.exit(app.exec_())
