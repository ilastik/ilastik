from ilastik.workflow import Workflow

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.vigraWatershedViewer import VigraWatershedViewerApplet

from lazyflow.graph import Graph

class VigraWatershedWorkflow(Workflow):

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, headless, workflow_cmdline_args, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()

        super(VigraWatershedWorkflow, self).__init__( headless, graph=graph, *args, **kwargs)
        self._applets = []

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.watershedApplet = VigraWatershedViewerApplet(self, "Watershed", "Watershed")

        # Expose to shell
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.watershedApplet)

    def connectLane(self, laneIndex):
        """
        Override from base class.
        """
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opWatershed = self.watershedApplet.topLevelOperator.getLane(laneIndex)

        # Connect top-level operators
        opWatershed.InputImage.connect( opData.Image )
        opWatershed.RawImage.connect( opData.Image )

