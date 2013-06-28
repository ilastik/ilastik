from ilastik.workflow import Workflow

#from ilastik.applets.pixelClassification import PixelClassificationApplet
from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.batchIo import BatchIoApplet

from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
#from context.applets.featureSelection.opFeatureSelection import OpFeatureSelection

from lazyflow.graph import Graph, Operator, OperatorWrapper
from lazyflow.operators import OpPredictRandomForest, OpAttributeSelector

#from context.applets.featureSelection import FeatureSelectionAutocontextApplet
from ilastik.applets.autocontextClassification import AutocontextClassificationApplet
from ilastik.applets.autocontextClassification.opAutocontextBatch import OpAutocontextBatch
from ilastik.applets.autocontextClassification.opBatchIoSelective import OpBatchIoSelective

class AutocontextClassificationWorkflow(Workflow):
    
    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName
    
    def __init__(self, headless, workflow_cmdline_args, appendBatchOperators=True, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(AutocontextClassificationWorkflow, self).__init__( headless, graph=graph, *args, **kwargs )
        self._applets = []
        
        ## Create applets 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.featureSelectionApplet = FeatureSelectionApplet(self, "Feature Selection", "FeatureSelections")
        self.pcApplet = AutocontextClassificationApplet(self, "PixelClassification")

        # Autocontext constant
        opClassifyTopLevel = self.pcApplet.topLevelOperator
        opClassifyTopLevel.AutocontextIterations.setValue(2)
        
        # Expose for shell
        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.pcApplet)

        if appendBatchOperators:
            # Create applets for batch workflow
            self.batchInputApplet = DataSelectionApplet(self, "Batch Prediction Input Selections", "BatchDataSelection", supportIlastik05Import=False, batchDataGui=True)
            self.batchResultsApplet = BatchIoApplet(self, "Batch Prediction Output Locations")
    
            # Expose in shell        
            self._applets.append(self.batchInputApplet)
            self._applets.append(self.batchResultsApplet)
    
            # Connect batch workflow (NOT lane-based)
            self._initBatchWorkflow()

    def connectLane(self, laneIndex):
        # Get a handle to each operator
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)
        opClassify = self.pcApplet.topLevelOperator.getLane(laneIndex)
        
        # Input Image -> Feature Op
        #         and -> Classification Op (for display)
        opTrainingFeatures.InputImage.connect( opData.Image )
        opClassify.InputImages.connect( opData.Image )
        
        # Feature Images -> Classification Op (for training, prediction)
        opClassify.FeatureImages.connect( opTrainingFeatures.OutputImage )
        opClassify.CachedFeatureImages.connect( opTrainingFeatures.CachedOutputImage )
        
        # Training flags -> Classification Op (for GUI restrictions)
        opClassify.LabelsAllowedFlags.connect( opData.AllowLabels )

    def _initBatchWorkflow(self):
        """
        Connect the batch-mode top-level operators to the training workflow and to eachother.
        """
        # Access applet operators from the training workflow
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator
        opClassify = self.pcApplet.topLevelOperator
        
        # Access the batch operators
        opBatchInputs = self.batchInputApplet.topLevelOperator
        opBatchResults = self.batchResultsApplet.topLevelOperator
        
        ## Create additional batch workflow operators
        opBatchFeatures = OperatorWrapper( OpFeatureSelection, operator_kwargs={'filter_implementation':'Original'}, parent=self, promotedSlotNames=['InputImage'] )
        opBatchPredictor = OperatorWrapper(OpAutocontextBatch, parent=self, promotedSlotNames=['FeatureImage'])
        
        ## Connect Operators ## 
        
        # Provide dataset paths from data selection applet to the batch export applet via an attribute selector
        opBatchResults.DatasetPath.connect( opBatchInputs.ImageName )
        
        # Connect (clone) the feature operator inputs from 
        #  the interactive workflow's features operator (which gets them from the GUI)
        opBatchFeatures.Scales.connect( opTrainingFeatures.Scales )
        opBatchFeatures.FeatureIds.connect( opTrainingFeatures.FeatureIds )
        opBatchFeatures.SelectionMatrix.connect( opTrainingFeatures.SelectionMatrix )
        
        # Classifier and LabelsCount are provided by the interactive workflow
        opBatchPredictor.Classifiers.connect( opClassify.Classifiers )
        opBatchPredictor.MaxLabelValue.connect( opClassify.MaxLabelValue )

        # Sync autocontext contant
        opBatchPredictor.AutocontextIterations.connect( opClassify.AutocontextIterations )
        
        # Connect Image pathway:
        # Input Image -> Features Op -> Prediction Op -> Export
        opBatchFeatures.InputImage.connect( opBatchInputs.Image )
        opBatchPredictor.FeatureImage.connect( opBatchFeatures.OutputImage )
        opBatchResults.ImageToExport.connect( opBatchPredictor.PredictionProbabilities )







