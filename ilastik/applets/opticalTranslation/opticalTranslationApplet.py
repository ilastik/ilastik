from ilastik.applets.base.standardApplet import StandardApplet

from ilastik.applets.opticalTranslation.opOpticalTranslation import OpOpticalTranslation

class OpticalTranslationApplet( StandardApplet ):    
    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(self.__class__, self).__init__( guiName, workflow )
#        self._serializableItems = [ ThresholdTwoLevelsSerializer(self.topLevelOperator, projectFileGroupName) ]
        
    @property
    def singleLaneOperatorClass(self):
        return OpOpticalTranslation

    @property
    def broadcastingSlots(self):
        return [ ]
    
    @property
    def singleLaneGuiClass(self):
        from opticalTranslationGui import OpticalTranslationGui
        return OpticalTranslationGui

    @property
    def dataSerializers(self):
        return self._serializableItems
