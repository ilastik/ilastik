import warnings

from lazyflow.graph import OperatorWrapper
from workflows.objectClassification.objectClassificationWorkflowBinary import ObjectClassificationWorkflowBinary
from ilastik.applets.blockwiseObjectClassification import BlockwiseObjectClassificationApplet, OpBlockwiseObjectClassification

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.batchIo import BatchIoApplet

class BlockwiseObjectClassificationWorkflow(ObjectClassificationWorkflowBinary):
    """
    This workflow adds an extra applet to the non-blockwise object classification workflow.
    """
    def __init__( self, *args, **kwargs ):
        super( self.__class__, self ).__init__( *args, **kwargs )

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

        self.batchResultsApplet = BatchIoApplet(self, "Batch Output Locations")

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

        warnings.warn("Instead of hard-coding blockshape/halo, use a GUI?  Or choose them automatically?  Or maybe use a config file?")
        opBlockwiseObjectClassification.BlockShape.setValue( (1,256,256,256,1) )
        opBlockwiseObjectClassification.HaloPadding.setValue( (1,50,50,50,1) )

    def _initBatchWorkflow(self):
        # Access applet operators from the training workflow
        opTrainingTopLevel = self.objectClassificationApplet.topLevelOperator

        # Access the batch INPUT applets
        opRawBatchInput = self.rawBatchInputApplet.topLevelOperator
        opBinaryBatchInput = self.binaryBatchInputApplet.topLevelOperator
        
        # Connect the blockwise classification operator
        opBatchClassify = OperatorWrapper( OpBlockwiseObjectClassification, parent=self )
        opBatchClassify.RawImage.connect( opRawBatchInput.Image )
        opBatchClassify.BinaryImage.connect( opBinaryBatchInput.Image )
        opBatchClassify.Classifier.connect( opTrainingTopLevel.Classifier )
        
        # Connect the batch OUTPUT applet
        opBatchOutput = self.batchResultsApplet.topLevelOperator
        opBatchOutput.DatasetPath.connect( opRawBatchInput.ImageName )
        opBatchOutput.RawImage.connect( opRawBatchInput.Image )
        opBatchOutput.ImageToExport.connect( opBatchClassify.PredictionImage )        

    def getHeadlessOutputSlot(self, slotId):
        
        raise Exception("Unknown headless output slot")
    
