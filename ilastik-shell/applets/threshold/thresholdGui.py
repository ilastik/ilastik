from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL, QObject
from PyQt4.QtGui import *
from PyQt4 import uic

from volumina.api import ArraySource, LazyflowSource, GrayscaleLayer, RGBALayer, ColortableLayer, \
                         AlphaModulatedLayer, LayerStackModel, VolumeEditor, LazyflowSinkSource

from lazyflow.graph import MultiInputSlot, MultiOutputSlot
from lazyflow.operators import OpSingleChannelSelector, OpMultiArraySlicer2

from functools import partial
import os
import utility # This is the ilastik shell utility module
import numpy
from utility import bind

from applets.genericViewer import GenericViewerGui
from volumina.widgets.thresholdingWidget import ThresholdingWidget

class ThresholdGui(GenericViewerGui):
    """
    """
    
    def __init__(self, mainOperator):
        """
        
        """
        super(ThresholdGui, self).__init__(mainOperator.OutputLayers)
        self.mainOperator = mainOperator
    
    def initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
        
        layout = QVBoxLayout( self )
        layout.setSpacing(0)
        self._drawer.setLayout( layout )

        thresholdWidget = ThresholdingWidget(self)
        thresholdWidget.valueChanged.connect( self.handleThresholdGuiValuesChanged )
        layout.addWidget( thresholdWidget )
        
        def enableDrawerControls(enabled):
            pass

        # Expose the enable function with the name the shell expects
        self._drawer.enableControls = enableDrawerControls
    
    def handleThresholdGuiValuesChanged(self, minVal, maxVal):
        self.mainOperator.MinValue.setValue(minVal)
        self.mainOperator.MaxValue.setValue(maxVal)
        self.editor.scheduleSlicesRedraw()

    def getAppletDrawerUi(self):
        return self._drawer
    
