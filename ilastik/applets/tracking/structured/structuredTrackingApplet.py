from ilastik.applets.base.standardApplet import StandardApplet
from ilastik.applets.tracking.structured.opStructuredTracking import OpStructuredTracking
from ilastik.applets.tracking.structured.structuredTrackingSerializer import StructuredTrackingSerializer


class StructuredTrackingApplet( StandardApplet ):
    def __init__( self, name="Tracking", workflow=None, projectFileGroupName="StructuredTracking" ):
        super(StructuredTrackingApplet, self).__init__( name=name, workflow=workflow )
        self._serializableItems = [ StructuredTrackingSerializer(self.topLevelOperator, projectFileGroupName) ]
        self.busy = False

    @property
    def singleLaneOperatorClass( self ):
        return OpStructuredTracking

    @property
    def broadcastingSlots( self ):
        return []

    @property
    def singleLaneGuiClass( self ):
        from ilastik.applets.tracking.structured.structuredTrackingGui import StructuredTrackingGui
        return StructuredTrackingGui

    @property
    def dataSerializers(self):
        return self._serializableItems
