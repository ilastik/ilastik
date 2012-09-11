from ilastik.workflow import Workflow

from lazyflow.graph import Graph

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.layerViewer import LayerViewerApplet

class LayerViewerWorkflow(Workflow):
    def __init__(self):
        super(LayerViewerWorkflow, self).__init__()
        self._applets = []

        # Create a graph to be shared by all operators
        graph = Graph()

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(graph, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.viewerApplet = LayerViewerApplet(graph)

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.viewerApplet )
        
        # Connect top-level operators
        self.viewerApplet.topLevelOperator.RawInput.connect( self.dataSelectionApplet.topLevelOperator.Image )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName
