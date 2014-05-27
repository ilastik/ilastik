from PyQt4 import uic
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QDialog, QFileDialog, QListWidgetItem
import os.path

class ExportToKnimeDialog(QDialog):
    
    def __init__(self, rawImageLayer, objectImageLayer, featureTableNames, imagePerObject=True, \
                 imagePerTime = True, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle("Export to Knime")
        ui_class, widget_class = uic.loadUiType(os.path.split(__file__)[0] + "/exportToKnimeDialog.ui")
        self.ui = ui_class()
        self.ui.setupUi(self)
        itemRaw = QListWidgetItem(rawImageLayer.name)
        self.ui.rawList.addItem(itemRaw)
        itemObjects = QListWidgetItem(objectImageLayer.name)
        self.ui.objectList.addItem(itemObjects)
        self.imagePerObject = imagePerObject
        self.imagePerTime = imagePerTime
        #FIXME: assume for now tht the feature table is a dict
        try: 
            for plugin, feature_dict in featureTableNames.iteritems():
                print plugin
                for feature_name in feature_dict.keys():
                    print "adding feature:", feature_name
                    item = QListWidgetItem(feature_name)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(Qt.Unchecked)
                    self.ui.featureList.addItem(item)
                    
        except:
            print "hahaha, doesn't work!"
        
        #self.ui.buttonBox.accepted.connect(self.accept)
        #self.ui.buttonBox.rejected.connect(self.reject)
       