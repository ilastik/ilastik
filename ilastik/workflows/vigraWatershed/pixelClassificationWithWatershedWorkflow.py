from ilastik.workflows.pixelClassification import PixelClassificationWorkflow
from ilastik.applets.vigraWatershedViewer import VigraWatershedViewerApplet

class PixelClassificationWithVigraWatershedWorkflow(PixelClassificationWorkflow):
    
    def __init__( self, *args, **kwargs ):
        super(PixelClassificationWithVigraWatershedWorkflow, self).__init__( appendBatchOperators=False, *args, **kwargs )

        # Create applets
        self.watershedApplet = VigraWatershedViewerApplet(self, "Watershed", "Watershed")
        
        # Expose for shell
        self._applets.append(self.watershedApplet)

    def connectLane(self, laneIndex):
        super( PixelClassificationWithVigraWatershedWorkflow, self ).connectLane( laneIndex )

        # Get the right lane from each operator
        opPixelClassification = self.pcApplet.topLevelOperator.getLane(laneIndex)
        opWatershedViewer = self.watershedApplet.topLevelOperator.getLane(laneIndex)

        # Connect them up
        opWatershedViewer.InputImage.connect( opPixelClassification.CachedPredictionProbabilities )
        opWatershedViewer.RawImage.connect( opPixelClassification.InputImages )
