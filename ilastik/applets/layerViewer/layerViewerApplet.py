from lazyflow.graph import OperatorWrapper
from ilastik.applets.base.applet import Applet
from opLayerViewer import OpLayerViewer

class LayerViewerApplet( Applet ):
    """
    This applet can be used as a simple viewer of raw image data.  
    Its main purpose is to provide a simple example of how to use the LayerViewerGui, 
    which is intended to be used as a base class for most other applet GUIs.
    """
    def __init__( self, workflow ):
        super(LayerViewerApplet, self).__init__("layer Viewer")

        self._topLevelOperator = OperatorWrapper( OpLayerViewer, parent=workflow, promotedSlotNames=set(['RawInput']) )
        self._topLevelOperator.name = "LayerViewer Top-Level Operator"
        self._preferencesManager = None
        self._serializableItems = []
        self._gui = None
    
    @property    
    def gui(self):
        if self._gui is None:
            from layerViewerGui import LayerViewerGui            
            self._gui = LayerViewerGui( self.topLevelOperator )
        return self._gui

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def topLevelOperator(self):
        return self._topLevelOperator
    
    @property
    def appletPreferencesManager(self):
        return self._preferencesManager
    