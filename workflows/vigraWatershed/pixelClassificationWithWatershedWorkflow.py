from ilastik.workflow import Workflow
from workflows.pixelClassification import PixelClassificationWorkflow
from ilastik.applets.vigraWatershedViewer import VigraWatershedViewerApplet

class PixelClassificationWithVigraWatershedWorkflow(Workflow):
    
    def __init__(self):
        super(PixelClassificationWithVigraWatershedWorkflow, self).__init__()

        self._pixelClassificationWorkflow = PixelClassificationWorkflow()
        
        self.dataSelectionApplet = self._pixelClassificationWorkflow.dataSelectionApplet

        self._graph = self._pixelClassificationWorkflow.graph
        graph = self._graph

        # Create applets
        self.watershedApplet = VigraWatershedViewerApplet(graph, "Watershed", "Watershed")
        
        # Connect top-level operators
        pixelClassificationApplet = self._pixelClassificationWorkflow.pcApplet
        opPixelClassification = pixelClassificationApplet.topLevelOperator

        opWatershedViewer = self.watershedApplet.topLevelOperator
        opWatershedViewer.InputImage.connect( opPixelClassification.CachedPredictionProbabilities )

        
        self._applets = []
        self._applets += self._pixelClassificationWorkflow.applets[0:4]
        self._applets.append(self.watershedApplet)

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self._pixelClassificationWorkflow.imageNameListSlot
    
    @property
    def graph( self ):
        '''the lazyflow graph shared by the applets'''
        return self._graph
