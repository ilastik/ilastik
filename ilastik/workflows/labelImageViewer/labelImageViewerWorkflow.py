from ilastik.workflow import Workflow

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.labelImageViewer import LabelImageViewerApplet
from lazyflow.graph import Graph

class LabelImageViewerWorkflow(Workflow):

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        # FIXME: The shell is very sensitive to the order in which these images are added in the GUI.
        # The slot that serves as the 'master' (this slot) for lane insertion purposes must be added last.
        # Hence, we are using the predictionSelection slot.
        # In the future, the shell and dataselection applets will be fixed to handle the multi-input-data case.
        #return self.rawDataSelectionApplet.topLevelOperator.ImageName
        return self.labelDataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, headless=False, workflow_cmdline_args=(), parent=None, graph=None):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(LabelImageViewerWorkflow, self ).__init__( headless=headless,
                                                         workflow_cmdline_args=workflow_cmdline_args,
                                                         parent=parent,
                                                         graph=graph)
        self._applets = []

        # Two data selection applets...
        self.rawDataSelectionApplet = DataSelectionApplet(self, "Raw Data", "Raw Data", supportIlastik05Import=False, batchDataGui=False)
        self.labelDataSelectionApplet = DataSelectionApplet(self, "Label Image", "Label Image", supportIlastik05Import=False, batchDataGui=False)
        self.viewerApplet = LabelImageViewerApplet(self)

        # Expose for shell
        self._applets.append(self.rawDataSelectionApplet)
        self._applets.append(self.labelDataSelectionApplet)
        self._applets.append(self.viewerApplet)

    def connectLane(self, laneIndex):
        # Get a handle to each operator lane
        opRawData = self.rawDataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opLabelData = self.labelDataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opViewer = self.viewerApplet.topLevelOperator.getLane(laneIndex)

        opViewer.RawImage.connect( opRawData.Image )
        opViewer.LabelImage.connect( opLabelData.Image )

