from lazyflow.graph import OperatorWrapper
from ilastik.applets.base.applet import Applet
from opLayerViewer import OpLayerViewer

class LayerViewerApplet( Applet ):
    """
    This is a simple viewer applet
    """
    def __init__( self, graph ):
        super(LayerViewerApplet, self).__init__("layer Viewer")

        self._topLevelOperator = OperatorWrapper( OpLayerViewer, graph=graph, promotedSlotNames=set(['RawInput']) )
        self._preferencesManager = None
        self._serializableItems = []
        self._gui = None
    
    @property    
    def gui(self):
        if self._gui is None:
            from layerViewerGui import LayerViewerGui            
            self._gui = LayerViewerGui( [ self.topLevelOperator.RawInput ] )
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
    