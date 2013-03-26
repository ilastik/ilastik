from ilastik.applets.base.standardApplet import StandardApplet

from lazyflow.graph import OperatorWrapper
from ilastik.applets.tracking.manual.opManualTracking import OpManualTracking
from ilastik.applets.tracking.manual.manualTrackingSerializer import ManualTrackingSerializer
from ilastik.applets.tracking.manual.manualTrackingGui import ManualTrackingGui

class ManualTrackingApplet(StandardApplet):
    def __init__( self, name="Manual Tracking", workflow=None, projectFileGroupName="ManualTracking" ):
        super(ManualTrackingApplet, self).__init__( name=name, workflow=workflow )        
        self._serializableItems = [  ]

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
