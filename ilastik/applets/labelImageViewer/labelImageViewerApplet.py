from ilastik.applets.layerViewer import LayerViewerApplet
from opLabelImageViewer import OpLabelImageViewer

class LabelImageViewerApplet( LayerViewerApplet ):
    """
    Viewer applet for prediction probabilities produced via headless or cluster mode.
    """
    def __init__( self, workflow ):
        super(LayerViewerApplet, self).__init__("Label Image Viewer", workflow)
        self._deserializers = []

    @property
    def singleLaneOperatorClass(self):
        return OpLabelImageViewer
    
    @property
    def singleLaneGuiClass(self):
        from labelImageViewerGui import LabelImageViewerGui
        return LabelImageViewerGui

    @property
    def broadcastingSlots(self):
        return []
    
    @property
    def dataSerializers(self):
        return self._deserializers
