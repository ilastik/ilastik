from ilastik.applets.base.standardApplet import StandardApplet

from opManualTracking import OpManualTracking
from manualTrackingSerializer import ManualTrackingSerializer
from manualTrackingGui import ManualTrackingGui

class ManualTrackingApplet(StandardApplet):
    def __init__( self, name="Manual Tracking", workflow=None, projectFileGroupName="ManualTracking" ):
        super(ManualTrackingApplet, self).__init__( name=name, workflow=workflow )
        self._serializableItems = [ ManualTrackingSerializer(self.topLevelOperator, projectFileGroupName) ]

    @property
    def singleLaneOperatorClass( self ):
        return OpManualTracking

    @property
    def broadcastingSlots( self ):
        return []

    @property
    def singleLaneGuiClass( self ):
        return ManualTrackingGui

    @property
    def dataSerializers(self):
        return self._serializableItems
