from ilastik.applets.base.standardApplet import StandardApplet
from opSplitBodyPostprocessing import OpSplitBodyPostprocessing
from splitBodyPostprocessingSerializer import SplitBodyPostprocessingSerializer

class SplitBodyPostprocessingApplet( StandardApplet ):
    def __init__( self, workflow ):
        super(SplitBodyPostprocessingApplet, self).__init__("Split-body post-processing", workflow)

        self._serializer = SplitBodyPostprocessingSerializer( self.topLevelOperator, "split-body-postprocessing" )

    @property
    def singleLaneOperatorClass(self):
        return OpSplitBodyPostprocessing
    
    @property
    def singleLaneGuiClass(self):
        from splitBodyPostprocessingGui import SplitBodyPostprocessingGui
        return SplitBodyPostprocessingGui

    @property
    def broadcastingSlots(self):
        return []
    
    @property
    def dataSerializers(self):
        return [self._serializer]
