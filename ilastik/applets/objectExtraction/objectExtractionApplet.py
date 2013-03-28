from ilastik.applets.base.standardApplet import StandardApplet
from ilastik.applets.objectExtraction.opObjectExtraction import OpObjectExtraction
from ilastik.applets.objectExtraction.objectExtractionSerializer import ObjectExtractionSerializer

class ObjectExtractionApplet( StandardApplet ):
    def __init__( self, name="Object Extraction", workflow=None, projectFileGroupName="ObjectExtraction" ):
        super(ObjectExtractionApplet, self).__init__( name=name, workflow=workflow )
        self._serializableItems = [ ObjectExtractionSerializer(self.topLevelOperator, projectFileGroupName) ]

    @property
    def singleLaneOperatorClass( self ):
        return OpObjectExtraction

    @property
    def broadcastingSlots( self ):
        return []

    @property
    def singleLaneGuiClass( self ):
        from ilastik.applets.objectExtraction.objectExtractionGui import ObjectExtractionGui
        return ObjectExtractionGui

    @property
    def dataSerializers(self):
        return self._serializableItems
