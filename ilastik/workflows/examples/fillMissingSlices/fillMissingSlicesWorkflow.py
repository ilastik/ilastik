from ilastik.workflow import Workflow

from lazyflow.graph import Graph

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.fillMissingSlices import FillMissingSlicesApplet

class FillMissingSlicesWorkflow(Workflow):
    def __init__(self, headless, workflow_cmdline_args, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(FillMissingSlicesWorkflow, self).__init__(headless, graph=graph, *args, **kwargs)
        self._applets = []

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.fillMissingSlicesApplet = FillMissingSlicesApplet(self, "Fill Missing Slices", "Fill Missing Slices")

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.fillMissingSlicesApplet )

    def connectLane(self, laneIndex):
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)        
        opFillMissingSlices =self.fillMissingSlicesApplet.topLevelOperator.getLane(laneIndex)

        # Connect top-level operators
        opFillMissingSlices.Input.connect( opDataSelection.Image )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName
