import warnings
import argparse

from ilastik.workflow import Workflow
from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.pixelClassification import PixelClassificationApplet
from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
from ilastik.applets.pixelClassification.opPixelClassification import OpPredictionPipeline
from ilastik.applets.thresholdTwoLevels import ThresholdTwoLevelsApplet, OpThresholdTwoLevels
from ilastik.applets.objectExtraction import ObjectExtractionApplet
from ilastik.applets.objectClassification import ObjectClassificationApplet, ObjectClassificationDataExportApplet
from ilastik.applets.fillMissingSlices import FillMissingSlicesApplet
from ilastik.applets.fillMissingSlices.opFillMissingSlices import OpFillMissingSlicesNoCache
from ilastik.applets.blockwiseObjectClassification import BlockwiseObjectClassificationApplet, OpBlockwiseObjectClassification

from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.operators.generic import OpTransposeSlots, OpSelectSubslot
from lazyflow.operators.valueProviders import OpAttributeSelector

class ObjectClassificationWorkflow(Workflow):
    workflowName = "Object Classification Workflow Base"
    defaultAppletIndex = 1 # show DataSelection by default

    def __init__(self, shell, headless,
                 workflow_cmdline_args,
                 *args, **kwargs):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs:
            del kwargs['graph']
        super(ObjectClassificationWorkflow, self).__init__(shell, headless=headless, graph=graph, *args, **kwargs)

        # Parse workflow-specific command-line args
        parser = argparse.ArgumentParser()
        parser.add_argument('--fillmissing', help="use 'fill missing' applet with chosen detection method", choices=['classic', 'svm', 'none'], default='none')
        parser.add_argument('--filter', help="pixel feature filter implementation.", choices=['Original', 'Refactored', 'Interpolated'], default='Original')
        parser.add_argument('--nobatch', help="do not append batch applets", action='store_true', default=False)
        
        parsed_args, unused_args = parser.parse_known_args(workflow_cmdline_args)
        if unused_args:
            warnings.warn("Unused command-line args: {}".format( unused_args ))

        self.fillMissing = parsed_args.fillmissing
        self.filter_implementation = parsed_args.filter
        self.batch = not parsed_args.nobatch

        self._applets = []

        self.projectMetadataApplet = ProjectMetadataApplet()
        self._applets.append(self.projectMetadataApplet)

        self.setupInputs()
        
        if self.fillMissing != 'none':
            self.fillMissingSlicesApplet = FillMissingSlicesApplet(
                self, "Fill Missing Slices", "Fill Missing Slices", self.fillMissing)
            self._applets.append(self.fillMissingSlicesApplet)


        # our main applets
        self.objectExtractionApplet = ObjectExtractionApplet(workflow=self, name = "Object Feature Selection")
        self.objectClassificationApplet = ObjectClassificationApplet(workflow=self)
        self.dataExportApplet = ObjectClassificationDataExportApplet(self, "Object Prediction Export")
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.WorkingDirectory.connect( self.dataSelectionApplet.topLevelOperator.WorkingDirectory )

        self._applets.append(self.objectExtractionApplet)
        self._applets.append(self.objectClassificationApplet)
        self._applets.append(self.dataExportApplet)

        self.pixel = False
        if isinstance(self, ObjectClassificationWorkflowPixel):
            self.pixel = True
        self.binary = False
        if isinstance(self, ObjectClassificationWorkflowBinary):
            self.binary = True
            
        if self.batch:
            self.dataSelectionAppletBatch = DataSelectionApplet(
                    self, "Batch Inputs", "Batch Inputs", batchDataGui=True)
            self.opDataSelectionBatch = self.dataSelectionAppletBatch.topLevelOperator
            
            if self.pixel:
                self.opDataSelectionBatch.DatasetRoles.setValue(['Raw Data'])
            else:
                if self.binary:
                    self.opDataSelectionBatch.DatasetRoles.setValue(['Raw Data', 'Binary Data'])
                else:
                    self.opDataSelectionBatch.DatasetRoles.setValue(['Raw Data', 'Prediction Maps'])
    
            self.blockwiseObjectClassificationApplet = BlockwiseObjectClassificationApplet(
                self, "Blockwise Object Classification", "Blockwise Object Classification")
            self._applets.append(self.blockwiseObjectClassificationApplet)

            self.batchExportApplet = ObjectClassificationDataExportApplet(
                self, "Batch Object Prediction Export", isBatch=True)
        
            opBatchDataExport = self.batchExportApplet.topLevelOperator
            opBatchDataExport.WorkingDirectory.connect( self.dataSelectionApplet.topLevelOperator.WorkingDirectory )

            self._applets.append(self.dataSelectionAppletBatch)
            self._applets.append(self.batchExportApplet)

            self._initBatchWorkflow()


    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def connectLane(self, laneIndex):
        rawslot, binaryslot = self.connectInputs(laneIndex)

        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)

        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)
        opObjClassification = self.objectClassificationApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)

        opObjExtraction.RawImage.connect(rawslot)
        opObjExtraction.BinaryImage.connect(binaryslot)

        opObjClassification.RawImages.connect(rawslot)
        opObjClassification.LabelsAllowedFlags.connect(opData.AllowLabels)
        opObjClassification.BinaryImages.connect(binaryslot)

        opObjClassification.SegmentationImages.connect(opObjExtraction.LabelImage)
        opObjClassification.ObjectFeatures.connect(opObjExtraction.RegionFeatures)
        opObjClassification.ComputedFeatureNames.connect(opObjExtraction.ComputedFeatureNames)

        # Data Export connections
        opDataExport.RawData.connect( opData.ImageGroup[0] )
        opDataExport.Input.connect( opObjClassification.UncachedPredictionImages )
        opDataExport.RawDatasetInfo.connect( opData.DatasetGroup[0] )

        if self.batch:
            opObjClassification = self.objectClassificationApplet.topLevelOperator.getLane(laneIndex)
            opBlockwiseObjectClassification = self.blockwiseObjectClassificationApplet.topLevelOperator.getLane(laneIndex)

            opBlockwiseObjectClassification.RawImage.connect(opObjClassification.RawImages)
            opBlockwiseObjectClassification.BinaryImage.connect(opObjClassification.BinaryImages)
            opBlockwiseObjectClassification.Classifier.connect(opObjClassification.Classifier)
            opBlockwiseObjectClassification.LabelsCount.connect(opObjClassification.NumLabels)
            opBlockwiseObjectClassification.SelectedFeatures.connect(opObjClassification.SelectedFeatures)

    def _initBatchWorkflow(self):
        # Access applet operators from the training workflow
        opObjectTrainingTopLevel = self.objectClassificationApplet.topLevelOperator
        
        opBlockwiseObjectClassification = self.blockwiseObjectClassificationApplet.topLevelOperator

        

        # If we are not in the binary workflow, connect the thresholding operator.
        # Parameter inputs are cloned from the interactive workflow,
        if not isinstance(self, ObjectClassificationWorkflowBinary):
            opInteractiveThreshold = self.thresholdingApplet.topLevelOperator
            opBatchThreshold = OperatorWrapper(OpThresholdTwoLevels, parent=self)
            opBatchThreshold.MinSize.connect(opInteractiveThreshold.MinSize)
            opBatchThreshold.MaxSize.connect(opInteractiveThreshold.MaxSize)
            opBatchThreshold.HighThreshold.connect(opInteractiveThreshold.HighThreshold)
            opBatchThreshold.LowThreshold.connect(opInteractiveThreshold.LowThreshold)
            opBatchThreshold.SingleThreshold.connect(opInteractiveThreshold.SingleThreshold)
            opBatchThreshold.SmootherSigma.connect(opInteractiveThreshold.SmootherSigma)
            opBatchThreshold.Channel.connect(opInteractiveThreshold.Channel)
            opBatchThreshold.CurOperator.connect(opInteractiveThreshold.CurOperator)

        # OpDataSelectionGroup.ImageGroup is indexed by [laneIndex][roleIndex],
        # but we need a slot that is indexed by [roleIndex][laneIndex]
        # so we can pass each role to the appropriate slots.
        # We use OpTransposeSlots to do this.
        opBatchInputByRole = OpTransposeSlots( parent=self )
        opBatchInputByRole.Inputs.connect( self.opDataSelectionBatch.ImageGroup )
        opBatchInputByRole.OutputLength.setValue(2)
        
        # Lane-indexed multislot for raw data
        batchInputsRaw = opBatchInputByRole.Outputs[0]
        # Lane-indexed multislot for binary/prediction-map data
        batchInputsOther = opBatchInputByRole.Outputs[1]

        # Connect the blockwise classification operator
        # Parameter inputs are cloned from the interactive workflow,
        opBatchClassify = OperatorWrapper(OpBlockwiseObjectClassification, parent=self,
                                          promotedSlotNames=['RawImage', 'BinaryImage'])
        opBatchClassify.Classifier.connect(opObjectTrainingTopLevel.Classifier)
        opBatchClassify.LabelsCount.connect(opObjectTrainingTopLevel.NumLabels)
        opBatchClassify.SelectedFeatures.connect(opObjectTrainingTopLevel.SelectedFeatures)
        opBatchClassify.BlockShape3dDict.connect(opBlockwiseObjectClassification.BlockShape3dDict)
        opBatchClassify.HaloPadding3dDict.connect(opBlockwiseObjectClassification.HaloPadding3dDict)

        #  but image pathway is from the batch pipeline
        op5Raw = OperatorWrapper(OpReorderAxes, parent=self)
        
        if self.fillMissing != 'none':
            opBatchFillMissingSlices = OperatorWrapper(OpFillMissingSlicesNoCache, parent=self)
            opBatchFillMissingSlices.Input.connect(batchInputsRaw)
            op5Raw.Input.connect(opBatchFillMissingSlices.Output)
        else:
            op5Raw.Input.connect(batchInputsRaw)
        
        
        op5Binary = OperatorWrapper(OpReorderAxes, parent=self)
        if not self.binary:
            op5Pred = OperatorWrapper(OpReorderAxes, parent=self)
            op5Pred.Input.connect(batchInputsOther)
            opBatchThreshold.RawInput.connect(op5Raw.Output)
            opBatchThreshold.InputImage.connect(op5Pred.Output)
            op5Binary.Input.connect(opBatchThreshold.Output)
        else:
            op5Binary.Input.connect(batchInputsOther)

        opBatchClassify.RawImage.connect(op5Raw.Output)
        opBatchClassify.BinaryImage.connect(op5Binary.Output)

        self.opBatchClassify = opBatchClassify

        # We need to transpose the dataset group, because it is indexed by [image_index][group_index]
        # But we want it to be indexed by [group_index][image_index] for the RawDatasetInfo connection, below.
        opTransposeDatasetGroup = OpTransposeSlots( parent=self )
        opTransposeDatasetGroup.OutputLength.setValue(1)
        opTransposeDatasetGroup.Inputs.connect( self.opDataSelectionBatch.DatasetGroup )

        # Connect the batch OUTPUT applet
        opBatchExport = self.batchExportApplet.topLevelOperator
        opBatchExport.RawData.connect( batchInputsRaw )
        opBatchExport.RawDatasetInfo.connect( opTransposeDatasetGroup.Outputs[0] )
        opBatchExport.Input.connect( opBatchClassify.PredictionImage )

    def getHeadlessOutputSlot(self, slotId):
        if slotId == "BatchPredictionImage":
            return self.opBatchClassify.PredictionImage
        raise Exception("Unknown headless output slot")

    def getSecondaryHeadlessOutputSlots(self, slotId):
        if slotId == "BatchPredictionImage":
            return [self.opBatchClassify.BlockwiseRegionFeatures]
        raise Exception("Unknown headless output slot")



class ObjectClassificationWorkflowPixel(ObjectClassificationWorkflow):
    workflowName = "Object Classification (from pixel classification)"

    def setupInputs(self):
        data_instructions = 'Use the "Raw Data" tab on the right to load your intensity image(s).'
        
        self.dataSelectionApplet = DataSelectionApplet( self, 
                                                        "Input Data", 
                                                        "Input Data", 
                                                        batchDataGui=False,
                                                        force5d=False, 
                                                        instructionText=data_instructions )
        opData = self.dataSelectionApplet.topLevelOperator
        opData.DatasetRoles.setValue(['Raw Data'])

        self.featureSelectionApplet = FeatureSelectionApplet(
            self,
            "Feature Selection",
            "FeatureSelections",
            filter_implementation=self.filter_implementation
        )

        self.pcApplet = PixelClassificationApplet(
            self, "PixelClassification")
        self.thresholdingApplet = ThresholdTwoLevelsApplet(
            self, "Thresholding", "ThresholdTwoLevels")

        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.pcApplet)
        self._applets.append(self.thresholdingApplet)


    def connectInputs(self, laneIndex):
               
        op5raw = OpReorderAxes(parent=self)
        op5raw.AxisOrder.setValue("txyzc")
        op5pred = OpReorderAxes(parent=self)
        op5pred.AxisOrder.setValue("txyzc")
        op5threshold = OpReorderAxes(parent=self)
        op5threshold.AxisOrder.setValue("txyzc")
        
        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)
        opClassify = self.pcApplet.topLevelOperator.getLane(laneIndex)
        opThreshold = self.thresholdingApplet.topLevelOperator.getLane(laneIndex)

        if self.fillMissing !='none':
            opFillMissingSlices = self.fillMissingSlicesApplet.topLevelOperator.getLane(laneIndex)
            opFillMissingSlices.Input.connect(opData.Image)
            rawslot = opFillMissingSlices.Output
        else:
            rawslot = opData.Image

        opTrainingFeatures.InputImage.connect(rawslot)

        opClassify.InputImages.connect(rawslot)
        opClassify.LabelsAllowedFlags.connect(opData.AllowLabels)
        opClassify.FeatureImages.connect(opTrainingFeatures.OutputImage)
        opClassify.CachedFeatureImages.connect(opTrainingFeatures.CachedOutputImage)

        op5raw.Input.connect(rawslot)
        op5pred.Input.connect(opClassify.PredictionProbabilities)

        opThreshold.RawInput.connect(op5raw.Output)
        opThreshold.InputImage.connect(op5pred.Output)

        op5threshold.Input.connect(opThreshold.CachedOutput)

        return op5raw.Output, op5threshold.Output

    def _initBatchWorkflow(self):
        
        # If we are in pixel workflow, start from raw data
        # The part below is simply copied from the pixel classification
        
        # Access applet operators from the training workflow
        opPixelTrainingDataSelection = self.dataSelectionApplet.topLevelOperator
        opPixelTrainingFeatures = self.featureSelectionApplet.topLevelOperator
        opPixelClassify = self.pcApplet.topLevelOperator
        
        # Access the batch operators
        opBatchInputs = self.dataSelectionAppletBatch.topLevelOperator
        opBatchExport = self.batchExportApplet.topLevelOperator
        
        opBatchInputs.DatasetRoles.connect( opPixelTrainingDataSelection.DatasetRoles )
        
        opSelectFirstLane = OperatorWrapper( OpSelectSubslot, parent=self )
        opSelectFirstLane.Inputs.connect( opPixelTrainingDataSelection.ImageGroup )
        opSelectFirstLane.SubslotIndex.setValue(0)
        
        opSelectFirstRole = OpSelectSubslot( parent=self )
        opSelectFirstRole.Inputs.connect( opSelectFirstLane.Output )
        opSelectFirstRole.SubslotIndex.setValue(0)
        
        ## Create additional batch workflow operators
        # FIXME: this should take the same filter_implementation as the pixel operator!!!
        opBatchPixelFeatures = OperatorWrapper( OpFeatureSelection, operator_kwargs={'filter_implementation':'Original'}, parent=self, promotedSlotNames=['InputImage'] )
        opBatchPixelPredictionPipeline = OperatorWrapper( OpPredictionPipeline, parent=self )
        
        # Connect (clone) the feature operator inputs from 
        #  the interactive workflow's features operator (which gets them from the GUI)
        opBatchPixelFeatures.Scales.connect( opPixelTrainingFeatures.Scales )
        opBatchPixelFeatures.FeatureIds.connect( opPixelTrainingFeatures.FeatureIds )
        opBatchPixelFeatures.SelectionMatrix.connect( opPixelTrainingFeatures.SelectionMatrix )
        
        # Classifier and LabelsCount are provided by the interactive workflow
        opBatchPixelPredictionPipeline.Classifier.connect( opPixelClassify.Classifier )
        opBatchPixelPredictionPipeline.NumClasses.connect( opPixelClassify.NumClasses )
        opBatchPixelPredictionPipeline.FreezePredictions.setValue( False )
                
        # Connect Image pathway:
        # Input Image -> Features Op -> Prediction Op -> Thresholding
        opBatchPixelFeatures.InputImage.connect( opBatchInputs.Image )
        opBatchPixelPredictionPipeline.FeatureImages.connect( opBatchPixelFeatures.OutputImage )

        # We don't actually need the cached path in the batch pipeline.
        # Just connect the uncached features here to satisfy the operator.
        opBatchPixelPredictionPipeline.CachedFeatureImages.connect( opBatchPixelFeatures.OutputImage ) 
        
        # Now connect the object part
        opObjectTrainingTopLevel = self.objectClassificationApplet.topLevelOperator
        
        opBlockwiseObjectClassification = self.blockwiseObjectClassificationApplet.topLevelOperator

        op5Raw = OperatorWrapper(OpReorderAxes, parent=self)

        if self.fillMissing != 'none':
            opBatchFillMissingSlices = OperatorWrapper(OpFillMissingSlicesNoCache, parent=self)
            opBatchFillMissingSlices.Input.connect(opBatchInputs.Image)
            op5Raw.Input.connect(opBatchFillMissingSlices.Output)
        else:
            op5Raw.Input.connect(opBatchInputs.Image)
        
        opInteractiveThreshold = self.thresholdingApplet.topLevelOperator
        opBatchThreshold = OperatorWrapper(OpThresholdTwoLevels, parent=self)
        opBatchThreshold.MinSize.connect(opInteractiveThreshold.MinSize)
        opBatchThreshold.MaxSize.connect(opInteractiveThreshold.MaxSize)
        opBatchThreshold.HighThreshold.connect(opInteractiveThreshold.HighThreshold)
        opBatchThreshold.LowThreshold.connect(opInteractiveThreshold.LowThreshold)
        opBatchThreshold.SingleThreshold.connect(opInteractiveThreshold.SingleThreshold)
        opBatchThreshold.SmootherSigma.connect(opInteractiveThreshold.SmootherSigma)
        opBatchThreshold.Channel.connect(opInteractiveThreshold.Channel)
        opBatchThreshold.CurOperator.connect(opInteractiveThreshold.CurOperator)
        
        #  Image pathway is from the batch pipeline
        op5Pred = OperatorWrapper(OpReorderAxes, parent=self)
        op5Pred.Input.connect(opBatchPixelPredictionPipeline.HeadlessPredictionProbabilities)
        op5Binary = OperatorWrapper(OpReorderAxes, parent=self)
        opBatchThreshold.RawInput.connect(op5Raw.Output)
        opBatchThreshold.InputImage.connect(op5Pred.Output)
        op5Binary.Input.connect(opBatchThreshold.Output)
        
        # BATCH outputs are computed BLOCKWISE.
        # Connect the blockwise classification operator
        # Parameter inputs are cloned from the interactive workflow,
        opBatchObjectClassify = OperatorWrapper(OpBlockwiseObjectClassification, parent=self,
                                          promotedSlotNames=['RawImage', 'BinaryImage'])
        opBatchObjectClassify.Classifier.connect(opObjectTrainingTopLevel.Classifier)
        opBatchObjectClassify.LabelsCount.connect(opObjectTrainingTopLevel.NumLabels)
        opBatchObjectClassify.SelectedFeatures.connect(opObjectTrainingTopLevel.SelectedFeatures)
        opBatchObjectClassify.BlockShape3dDict.connect(opBlockwiseObjectClassification.BlockShape3dDict)
        opBatchObjectClassify.HaloPadding3dDict.connect(opBlockwiseObjectClassification.HaloPadding3dDict)        
        
        opBatchObjectClassify.RawImage.connect(op5Raw.Output)
        opBatchObjectClassify.BinaryImage.connect(op5Binary.Output)

        self.opBatchClassify = opBatchObjectClassify

        # We need to transpose the dataset group, because it is indexed by [image_index][group_index]
        # But we want it to be indexed by [group_index][image_index] for the RawDatasetInfo connection, below.
        opTransposeDatasetGroup = OpTransposeSlots( parent=self )
        opTransposeDatasetGroup.OutputLength.setValue(1)
        opTransposeDatasetGroup.Inputs.connect( opBatchInputs.DatasetGroup )

        # Connect the batch OUTPUT applet
        opBatchExport.Input.connect( opBatchObjectClassify.PredictionImage )
        opBatchExport.RawData.connect( opBatchInputs.Image )
        opBatchExport.RawDatasetInfo.connect( opTransposeDatasetGroup.Outputs[0] )

class ObjectClassificationWorkflowBinary(ObjectClassificationWorkflow):
    workflowName = "Object Classification (from binary image)"

    def setupInputs(self):
        data_instructions = 'Use the "Raw Data" tab to load your intensity image(s).\n\n'\
                            'Use the "Segmentation Image" tab to load your binary mask image(s).'
        
        self.dataSelectionApplet = DataSelectionApplet( self,
                                                        "Input Data",
                                                        "Input Data",
                                                        batchDataGui=False,
                                                        force5d=True,
                                                        instructionText=data_instructions )

        opData = self.dataSelectionApplet.topLevelOperator
        opData.DatasetRoles.setValue(['Raw Data', 'Segmentation Image'])
        self._applets.append(self.dataSelectionApplet)

    def connectInputs(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        if self.fillMissing != 'none':
            opFillMissingSlices = self.fillMissingSlicesApplet.topLevelOperator.getLane(laneIndex)
            opFillMissingSlices.Input.connect(opData.ImageGroup[0])
            rawslot = opFillMissingSlices.Output
        else:
            rawslot = opData.ImageGroup[0]

        return rawslot, opData.ImageGroup[1]


class ObjectClassificationWorkflowPrediction(ObjectClassificationWorkflow):
    workflowName = "Object Classification (from prediction image)"

    def setupInputs(self):
        data_instructions = 'Use the "Raw Data" tab to load your intensity image(s).\n\n'\
                            'Use the "Prediction Maps" tab to load your pixel-wise probability image(s).'
        
        self.dataSelectionApplet = DataSelectionApplet( self,
                                                        "Input Data",
                                                        "Input Data",
                                                        batchDataGui=False,
                                                        force5d=True,
                                                        instructionText=data_instructions )

        opData = self.dataSelectionApplet.topLevelOperator
        opData.DatasetRoles.setValue(['Raw Data', 'Prediction Maps'])
        self._applets.append(self.dataSelectionApplet)

        self.thresholdingApplet = ThresholdTwoLevelsApplet(self, "Threshold and Size Filter", "ThresholdTwoLevels")
        self._applets.append(self.thresholdingApplet)

    def connectInputs(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTwoLevelThreshold = self.thresholdingApplet.topLevelOperator.getLane(laneIndex)

        op5raw = OpReorderAxes(parent=self)
        op5raw.AxisOrder.setValue("txyzc")
        op5predictions = OpReorderAxes(parent=self)
        op5predictions.AxisOrder.setValue("txyzc")

        if self.fillMissing != 'none':
            opFillMissingSlices = self.fillMissingSlicesApplet.topLevelOperator.getLane(laneIndex)
            opFillMissingSlices.Input.connect(opData.ImageGroup[0])
            rawslot = opFillMissingSlices.Output
        else:
            rawslot = opData.ImageGroup[0]

        op5raw.Input.connect(rawslot)
        op5predictions.Input.connect(opData.ImageGroup[1])

        opTwoLevelThreshold.RawInput.connect(op5raw.Output)
        opTwoLevelThreshold.InputImage.connect(op5predictions.Output)

        op5Binary = OpReorderAxes(parent=self)
        op5Binary.AxisOrder.setValue("txyzc")
        op5Binary.Input.connect(opTwoLevelThreshold.CachedOutput)

        return op5raw.Output, op5Binary.Output

if __name__ == "__main__":
    from sys import argv
    w = ObjectClassificationWorkflow(True, argv)
    
