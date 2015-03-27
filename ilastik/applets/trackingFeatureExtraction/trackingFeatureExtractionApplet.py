from ilastik.applets.base.standardApplet import StandardApplet
from ilastik.applets.trackingFeatureExtraction.opTrackingFeatureExtraction import OpTrackingFeatureExtraction
from ilastik.applets.trackingFeatureExtraction.trackingFeatureExtractionSerializer import TrackingFeatureExtractionSerializer

class TrackingFeatureExtractionApplet( StandardApplet ):
    def __init__( self, name="Object Extraction", workflow=None, interactive=True, projectFileGroupName="TrackingFeatureExtraction" ):
        super(TrackingFeatureExtractionApplet, self).__init__( name=name, workflow=workflow, interactive=interactive )
        self._serializableItems = [ TrackingFeatureExtractionSerializer(self.topLevelOperator, projectFileGroupName) ]

    @property
    def singleLaneOperatorClass( self ):
        return OpTrackingFeatureExtraction

    @property
    def broadcastingSlots( self ):
        return []

    @property
    def singleLaneGuiClass( self ):
        from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
        return LayerViewerGui

    @property
    def dataSerializers(self):
        return self._serializableItems
