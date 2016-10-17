from ilastik.applets.base.standardApplet import StandardApplet
from ilastik.applets.tracking.base.trackingSerializer import TrackingSerializer

import logging
logger = logging.getLogger(__name__)

import os

if os.name == 'nt': # Use old PgmLink tracking if OS is Windows
    from ilastik.applets.tracking.conservation.opConservationTrackingPgmLink import OpConservationTrackingPgmLink as OpConservationTracking
    logger.info("Using old conservation tracking workflow (PgmLink)")
else:
    from ilastik.applets.tracking.conservation.opConservationTracking import OpConservationTracking

class ConservationTrackingApplet( StandardApplet ):
    def __init__( self, name="Tracking", workflow=None, projectFileGroupName="ConservationTracking" ):
        super(ConservationTrackingApplet, self).__init__( name=name, workflow=workflow )        
        self._serializableItems = [ TrackingSerializer(self.topLevelOperator, projectFileGroupName) ]
        self.busy = False

    @property
    def singleLaneOperatorClass( self ):
        return OpConservationTracking

    @property
    def broadcastingSlots( self ):
        return ['Parameters', 'ExportSettings']

    @property
    def singleLaneGuiClass( self ):
        from ilastik.applets.tracking.conservation.conservationTrackingGui import ConservationTrackingGui
        return ConservationTrackingGui

    @property
    def dataSerializers(self):
        return self._serializableItems
