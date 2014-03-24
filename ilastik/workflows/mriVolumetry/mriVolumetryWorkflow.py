from ilastik.workflow import Workflow

from lazyflow.graph import Graph

from ilastik.applets.dataSelection import DataSelectionApplet
from mriVolPreprocApplet import MriVolPreprocApplet

class MriVolumetryWorkflow(Workflow):
    def __init__(self, shell, headless, workflow_cmdline_args, *args, **kwargs):
        
        # Create a graph to be shared by all operators
        graph = Graph()
        super(MriVolumetryWorkflow, self).__init__(shell, headless, 
                                                   graph=graph, *args, **kwargs)

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, 
                                                       "Input Data", 
                                                       "Input Data", 
                                                       supportIlastik05Import=False, 
                                                       batchDataGui=False,
                                                       force5d=True)

        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ['Prediction Maps'] )

        self.mriVolPreprocApplet = MriVolPreprocApplet(self, 
                                                       'Prediction Filter',
                                                       'PredictionFilter')

        self._applets = []
        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.mriVolPreprocApplet )

        # self._workflow_cmdline_args = workflow_cmdline_args

    def connectLane(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opMriVolPreproc = self.mriVolPreprocApplet.topLevelOperator.getLane(laneIndex)

        # Connect top-level operators
        opMriVolPreproc.PredImage.connect( opData.ImageGroup[0] )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

'''
Questions:
Where does this error come from?
014-02-09 09:35:35.716 ilastik[35869:507] modalSession has been exited prematurely - check for a reentrant call to endModalSession:
QWidget::repaint: Recursive repaint detected
QPainter::begin: A paint device can only be painted by one painter at a time.
Segmentation fault: 11
'''
