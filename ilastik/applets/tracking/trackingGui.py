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

    def appletDrawer( self ):
        return self._drawer

    def menus( self ):
        return []

    def viewerControlWidget( self ):
        return self._viewerControlWidget

    def stopAndCleanUp( self ):
        pass

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

        self._viewerControlWidget = None
        self._initViewerControlUi()

        self.editor = None
        self._initEditor()

        self._initAppletDrawerUi()
        
        if self.mainOperator.LabelImage.meta.shape:
            self.editor.dataShape = self.mainOperator.LabelImage.meta.shape
        self.mainOperator.LabelImage.notifyMetaChanged( self._onMetaChanged)
        self._initViewer()

    def _onMetaChanged( self, slot ):
        if slot is self.mainOperator.LabelImage:
            if slot.meta.shape:
                print slot.meta.shape
                self.editor.dataShape = slot.meta.shape

                maxt = slot.meta.shape[0]
                self._drawer.from_time.setRange(0,maxt-1)
                self._drawer.from_time.setValue(0)
                self._drawer.to_time.setRange(0,maxt-1)
                self._drawer.to_time.setValue(maxt-1)       

    def _initViewer( self ):
        mainOperator = self.mainOperator

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

        ct[255] = QColor(0,0,0,255).rgba() # misdetections        
        self.trackingsrc = LazyflowSource( mainOperator.Output )
        layer = ColortableLayer( self.trackingsrc, ct )
        layer.name = "Tracking"
        self.layerstack.append(layer)

        if mainOperator.LabelImage.meta.shape:
            self.editor.dataShape = mainOperator.LabelImage.meta.shape

            maxt = mainOperator.LabelImage.meta.shape[0]
            maxx = mainOperator.LabelImage.meta.shape[1]
            maxy = mainOperator.LabelImage.meta.shape[2]
            maxz = mainOperator.LabelImage.meta.shape[3]            
            self._drawer.from_time.setRange(0,maxt-1)
            self._drawer.from_time.setValue(0)
            self._drawer.to_time.setRange(0,maxt-1)
            self._drawer.to_time.setValue(maxt-1)       

            self._drawer.from_x.setRange(0,maxx-1)
            self._drawer.from_x.setValue(0)
            self._drawer.to_x.setRange(0,maxx-1)
            self._drawer.to_x.setValue(maxx-1)       
        
            self._drawer.from_y.setRange(0,maxy-1)
            self._drawer.from_y.setValue(0)
            self._drawer.to_y.setRange(0,maxy-1)
            self._drawer.to_y.setValue(maxy-1)       

            self._drawer.from_z.setRange(0,maxz-1)
            self._drawer.from_z.setValue(0)
            self._drawer.to_z.setRange(0,maxz-1)
            self._drawer.to_z.setValue(maxz-1)       

        ## raw data layer
        self.rawsrc = None
        self.rawsrc = LazyflowSource( self.mainOperator.RawImage )
        layerraw = GrayscaleLayer( self.rawsrc )
        layerraw.name = "Raw"
        self.layerstack.insert( len(self.layerstack), layerraw )

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
        
        from_t = self._drawer.from_time.value()
        to_t = self._drawer.to_time.value()
        from_x = self._drawer.from_x.value()
        to_x = self._drawer.to_x.value()
        from_y = self._drawer.from_y.value()
        to_y = self._drawer.to_y.value()        
        from_z = self._drawer.from_z.value()
        to_z = self._drawer.to_z.value()        
        from_size = self._drawer.from_size.value()
        to_size = self._drawer.to_size.value()        

        self.mainOperator.track(
            time_range = range(from_t, to_t + 1),
            x_range = (from_x, to_x + 1),
            y_range = (from_y, to_y + 1),
            z_range = (from_z, to_z + 1),
            size_range = (from_size, to_size + 1),
            x_scale = self._drawer.x_scale.value(),
            y_scale = self._drawer.y_scale.value(),
            z_scale = self._drawer.z_scale.value(),
                                                  app=app,
                                                  dis=dis,
                                                  opp=opp,
                                                  det=det,
                                                  mdet=mdet,
                                                  ep_gap=epGap)
                
    def handleThresholdGuiValuesChanged(self, minVal, maxVal):
        with Tracer(traceLogger):
            self.mainOperator.MinValue.setValue(minVal)
            self.mainOperator.MaxValue.setValue(maxVal)
    














