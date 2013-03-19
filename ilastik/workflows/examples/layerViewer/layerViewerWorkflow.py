from ilastik.workflow import Workflow

from lazyflow.graph import Graph

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.layerViewer import LayerViewerApplet

class LayerViewerWorkflow(Workflow):
    def __init__(self, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(LayerViewerWorkflow, self).__init__(graph=graph, *args, **kwargs)
        self._applets = []

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.viewerApplet = LayerViewerApplet(self)

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.viewerApplet )

    def connectLane(self, laneIndex):
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opLayerViewer = self.viewerApplet.topLevelOperator.getLane(laneIndex)

        # Connect top-level operators
        opLayerViewer.RawInput.connect( opDataSelection.Image )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

