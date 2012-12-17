from ilastik.applets.base.standardApplet import StandardApplet
from ilastik.applets.tracking.conservation.opConservationTracking import OpConservationTracking
from ilastik.applets.tracking.base.trackingSerializer import TrackingSerializer
from ilastik.applets.tracking.conservation.conservationTrackingGui import ConservationTrackingGui


class ConservationTrackingApplet( StandardApplet ):
    def __init__( self, name="Tracking", workflow=None, projectFileGroupName="Tracking" ):
        super(ConservationTrackingApplet, self).__init__( name=name, workflow=workflow )        
        self._serializableItems = [ TrackingSerializer(self.topLevelOperator, projectFileGroupName) ]

    @property
    def singleLaneOperatorClass( self ):
        return OpConservationTracking

    @property
    def broadcastingSlots( self ):
        return []

    @property
    def singleLaneGuiClass( self ):
        return ConservationTrackingGui

    @property
    def dataSerializers(self):
        return self._serializableItems
