from ilastik.applets.base.standardApplet import StandardApplet

from opCostVolumeFilter import OpMriVolPreproc

class MriVolPreprocApplet( StandardApplet ):
    """
    Applet that applies different metods 
    to 'polish' the prediction maps
    """

    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(self.__class__, self).__init__( guiName, workflow )
        # self._serializableItems = [ ThresholdTwoLevelsSerializer(self.topLevelOperator, projectFileGroupName) ]
        
    @property
    def singleLaneOperatorClass(self):
        return OpMriVolPreproc

    @property
    def broadcastingSlots(self):
        return [ 'Sigma', 'Threshold']

    @property
    def singleLaneGuiClass(self):
        from mriVolPreprocGui import MriVolPreprocGui
        return MriVolPreprocGui
