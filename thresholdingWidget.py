from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QWidget

from os import path

class ThresholdingWidget(QWidget):
    rangeChanged = pyqtSignal(int, int)
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
            
        p = path.split(__file__)[0]
        
        uic.loadUi(p+"/designerElements/thresholdingWidget.ui", self)
        self.setRange(0,255)
                    
        self._minSlider.valueChanged.connect(self._onMinSliderMoved)
        self._maxSlider.valueChanged.connect(self._onMaxSliderMoved)
    
    def _onMinSliderMoved(self, v):
        #FIXME: assumes lower bound is 0
        if v >= self._maxSlider.value():
            if v < self._maxSlider.maximum():
                self._maxSlider.setValue(v+1)
            else:
                self._minSlider.setValue(v-1)
        self.rangeChanged.emit(self._minSlider.value(), self._maxSlider.value())
    
    def _onMaxSliderMoved(self, v):
        #FIXME: assumes lower bound is 0
        if v <= self._minSlider.value():
            if self._minSlider.value() >= 1:
                self._minSlider.setValue(v-1)
            else:
                self._maxSlider.setValue(1)
        self.rangeChanged.emit(self._minSlider.value(), self._maxSlider.value())
    
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