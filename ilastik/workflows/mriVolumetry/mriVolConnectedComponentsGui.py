import os

from PyQt4 import uic
from PyQt4.QtCore import Qt, QEvent
from PyQt4.QtGui import QColor

from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

class MriVolConnectedComponentsGui ( LayerViewerGui ):

    def __init__(self, *args, **kwargs):
        super( MriVolConnectedComponentsGui, self ).__init__(*args, **kwargs)

    def initAppletDrawerUi(self):
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/cc_drawer.ui")

        self._drawer.applyButton.clicked.connect( self._onApplyButtonClicked )

        ## syncronize slider and spinbox
        self._drawer.slider.valueChanged.connect( self._slider_value_changed )
        self._drawer.thresSpinBox.valueChanged.connect( \
                                                self._spinbox_value_changed )

    def _onApplyButtonClicked(self):
        print 'button pressed'


    def _updateOperatorFromGui(self):
        op = self.topLevelOperatorView
        thres = self._drawer.thresSpinBox.value()
        op.Threshold.setValue(thres)

    def _slider_value_changed(self, value):
        self._drawer.thresSpinBox.setValue(value)

    def _spinbox_value_changed(self, value):
        self._drawer.slider.setValue(value)
