from ilastik.workflow import Workflow

from lazyflow.graph import Graph, Operator, OutputSlot
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.stopWatch import StopWatchApplet

class OpName( Operator ):
    Output = OutputSlot(level=1)


class StopWatchWorkflow(Workflow):
    def __init__(self, headless, workflow_cmdline_args, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(StopWatchWorkflow, self).__init__(headless, graph=graph, *args, **kwargs)
        #self.name = OperatorWrapper(OpName( graph=graph)
        #self.name.Output[0].setValue("void")

        self._applets = []

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.stopWatchApplet = StopWatchApplet(self, "Stop Watch", "Stop Watch")

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.stopWatchApplet )

    def connectLane(self, laneIndex):
        pass
        ##opThresholdMasking.InputImage.connect( opDataSelection.Image )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):

        #return self.name.Output
        return self.dataSelectionApplet.topLevelOperator.ImageName
