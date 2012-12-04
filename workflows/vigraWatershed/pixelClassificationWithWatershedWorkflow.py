from ilastik.workflow import Workflow
from workflows.pixelClassification import PixelClassificationWorkflow
from ilastik.applets.vigraWatershedViewer import VigraWatershedViewerApplet

from lazyflow.graph import Graph

class PixelClassificationWithVigraWatershedWorkflow(Workflow):
    
    def __init__( self, *args, **kwargs ):
        graph = Graph()
        self._pixelClassificationWorkflow = PixelClassificationWorkflow(graph=graph, *args, **kwargs)
        super(PixelClassificationWithVigraWatershedWorkflow, self).__init__( graph=graph )
        self.dataSelectionApplet = self._pixelClassificationWorkflow.dataSelectionApplet

        # Create applets
        self.watershedApplet = VigraWatershedViewerApplet(self, "Watershed", "Watershed")
        
        # Connect top-level operators
        pixelClassificationApplet = self._pixelClassificationWorkflow.pcApplet
        opPixelClassification = pixelClassificationApplet.topLevelOperator

        opWatershedViewer = self.watershedApplet.topLevelOperator
        opWatershedViewer.InputImage.connect( opPixelClassification.CachedPredictionProbabilities )
        opWatershedViewer.RawImage.connect( opPixelClassification.InputImages )

        self._applets = []
        self._applets += self._pixelClassificationWorkflow.applets[0:4]
        self._applets.append(self.watershedApplet)

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self._pixelClassificationWorkflow.imageNameListSlot
