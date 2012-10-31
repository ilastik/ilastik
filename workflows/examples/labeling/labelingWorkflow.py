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
        
        # Connect top-level operators
        self.labelingApplet.topLevelOperator.InputImages.connect( self.dataSelectionApplet.topLevelOperator.Image )
        self.labelingApplet.topLevelOperator.LabelsAllowedFlags.connect( self.dataSelectionApplet.topLevelOperator.AllowLabels )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName
