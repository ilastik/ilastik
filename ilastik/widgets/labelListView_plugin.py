from PyQt4.QtDesigner import QPyDesignerCustomWidgetPlugin
from PyQt4.QtGui import QPixmap, QIcon, QColor

from ilastik.widgets.labelListView import LabelListView
from ilastik.widgets.labelListModel import Label, LabelListModel

class PyLabelListViewPlugin(QPyDesignerCustomWidgetPlugin):

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
        model = LabelListModel([Label("Label 1", red), Label("Label 2", green), Label("Label 3", blue)])
        
        a=LabelListView(parent)
        a.setModel(model)
        
        return a
    
    def name(self):
        return "LabelListView"

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
               '<widget class="LabelListView" name=\"labelListView\">\n'
               "</widget>\n"
               )
    
    def includeFile(self):
        return "ilastik.widgets.labelListView"
 