from ilastik.workflow import Workflow

from lazyflow.graph import Graph

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet

class FeatureSelectionWorkflow(Workflow):
    def __init__(self):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(FeatureSelectionWorkflow, self).__init__(graph=graph)
        self._applets = []

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.featureSelectionApplet = FeatureSelectionApplet(self, "FeatureSelection", "Feature Selection")

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.featureSelectionApplet )

    def connectLane(self, laneIndex):
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)        
        opFeatureSelection = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)

        # Connect top-level operators
        opFeatureSelection.InputImage.connect( opDataSelection.Image )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName
