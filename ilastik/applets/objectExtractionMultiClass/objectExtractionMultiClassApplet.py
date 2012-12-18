from ilastik.applets.base.standardApplet import StandardApplet
from ilastik.applets.objectExtractionMultiClass.opObjectExtractionMultiClass import OpObjectExtractionMultiClass
from ilastik.applets.objectExtractionMultiClass.objectExtractionMultiClassSerializer import ObjectExtractionMultiClassSerializer
from ilastik.applets.objectExtractionMultiClass.objectExtractionMultiClassGui import ObjectExtractionMultiClassGui

class ObjectExtractionMultiClassApplet( StandardApplet ):
    def __init__( self, name="Object Extraction Multi-Class", workflow=None, projectFileGroupName="ObjectExtractionMultiClass" ):
        super(ObjectExtractionMultiClassApplet, self).__init__( name=name, workflow=workflow )
        self._serializableItems = [ ObjectExtractionMultiClassSerializer(self.topLevelOperator, projectFileGroupName) ]

    @property
    def singleLaneOperatorClass( self ):
        return OpObjectExtractionMultiClass

    @property
    def broadcastingSlots( self ):
        return []

    @property
    def singleLaneGuiClass( self ):
        return ObjectExtractionMultiClassGui

    @property
    def dataSerializers(self):
        return self._serializableItems