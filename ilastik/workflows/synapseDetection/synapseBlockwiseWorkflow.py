from lazyflow.graph import OperatorWrapper
from lazyflow.operators import Op5ifyer
from synapseObjectClassificationWorkflow import SynapseObjectClassificationWorkflow
from ilastik.applets.thresholdTwoLevels import OpThresholdTwoLevels
from ilastik.applets.blockwiseObjectClassification \
    import BlockwiseObjectClassificationApplet, OpBlockwiseObjectClassification, BlockwiseObjectClassificationBatchApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.fillMissingSlices import FillMissingSlicesApplet
from ilastik.applets.fillMissingSlices.opFillMissingSlices import OpFillMissingSlicesNoCache

class SynapseBlockwiseWorkflow(SynapseObjectClassificationWorkflow):
    """
    This workflow adds an extra applet to the non-blockwise object classification workflow.
    """
    def __init__( self, *args, **kwargs ):
        super( SynapseBlockwiseWorkflow, self ).__init__( *args, **kwargs )

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
        self.predictionBatchInputApplet = DataSelectionApplet( self,
                                                     "Prediction Batch Input Selections",
                                                     "PredictionBatchDataSelection",
                                                     supportIlastik05Import=False,
                                                     batchDataGui=True)

        self.batchResultsApplet = BlockwiseObjectClassificationBatchApplet(self, "Prediction Output Locations")

        # Expose in shell        
        self._applets.append(self.rawBatchInputApplet)
        self._applets.append(self.predictionBatchInputApplet)
        self._applets.append(self.batchResultsApplet)

        # Connect batch workflow (NOT lane-based)
        self._initBatchWorkflow()


    def connectLane(self, laneIndex):
        super( SynapseBlockwiseWorkflow, self ).connectLane( laneIndex )

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
        opInteractiveThreshold = self.thresholdTwoLevelsApplet.topLevelOperator
        opBlockwiseObjectClassification = self.blockwiseObjectClassificationApplet.topLevelOperator

        # Access the batch INPUT applets
        opRawBatchInput = self.rawBatchInputApplet.topLevelOperator
        opPredictionBatchInput = self.predictionBatchInputApplet.topLevelOperator
        
        opBatchFillMissingSlices = OperatorWrapper( OpFillMissingSlicesNoCache, parent=self )

        # Connect the thresholding operator.
        # Parameter inputs are cloned from the interactive workflow,
        opBatchThreshold = OperatorWrapper( OpThresholdTwoLevels, parent=self )
        opBatchThreshold.MinSize.connect( opInteractiveThreshold.MinSize )
        opBatchThreshold.MaxSize.connect( opInteractiveThreshold.MaxSize )
        opBatchThreshold.HighThreshold.connect( opInteractiveThreshold.HighThreshold )
        opBatchThreshold.LowThreshold.connect( opInteractiveThreshold.LowThreshold )
        opBatchThreshold.SmootherSigma.connect( opInteractiveThreshold.SmootherSigma )
        opBatchThreshold.Channel.connect( opInteractiveThreshold.Channel )
        #  but image inputs come from the batch data selection.        
        opBatchThreshold.RawInput.connect( opRawBatchInput.Image )
        opBatchThreshold.InputImage.connect( opPredictionBatchInput.Image )
        
        # Connect the blockwise classification operator
        # Parameter inputs are cloned from the interactive workflow,
        opBatchClassify = OperatorWrapper( OpBlockwiseObjectClassification, parent=self )
        opBatchClassify.Classifier.connect( opTrainingTopLevel.Classifier )
        opBatchClassify.LabelsCount.connect( opTrainingTopLevel.LabelsCount )
        opBatchClassify.BlockShape3dDict.connect( opBlockwiseObjectClassification.BlockShape3dDict )
        opBatchClassify.HaloPadding3dDict.connect( opBlockwiseObjectClassification.HaloPadding3dDict )
        
        #  but image pathway is from the batch pipeline
        opBatchFillMissingSlices.Input.connect( opRawBatchInput.Image )
        op5Raw = OperatorWrapper( Op5ifyer, parent=self )
        op5Raw.input.connect( opBatchFillMissingSlices.Output )
        op5Binary = OperatorWrapper( Op5ifyer, parent=self )
        op5Binary.input.connect( opBatchThreshold.Output )
        
        opBatchClassify.RawImage.connect( op5Raw.output )
        opBatchClassify.BinaryImage.connect( op5Binary.output )
        
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
    
    def getSecondaryHeadlessOutputSlots(self, slotId):
        if slotId == "BatchPredictionImage":
            return [self.opBatchClassify.BlockwiseRegionFeatures]        
        raise Exception("Unknown headless output slot")
