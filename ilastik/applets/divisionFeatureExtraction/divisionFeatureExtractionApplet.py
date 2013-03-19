from ilastik.applets.base.standardApplet import StandardApplet
from ilastik.applets.divisionFeatureExtraction.divisionFeatureExtractionSerializer import DivisionFeatureExtractionSerializer
from ilastik.applets.divisionFeatureExtraction.opDivisionFeatureExtraction import OpDivisionFeatureExtraction
from ilastik.applets.divisionFeatureExtraction.divisionFeatureExtractionGui import DivisionFeatureExtractionGui

class DivisionFeatureExtractionApplet( StandardApplet ):
    def __init__( self, name="Division Feature Extraction", workflow=None, projectFileGroupName="DivisionFeatureExtraction" ):
        super(DivisionFeatureExtractionApplet, self).__init__( name=name, workflow=workflow )
        self._serializableItems = [ DivisionFeatureExtractionSerializer(self.topLevelOperator, projectFileGroupName) ]

    @property
    def singleLaneOperatorClass( self ):
        return OpDivisionFeatureExtraction

    @property
    def broadcastingSlots( self ):
        return []

    @property
    def singleLaneGuiClass( self ):
        return DivisionFeatureExtractionGui

    @property
    def dataSerializers(self):
        return self._serializableItems
