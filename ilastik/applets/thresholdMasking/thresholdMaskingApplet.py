from ilastik.applets.base.applet import StandardApplet

from opThresholdMasking import OpThresholdMasking
from thresholdMaskingSerializer import ThresholdMaskingSerializer

class ThresholdMaskingApplet( StandardApplet ):
    """
    This is a simple thresholding applet
    """
    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(ThresholdMaskingApplet, self).__init__(guiName, workflow)
        self._serializableItems = [ ThresholdMaskingSerializer(self.topLevelOperator, projectFileGroupName) ]
        
    @property
    def singleLaneOperatorClass(self):
        return OpThresholdMasking

    @property
    def broadcastingSlots(self):
        return ['MinValue', 'MaxValue']
    
    @property
    def singleLaneGuiClass(self):
        from thresholdMaskingGui import ThresholdMaskingGui
        return ThresholdMaskingGui

    @property
    def dataSerializers(self):
        return self._serializableItems
