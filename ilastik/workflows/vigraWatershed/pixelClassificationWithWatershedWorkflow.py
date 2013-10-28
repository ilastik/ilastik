from ilastik.workflows.pixelClassification import PixelClassificationWorkflow
from ilastik.applets.vigraWatershedViewer import VigraWatershedViewerApplet

class PixelClassificationWithWatershedWorkflow(PixelClassificationWorkflow):

    workflowName = "Pixel Classification (with Watershed Preview)"
    
    def __init__( self, shell, headless, workflow_cmdline_args, *args, **kwargs ):
        super(PixelClassificationWithWatershedWorkflow, self).__init__( shell, headless, workflow_cmdline_args, appendBatchOperators=False, *args, **kwargs )

        # Create applets
        self.watershedApplet = VigraWatershedViewerApplet(self, "Watershed", "Watershed")
        
        # Expose for shell
        self._applets.append(self.watershedApplet)

    def connectLane(self, laneIndex):
        super( PixelClassificationWithWatershedWorkflow, self ).connectLane( laneIndex )

        # Get the right lane from each operator
        opPixelClassification = self.pcApplet.topLevelOperator.getLane(laneIndex)
        opWatershedViewer = self.watershedApplet.topLevelOperator.getLane(laneIndex)

        # Connect them up
        opWatershedViewer.InputImage.connect( opPixelClassification.CachedPredictionProbabilities )
        opWatershedViewer.RawImage.connect( opPixelClassification.InputImages )
