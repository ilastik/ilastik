from ilastik.applets.base.standardApplet import StandardApplet
from opticalTranslationGui import OpticalTranslationGui
from ilastik.applets.opticalTranslation.opOpticalTranslation import OpOpticalTranslation
from ilastik.applets.opticalTranslation.opticalTranslationSerializer import OpticalTranslationSerializer

class OpticalTranslationApplet( StandardApplet ):    
    def __init__( self, workflow, name="Optical Translation", projectFileGroupName="OpticalTranslation" ):
        super(OpticalTranslationApplet, self).__init__( name=name, workflow=workflow )
        self._serializableItems = [ OpticalTranslationSerializer(self.topLevelOperator, projectFileGroupName) ]
#        self._serializableItems = [ ]
        
    @property
    def singleLaneOperatorClass(self):
        return OpOpticalTranslation

    @property
    def broadcastingSlots(self):
        return [ ]
    
    @property
    def singleLaneGuiClass(self):
        return OpticalTranslationGui

    @property
    def dataSerializers(self):
        return self._serializableItems
