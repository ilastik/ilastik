from ilastik.applets.base.standardApplet import StandardApplet

from opThresholdTwoLevels import OpThresholdTwoLevels
from thresholdTwoLevelsSerializer import ThresholdTwoLevelsSerializer

class ThresholdTwoLevelsApplet( StandardApplet ):
    """
    This is a simple thresholding applet
    """
    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(self.__class__, self).__init__( guiName, workflow )
        self._serializableItems = [ ThresholdTwoLevelsSerializer(self.topLevelOperator, projectFileGroupName) ]
        
    @property
    def singleLaneOperatorClass(self):
        return OpThresholdTwoLevels

    @property
    def broadcastingSlots(self):
        return [ 'MinSize',
                 'MaxSize',
                 'HighThreshold',
                 'LowThreshold',
                 'SmootherSigma',
                 'CurOperator',
                 'SingleThreshold',
                 'Channel' ]
    
    @property
    def singleLaneGuiClass(self):
        from thresholdTwoLevelsGui import ThresholdTwoLevelsGui
        return ThresholdTwoLevelsGui

    @property
    def dataSerializers(self):
        return self._serializableItems
