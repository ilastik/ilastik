from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor

from lazyflow.operators import OpMultiArraySlicer2
from volumina.api import LazyflowSource, AlphaModulatedLayer
from ilastik.utility import bind
from ilastik.applets.layerViewer import LayerViewerGui

from lazyflow.graph import Operator, InputSlot

class OpPredictionViewer( Operator ):

    PredictionProbabilities = InputSlot()
    
    RawImage = InputSlot(optional=True)
    PmapColors = InputSlot(optional=True)
    LabelNames = InputSlot(optional=True)

class PreprocessingViewerGui( LayerViewerGui ):
    
    def __init__(self, *args, **kwargs):
        super(PreprocessingViewerGui, self).__init__(*args, **kwargs)
    
    def setupLayers(self):
        opLane = self.topLevelOperatorView
        rawSlot = opLane.RawData
        layers = []
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot( rawSlot )
            rawLayer.name = "Raw Data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append( rawLayer )
        return layers 
