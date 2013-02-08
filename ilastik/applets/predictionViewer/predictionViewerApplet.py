from ilastik.applets.layerViewer import LayerViewerApplet
from opPredictionViewer import OpPredictionViewer
from predictionViewerSerializer import PredictionViewerSerializer

class PredictionViewerApplet( LayerViewerApplet ):
    """
    Viewer applet for prediction probabilities produced via headless or cluster mode.
    """
    def __init__( self, workflow ):
        super(LayerViewerApplet, self).__init__("Prediction Viewer", workflow)
        self._deserializers = [ PredictionViewerSerializer( self.topLevelOperator, "PixelClassification" ) ] # FIXME this shouldn't be hard-coded.

    @property
    def singleLaneOperatorClass(self):
        return OpPredictionViewer
    
    @property
    def singleLaneGuiClass(self):
        from predictionViewerGui import PredictionViewerGui
        return PredictionViewerGui

    @property
    def broadcastingSlots(self):
        return []
    
    @property
    def dataSerializers(self):
        return self._deserializers
