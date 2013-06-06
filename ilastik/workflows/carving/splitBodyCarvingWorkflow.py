from lazyflow.graph import Graph
from lazyflow.operators.adaptors import Op5ifyer

from ilastik.workflow import Workflow

from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.splitBodyCarving.splitBodyCarvingApplet import SplitBodyCarvingApplet

from lazyflow.operators.generic import OpSingleChannelSelector

from preprocessingApplet import PreprocessingApplet

class SplitBodyCarvingWorkflow(Workflow):
    
    workflowName = "Split Body Tool Workflow"
    defaultAppletIndex = 1 # show DataSelection by default

    DATA_ROLE_RAW = 0
    DATA_ROLE_PIXEL_PROB = 1
    DATA_ROLE_RAVELER_LABELS = 2

    @property
    def applets(self):
        return self._applets
    
    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, headless, workflow_cmdline_args, hintoverlayFile=None, pmapoverlayFile=None, *args, **kwargs):
        if workflow_cmdline_args:
            assert False, "Not using workflow cmdline args yet."
        
        graph = Graph()
        
        super(SplitBodyCarvingWorkflow, self).__init__(headless, *args, graph=graph, **kwargs)
        
        ## Create applets 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        opDataSelection = self.dataSelectionApplet.topLevelOperator

        opDataSelection.DatasetRoles.setValue( ['Raw Data', 'Pixel Probabilities', 'Raveler Labels'] )

        self.splitBodyCarvingApplet = SplitBodyCarvingApplet(workflow=self,
                                           projectFileGroupName="carving")
        
        self.preprocessingApplet = PreprocessingApplet(workflow=self,
                                           title = "Preprocessing",
                                           projectFileGroupName="preprocessing")
        
        #self.carvingApplet.topLevelOperator.MST.connect(self.preprocessingApplet.topLevelOperator.PreprocessedData)
        
        # Expose to shell
        self._applets = []
        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.preprocessingApplet)
        self._applets.append(self.splitBodyCarvingApplet)
        
    def connectLane(self, laneIndex):
        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opPreprocessing = self.preprocessingApplet.topLevelOperator.getLane(laneIndex)
        opSplitBodyCarving = self.splitBodyCarvingApplet.topLevelOperator.getLane(laneIndex)

        op5Raw = Op5ifyer(parent=self)
        op5Raw.order.setValue("txyzc")
        op5Raw.input.connect(opData.ImageGroup[self.DATA_ROLE_RAW])
        
        op5PixelProb = Op5ifyer(parent=self)
        op5PixelProb.order.setValue("txyzc")
        op5PixelProb.input.connect(opData.ImageGroup[self.DATA_ROLE_PIXEL_PROB])

        op5RavelerLabels = Op5ifyer(parent=self)
        op5RavelerLabels.order.setValue("txyzc")
        op5RavelerLabels.input.connect(opData.ImageGroup[self.DATA_ROLE_RAVELER_LABELS])

        # We assume the membrane boundaries are found in the first prediction class (channel 0)
        opSingleChannelSelector = OpSingleChannelSelector(parent=self)
        opSingleChannelSelector.Input.connect( op5PixelProb.output )
        opSingleChannelSelector.Index.setValue(0)
        
        opPreprocessing.InputData.connect( opSingleChannelSelector.Output )
        opPreprocessing.RawData.connect( op5Raw.output )
        opSplitBodyCarving.RawData.connect( op5Raw.output )
        opSplitBodyCarving.InputData.connect( opSingleChannelSelector.Output )
        opSplitBodyCarving.RavelerLabels.connect( op5RavelerLabels.output )
        opSplitBodyCarving.FilteredInputData.connect( opPreprocessing.FilteredImage )

        # Special input-input connection: WriteSeeds metadata must mirror the input data
        opSplitBodyCarving.WriteSeeds.connect( opSplitBodyCarving.InputData )

        opSplitBodyCarving.MST.connect(opPreprocessing.PreprocessedData)
        opSplitBodyCarving.UncertaintyType.setValue("none")
        
        self.preprocessingApplet.enableDownstream(False)
