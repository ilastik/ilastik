import os
from PyQt4.QtGui import QTableView, QColorDialog, \
    QAbstractItemView, QVBoxLayout, QPushButton, \
    QColor, QWidget, QHeaderView, QDialog, QStackedWidget, \
    QLabel, QSizePolicy
from PyQt4.QtCore import Qt, QString
from PyQt4 import uic
from labelListModel import LabelListModel, Label
from listView import ListView


class BoxDialog(QDialog):
    #FIXME:
    #This is an hack to the functionality of the old ColorDialog
    
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self._color = None
        self.ui = uic.loadUi(os.path.join(os.path.split(__file__)[0],
                                          'box_dialog.ui'),
                             self)
        self.ui.colorButton.clicked.connect(self.onColor)

    def setColor(self, c):
        self._color = c
        self.ui.colorButton.setStyleSheet("background-color: {}".format(c.name()))

    def onColor(self):
        color=QColorDialog().getColor()
        self.setColor(color)
        
    def brushColor(self):
        return self._color
    
    def pmapColor(self):
        return self._color
    

class BoxListView(ListView):

    def __init__(self, parent = None):
        super(BoxListView, self).__init__(parent=parent)
        
        self.emptyMessage = QLabel("no labels defined yet")
        self._colorDialog = BoxDialog()
    
    def resetEmptyMessage(self,pystring):
        self.emptyMessage.setText(QString(pystring))
        
    
    def tableViewCellDoubleClicked(self, modelIndex):
        if modelIndex.column() == self.model.ColumnID.Color:
            self._colorDialog.setColor(self._table.model()[modelIndex.row()].color())
            self._colorDialog.exec_()
            self._table.model().setData(modelIndex, (self._colorDialog.brushColor(),
                                              self._colorDialog.pmapColor ()))
            
    def tableViewCellClicked(self, modelIndex):
        if (modelIndex.column() == self.model.ColumnID.Delete and
            not self._table.model().flags(modelIndex) == Qt.NoItemFlags):
            self._table.model().removeRow(modelIndex.row())

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