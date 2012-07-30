from PyQt4.QtGui import QWidget
from PyQt4 import uic

import os

from ilastik.applets.layerViewer import LayerViewerGui
from volumina.widgets.thresholdingWidget import ThresholdingWidget
from volumina.api import LazyflowSource, GrayscaleLayer, RGBALayer, \
                         AlphaModulatedLayer, LayerStackModel, VolumeEditor, VolumeEditorWidget


import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)
from lazyflow.tracer import Tracer

from ilastik.utility import bind

class TrackingGui( QWidget ):
    """
    """
    
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    def centralWidget( self ):
        return self.volumeEditorWidget

    def appletDrawers( self ):
        return [ ("Tracking", QWidget() ) ]

    def menus( self ):
        return []

    def viewerControlWidget( self ):
        return QWidget()

    def setImageIndex( self, imageIndex ):
        print "tracking.setImageIndex not implemented"

    def reset( self ):
        print "TrackinGui.reset(): not implemented"

    ###########################################
    ###########################################
    
    def __init__(self, mainOperator):
        """
        """
        super(TrackingGui, self).__init__()
        self.mainOperator = mainOperator
        self.layerstack = LayerStackModel()
        self.editor = None
        self.initEditor()

        src = LazyflowSource( self.mainOperator.Output )
        layer = GrayscaleLayer( src )
        self.layerstack.append(layer)

    def initEditor(self):
        """
        Initialize the Volume Editor GUI.
        """

        self.editor = VolumeEditor(self.layerstack)

        #self.editor.newImageView2DFocus.connect(self.setIconToViewMenu)
        #self.editor.setInteractionMode( 'navigation' )
        self.volumeEditorWidget = VolumeEditorWidget()
        self.volumeEditorWidget.init(self.editor)

        # The editor's layerstack is in charge of which layer movement buttons are enabled
        model = self.editor.layerStack

        # if self.__viewerControlWidget is not None:
        #     model.canMoveSelectedUp.connect(self.__viewerControlWidget.UpButton.setEnabled)
        #     model.canMoveSelectedDown.connect(self.__viewerControlWidget.DownButton.setEnabled)
        #     model.canDeleteSelected.connect(self.__viewerControlWidget.DeleteButton.setEnabled)     

        #     # Connect our layer movement buttons to the appropriate layerstack actions
        #     self.__viewerControlWidget.layerWidget.init(model)
        #     self.__viewerControlWidget.UpButton.clicked.connect(model.moveSelectedUp)
        #     self.__viewerControlWidget.DownButton.clicked.connect(model.moveSelectedDown)
        #     self.__viewerControlWidget.DeleteButton.clicked.connect(model.deleteSelected)

        self.editor._lastImageViewFocus = 0

            
    def initAppletDrawerUi(self):
        with Tracer(traceLogger):
            # Load the ui file (find it in our own directory)
            localDir = os.path.split(__file__)[0]
            self._drawer = uic.loadUi(localDir+"/drawer.ui")
            
            layout = QVBoxLayout( self )
            layout.setSpacing(0)
            self._drawer.setLayout( layout )
    
            thresholdWidget = ThresholdingWidget(self)
            #thresholdWidget.valueChanged.connect( self.handleThresholdGuiValuesChanged )
            layout.addWidget( thresholdWidget )
            
            # def updateDrawerFromOperator():
            #     minValue, maxValue = (0,255)

            #     if self.mainOperator.MinValue.ready():
            #         minValue = self.mainOperator.MinValue.value
            #     if self.mainOperator.MaxValue.ready():
            #         maxValue = self.mainOperator.MaxValue.value

            #     thresholdWidget.setValue(minValue, maxValue)                
                
            # self.mainOperator.MinValue.notifyDirty( bind(updateDrawerFromOperator) )
            # self.mainOperator.MaxValue.notifyDirty( bind(updateDrawerFromOperator) )
                
    def handleThresholdGuiValuesChanged(self, minVal, maxVal):
        with Tracer(traceLogger):
            self.mainOperator.MinValue.setValue(minVal)
            self.mainOperator.MaxValue.setValue(maxVal)
    
    def getAppletDrawerUi(self):
        return self._drawer
    
    def setupLayers(self, currentImageIndex):
        print "tracking: setupLayers"
        with Tracer(traceLogger):
            layers = []
    
            # Show the thresholded data
            outputImageSlot = self.mainOperator.Output
            if outputImageSlot.ready():
                outputLayer = self.createStandardLayerFromSlot( outputImageSlot )
                outputLayer.name = "min <= x <= max"
                outputLayer.visible = True                
                outputLayer.opacity = 1.0
                layers.append(outputLayer)
            
            # # Show the  data
            # invertedOutputSlot = self.mainOperator.InvertedOutput[ currentImageIndex ]
            # if invertedOutputSlot.ready():
            #     invertedLayer = self.createStandardLayerFromSlot( invertedOutputSlot )
            #     invertedLayer.name = "(x < min) U (x > max)"
            #     invertedLayer.visible = True
            #     invertedLayer.opacity = 0.25
            #     layers.append(invertedLayer)
            
            # # Show the raw input data
            # inputImageSlot = self.mainOperator.InputImage[ currentImageIndex ]
            # if inputImageSlot.ready():
            #     inputLayer = self.createStandardLayerFromSlot( inputImageSlot )
            #     inputLayer.name = "Raw Input"
            #     inputLayer.visible = True
            #     inputLayer.opacity = 1.0
            #     layers.append(inputLayer)
    
            return layers














