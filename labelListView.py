from PyQt4.QtGui import QTableView, QColorDialog, QAbstractItemView, QGroupBox, QHBoxLayout, QVBoxLayout, QPushButton, QColor, QWidget
from PyQt4.QtCore import Qt, QSize
from labelListModel import LabelListModel
import sys
        
                             
class Label:
    def __init__(self, name, color):
        self.name = name
        self.color = color  



class LabelListView(QTableView):        
    def __init__(self, parent = None):
        QTableView.__init__(self, parent)
        self.clicked.connect(self.tableViewCellClicked)
        self.doubleClicked.connect(self.tableViewCellDoubleClicked)
        self.verticalHeader().sectionMoved.connect(self.rowMovedTest)
        
    def tableViewCellDoubleClicked(self, modelIndex):
        if modelIndex.column() == 0:
            color = QColorDialog().getColor()
            self.model().setData(modelIndex, color)
        
    def rowMovedTest(self, logicalIndex, oldVisualIndex, newVisualIndex):
        print logicalIndex, " ", oldVisualIndex, " ", newVisualIndex
        
    def _setListViewLook(self):
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setShowGrid(False)
        self.setColumnWidth(0, 30)
        self.setColumnWidth(2, 30)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setSelectionMode(QAbstractItemView.NoSelection)
    
    def setModel(self, model):
        QTableView.setModel(self, model)
        self._setPushButtonToColumn2(None, 0, model.rowCount())
        model.rowsInserted.connect(self._setPushButtonToColumn2)
        
    def _setPushButtonToColumn2(self, parent, start, end):
        if end == start:
            end+=1
        for row in range(end - start):
            box = QGroupBox()
            box.setContentsMargins(0,0,0,0)
            box.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            box.setFlat(True)
            box.setStyleSheet("QGroupBox {border:0;}")
            layout = QHBoxLayout()
            layout.setContentsMargins(0,0,0,0)
            button = QPushButton()
            button.setFixedSize(QSize(18, 18))
            button.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            button.setFocusPolicy(Qt.NoFocus)
            button.setText("x")
            layout.addWidget(button)
            box.setLayout(layout)
            
            self.setIndexWidget(self.model().index(start+row,2), box)
            print start + row
        self._setListViewLook()
            
    def tableViewCellClicked(self, modelIndex):
        if modelIndex.column() == 2:
            self.model().removeRow(modelIndex.row())
            


if __name__ == '__main__':
    import numpy
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
    l.addWidget(tableView2)
    
    sys.exit(app.exec_())
