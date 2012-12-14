from ilastik.applets.base.standardApplet import StandardApplet

from opTracking import OpTracking
from trackingGui import TrackingGui
from trackingSerializer import TrackingSerializer

class TrackingApplet( StandardApplet ):
    """
    This is a simple thresholding applet
    """
    def __init__( self, name="Tracking", workflow=None, projectFileGroupName="Tracking" ):
        super(TrackingApplet, self).__init__( name=name, workflow=workflow )
        self._serializableItems = [ TrackingSerializer(self.topLevelOperator, projectFileGroupName) ]

    @property
    def singleLaneOperatorClass( self ):
        return OpTracking

    @property
    def broadcastingSlots( self ):
        return []

    @property
    def singleLaneGuiClass( self ):
        return TrackingGui

    @property
    def dataSerializers(self):
        return self._serializableItems
