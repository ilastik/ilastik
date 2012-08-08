from PyQt4.QtGui import QWidget, QColor, QVBoxLayout
from PyQt4 import uic

import os

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
        return self.volumeEditorWidget

    def appletDrawers( self ):
        return [ ("Object Extraction", self._drawer ) ]

    def menus( self ):
        return []

    def viewerControlWidget( self ):
        return self._viewerControlWidget

    def setImageIndex( self, imageIndex ):
        print "setImageIndex not implemented"

    def reset( self ):
        print "reset(): not implemented"

    ###########################################
    ###########################################
    
    def __init__(self, mainOperator):
        """
        """
        super(ObjectExtractionGui, self).__init__()
        self.mainOperator = mainOperator
        self.layerstack = LayerStackModel()

        #self.rawsrc = LazyflowSource( self.mainOperator.RawData )
        #layerraw = GrayscaleLayer( self.rawsrc )
        #layerraw.name = "Raw"
        #self.layerstack.append( layerraw )


        self.objectssrc = LazyflowSource( self.mainOperator.LabelImage )
        ct = colortables.create_default_8bit()
        ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        layer = ColortableLayer( self.objectssrc, ct )
        layer.name = "Objects"
        self.layerstack.append(layer)

        self._viewerControlWidget = None
        self._initViewerControlUi()

        self.editor = None
        self._initEditor()

        self._initAppletDrawerUi()

        #self.editor.dataShape = self.mainOperator.RawData.meta.shape

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

    def _initViewerControlUi( self ):
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        self._viewerControlWidget = uic.loadUi(p+"viewerControls.ui")








