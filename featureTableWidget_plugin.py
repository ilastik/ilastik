from PyQt4.QtDesigner import QPyDesignerCustomWidgetPlugin
from PyQt4.QtGui import QPixmap, QIcon, QColor

from featureTableWidget import FeatureTableWidget, FeatureEntry

class PyFeatureTableWidgetPlugin(QPyDesignerCustomWidgetPlugin):

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
        t = FeatureTableWidget(parent)
        t.createTableForFeatureDlg( \
            {"Color": [FeatureEntry("Banana")],
             "Edge": [FeatureEntry("Mango"),
                      FeatureEntry("Cherry")] \
            }, \
            [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0] \
        )
        return t
    
    def name(self):
        return "FeatureTableWidget"

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
               '<widget class="FeatureTableWidget" name=\"featureTableWidget\">\n'
               "</widget>\n"
               )
    
    def includeFile(self):
        return "tableWidget"
 
