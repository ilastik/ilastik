import warnings

from lazyflow.graph import OperatorWrapper
from ilastik.workflows.objectClassification.objectClassificationWorkflow import ObjectClassificationWorkflowBinary
from ilastik.applets.blockwiseObjectClassification import BlockwiseObjectClassificationApplet, OpBlockwiseObjectClassification, BlockwiseObjectClassificationBatchApplet
from ilastik.applets.dataSelection import DataSelectionApplet

class BlockwiseObjectClassificationWorkflow(ObjectClassificationWorkflowBinary):
    """
    This workflow adds an extra applet to the non-blockwise object classification workflow.
    """
    def __init__( self, headless, workflow_cmdline_args, *args, **kwargs ):
        super( BlockwiseObjectClassificationWorkflow, self ).__init__( headless, workflow_cmdline_args, *args, **kwargs )

        ### INTERACTIVE ###

        # Create applet
        self.blockwiseObjectClassificationApplet = BlockwiseObjectClassificationApplet( self, "Blockwise Object Classification", "Blockwise Object Classification" )
        
        # Expose for shell
        self._applets.append(self.blockwiseObjectClassificationApplet)

        ### BATCH ###

        # Create applets for batch workflow
        self.rawBatchInputApplet = DataSelectionApplet( self,
                                                     "Raw Batch Input Selections",
                                                     "RawBatchDataSelection",
                                                     supportIlastik05Import=False,
                                                     batchDataGui=True)

        # Create applets for batch workflow
        self.binaryBatchInputApplet = DataSelectionApplet( self,
                                                     "Binary Batch Input Selections",
                                                     "BinaryBatchDataSelection",
                                                     supportIlastik05Import=False,
                                                     batchDataGui=True)

        self.batchResultsApplet = BlockwiseObjectClassificationBatchApplet(self, "Batch Output Locations")

        # Expose in shell        
        self._applets.append(self.rawBatchInputApplet)
        self._applets.append(self.binaryBatchInputApplet)
        self._applets.append(self.batchResultsApplet)

        # Connect batch workflow (NOT lane-based)
        self._initBatchWorkflow()


    def connectLane(self, laneIndex):
        super( self.__class__, self ).connectLane( laneIndex )

        # Get the correct lane from each operator
        opTrainingTopLevel = self.objectClassificationApplet.topLevelOperator.getLane(laneIndex)
        opBlockwiseObjectClassification = self.blockwiseObjectClassificationApplet.topLevelOperator.getLane(laneIndex)

        # Wire up the pipeline for this lane
        opBlockwiseObjectClassification.RawImage.connect( opTrainingTopLevel.RawImages )
        opBlockwiseObjectClassification.BinaryImage.connect( opTrainingTopLevel.BinaryImages )
        opBlockwiseObjectClassification.Classifier.connect( opTrainingTopLevel.Classifier )
        opBlockwiseObjectClassification.LabelsCount.connect( opTrainingTopLevel.LabelsCount )

    def _initBatchWorkflow(self):
        # Access applet operators from the training workflow
        opTrainingTopLevel = self.objectClassificationApplet.topLevelOperator
        opBlockwiseObjectClassification = self.blockwiseObjectClassificationApplet.topLevelOperator

        # Access the batch INPUT applets
        opRawBatchInput = self.rawBatchInputApplet.topLevelOperator
        opBinaryBatchInput = self.binaryBatchInputApplet.topLevelOperator
        
        # Connect the blockwise classification operator
        opBatchClassify = OperatorWrapper( OpBlockwiseObjectClassification, parent=self )
        opBatchClassify.RawImage.connect( opRawBatchInput.Image )
        opBatchClassify.BinaryImage.connect( opBinaryBatchInput.Image )
        opBatchClassify.Classifier.connect( opTrainingTopLevel.Classifier )
        opBatchClassify.LabelsCount.connect( opTrainingTopLevel.LabelsCount )
        opBatchClassify.BlockShape3dDict.connect( opBlockwiseObjectClassification.BlockShape3dDict )
        opBatchClassify.HaloPadding3dDict.connect( opBlockwiseObjectClassification.HaloPadding3dDict )
        
        self.opBatchClassify = opBatchClassify
        
        # Connect the batch OUTPUT applet
        opBatchOutput = self.batchResultsApplet.topLevelOperator
        opBatchOutput.DatasetPath.connect( opRawBatchInput.ImageName )
        opBatchOutput.RawImage.connect( opRawBatchInput.Image )
        opBatchOutput.ImageToExport.connect( opBatchClassify.PredictionImage )

    def getHeadlessOutputSlot(self, slotId):
        if slotId == "BatchPredictionImage":
            return self.opBatchClassify.PredictionImage
        
        raise Exception("Unknown headless output slot")
    
