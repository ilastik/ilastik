from ilastik.applets.base.standardApplet import StandardApplet

from opObjectExtraction import OpObjectExtraction
from objectExtractionGui import ObjectExtractionGui
from objectExtractionSerializer import ObjectExtractionSerializer

class ObjectExtractionApplet( StandardApplet ):
    def __init__( self, name="Object Extraction", workflow=None ):
        super(ObjectExtractionApplet, self).__init__( name=name, workflow=workflow )
        self._serializableItems = [ ObjectExtractionSerializer(self.topLevelOperator, projectFileGroupName) ]

    @property
    def singleLaneOperatorClass( self ):
        return OpObjectExtraction

    @property
    def singleLaneGuiClass( self ):
        return ObjectExtractionGui

    @property
    def dataSerializers(self):
        return self._serializableItems
