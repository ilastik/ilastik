import os
from PyQt4.QtGui import QTableView, QColorDialog, \
    QAbstractItemView, QVBoxLayout, QPushButton, \
    QColor, QWidget, QHeaderView, QDialog, QStackedWidget, \
    QLabel, QSizePolicy
from PyQt4.QtCore import Qt
from PyQt4 import uic
from labelListModel import LabelListModel, Label, ColumnID


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


class LabelListView(QStackedWidget):
    PAGE_EMPTY    = 0 
    PAGE_LISTVIEW = 1

    def __init__(self, parent = None):
        super(LabelListView, self).__init__(parent=parent)
        
        self.emptyMessage = QLabel("no labels defined yet")
        self.emptyMessage.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter )
        self.emptyMessage.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.addWidget(self.emptyMessage)
        
        self._table = QTableView()
        self.addWidget(self._table)
        self._table.clicked.connect(self.tableViewCellClicked)
        self._table.doubleClicked.connect(self.tableViewCellDoubleClicked)
        self._table.verticalHeader().sectionMoved.connect(self.rowMovedTest)
        self._table.setShowGrid(False)
        self._colorDialog = ColorDialog()

    def tableViewCellDoubleClicked(self, modelIndex):
        if modelIndex.column() == ColumnID.Color:
            self._colorDialog.setBrushColor(self._table.model()[modelIndex.row()].brushColor())
            self._colorDialog.setPmapColor (self._table.model()[modelIndex.row()].pmapColor())
            self._colorDialog.exec_()
            #print "brush color = {}".format(self._colorDialog.brushColor().name())
            #print "pmap color  = {}".format(self._colorDialog.pmapColor().name())
            self._table.model().setData(modelIndex, (self._colorDialog.brushColor(),
                                              self._colorDialog.pmapColor ()))

    def rowMovedTest(self, logicalIndex, oldVisualIndex, newVisualIndex):
        print "{} {} {}".format(logicalIndex, oldVisualIndex, newVisualIndex)

    def _setListViewLook(self):
        table = self._table
        table.setDragEnabled(True)
        table.setAcceptDrops(True)
        table.setFocusPolicy(Qt.NoFocus)
        table.setShowGrid(False)
        table.horizontalHeader().hide()
        table.verticalHeader().hide()
        table.resizeColumnToContents(ColumnID.Color)
        table.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        table.resizeColumnToContents(ColumnID.Delete)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
     
    def selectRow(self, *args, **kwargs):
        self._table.selectRow(*args, **kwargs)
        
    def _onRowsChanged(self, parent, start, end):
        model = self._table.model()
        if model and model.rowCount() > 0:
            self.setCurrentIndex(self.PAGE_LISTVIEW)
        else:
            self.setCurrentIndex(self.PAGE_EMPTY)
        self.parent().updateGeometry()

    def setModel(self, model):
        QTableView.setModel(self._table, model)
        self._table.setSelectionModel(model._selectionModel)
        
        if model.rowCount() > 0:
            self.setCurrentIndex(self.PAGE_LISTVIEW)
        else:
            self.setCurrentIndex(self.PAGE_EMPTY)
            
        model.rowsInserted.connect(self._onRowsChanged)
        model.rowsRemoved.connect(self._onRowsChanged)
        
        self._setListViewLook()
        
    def tableViewCellClicked(self, modelIndex):
        if (modelIndex.column() == ColumnID.Delete and
            not self._table.model().flags(modelIndex) == Qt.NoItemFlags):
            self._table.model().removeRow(modelIndex.row())

    @property
    def allowDelete(self):
        return not self._table.isColumnHidden(ColumnID.Delete)

    @allowDelete.setter
    def allowDelete(self, allow):
        self._table.setColumnHidden(ColumnID.Delete, not allow)

    def minimumSizeHint(self):
        #http://www.qtcentre.org/threads/14764-QTableView-sizeHint%28%29-issues
        t = self._table
        vHeader = t.verticalHeader()
        hHeader = t.horizontalHeader()
        doubleFrame = 2 * t.frameWidth()
        w = hHeader.length() + vHeader.width() + doubleFrame;
     
        contentH = 0
        if self._table.model(): 
            for i in range(self._table.model().rowCount()):
                contentH += self._table.rowHeight(i)
        contentH = max(90, contentH) 
        
        h = hHeader.height() + contentH + doubleFrame;
        from PyQt4.QtCore import QSize
        return QSize(w,h)

    def sizeHint(self):
        return self.minimumSizeHint()
    
    def shrinkToMinimum(self):
        """
        shrink the view to the minimum around the 
        labels which are currently there
        """
        t = self._table
        hHeader = t.horizontalHeader()
        doubleFrame = 2 * t.frameWidth()     
        contentH = 0
        if self._table.model(): 
            for i in range(self._table.model().rowCount()):
                contentH += self._table.rowHeight(i)
        h =  contentH+2
        self.setFixedHeight(h)
        
        

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
