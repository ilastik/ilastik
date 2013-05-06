from ilastik.applets.base.standardApplet import StandardApplet
from ilastik.applets.tracking.chaingraph.opChaingraphTracking import OpChaingraphTracking
from ilastik.applets.tracking.chaingraph.chaingraphTrackingGui import ChaingraphTrackingGui
from ilastik.applets.tracking.base.trackingSerializer import TrackingSerializer

class ChaingraphTrackingApplet( StandardApplet ):
    def __init__( self, name="Tracking", workflow=None, projectFileGroupName="ChaingraphTracking" ):
        super(ChaingraphTrackingApplet, self).__init__( name=name, workflow=workflow )
        self._serializableItems = [ TrackingSerializer(self.topLevelOperator, projectFileGroupName) ]

    @property
    def singleLaneOperatorClass( self ):
        return OpChaingraphTracking

    @property
    def broadcastingSlots( self ):
        return []

    @property
    def singleLaneGuiClass( self ):
        return ChaingraphTrackingGui

    @property
    def dataSerializers(self):
        return self._serializableItems
