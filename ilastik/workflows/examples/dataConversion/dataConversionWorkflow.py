import sys
from lazyflow.roi import TinyVector
from lazyflow.graph import Graph
from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet

class DataConversionWorkflow(Workflow):
    def __init__(self, shell, headless, workflow_cmdline_args, *args, **kwargs):
        
        # Create a graph to be shared by all operators
        graph = Graph()
        super(DataConversionWorkflow, self).__init__(shell, headless, graph=graph, *args, **kwargs)
        self._applets = []

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, 
                                                       "Input Data", 
                                                       "Input Data", 
                                                       supportIlastik05Import=True, 
                                                       batchDataGui=False,
                                                       force5d=False)

        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ["Input Data"] )

        self.dataExportApplet = DataExportApplet(self, "Data Export")

        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.WorkingDirectory.connect( opDataSelection.WorkingDirectory )

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.dataExportApplet )

        self._workflow_cmdline_args = workflow_cmdline_args

    def onProjectLoaded(self, projectManager):
        """
        Overridden from Workflow base class.  Called by the Project Manager.
        """
        print "DataConversionWorkflow Project was opened with the following args: "
        print self._workflow_cmdline_args
        if self._workflow_cmdline_args:
            sys.stderr.write('Command-line interface not supported yet.')

    def connectLane(self, laneIndex):
        opDataSelectionView = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opDataExportView = self.dataExportApplet.topLevelOperator.getLane(laneIndex)

        opDataExportView.Input.connect( opDataSelectionView.ImageGroup[0] )
        opDataExportView.RawDatasetInfo.connect( opDataSelectionView.DatasetGroup[0] )        

        # There is no special "raw" display layer in this workflow.
        #opDataExportView.RawData.connect( opDataSelectionView.ImageGroup[0] )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.statusUpdateSignal`
        """
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        input_ready = len(opDataSelection.ImageGroup) > 0

        opDataExport = self.dataExportApplet.topLevelOperator
        export_data_ready = input_ready and \
                            len(opDataExport.Input) > 0 and \
                            opDataExport.Input[0].ready() and \
                            (TinyVector(opDataExport.Input[0].meta.shape) > 0).all()

        self._shell.setAppletEnabled(self.dataExportApplet, export_data_ready)
        
        # Lastly, check for certain "busy" conditions, during which we 
        #  should prevent the shell from closing the project.
        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= self.dataExportApplet.busy
        self._shell.enableProjectChanges( not busy )
