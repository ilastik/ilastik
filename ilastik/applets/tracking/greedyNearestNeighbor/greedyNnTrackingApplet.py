from ilastik.applets.base.standardApplet import StandardApplet
from ilastik.applets.tracking.base.trackingSerializer import TrackingSerializer
from ilastik.applets.tracking.greedyNearestNeighbor.opGreedyNnTracking import OpGreedyNnTracking
from ilastik.applets.tracking.greedyNearestNeighbor.greedyNnTrackingGui import GreedyNnTrackingGui


class GreedyNnTrackingApplet( StandardApplet ):
    def __init__( self, name="Tracking", workflow=None, projectFileGroupName="Tracking" ):
        super(GreedyNnTrackingApplet, self).__init__( name=name, workflow=workflow )        
        self._serializableItems = [ TrackingSerializer(self.topLevelOperator, projectFileGroupName) ]

    @property
    def singleLaneOperatorClass( self ):
        return OpGreedyNnTracking

    @property
    def broadcastingSlots( self ):
        return []

    @property
    def singleLaneGuiClass( self ):
        return GreedyNnTrackingGui

    @property
    def dataSerializers(self):
        return self._serializableItems
