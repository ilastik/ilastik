from PyQt4.QtDesigner import QPyDesignerCustomWidgetPlugin
from PyQt4.QtGui import QPixmap, QIcon, QColor

from overlayTreeWidget import OverlayTreeWidget, OverlayEntry

class PyOverlayTreeWidgetPlugin(QPyDesignerCustomWidgetPlugin):

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
        o = OverlayTreeWidget(parent)
        a = OverlayEntry("Labels")
        b = OverlayEntry("Raw Data")
        p0 = OverlayEntry("Probability")
        o.addOverlaysToTreeWidget({"Classification/Labels": a, "Classification/Probability 0": p0, "Raw Data": b}, [], [], True)
    
        return o
    
    def name(self):
        return "OverlayTreeWidget"

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
               '<widget class="OverlayTreeWidget" name=\"overlayTreeWidget\">\n'
               "</widget>\n"
               )
    
    def includeFile(self):
        return "overlayTreeWidget"
 
