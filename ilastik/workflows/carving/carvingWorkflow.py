from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators.valueProviders import OpAttributeSelector
from lazyflow.operators.adaptors import Op5ifyer

from ilastik.workflow import Workflow

from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet

from carvingApplet import CarvingApplet
from preprocessingApplet import PreprocessingApplet

class CarvingWorkflow(Workflow):
    
    workflowName = "Carving"
    defaultAppletIndex = 1 # show DataSelection by default
    
    @property
    def applets(self):
        return self._applets
    
    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, headless, workflow_cmdline_args, hintoverlayFile=None, pmapoverlayFile=None, *args, **kwargs):
        if hintoverlayFile is not None:
            assert isinstance(hintoverlayFile, str), "hintoverlayFile should be a string, not '%s'" % type(hintoverlayFile)
        if pmapoverlayFile is not None:
            assert isinstance(pmapoverlayFile, str), "pmapoverlayFile should be a string, not '%s'" % type(pmapoverlayFile)

        graph = Graph()
        
        super(CarvingWorkflow, self).__init__(headless, graph=graph, *args, **kwargs)
        
        ## Create applets 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet(self,
                                                       "Input Data",
                                                       "Input Data",
                                                       supportIlastik05Import=True,
                                                       batchDataGui=False)
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ['Raw Data'] )
        
        self.carvingApplet = CarvingApplet(workflow=self,
                                           projectFileGroupName="carving",
                                           hintOverlayFile=hintoverlayFile,
                                           pmapOverlayFile=pmapoverlayFile)
        
        self.preprocessingApplet = PreprocessingApplet(workflow=self,
                                           title = "Preprocessing",
                                           projectFileGroupName="preprocessing")
        
        #self.carvingApplet.topLevelOperator.MST.connect(self.preprocessingApplet.topLevelOperator.PreprocessedData)
        
        # Expose to shell
        self._applets = []
        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.preprocessingApplet)
        self._applets.append(self.carvingApplet)
        
    def connectLane(self, laneIndex):
        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opPreprocessing = self.preprocessingApplet.topLevelOperator.getLane(laneIndex)
        opCarvingLane = self.carvingApplet.topLevelOperator.getLane(laneIndex)
        op5 = Op5ifyer(parent=self)
        op5.order.setValue("txyzc")
        op5.input.connect(opData.Image)

        ## Connect operators
        opPreprocessing.InputData.connect(op5.output)
        #opCarvingTopLevel.RawData.connect(op5.output)
        opCarvingLane.InputData.connect(op5.output)
        opCarvingLane.FilteredInputData.connect(opPreprocessing.FilteredImage)
        opCarvingLane.MST.connect(opPreprocessing.PreprocessedData)
        opCarvingLane.UncertaintyType.setValue("none")

        # Special input-input connection: WriteSeeds metadata must mirror the input data
        opCarvingLane.WriteSeeds.connect( opCarvingLane.InputData )
        
        self.preprocessingApplet.enableDownstream(False)
