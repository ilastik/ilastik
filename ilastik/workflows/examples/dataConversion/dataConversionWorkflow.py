import sys
from lazyflow.graph import Graph
from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet

class DataConversionWorkflow(Workflow):
    def __init__(self, headless, workflow_cmdline_args, *args, **kwargs):
        
        # Create a graph to be shared by all operators
        graph = Graph()
        super(DataConversionWorkflow, self).__init__(headless, graph=graph, *args, **kwargs)
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

