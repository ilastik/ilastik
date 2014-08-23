from ilastik.workflow import Workflow

from lazyflow.graph import Graph

from ilastik.applets.dataSelection import DataSelectionApplet
from mriVolPreprocApplet import MriVolPreprocApplet
from mriVolConnectedComponentsApplet import MriVolConnectedComponentsApplet
from mriVolReportApplet import MriVolReportApplet

class MriVolumetryWorkflow(Workflow):
    def __init__(self, shell, headless, workflow_cmdline_args, *args, **kwargs):
        
        # Create a graph to be shared by all operators
        graph = Graph()
        super(MriVolumetryWorkflow, self).__init__(shell, headless, 
                                                   graph=graph, *args, 
                                                   **kwargs)

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, 
                                                       "Input Data", 
                                                       "Input Data", 
                                                supportIlastik05Import=False, 
                                                       batchDataGui=False,
                                                       force5d=True)

        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ['Raw Data',
                                                'Prediction Maps'] )

        self.mriVolPreprocApplet = MriVolPreprocApplet(self, 
                                                       'Clean-up Predictions',
                                                       'PredictionFilter')

        self.mriVolCCApplet = MriVolConnectedComponentsApplet(self, \
                                                'Size Filter',
                                                'ConnectedComponents')
        self.mriVolReportApplet = MriVolReportApplet(self, \
                                                     'Report', 'Report')


        self._applets = []
        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.mriVolPreprocApplet )
        self._applets.append( self.mriVolCCApplet )
        self._applets.append( self.mriVolReportApplet )

        # self._workflow_cmdline_args = workflow_cmdline_args

    def connectLane(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opMriVolPreproc = self.mriVolPreprocApplet.topLevelOperator.getLane( \
                                                                    laneIndex)
        opMriVolCC = self.mriVolCCApplet.topLevelOperator.getLane(laneIndex)

        # Connect top-level operators
        opMriVolPreproc.RawInput.connect( opData.ImageGroup[0] )
        opMriVolPreproc.Input.connect( opData.ImageGroup[1] )

        # opMriVolCC.Input.connect( opMriVolPreproc.FinalOutput )
        opMriVolCC.Input.connect( opMriVolPreproc.FanOutOutput )
        opMriVolCC.RawInput.connect( opData.ImageGroup[0] )

        opMriVolCC.LabelNames.connect( opMriVolPreproc.LabelNames )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the
        :py:attr:`Applet.appletStateUpdateRequested`
        
        This method will be called by the child classes with the result of
        their own applet readyness findings as keyword argument.
        """
        nRoles = 2 # both, raw and prediction have to be provided
        slot = self.dataSelectionApplet.topLevelOperator.ImageGroup
        if len(slot) > 0:
            input_ready = True
            for sub in slot:
                input_ready = input_ready and \
                              all([sub[i].ready() for i in range(nRoles)])
        else:
            input_ready = False
        for applet in self.applets[1:]:
            self._shell.setAppletEnabled(applet, input_ready)


'''
Questions:
Where does this error come from?
014-02-09 09:35:35.716 ilastik[35869:507] modalSession has been exited prematurely - check for a reentrant call to endModalSession:
QWidget::repaint: Recursive repaint detected
QPainter::begin: A paint device can only be painted by one painter at a time.
Segmentation fault: 11
'''
