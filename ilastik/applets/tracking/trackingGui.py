from PyQt4.QtGui import QWidget, QColor, QVBoxLayout
from PyQt4 import uic

import os
import math

from ilastik.applets.layerViewer import LayerViewerGui
from volumina.widgets.thresholdingWidget import ThresholdingWidget
from volumina.api import LazyflowSource, GrayscaleLayer, RGBALayer, ConstantSource, \
                         AlphaModulatedLayer, LayerStackModel, VolumeEditor, VolumeEditorWidget, ColortableLayer
import volumina.colortables as colortables


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
        return [ ("Tracking", self._drawer ) ]

    def menus( self ):
        return []

    def viewerControlWidget( self ):
        return self._viewerControlWidget

    def setImageIndex( self, imageIndex ):
        mainOperator = self.mainOperator.innerOperators[imageIndex]

        # self.rawsrc = LazyflowSource( mainOperator.RawData )
        # layerraw = GrayscaleLayer( self.rawsrc )
        # layerraw.name = "Raw"
        # self.layerstack.append( layerraw )

        self.objectssrc = LazyflowSource( mainOperator.LabelImage )
        ct = colortables.create_default_8bit()
        ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        layer = ColortableLayer( self.objectssrc, ct )
        layer.name = "Objects"
        self.layerstack.append(layer)

        self.trackingsrc = LazyflowSource( mainOperator.Output )
        layer = ColortableLayer( self.trackingsrc, ct )
        layer.name = "Tracking"
        self.layerstack.append(layer)

        # self.locpicsrc = LazyflowSource( mainOperator.Locpic )
        # layerlocpic = RGBALayer( red=ConstantSource(255), alpha=self.locpicsrc )
        # layerlocpic.name = "Locpic"
        # self.layerstack.append( layerlocpic )

        if mainOperator.LabelImage.meta.shape:
            self.editor.dataShape = mainOperator.LabelImage.meta.shape
        

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

        # self.rawsrc = LazyflowSource( self.mainOperator.RawData )
        # layerraw = GrayscaleLayer( self.rawsrc )
        # layerraw.name = "Raw"
        # self.layerstack.append( layerraw )


        # self.objectssrc = LazyflowSource( self.mainOperator.LabelImage )
        # ct = colortables.create_default_8bit()
        # ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        # layer = ColortableLayer( self.objectssrc, ct )
        # layer.name = "Objects"
        # self.layerstack.append(layer)

        # self.trackingsrc = LazyflowSource( self.mainOperator.Output )
        # layer = ColortableLayer( self.trackingsrc, ct )
        # layer.name = "Tracking"
        # self.layerstack.append(layer)

        # self.locpicsrc = LazyflowSource( self.mainOperator.Locpic )
        # layerlocpic = RGBALayer( red=ConstantSource(255), alpha=self.locpicsrc )
        # layerlocpic.name = "Locpic"
        # self.layerstack.append( layerlocpic )
                               
        # self.src = LazyflowSource( self.mainOperator.Output )
        # ct = colortables.create_default_8bit()
        # ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        # layer = ColortableLayer( self.src, ct )
        # layer.name = "Tracking"
        # self.layerstack.append(layer)

        self._viewerControlWidget = None
        self._initViewerControlUi()

        self.editor = None
        self._initEditor()

        self._initAppletDrawerUi()
        
        if self.mainOperator.LabelImage.meta.shape:
            self.editor.dataShape = self.mainOperator.LabelImage.meta.shape
        self.mainOperator.LabelImage.notifyMetaChanged( self._onMetaChanged)


    def _onMetaChanged( self, slot ):
        if slot is self.mainOperator.LabelImage:
            if slot.meta.shape:
                print slot.meta.shape
                self.editor.dataShape = slot.meta.shape

    def _initEditor(self):
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
        model.canMoveSelectedUp.connect(self._viewerControlWidget.UpButton.setEnabled)
        model.canMoveSelectedDown.connect(self._viewerControlWidget.DownButton.setEnabled)
        model.canDeleteSelected.connect(self._viewerControlWidget.DeleteButton.setEnabled)     

        # Connect our layer movement buttons to the appropriate layerstack actions
        self._viewerControlWidget.layerWidget.init(model)
        self._viewerControlWidget.UpButton.clicked.connect(model.moveSelectedUp)
        self._viewerControlWidget.DownButton.clicked.connect(model.moveSelectedDown)
        self._viewerControlWidget.DeleteButton.clicked.connect(model.deleteSelected)

        self.editor._lastImageViewFocus = 0

            
    def _initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")

        self._drawer.TrackButton.pressed.connect(self._onTrackButtonPressed)
        #     thresholdWidget = ThresholdingWidget(self)
            #thresholdWidget.valueChanged.connect( self.handleThresholdGuiValuesChanged )
        #      layout.addWidget( thresholdWidget )
            
            # def updateDrawerFromOperator():
            #     minValue, maxValue = (0,255)

            #     if self.mainOperator.MinValue.ready():
            #         minValue = self.mainOperator.MinValue.value
            #     if self.mainOperator.MaxValue.ready():
            #         maxValue = self.mainOperator.MaxValue.value

            #     thresholdWidget.setValue(minValue, maxValue)                
                
            # self.mainOperator.MinValue.notifyDirty( bind(updateDrawerFromOperator) )
            # self.mainOperator.MaxValue.notifyDirty( bind(updateDrawerFromOperator) )

    def _initViewerControlUi( self ):
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        self._viewerControlWidget = uic.loadUi(p+"viewerControls.ui")

    def _onTrackButtonPressed( self ):
        app = self._drawer.appSpinBox.value()
        dis = self._drawer.disSpinBox.value()
        opp = self._drawer.oppSpinBox.value()
        noiserate = self._drawer.noiseRateSpinBox.value()
        noiseweight = self._drawer.noiseWeightSpinBox.value()
        epGap = self._drawer.epGapSpinBox.value()

        det = noiseweight*(-1)*math.log(1-noiserate)
        mdet = noiseweight*(-1)*math.log(noiserate)
        self.mainOperator.track(app=app,
                                dis=dis,
                                opp=opp,
                                det=det,
                                mdet=mdet,
                                ep_gap=epGap)
                
    def handleThresholdGuiValuesChanged(self, minVal, maxVal):
        with Tracer(traceLogger):
            self.mainOperator.MinValue.setValue(minVal)
            self.mainOperator.MaxValue.setValue(maxVal)
    
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














