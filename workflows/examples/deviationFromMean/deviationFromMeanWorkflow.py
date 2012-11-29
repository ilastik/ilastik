from ilastik.workflow import Workflow

from lazyflow.graph import Graph

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.deviationFromMean import DeviationFromMeanApplet

class DeviationFromMeanWorkflow(Workflow):
    def __init__(self):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(DeviationFromMeanWorkflow, self).__init__(graph=graph)
        self._applets = []

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.deviationFromMeanApplet = DeviationFromMeanApplet(self, "Deviation From Mean")

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.deviationFromMeanApplet )

    def connectLane(self, laneIndex):
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opDeviationFromMean = self.deviationFromMeanApplet.topLevelOperator.getLane(laneIndex)

        # Connect top-level operators
        opDeviationFromMean.Input.connect( opDataSelection.Image )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName
