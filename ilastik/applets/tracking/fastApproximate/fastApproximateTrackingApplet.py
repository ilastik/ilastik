from ilastik.applets.base.standardApplet import StandardApplet
from ilastik.applets.tracking.base.trackingSerializer import TrackingSerializer
from ilastik.applets.tracking.fastApproximate.opFastApproximateTracking import OpFastApproximateTracking
from ilastik.applets.tracking.fastApproximate.fastApproximateTrackingGui import FastApproximateTrackingGui


class FastApproximateTrackingApplet( StandardApplet ):
    def __init__( self, name="Tracking", workflow=None, projectFileGroupName="Tracking" ):
        super(FastApproximateTrackingApplet, self).__init__( name=name, workflow=workflow )        
        self._serializableItems = [ TrackingSerializer(self.topLevelOperator, projectFileGroupName) ]

    @property
    def singleLaneOperatorClass( self ):
        return OpFastApproximateTracking

    @property
    def broadcastingSlots( self ):
        return []

    @property
    def singleLaneGuiClass( self ):
        return FastApproximateTrackingGui

    @property
    def dataSerializers(self):
        return self._serializableItems
