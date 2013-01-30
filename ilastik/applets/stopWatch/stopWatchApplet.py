from ilastik.applets.base.standardApplet import StandardApplet
from lazyflow.graph import Operator

class OpNoOp( Operator ):
    pass

class StopWatchApplet( StandardApplet ):
    """
    This is a simple thresholding applet
    """
    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(StopWatchApplet, self).__init__(guiName, workflow)
        self._serializableItems = [ ] #ThresholdMaskingSerializer(self.topLevelOperator, projectFileGroupName) ]
        
    @property
    def singleLaneOperatorClass(self):
        return OpNoOp

    @property
    def broadcastingSlots(self):
        return []
    
    @property
    def singleLaneGuiClass(self):
        from stopWatchGui import StopWatchGui
        return StopWatchGui

    @property
    def dataSerializers(self):
        return self._serializableItems
