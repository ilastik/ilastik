from PyQt4.QtGui import QWidget, QColor, QVBoxLayout, QProgressDialog
from PyQt4 import uic
from PyQt4.QtCore import Qt, QString

from lazyflow.rtype import SubRegion

import os

from ilastik.applets.base.appletGuiInterface import AppletGuiInterface

from volumina.api import LazyflowSource, GrayscaleLayer, RGBALayer, ConstantSource, \
                         AlphaModulatedLayer, LayerStackModel, VolumeEditor, VolumeEditorWidget, ColortableLayer
import volumina.colortables as colortables


import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)
from lazyflow.tracer import Tracer



class ObjectExtractionGui( QWidget ):
    """
    """
   
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################

    def centralWidget( self ):
        """ Return the widget that will be displayed in the main viewer area. """ 
        return self.volumeEditorWidget

    def appletDrawer( self ):
        return self._drawer

    def menus( self ):
        return []

    def viewerControlWidget( self ):
        return self._viewerControlWidget

    def stopAndCleanUp( self ):
        pass

    ###########################################
    ###########################################
    
    def __init__(self, topLevelOperatorView):
        """
        """
        super(ObjectExtractionGui, self).__init__()
        self.mainOperator = topLevelOperatorView
        self.curOp = None
        self.layerstack = LayerStackModel()

        #self.rawsrc = LazyflowSource( self.mainOperator.RawData )
        #layerraw = GrayscaleLayer( self.rawsrc )
        #layerraw.name = "Raw"
        #self.layerstack.append( layerraw )

        self._viewerControlWidget = None
        self._initViewerControlUi()

        self.editor = None
        self._initEditor()

        self._initAppletDrawerUi()
        assert(self.appletDrawer() is not None)
        self._initViewer()

    def _onMetaChanged( self, slot ):
        if slot is self.mainOperator.BinaryImage:
            if slot.meta.shape:
                self.editor.dataShape = slot.meta.shape

    def _initViewer( self ):
        mainOperator = self.mainOperator

        ct = colortables.create_default_8bit()
        self.binaryimagesrc = LazyflowSource( mainOperator.BinaryImage )
        layer = GrayscaleLayer( self.binaryimagesrc, range=(0,1), normalize=(0,1) )
        layer.name = "Binary Image"
        self.layerstack.append(layer)

        ct = colortables.create_default_16bit()
        self.objectssrc = LazyflowSource( mainOperator.LabelImage )
        ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        layer = ColortableLayer( self.objectssrc, ct )
        layer.name = "Label Image"
        layer.opacity = 0.5
        self.layerstack.append(layer)

        self.centerimagesrc = LazyflowSource( mainOperator.ObjectCenterImage )
        layer = RGBALayer( red=ConstantSource(255), alpha=self.centerimagesrc )
        layer.name = "Object Centers"
        self.layerstack.append( layer )

        if mainOperator.BinaryImage.meta.shape:
            self.editor.dataShape = mainOperator.LabelImage.meta.shape
        mainOperator.BinaryImage.notifyMetaChanged( self._onMetaChanged )            
 
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

        self._drawer.labelImageButton.pressed.connect(self._onLabelImageButtonPressed)
        self._drawer.extractObjectsButton.pressed.connect(self._onExtractObjectsButtonPressed)

    def _initViewerControlUi( self ):
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        self._viewerControlWidget = uic.loadUi(p+"viewerControls.ui")

    def _onLabelImageButtonPressed( self ):
        m = self.curOp.LabelImage.meta
        maxt = m.shape[0]
        progress = QProgressDialog("Labelling Binary Image...", "Stop", 0, maxt)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setCancelButtonText(QString())
        progress.forceShow()

        for t in range(maxt):
            progress.setValue(t)
            if progress.wasCanceled():
                break
            else:
                self.curOp.updateLabelImageAt( t )
        progress.setValue(maxt)                
        roi = SubRegion(self.curOp.LabelImage, start=5*(0,), stop=m.shape)
        self.curOp.LabelImage.setDirty(roi)

    def _onExtractObjectsButtonPressed( self ):
        maxt = self.curOp.LabelImage.meta.shape[0]
        progress = QProgressDialog("Extracting objects...", "Stop", 0, maxt)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setCancelButtonText(QString())

        reqs = []
        self.curOp._opRegFeats.fixed = False
        for t in range(maxt):
            reqs.append(self.curOp.RegionFeatures([t]))
            reqs[-1].submit()
        for i, req in enumerate(reqs):
            progress.setValue(i)
            if progress.wasCanceled():
                req.cancel()
            else:
                req.wait()
                
        self.curOp._opRegFeats.fixed = True 
        progress.setValue(maxt)
        self.curOp.ObjectCenterImage.setDirty( SubRegion(self.curOp.ObjectCenterImage))
