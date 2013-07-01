from PyQt4.QtDesigner import QPyDesignerCustomWidgetPlugin
from PyQt4.QtGui import QPixmap, QIcon, QColor

from ilastik.widgets.boxListView import BoxListView
from ilastik.widgets.boxListModel import BoxLabel, BoxListModel

class PyBoxListViewPlugin(QPyDesignerCustomWidgetPlugin):

    def __init__(self, parent = None):
        QPyDesignerCustomWidgetPlugin.__init__(self)
        self.initialized = False
        
    def initialize(self, core):
        if self.initialized:
            return
        self.initialized = True

    def isInitialized(self):
        return self.initialized
    
    def createWidget(self, parent):
        red   = QColor(255,0,0)
        green = QColor(0,255,0)
        blue  = QColor(0,0,255)
        model = BoxListModel()
        model.insertRow(model.rowCount(),BoxLabel("Box 1", red))
        model.insertRow(model.rowCount(),BoxLabel("Box 1", green))
        model.insertRow(model.rowCount(),BoxLabel("Box 1", blue))
        a=BoxListView(parent)
        a.setModel(model)
        return a
    
    def name(self):
        return "BoxListView"

    def group(self):
        return "ilastik widgets"
    
    def icon(self):
        return QIcon(QPixmap(16,16))
                           
    def toolTip(self):
        return ""
    
    def whatsThis(self):
        return ""
    
    def isContainer(self):
        return False
    
    def domXml(self):
        return (
               '<widget class="BoxListView" name=\"boxListView\">\n'
               "</widget>\n"
               )
    
    def includeFile(self):
        return "ilastik.widgets.boxListView"
 