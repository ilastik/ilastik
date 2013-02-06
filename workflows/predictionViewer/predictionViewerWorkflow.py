from ilastik.workflow import Workflow

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.predictionViewer import PredictionViewerApplet

from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection

from lazyflow.graph import Graph, Operator, OperatorWrapper
from lazyflow.operators import OpPredictRandomForest

class PredictionViewerWorkflow(Workflow):

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, appendBatchOperators=True, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(PredictionViewerWorkflow, self ).__init__( graph=graph, *args, **kwargs )
        self._applets = []

        # Applets for training (interactive) workflow 
        self.dataSelectionApplet = DataSelectionApplet(self, "Viewed Predictions", "Viewed Predictions", supportIlastik05Import=False, batchDataGui=False)
        self.viewerApplet = PredictionViewerApplet(self)

        # Expose for shell
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.viewerApplet)

    def connectLane(self, laneIndex):
        # Get a handle to each operator lane
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opViewer = self.viewerApplet.topLevelOperator.getLane(laneIndex)

        opViewer.PredictionProbabilities.connect( opData.Image )