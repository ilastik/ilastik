from ilastik.workflow import Workflow

from ilastik.applets.pixelClassification import PixelClassificationApplet
from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.batchIo import BatchIoApplet

from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection

from lazyflow.graph import Graph, Operator, OperatorWrapper
from lazyflow.operators import OpPredictRandomForest, OpAttributeSelector

class PixelClassificationWorkflow(Workflow):

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(PixelClassificationWorkflow, self).__init__( graph=graph )
        self._applets = []

        ######################
        # Interactive workflow
        ######################
        
        ## Create applets 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.featureSelectionApplet = FeatureSelectionApplet(self, "Feature Selection", "FeatureSelections")
        self.pcApplet = PixelClassificationApplet(self, "PixelClassification")

        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.pcApplet)

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
        
#        ######################
#        # Batch workflow
#        ######################
#        
#        ## Create applets
#        self.batchInputApplet = DataSelectionApplet(self, "Batch Prediction Input Selections", "BatchDataSelection", supportIlastik05Import=False, batchDataGui=True)
#        self.batchResultsApplet = BatchIoApplet(self, "Batch Prediction Output Locations")
#
#        ## Access applet operators
#        opBatchInputs = self.batchInputApplet.topLevelOperator
#        opBatchInputs.name = 'opBatchInputs'
#        opBatchResults = self.batchResultsApplet.topLevelOperator
#        
#        ## Create additional batch workflow operators
#        opBatchFeatures = OperatorWrapper( OpFeatureSelection, graph=graph, parent=self, promotedSlotNames=['InputImage'] )
#        opBatchFeatures.name = "opBatchFeatures"
#        opBatchPredictor = OperatorWrapper( OpPredictRandomForest, graph=graph, parent=self, promotedSlotNames=['Image'])
#        opBatchPredictor.name = "opBatchPredictor"
#        opSelectBatchDatasetPath = OperatorWrapper( OpAttributeSelector, graph=graph, parent=self )
#        
#        ## Connect Operators ## 
#        
#        # Provide dataset paths from data selection applet to the batch export applet via an attribute selector
#        opSelectBatchDatasetPath.InputObject.connect( opBatchInputs.Dataset )
#        opSelectBatchDatasetPath.AttributeName.setValue( 'filePath' )
#        opBatchResults.DatasetPath.connect( opSelectBatchDatasetPath.Result )
#        
#        # Connect (clone) the feature operator inputs from 
#        #  the interactive workflow's features operator (which gets them from the GUI)
#        opBatchFeatures.Scales.connect( opTrainingFeatures.Scales )
#        opBatchFeatures.FeatureIds.connect( opTrainingFeatures.FeatureIds )
#        opBatchFeatures.SelectionMatrix.connect( opTrainingFeatures.SelectionMatrix )
#        
#        # Classifier and LabelsCount are provided by the interactive workflow
#        opBatchPredictor.Classifier.connect( opClassify.Classifier )
#        opBatchPredictor.LabelsCount.connect( opClassify.MaxLabelValue )
#        
#        # Connect Image pathway:
#        # Input Image -> Features Op -> Prediction Op -> Export
#        opBatchFeatures.InputImage.connect( opBatchInputs.Image )
#        opBatchPredictor.Image.connect( opBatchFeatures.OutputImage )
#        opBatchResults.ImageToExport.connect( opBatchPredictor.PMaps )

#        self._applets.append(self.batchInputApplet)
#        self._applets.append(self.batchResultsApplet)

        # The shell needs a slot from which he can read the list of image names to switch between.
        # Use an OpAttributeSelector to create a slot containing just the filename from the OpDataSelection's DatasetInfo slot.
#        opSelectFilename = OperatorWrapper( OpAttributeSelector, graph=graph, parent=self )
#        opSelectFilename.InputObject.connect( opData.Dataset )
#        opSelectFilename.AttributeName.setValue( 'filePath' )
#
#        self._imageNameListSlot = opSelectFilename.Result
