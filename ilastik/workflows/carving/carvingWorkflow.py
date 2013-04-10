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
    
    @property
    def applets(self):
        return self._applets
    
    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, hintoverlayFile=None, pmapoverlayFile=None, *args, **kwargs):
        if hintoverlayFile is not None:
            assert isinstance(hintoverlayFile, str), "hintoverlayFile should be a string, not '%s'" % type(hintoverlayFile)
        if pmapoverlayFile is not None:
            assert isinstance(pmapoverlayFile, str), "pmapoverlayFile should be a string, not '%s'" % type(pmapoverlayFile)

        graph = Graph()
        
        super(CarvingWorkflow, self).__init__(graph=graph, *args, **kwargs)
        
        ## Create applets 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        
        self.carvingApplet = CarvingApplet(workflow=self,
                                           projectFileGroupName="carving",
                                           hintOverlayFile=hintoverlayFile,
                                           pmapOverlayFile=pmapoverlayFile)
        
        self.preprocessingApplet = PreprocessingApplet(workflow=self,
                                           title = "Preprocessing",
                                           projectFileGroupName="carving")
        
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
        opCarvingTopLevel = self.carvingApplet.topLevelOperator.getLane(laneIndex)
        op5 = Op5ifyer(parent=self)
        op5.order.setValue("txyzc")
        op5.input.connect(opData.Image)
        
        ## Connect operators
        opPreprocessing.RawData.connect(op5.output)
        opCarvingTopLevel.RawData.connect(op5.output)
        opCarvingTopLevel.opCarving.MST.connect(opPreprocessing.PreprocessedData)
        opCarvingTopLevel.opCarving.opLabeling.LabelsAllowedFlag.connect( opData.AllowLabels )
        opCarvingTopLevel.opCarving.UncertaintyType.setValue("none")
        
        self.preprocessingApplet.enableDownstream(False)
