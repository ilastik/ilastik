from ilastik.workflow import Workflow

from lazyflow.graph import Graph

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.thresholdMasking import ThresholdMaskingApplet

class ThresholdMaskingWorkflow(Workflow):
    def __init__(self, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(ThresholdMaskingWorkflow, self).__init__(graph=graph, *args, **kwargs)
        self._applets = []

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.thresholdMaskingApplet = ThresholdMaskingApplet(self, "Thresholding", "Thresholding Stage 1")

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.thresholdMaskingApplet )

    def connectLane(self, laneIndex):
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)        
        opThresholdMasking = self.thresholdMaskingApplet.topLevelOperator.getLane(laneIndex)

        # Connect top-level operators
        opThresholdMasking.InputImage.connect( opDataSelection.Image )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName
