import numpy as np

from ilastik.workflow import Workflow
from lazyflow.graph import Graph


from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.eigenesThreshold import EigenesThresholdApplet



class EigenesThresholdWorkflow(Workflow):

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_workflow, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()

        #call the __init__ of its upperclass, here Workflow
        super(EigenesThresholdWorkflow, self).__init__( \
                shell, headless, workflow_cmdline_args, project_creation_workflow, graph=graph, *args, **kwargs)


        #################################################################
        # Create the added applets
        #################################################################
        self._applets = []



        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)


        self.eigenesThresholdApplet = EigenesThresholdApplet(self, "eigenes Thresholding", "Thresholding Stage 1")
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ['Raw Data'] )

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.eigenesThresholdApplet )

    def connectLane(self, laneIndex):
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)        
        opEigenesThreshold = self.eigenesThresholdApplet.topLevelOperator.getLane(laneIndex)

        # Connect top-level operators
        opEigenesThreshold.InputImage.connect( opDataSelection.Image )


    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName



