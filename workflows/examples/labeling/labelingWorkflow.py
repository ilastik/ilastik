from ilastik.workflow import Workflow

from lazyflow.graph import Graph

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.labeling import LabelingApplet

class LabelingWorkflow(Workflow):
    def __init__(self):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(LabelingWorkflow, self).__init__(graph=graph)
        self._applets = []

        # Create applets
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.labelingApplet = LabelingApplet(self, "Generic Labeling Data")

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.labelingApplet )

    def connectLane(self, laneIndex):
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opLabeling = self.labelingApplet.topLevelOperator.getLane(laneIndex)
        
        # Connect top-level operators
        opLabeling.InputImages.connect( opDataSelection.Image )
        opLabeling.LabelsAllowedFlags.connect( opDataSelection.AllowLabels )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName
