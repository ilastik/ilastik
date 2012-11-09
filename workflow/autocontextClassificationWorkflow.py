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
from context.applets.pixelClassification import AutocontextClassificationApplet
from context.applets.pixelClassification.opAutocontextBatch import OpAutocontextBatch

class AutocontextClassificationWorkflow(Workflow):
    
    def __init__(self):
        graph = Graph()
        super(AutocontextClassificationWorkflow, self).__init__( graph=graph )
        self._applets = []

        ######################
        # Interactive workflow
        ######################
        
        ## Create applets 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.featureSelectionApplet = FeatureSelectionApplet(self, "Feature Selection", "FeatureSelections")
        self.pcApplet = AutocontextClassificationApplet(self, "PixelClassification")

        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator
        opClassify = self.pcApplet.topLevelOperator
        
        ## Connect operators ##
        
        # Input Image -> Feature Op
        #         and -> Classification Op (for display)
        opTrainingFeatures.InputImage.connect( opData.Image )
        opClassify.InputImages.connect( opData.Image )
        
        # Feature Images -> Classification Op (for training, prediction)
        opClassify.FeatureImages.connect( opTrainingFeatures.OutputImage )
        opClassify.CachedFeatureImages.connect( opTrainingFeatures.CachedOutputImage )
        
        # Training flags -> Classification Op (for GUI restrictions)
        opClassify.LabelsAllowedFlags.connect( opData.AllowLabels )
        opClassify.AutocontextIterations.setValue(2)
        
        ######################
        # Batch workflow
        ######################
        ## Create applets
        self.batchInputApplet = DataSelectionApplet(self, "Batch Inputs", "BatchDataSelection", supportIlastik05Import=False, batchDataGui=True)
        self.batchResultsApplet = BatchIoApplet(self, "Batch Results")

        ## Access applet operators
        opBatchInputs = self.batchInputApplet.topLevelOperator
        opBatchInputs.name = 'opBatchInputs'
        opBatchResults = self.batchResultsApplet.topLevelOperator
        
        ## Create additional batch workflow operators
        opBatchFeatures = OperatorWrapper( OpFeatureSelection, graph=graph, parent=self, promotedSlotNames=['InputImage'] )
        opBatchFeatures.name = "opBatchFeatures"
        
        opBatchPredictor = OperatorWrapper(OpAutocontextBatch, graph=graph, parent=self, promotedSlotNames=['FeatureImage'])
        #opBatchPredictor = OperatorWrapper( OpPredictRandomForest, graph=graph, parent=self, promotedSlotNames=['Image'])
        opBatchPredictor.name = "opBatchPredictor"
        opSelectBatchDatasetPath = OperatorWrapper( OpAttributeSelector, graph=graph, parent=self )
        
        ## Connect Operators ## 
        
        # Provide dataset paths from data selection applet to the batch export applet via an attribute selector
        opSelectBatchDatasetPath.InputObject.connect( opBatchInputs.Dataset )
        opSelectBatchDatasetPath.AttributeName.setValue( 'filePath' )
        opBatchResults.DatasetPath.connect( opSelectBatchDatasetPath.Result )
        
        # Connect (clone) the feature operator inputs from 
        #  the interactive workflow's features operator (which gets them from the GUI)
        opBatchFeatures.Scales.connect( opTrainingFeatures.Scales )
        opBatchFeatures.FeatureIds.connect( opTrainingFeatures.FeatureIds )
        opBatchFeatures.SelectionMatrix.connect( opTrainingFeatures.SelectionMatrix )
        
        # Classifier and LabelsCount are provided by the interactive workflow
        opBatchPredictor.Classifiers.connect( opClassify.Classifiers )
        opBatchPredictor.MaxLabelValue.connect( opClassify.MaxLabelValue )
        opBatchPredictor.AutocontextIterations.connect( opClassify.AutocontextIterations )
        
        # Connect Image pathway:
        # Input Image -> Features Op -> Prediction Op -> Export
        opBatchFeatures.InputImage.connect( opBatchInputs.Image )
        opBatchPredictor.FeatureImage.connect( opBatchFeatures.OutputImage )
        opBatchResults.ImageToExport.connect( opBatchPredictor.PredictionProbabilities )
        
        #TEST
        '''
        opBatchResults.Scales.connect( opBatchFeatures.Scales )
        opBatchResults.FeatureIds.connect( opBatchFeatures.FeatureIds )
        opBatchResults.SelectionMatrix.connect( opBatchFeatures.SelectionMatrix )
        opBatchResults.InputImage.connect( opBatchFeatures.InputImage )
        
        opBatchResults.Classifiers.connect( opBatchPredictor.Classifiers )
        opBatchResults.MaxLabelValue.connect( opBatchPredictor.MaxLabelValue )
        opBatchResults.AutocontextIterations.connect( opBatchPredictor.AutocontextIterations )
        opBatchPredictor.FeatureImage.connect( opBatchFeatures.OutputImage )
        '''
        ## Create applets

        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.pcApplet)
        self._applets.append(self.batchInputApplet)
        self._applets.append(self.batchResultsApplet)
        
        # The shell needs a slot from which he can read the list of image names to switch between.
        # Use an OpAttributeSelector to create a slot containing just the filename from the OpDataSelection's DatasetInfo slot.
        opSelectFilename = OperatorWrapper( OpAttributeSelector, graph=graph, parent=self)
        opSelectFilename.InputObject.connect( opData.Dataset )
        opSelectFilename.AttributeName.setValue( 'filePath' )
        
        self._imageNameListSlot = opSelectFilename.Result
        
    @property
    def applets(self):
        return self._applets
    

    @property
    def imageNameListSlot(self):
        return self._imageNameListSlot
    
