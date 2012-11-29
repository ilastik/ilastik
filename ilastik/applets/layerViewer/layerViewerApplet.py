from ilastik.applets.base.applet import StandardApplet
from opLayerViewer import OpLayerViewer

class LayerViewerApplet( StandardApplet ):
    """
    This applet can be used as a simple viewer of raw image data.  
    Its main purpose is to provide a simple example of how to use the LayerViewerGui, 
    which is intended to be used as a base class for most other applet GUIs.
    """
    def __init__( self, workflow ):
        super(LayerViewerApplet, self).__init__("layer Viewer", workflow)
        self._serializableItems = []

    @property
    def singleLaneOperatorClass(self):
        return OpLayerViewer
    
    @property
    def singleLaneGuiClass(self):
        from layerViewerGui import LayerViewerGui
        return LayerViewerGui

    @property
    def broadcastingSlots(self):
        return []
    
    @property
    def dataSerializers(self):
        return self._serializableItems
