from ilastik.workflow import Workflow

from lazyflow.graph import Graph

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.labeling import LabelingApplet
from ilastik.applets.labeling import LabelingSingleLaneApplet

class LabelingWorkflow(Workflow):
    def __init__( self, headless, workflow_cmdline_args, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(LabelingWorkflow, self).__init__( headless, graph=graph, *args, **kwargs )
        self._applets = []

        # Create applets
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.labelingSingleLaneApplet = LabelingSingleLaneApplet(self, "Generic Labeling (single-lane)")
        self.labelingMultiLaneApplet = LabelingApplet(self, "Generic Labeling (multi-lane)")

        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ["Raw Data"] )

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.labelingSingleLaneApplet )
        self._applets.append( self.labelingMultiLaneApplet )

    def connectLane(self, laneIndex):
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opSingleLaneLabeling = self.labelingSingleLaneApplet.topLevelOperator.getLane(laneIndex)
        opMultiLabeling = self.labelingMultiLaneApplet.topLevelOperator.getLane(laneIndex)
        
        # Connect top-level operators
        opSingleLaneLabeling.InputImage.connect( opDataSelection.Image )
        opSingleLaneLabeling.LabelsAllowedFlag.connect( opDataSelection.AllowLabels )

        opMultiLabeling.InputImages.connect( opDataSelection.Image )
        opMultiLabeling.LabelsAllowedFlags.connect( opDataSelection.AllowLabels )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName
