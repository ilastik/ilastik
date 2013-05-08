from ilastik.applets.base.standardApplet import StandardApplet
from ilastik.applets.trackingFeatureExtraction.opTrackingFeatureExtraction import OpTrackingFeatureExtraction
from ilastik.applets.trackingFeatureExtraction.trackingFeatureExtractionGui import TrackingFeatureExtractionGui
from ilastik.applets.trackingFeatureExtraction.trackingFeatureExtractionSerializer import TrackingFeatureExtractionSerializer

class TrackingFeatureExtractionApplet( StandardApplet ):
    def __init__( self, name="Object Extraction", workflow=None, projectFileGroupName="ObjectExtraction" ):
        super(TrackingFeatureExtractionApplet, self).__init__( name=name, workflow=workflow )
        self._serializableItems = [ TrackingFeatureExtractionSerializer(self.topLevelOperator, projectFileGroupName) ]

    @property
    def singleLaneOperatorClass( self ):
        return OpTrackingFeatureExtraction

    @property
    def broadcastingSlots( self ):
        return []

    @property
    def singleLaneGuiClass( self ):
        return TrackingFeatureExtractionGui

    @property
    def dataSerializers(self):
        return self._serializableItems
