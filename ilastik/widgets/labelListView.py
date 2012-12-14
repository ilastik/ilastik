from PyQt4.QtGui import QTableView, QColorDialog, QAbstractItemView, QVBoxLayout, QPushButton, QColor, QWidget, \
                        QHeaderView, QSizePolicy
from PyQt4.QtCore import Qt
from labelListModel import LabelListModel, Label

class LabelListView(QTableView):

    class ColumnID():
        Color = 0
        Name = 1
        Delete = 2
      
    def __init__(self, parent = None):
        QTableView.__init__(self, parent)
        self.clicked.connect(self.tableViewCellClicked)
        self.doubleClicked.connect(self.tableViewCellDoubleClicked)
        self.verticalHeader().sectionMoved.connect(self.rowMovedTest)
        self.setShowGrid(False)
        
    def tableViewCellDoubleClicked(self, modelIndex):
        if modelIndex.column() == LabelListView.ColumnID.Color:
            color = QColorDialog().getColor()
            self.model().setData(modelIndex, color)
        
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
