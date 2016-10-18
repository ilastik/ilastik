from ilastik.applets.base.standardApplet import StandardApplet
from ilastik.applets.tracking.base.trackingSerializer import TrackingSerializer

import logging
logger = logging.getLogger(__name__)

try:
    import hytra
    WITH_HYTRA = True
except ImportError as e:
    WITH_HYTRA = False

if WITH_HYTRA:
    from ilastik.applets.tracking.conservation.opConservationTracking import OpConservationTracking
else:
    # Use old PgmLink tracking operator if we can't import Hytra (When OS is Windows)
    from ilastik.applets.tracking.conservation.opConservationTrackingPgmLink import OpConservationTrackingPgmLink as OpConservationTracking
    logger.info("Using old conservation tracking workflow (PgmLink)")

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
