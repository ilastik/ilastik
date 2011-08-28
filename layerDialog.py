from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QDialog

import os

class GrayscaleLayerDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        p = os.path.split(os.path.abspath(__file__))[0]
        uic.loadUi(p+"/designerElements/grayLayerDialog.ui", self)
        self.setLayername("testname")
    def setLayername(self, n):
        self._layerLabel.setText("<b>%s</b>" % n)
    
    #grayChannelThresholdingWidget

class RGBALayerDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        p = os.path.split(os.path.abspath(__file__))[0]
        uic.loadUi(p+"/designerElements/rgbaLayerDialog.ui", self)
        self.setLayername("testname")
    
    def showRedThresholds(self, show):
        self.redChannel.setVisible(show)
    def showGreenThresholds(self, show):
        self.greenChannel.setVisible(show)
    def showBlueThresholds(self, show):
        self.blueChannel.setVisible(show)
    def showAlphaThresholds(self, show):
        self.alphaChannel.setVisible(show)
    
    def setLayername(self, n):
        self._layerLabel.setText("<b>%s</b>" % n)
        
if __name__ == "__main__":
    from PyQt4.QtGui import QApplication
    app = QApplication([])
    l = RGBALayerDialog()
    l.show()
    app.exec_()