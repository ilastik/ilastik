from ilastik.workflow import Workflow

#from ilastik.applets.pixelClassification import PixelClassificationApplet
from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
#from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.batchIo import BatchIoApplet

from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection

from lazyflow.graph import Graph, Operator, OperatorWrapper
from lazyflow.operators import OpPredictRandomForest, OpAttributeSelector

from applets.featureSelection import FeatureSelectionAutocontextApplet
from applets.pixelClassification import AutocontextClassificationApplet

class PixelClassificationWorkflow(Workflow):
    
    def __init__(self):
        super(PixelClassificationWorkflow, self).__init__()
        self._applets = []

        # Create a graph to be shared by all operators
        graph = Graph()
        self._graph = graph

        ######################
        # Interactive workflow
        ######################
        
        ## Create applets 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet(graph, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        opData = self.dataSelectionApplet.topLevelOperator
        self.featureSelectionApplet = FeatureSelectionAutocontextApplet(graph, "Feature Selection", "FeatureSelections")
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator
        self.pcApplet = AutocontextClassificationApplet(graph, "PixelClassification")

        ## Access applet operators
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
        
        ######################
        # Batch workflow
        ######################
        
        ## Create applets
        '''
        self.batchInputApplet = DataSelectionApplet(graph, "Batch Inputs", "BatchDataSelection", supportIlastik05Import=False, batchDataGui=True)
        self.batchResultsApplet = BatchIoApplet(graph, "Batch Results")

        ## Access applet operators
        opBatchInputs = self.batchInputApplet.topLevelOperator
        opBatchInputs.name = 'opBatchInputs'
        opBatchResults = self.batchResultsApplet.topLevelOperator
        
        ## Create additional batch workflow operators
        opBatchFeatures = OperatorWrapper( OpFeatureSelection(graph=graph), promotedSlotNames=['InputImage'] )
        opBatchFeatures.name = "opBatchFeatures"
        opBatchPredictor = OperatorWrapper( OpPredictRandomForest(graph=graph), promotedSlotNames=['Image'])
        opBatchPredictor.name = "opBatchPredictor"
        opSelectBatchDatasetPath = OperatorWrapper( OpAttributeSelector(graph=graph) )
        
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
        opBatchPredictor.Classifier.connect( opClassify.Classifier )
        opBatchPredictor.LabelsCount.connect( opClassify.MaxLabelValue )
        
        # Connect Image pathway:
        # Input Image -> Features Op -> Prediction Op -> Export
        opBatchFeatures.InputImage.connect( opBatchInputs.Image )
        opBatchPredictor.Image.connect( opBatchFeatures.OutputImage )
        opBatchResults.ImageToExport.connect( opBatchPredictor.PMaps )
        '''
        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.pcApplet)
        #self._applets.append(self.batchInputApplet)
        #self._applets.append(self.batchResultsApplet)
        
        # The shell needs a slot from which he can read the list of image names to switch between.
        # Use an OpAttributeSelector to create a slot containing just the filename from the OpDataSelection's DatasetInfo slot.
        opSelectFilename = OperatorWrapper( OpAttributeSelector(graph=graph) )
        opSelectFilename.InputObject.connect( opData.Dataset )
        opSelectFilename.AttributeName.setValue( 'filePath' )
        
        self._imageNameListSlot = opSelectFilename.Result
        
    @property
    def applets(self):
        return self._applets
    

    @property
    def imageNameListSlot(self):
        return self._imageNameListSlot
    
    @property
    def graph( self ):
        '''the lazyflow graph shared by the applets'''
        return self._graph
