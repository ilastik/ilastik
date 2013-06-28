from ilastik.workflow import Workflow

from lazyflow.graph import Graph

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.layerViewer import LayerViewerApplet

class LayerViewerWorkflow(Workflow):
    def __init__(self, headless, workflow_cmdline_args, *args, **kwargs):
        
        # Create a graph to be shared by all operators
        graph = Graph()
        super(LayerViewerWorkflow, self).__init__(headless, graph=graph, *args, **kwargs)
        self._applets = []

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.viewerApplet = LayerViewerApplet(self)

        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ["Raw Data", "Other Data"] )

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.viewerApplet )

        self._workflow_cmdline_args = workflow_cmdline_args

    def onProjectLoaded(self, projectManager):
        """
        Overridden from Workflow base class.  Called by the Project Manager.
        """
        print "LayerViewerWorkflow Project was opened with the following args: "
        print self._workflow_cmdline_args

    def connectLane(self, laneIndex):
        opDataSelectionView = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opLayerViewerView = self.viewerApplet.topLevelOperator.getLane(laneIndex)

        # Connect top-level operators                                                                                                                 
        opLayerViewerView.RawInput.connect( opDataSelectionView.ImageGroup[0] )
        opLayerViewerView.OtherInput.connect( opDataSelectionView.ImageGroup[1] )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

