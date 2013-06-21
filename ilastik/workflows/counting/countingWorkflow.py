from lazyflow.graph import Graph, Operator, OperatorWrapper

from ilastik.workflow import Workflow

from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet

#    PixelClassificationApplet, PixelClassificationBatchResultsApplet
#from ilastik.applets.objectExtraction import ObjectExtractionApplet
#from ilastik.applets.objectClassification import ObjectClassificationApplet
#from ilastik.applets.objectViewer import ObjectViewerApplet
from ilastik.applets.counting3d import Counting3dApplet, CountingBatchResultsApplet
from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
from ilastik.applets.counting3d.opCounting3d import OpPredictionPipeline

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.operators.ioOperators.opInputDataReader import OpInputDataReader 
from lazyflow.operators import OpAttributeSelector, OpTransposeSlots


class CountingWorkflow(Workflow):
    name = "Counting Workflow"

    def __init__(self, headless, workflow_cmdline_args, appendBatchOperators=True, *args, **kwargs):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs: del kwargs['graph']
        super( CountingWorkflow, self ).__init__( headless, graph=graph, *args, **kwargs )

        ######################
        # Interactive workflow
        ######################

        self.projectMetadataApplet = ProjectMetadataApplet()

        self.dataSelectionApplet = DataSelectionApplet(self,
                                                       "Data Selection",
                                                       "DataSelection",
                                                       batchDataGui=False,
                                                       force5d=False
                                                      )
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ['Raw Data'] )

        self.featureSelectionApplet = FeatureSelectionApplet(self,
                                                             "Feature Selection",
                                                             "FeatureSelections")

        #self.pcApplet = PixelClassificationApplet(self, "PixelClassification")
        self.counting3dApplet = Counting3dApplet(workflow=self)

        self._applets = []
        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.counting3dApplet)


        if appendBatchOperators:
            # Create applets for batch workflow
            self.batchInputApplet = DataSelectionApplet(self, "Batch Prediction Input Selections", "BatchDataSelection", supportIlastik05Import=False, batchDataGui=True)
            self.batchResultsApplet = CountingBatchResultsApplet(self, "Batch Prediction Output Locations")
    
            # Expose in shell        
            self._applets.append(self.batchInputApplet)
            self._applets.append(self.batchResultsApplet)
    
            # Connect batch workflow (NOT lane-based)
            self._initBatchWorkflow()

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def connectLane(self, laneIndex):
        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)
        opCounting3d = self.counting3dApplet.topLevelOperator.getLane(laneIndex)

        #### connect input image
        opTrainingFeatures.InputImage.connect(opData.Image)

        opCounting3d.InputImages.connect(opData.Image)
        opCounting3d.FeatureImages.connect(opTrainingFeatures.OutputImage)
        opCounting3d.LabelsAllowedFlags.connect(opData.AllowLabels)
        opCounting3d.CachedFeatureImages.connect( opTrainingFeatures.CachedOutputImage )
        #opCounting3d.UserLabels.connect(opClassify.LabelImages)
        #opCounting3d.ForegroundLabels.connect(opObjExtraction.LabelImage)

    def _initBatchWorkflow(self):
        """
        Connect the batch-mode top-level operators to the training workflow and to eachother.
        """
        # Access applet operators from the training workflow
        opTrainingDataSelection = self.dataSelectionApplet.topLevelOperator
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator
        opClassify = self.counting3dApplet.topLevelOperator
        
        # Access the batch operators
        opBatchInputs = self.batchInputApplet.topLevelOperator
        opBatchResults = self.batchResultsApplet.topLevelOperator
        
        opBatchInputs.DatasetRoles.connect( opTrainingDataSelection.DatasetRoles )
        
        ## Create additional batch workflow operators
        opBatchFeatures = OperatorWrapper( OpFeatureSelection, operator_kwargs={'filter_implementation':'Original'}, parent=self, promotedSlotNames=['InputImage'] )
        opBatchPredictionPipeline = OperatorWrapper( OpPredictionPipeline, parent=self )
        
        ## Connect Operators ##
        opTranspose = OpTransposeSlots( parent=self )
        opTranspose.OutputLength.setValue(1)
        opTranspose.Inputs.connect( opBatchInputs.DatasetGroup )
        
        opFilePathProvider = OperatorWrapper(OpAttributeSelector, parent=self)
        opFilePathProvider.InputObject.connect( opTranspose.Outputs[0] )
        opFilePathProvider.AttributeName.setValue( 'filePath' )
        
        # Provide dataset paths from data selection applet to the batch export applet
        opBatchResults.DatasetPath.connect( opFilePathProvider.Result )
        
        # Connect (clone) the feature operator inputs from 
        #  the interactive workflow's features operator (which gets them from the GUI)
        opBatchFeatures.Scales.connect( opTrainingFeatures.Scales )
        opBatchFeatures.FeatureIds.connect( opTrainingFeatures.FeatureIds )
        opBatchFeatures.SelectionMatrix.connect( opTrainingFeatures.SelectionMatrix )
        
        # Classifier and LabelsCount are provided by the interactive workflow
        opBatchPredictionPipeline.Classifier.connect( opClassify.Classifier )
        opBatchPredictionPipeline.MaxLabel.connect( opClassify.MaxLabelValue )
        opBatchPredictionPipeline.FreezePredictions.setValue( False )
        
        # Provide these for the gui
        opBatchResults.RawImage.connect( opBatchInputs.Image )
        opBatchResults.PmapColors.connect( opClassify.PmapColors )
        opBatchResults.LabelNames.connect( opClassify.LabelNames )
        
        # Connect Image pathway:
        # Input Image -> Features Op -> Prediction Op -> Export
        opBatchFeatures.InputImage.connect( opBatchInputs.Image )
        opBatchPredictionPipeline.FeatureImages.connect( opBatchFeatures.OutputImage )
        opBatchResults.ImageToExport.connect( opBatchPredictionPipeline.HeadlessPredictionProbabilities )

        # We don't actually need the cached path in the batch pipeline.
        # Just connect the uncached features here to satisfy the operator.
        opBatchPredictionPipeline.CachedFeatureImages.connect( opBatchFeatures.OutputImage )

        self.opBatchPredictionPipeline = opBatchPredictionPipeline

    def getHeadlessOutputSlot(self, slotId):
        # "Regular" (i.e. with the images that the user selected as input data)
        if slotId == "Predictions":
            return self.counting3dApplet.topLevelOperator.HeadlessPredictionProbabilities
        elif slotId == "PredictionsUint8":
            return self.counting3dApplet.topLevelOperator.HeadlessUint8PredictionProbabilities
        # "Batch" (i.e. with the images that the user selected as batch inputs).
        elif slotId == "BatchPredictions":
            return self.opBatchPredictionPipeline.HeadlessPredictionProbabilities
        if slotId == "BatchPredictionsUint8":
            return self.opBatchPredictionPipeline.HeadlessUint8PredictionProbabilities
        
        raise Exception("Unknown headless output slot")
    
