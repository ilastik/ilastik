from ilastik.workflow import Workflow

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.vigraWatershedViewer import VigraWatershedViewerApplet

from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators import OpAttributeSelector

class VigraWatershedWorkflow(Workflow):
    
    def __init__(self, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()

        super(VigraWatershedWorkflow, self).__init__(graph=graph, *args, **kwargs)
        self._applets = []

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.watershedApplet = VigraWatershedViewerApplet(self, "Watershed", "Watershed")
        
        # Connect top-level operators
        self.watershedApplet.topLevelOperator.InputImage.connect( self.dataSelectionApplet.topLevelOperator.Image )
        self.watershedApplet.topLevelOperator.RawImage.connect( self.dataSelectionApplet.topLevelOperator.Image )
        
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.watershedApplet)

        # The shell needs a slot from which he can read the list of image names to switch between.
        # Use an OpAttributeSelector to create a slot containing just the filename from the OpDataSelection's DatasetInfo slot.
        opSelectFilename = OperatorWrapper( OpAttributeSelector, graph=graph )
        opSelectFilename.InputObject.connect( self.dataSelectionApplet.topLevelOperator.Dataset )
        opSelectFilename.AttributeName.setValue( 'filePath' )

        self._imageNameListSlot = opSelectFilename.Result

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self._imageNameListSlot
