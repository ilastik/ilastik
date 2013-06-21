import os
from PyQt4.QtGui import QTableView, QColorDialog, \
    QAbstractItemView, QVBoxLayout, QPushButton, \
    QColor, QWidget, QHeaderView, QDialog, QStackedWidget, \
    QLabel, QSizePolicy,QItemSelectionModel
from PyQt4.QtCore import Qt, QString,QModelIndex
from PyQt4 import uic
from labelListModel import LabelListModel, Label
from listView import ListView



class BoxDialog(QDialog):
    #FIXME:
    #This is an hack to the functionality of the old ColorDialog

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self._color = None
        self._linewidth=None
        
        self._fontcolor=None
        self._fontsize=None
        
        self.ui = uic.loadUi(os.path.join(os.path.split(__file__)[0],
                                          'box_dialog.ui'),
                             self)
        self.ui.colorButton.clicked.connect(self.onColor)
        self.ui.fontColorButton.clicked.connect(self.onFontColor)
        self.ui.spinBoxWidth.valueChanged.connect(self.setLineWidth)
        self.ui.spinFontSize.valueChanged.connect(self.setFontSize)
        
        self._modelIndex=None
        
    def setColor(self, c):
        self._color = c
        self.ui.colorButton.setStyleSheet("background-color: {}".format(c.name()))

    def setFontColor(self,c):
        self._fontcolor = c
        self.ui.fontColorButton.setStyleSheet("background-color: {}".format(c.name()))

    def setLineWidth(self,w):
        self._linewidth = w
        self.ui.spinBoxWidth.setValue(w)
        
    def setFontSize(self,s):
        self._fontsize = s
        self.ui.spinFontSize.setValue(s)
    
    
    def onFontColor(self):
        color=QColorDialog().getColor()
        self.setFontColor(color)
    
    def onColor(self):
        color=QColorDialog().getColor()
        self.setColor(color)
    
    
    def getColor(self):
        return self._color
    
    def getFontSize(self):
        return self._fontsize
    
    def getLineWidth(self):
        return self._linewidth
    
    def getFontColor(self):
        return self._fontcolor
    
    def getModelIndex(self):
        return self._modelIndex
    
    def setModelIndex(self,index):
        self._modelIndex=index
    

    

class BoxListView(ListView):

    def __init__(self, parent = None):
        super(BoxListView, self).__init__(parent=parent)
        
        self.emptyMessage = QLabel("no boxes defined yet")
        self._colorDialog = BoxDialog()
        self._colorDialog.accepted.connect(self.onDialogAccept)
        
        
    def resetEmptyMessage(self,pystring):
        self.emptyMessage.setText(QString(pystring))
        
    
    def tableViewCellDoubleClicked(self, modelIndex):
        if modelIndex.column() == self.model.ColumnID.Color:
            
            print "RESETTING", modelIndex.row(), self._table.model()[modelIndex.row()].linewidth
            
            self._colorDialog.setColor(self._table.model()[modelIndex.row()].color)
            self._colorDialog.setFontColor(self._table.model()[modelIndex.row()].fontcolor)
            self._colorDialog.setLineWidth(self._table.model()[modelIndex.row()].linewidth)
            self._colorDialog.setFontSize(self._table.model()[modelIndex.row()].fontsize)
            self._colorDialog.setModelIndex(modelIndex)
            
            self._colorDialog.exec_()
    
    def setModel(self, model):
        ListView.setModel(self, model)
        self._table.setColumnHidden(self.model.ColumnID.Fix,True)
    
    def onDialogAccept(self):
        prop=(self._colorDialog.getColor(),self._colorDialog.getFontSize(),
                                                     self._colorDialog.getLineWidth(),
                                                     self._colorDialog.getFontColor())
        names=["color","fontsize","linewidth",'fontcolor']
        d=dict(zip(names,prop))
            
        modelIndex=self._colorDialog.getModelIndex()
        self._table.model().setData(modelIndex,d)
            
            
    def tableViewCellClicked(self, modelIndex):
        if (modelIndex.column() == self.model.ColumnID.Delete and
            not self._table.model().flags(modelIndex) == Qt.NoItemFlags):
            self._table.model().removeRow(modelIndex.row())
        
        elif (modelIndex.column() == self.model.ColumnID.FixIcon):
            state=self._table.isColumnHidden(self.model.ColumnID.Fix)
            
            #self._table.setColumnHidden(self.model.ColumnID.Fix, not state)
            self._table.setColumnHidden(self.model.ColumnID.Fix, False)
            #if state:
            index=self.model.index(modelIndex.row(),self.model.ColumnID.Fix)
            self._table.edit(index)
            #self._table.selectionModel().select(index,QItemSelectionModel.ClearAndSelect)
            
            
            
        
    def _setListViewLook(self):
        ListView._setListViewLook(self)
        
        self._table.resizeColumnToContents(self.model.ColumnID.Color)
        self._table.resizeColumnToContents(self.model.ColumnID.Delete)
             
    @property
    def allowDelete(self):
        return not self._table.isColumnHidden(self.model.ColumnID.Delete)

    @allowDelete.setter
    def allowDelete(self, allow):
        self._table.setColumnHidden(self.model.ColumnID.Delete, not allow)
    
    @property
    def allowFixValues(self):
        return not self._table.isColumnHidden(self.model.ColumnID.Fix)

    @allowFixValues.setter
    def allowFixValues(self, allow):
        self._table.setColumnHidden(self.model.ColumnID.Fix, not allow)

    @property
    def allowFixIcon(self):
        return not self._table.isColumnHidden(self.model.ColumnID.FixIcon)

    @allowFixIcon.setter
    def allowFixIcon(self, allow):
        self._table.setColumnHidden(self.model.ColumnID.FixIcon, not allow)

    
if __name__=="__main__":
    from boxListModel import BoxListModel,BoxLabel
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
    model = BoxListModel()

    l = QVBoxLayout()
    w = QWidget(None)
    w.setLayout(l)
    addButton = QPushButton("Add random label")
    l.addWidget(addButton)


    
    def addRandomLabel():
        import numpy as np
        dens=QString("%.1f"%np.random.rand())
        ll= BoxLabel("BoxLabel {}".format(model.rowCount() + 1),
                              QColor(numpy.random.randint(0, 255),
                                     numpy.random.randint(0, 255),
                                     numpy.random.randint(0, 255)),
                     dens
                     )
        model.insertRow(model.rowCount(),ll)
        
        print "added ",ll
        return ll
    
    addButton.clicked.connect(addRandomLabel)
    
    ll=addRandomLabel()
    ll=addRandomLabel()
    ll=addRandomLabel()
    
    
    w.show()
    w.raise_()

    tableView = BoxListView()
    l.addWidget(tableView)
    tableView.setModel(model)
    
    tableView2 = BoxListView()

    tableView2.setModel(model)
    tableView2._table.setShowGrid(True)
    l.addWidget(tableView2)

    ll.density=125
    sys.exit(app.exec_())