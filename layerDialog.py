from PyQt4 import uic

from PyQt4.QtGui import QDialog

class LayerDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        uic.loadUi("designerElements/layerDialog.ui", self)
        self.setRange(0,255)
        self.setLayername("testname")
                    
        self._minSlider.valueChanged.connect(self._onMinSliderMoved)
        self._maxSlider.valueChanged.connect(self._onMaxSliderMoved)
    
    def _onMinSliderMoved(self, v):
        if v >= self._maxSlider.value():
            if v < self._maxSlider.maximum():
                self._maxSlider.setValue(v+1)
            else:
                self._minSlider.setValue(v-1)
    
    def _onMaxSliderMoved(self, v):
        if v <= self._minSlider.value():
            if self._minSlider.value() >= 1:
                self._minSlider.setValue(v-1)
            else:
                self._maxSlider.setValue(1)
    
    def setLayername(self, n):
        self._layerLabel.setText("Layer <b>%s</b>" % n)
        
    def setRange(self, minimum, maximum):
        self._minSlider.setRange(minimum, maximum)
        self._minSpin.setRange(minimum, maximum)
        self._maxSlider.setRange(minimum, maximum)
        self._maxSpin.setRange(minimum, maximum)
        self._minSpin.setSuffix("/%d" % maximum)
        self._maxSpin.setSuffix("/%d" % maximum)
        self._minSlider.setValue(minimum)
        self._maxSlider.setValue(maximum)
        self._minSpin.setValue(minimum)
        self._maxSpin.setValue(maximum)
        
if __name__ == "__main__":
    from PyQt4.QtGui import QApplication
    app = QApplication([])
    l = LayerDialog()
    l.show()
    app.exec_()