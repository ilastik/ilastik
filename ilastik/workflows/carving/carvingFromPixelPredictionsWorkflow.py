from lazyflow.graph import Graph
from lazyflow.operators.adaptors import Op5ifyer

from ilastik.workflow import Workflow

from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.pixelClassification import PixelClassificationApplet

from lazyflow.operators import OpSingleChannelSelector

from carvingApplet import CarvingApplet
from preprocessingApplet import PreprocessingApplet

class CarvingFromPixelPredictionsWorkflow(Workflow):
    
    workflowName = "Carving From Pixel Predictions"
    defaultAppletIndex = 1 # show DataSelection by default
    
    @property
    def applets(self):
        return self._applets
    
    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, headless, workflow_cmdline_args, hintoverlayFile=None, pmapoverlayFile=None, *args, **kwargs):
        if workflow_cmdline_args:
            assert False, "Not using workflow cmdline args yet."
        
        if hintoverlayFile is not None:
            assert isinstance(hintoverlayFile, str), "hintoverlayFile should be a string, not '%s'" % type(hintoverlayFile)
        if pmapoverlayFile is not None:
            assert isinstance(pmapoverlayFile, str), "pmapoverlayFile should be a string, not '%s'" % type(pmapoverlayFile)

        graph = Graph()
        
        super(CarvingFromPixelPredictionsWorkflow, self).__init__(headless, *args, graph=graph, **kwargs)
        
        ## Create applets 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ['Raw Data'] )

        self.featureSelectionApplet = FeatureSelectionApplet(self, "Feature Selection", "FeatureSelections")
        self.pixelClassificationApplet = PixelClassificationApplet(self, "PixelClassification")
        
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
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.pixelClassificationApplet)
        self._applets.append(self.preprocessingApplet)
        self._applets.append(self.carvingApplet)
        
    def connectLane(self, laneIndex):
        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opFeatureSelection = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)
        opPixelClassification = self.pixelClassificationApplet.topLevelOperator.getLane(laneIndex)
        opPreprocessing = self.preprocessingApplet.topLevelOperator.getLane(laneIndex)
        opCarvingTopLevel = self.carvingApplet.topLevelOperator.getLane(laneIndex)

        op5 = Op5ifyer(parent=self)
        op5.order.setValue("txyzc")
        op5.input.connect(opData.Image)
        
        ## Connect operators
        opFeatureSelection.InputImage.connect( op5.output )
        opPixelClassification.InputImages.connect( op5.output )
        opPixelClassification.FeatureImages.connect( opFeatureSelection.OutputImage )
        opPixelClassification.CachedFeatureImages.connect( opFeatureSelection.CachedOutputImage )
        opPixelClassification.LabelsAllowedFlags.connect( opData.AllowLabels )
        
        # We assume the membrane boundaries are found in the first prediction class (channel 0)
        opSingleChannelSelector = OpSingleChannelSelector(parent=self)
        opSingleChannelSelector.Input.connect( opPixelClassification.PredictionProbabilities )
        opSingleChannelSelector.Index.setValue(0)
        
        opPreprocessing.RawData.connect( opSingleChannelSelector.Output )
        opCarvingTopLevel.RawData.connect( op5.output )
        opCarvingTopLevel.InputData.connect( opSingleChannelSelector.Output )
        opCarvingTopLevel.FilteredInputData.connect( opPreprocessing.FilteredImage )

        opCarvingTopLevel.MST.connect(opPreprocessing.PreprocessedData)
        #opCarvingTopLevel.opCarving.opLabeling.LabelsAllowedFlag.connect( opData.AllowLabels )
        opCarvingTopLevel.opCarving.UncertaintyType.setValue("none")
        
        self.preprocessingApplet.enableDownstream(False)
