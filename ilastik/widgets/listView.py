import os
from PyQt4.QtGui import QTableView, \
    QAbstractItemView, \
    QHeaderView,  QStackedWidget, \
    QLabel, QSizePolicy
from PyQt4.QtCore import Qt, QString

#===============================================================================
# Common base class that can be used by the labelListView and the boxListView
#===============================================================================

class ListView(QStackedWidget):
    PAGE_EMPTY    = 0 
    PAGE_LISTVIEW = 1

    def __init__(self, parent = None):
        
        super(ListView, self).__init__(parent=parent)
        
        self.emptyMessage = QLabel("no elements defined yet")
        self.emptyMessage.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter )
        self.emptyMessage.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.addWidget(self.emptyMessage)
        
        self._table = QTableView()
        self.addWidget(self._table)
        self._table.clicked.connect(self.tableViewCellClicked)
        self._table.doubleClicked.connect(self.tableViewCellDoubleClicked)
        self._table.verticalHeader().sectionMoved.connect(self.rowMovedTest)
        self._table.setShowGrid(False)
    
    def resetEmptyMessage(self,pystring):
        self.emptyMessage.setText(QString(pystring))

    def tableViewCellClicked(self, modelIndex):
        '''
        Reimplemt this function to get interaction when double click
        :param modelIndex:
        '''
        
#         if (modelIndex.column() == self.model.ColumnID.Delete and
#             not self._table.model().flags(modelIndex) == Qt.NoItemFlags):
#             self._table.model().removeRow(modelIndex.row())
#     
    def tableViewCellDoubleClicked(self, modelIndex):
        '''
        Reimplement this function to get interaction when single click
        :param modelIndex:
        '''
#         if modelIndex.column() == self.model.ColumnID.Color:
#             self._colorDialog.setBrushColor(self._table.model()[modelIndex.row()].brushColor())
#             self._colorDialog.setPmapColor (self._table.model()[modelIndex.row()].pmapColor())
#             self._colorDialog.exec_()
#             #print "brush color = {}".format(self._colorDialog.brushColor().name())
#             #print "pmap color  = {}".format(self._colorDialog.pmapColor().name())
#             self._table.model().setData(modelIndex, (self._colorDialog.brushColor(),
#                                               self._colorDialog.pmapColor ()))

    def rowMovedTest(self, logicalIndex, oldVisualIndex, newVisualIndex):
        print "{} {} {}".format(logicalIndex, oldVisualIndex, newVisualIndex)

    def _setListViewLook(self):
        table = self._table
        #table.setDragEnabled(True)
        table.setAcceptDrops(True)
        table.setFocusPolicy(Qt.NoFocus)
        table.setShowGrid(False)
        table.horizontalHeader().hide()
        table.verticalHeader().hide()
        #table.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)
        
        
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
        if self.parent()!=None: self.parent().updateGeometry()

    def setModel(self, model):
        QTableView.setModel(self._table, model)
        self._table.setSelectionModel(model._selectionModel)
        
        if model.rowCount() > 0:
            self.setCurrentIndex(self.PAGE_LISTVIEW)
        else:
            self.setCurrentIndex(self.PAGE_EMPTY)
            
        model.rowsInserted.connect(self._onRowsChanged)
        model.rowsRemoved.connect(self._onRowsChanged)
        self.model=model
        
        self._setListViewLook()
        


    @property
    def allowDelete(self):
        return not self._table.isColumnHidden(self.model.ColumnID.Delete)

    @allowDelete.setter
    def allowDelete(self, allow):
        self._table.setColumnHidden(self.model.ColumnID.Delete, not allow)

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
        shrink the view around the 
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
        