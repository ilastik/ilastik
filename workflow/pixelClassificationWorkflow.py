from ilastik.workflow import Workflow

#from ilastik.applets.pixelClassification import PixelClassificationApplet
from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
#from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.batchIo import BatchIoApplet

from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection

from lazyflow.graph import Graph, Operator, OperatorWrapper
from lazyflow.operators import OpPredictRandomForest, OpAttributeSelector

from context.applets.featureSelection import FeatureSelectionAutocontextApplet
from context.applets.pixelClassification import AutocontextClassificationApplet

class PixelClassificationWorkflow(Workflow):
    
    def __init__(self):
        graph = Graph()
        super(PixelClassificationWorkflow, self).__init__( graph=graph )
        self._applets = []

        ######################
        # Interactive workflow
        ######################
        
        ## Create applets 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.featureSelectionApplet = FeatureSelectionAutocontextApplet(self, "Feature Selection", "FeatureSelections")
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
        
        ######################
        # Batch workflow
        ######################
        
        ## Create applets

        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.pcApplet)
        #self._applets.append(self.batchInputApplet)
        #self._applets.append(self.batchResultsApplet)
        
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
    
