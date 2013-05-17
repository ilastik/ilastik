import warnings
from ilastik.workflow import Workflow
from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.pixelClassification import PixelClassificationApplet
from ilastik.applets.thresholdTwoLevels import ThresholdTwoLevelsApplet, OpThresholdTwoLevels
from ilastik.applets.objectExtraction import ObjectExtractionApplet
from ilastik.applets.objectClassification import ObjectClassificationApplet
from ilastik.applets.fillMissingSlices import FillMissingSlicesApplet
from ilastik.applets.fillMissingSlices.opFillMissingSlices import OpFillMissingSlicesNoCache
from ilastik.applets.blockwiseObjectClassification \
    import BlockwiseObjectClassificationApplet, OpBlockwiseObjectClassification, BlockwiseObjectClassificationBatchApplet

from lazyflow.graph import Graph
from lazyflow.operators import OpSegmentation, Op5ifyer, OpTransposeSlots
from lazyflow.graph import OperatorWrapper

import argparse

class ObjectClassificationWorkflow(Workflow):
    workflowName = "Object Classification Workflow Base"
    defaultAppletIndex = 1 # show DataSelection by default

    def __init__(self, headless,
                 workflow_cmdline_args,
                 *args, **kwargs):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs:
            del kwargs['graph']
        super(ObjectClassificationWorkflow, self).__init__(headless=headless, graph=graph, *args, **kwargs)

        # Parse workflow-specific command-line args
        parser = argparse.ArgumentParser()
        parser.add_argument('--fillmissing', help="use 'fill missing' applet", action='store_true', default=False)
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

        if self.fillMissing:
            self.fillMissingSlicesApplet = FillMissingSlicesApplet(
                self, "Fill Missing Slices", "Fill Missing Slices")
            self._applets.append(self.fillMissingSlicesApplet)

        # our main applets
        self.objectExtractionApplet = ObjectExtractionApplet(workflow=self)
        self.objectClassificationApplet = ObjectClassificationApplet(workflow=self)
        self._applets.append(self.objectExtractionApplet)
        self._applets.append(self.objectClassificationApplet)

        if self.batch:
            self.dataSelectionAppletBatch = DataSelectionApplet(
                self, "Batch Inputs", "Batch Inputs", batchDataGui=True, force5d=True)
            self.opDataSelectionBatch = self.dataSelectionAppletBatch.topLevelOperator
            if isinstance(self, ObjectClassificationWorkflowBinary):
                self.opDataSelectionBatch.DatasetRoles.setValue(['Raw Data', 'Binary Data'])
            else:
                self.opDataSelectionBatch.DatasetRoles.setValue(['Raw Data', 'Prediction Maps'])

            self.blockwiseObjectClassificationApplet = BlockwiseObjectClassificationApplet(
                self, "Blockwise Object Classification", "Blockwise Object Classification")
            self._applets.append(self.blockwiseObjectClassificationApplet)

            self.batchResultsApplet = BlockwiseObjectClassificationBatchApplet(
                self, "Prediction Output Locations")
            self._applets.append(self.dataSelectionAppletBatch)
            self._applets.append(self.batchResultsApplet)

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

        opObjExtraction.RawImage.connect(rawslot)
        opObjExtraction.BinaryImage.connect(binaryslot)

        opObjClassification.RawImages.connect(rawslot)
        opObjClassification.LabelsAllowedFlags.connect(opData.AllowLabels)
        opObjClassification.BinaryImages.connect(binaryslot)

        opObjClassification.SegmentationImages.connect(opObjExtraction.LabelImage)
        opObjClassification.ObjectFeatures.connect(opObjExtraction.RegionFeatures)
        opObjClassification.ComputedFeatureNames.connect(opObjExtraction.ComputedFeatureNames)

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
        opTrainingTopLevel = self.objectClassificationApplet.topLevelOperator
        
        opBlockwiseObjectClassification = self.blockwiseObjectClassificationApplet.topLevelOperator

        opBatchFillMissingSlices = OperatorWrapper(OpFillMissingSlicesNoCache, parent=self)

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

        # FIXME: need op5ifiers

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
        opBatchClassify.Classifier.connect(opTrainingTopLevel.Classifier)
        opBatchClassify.LabelsCount.connect(opTrainingTopLevel.NumLabels)
        opBatchClassify.SelectedFeatures.connect(opTrainingTopLevel.SelectedFeatures)
        opBatchClassify.BlockShape3dDict.connect(opBlockwiseObjectClassification.BlockShape3dDict)
        opBatchClassify.HaloPadding3dDict.connect(opBlockwiseObjectClassification.HaloPadding3dDict)

        #  but image pathway is from the batch pipeline
        opBatchFillMissingSlices.Input.connect(batchInputsRaw)
        op5Raw = OperatorWrapper(Op5ifyer, parent=self)
        op5Raw.input.connect(opBatchFillMissingSlices.Output)
        op5Binary = OperatorWrapper(Op5ifyer, parent=self)
        if not isinstance(self, ObjectClassificationWorkflowBinary):
            opBatchThreshold.RawInput.connect(batchInputsRaw)
            opBatchThreshold.InputImage.connect(batchInputsOther)
            op5Binary.input.connect(opBatchThreshold.Output)
        else:
            op5Binary.input.connect(batchInputsOther)

        opBatchClassify.RawImage.connect(op5Raw.output)
        opBatchClassify.BinaryImage.connect(op5Binary.output)

        self.opBatchClassify = opBatchClassify

        # Connect the batch OUTPUT applet
        opBatchOutput = self.batchResultsApplet.topLevelOperator
        opBatchOutput.DatasetPath.connect(self.opDataSelectionBatch.ImageName)
        opBatchOutput.RawImage.connect(batchInputsRaw)
        opBatchOutput.ImageToExport.connect(opBatchClassify.PredictionImage)

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
        self.dataSelectionApplet = DataSelectionApplet(
            self, "Data Selection", "DataSelection", batchDataGui=False,
            force5d=False)
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
        op5raw = Op5ifyer(parent=self)
        op5pred = Op5ifyer(parent=self)
        op5threshold = Op5ifyer(parent=self)

        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)
        opClassify = self.pcApplet.topLevelOperator.getLane(laneIndex)
        opThreshold = self.thresholdingApplet.topLevelOperator.getLane(laneIndex)

        if self.fillMissing:
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

        op5raw.input.connect(rawslot)
        op5pred.input.connect(opClassify.HeadlessPredictionProbabilities)

        opThreshold.RawInput.connect(op5raw.output)
        opThreshold.InputImage.connect(op5pred.output)

        op5threshold.input.connect(opThreshold.CachedOutput)

        return op5raw.output, op5threshold.output


class ObjectClassificationWorkflowBinary(ObjectClassificationWorkflow):
    workflowName = "Object Classification (from binary image)"

    def setupInputs(self):
        self.dataSelectionApplet = DataSelectionApplet(self,
                                                       "Input Data",
                                                       "Input Data",
                                                       batchDataGui=False,
                                                       force5d=True)

        opData = self.dataSelectionApplet.topLevelOperator
        opData.DatasetRoles.setValue(['Raw Data', 'Segmentation Image'])
        self._applets.append(self.dataSelectionApplet)

    def connectInputs(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        if self.fillMissing:
            opFillMissingSlices = self.fillMissingSlicesApplet.topLevelOperator.getLane(laneIndex)
            opFillMissingSlices.Input.connect(opData.ImageGroup[0])
            rawslot = opFillMissingSlices.Output
        else:
            rawslot = opData.ImageGroup[0]

        return rawslot, opData.ImageGroup[1]


class ObjectClassificationWorkflowPrediction(ObjectClassificationWorkflow):
    workflowName = "Object Classification (from prediction image)"

    def setupInputs(self):
        self.dataSelectionApplet = DataSelectionApplet(self,
                                                       "Input Data",
                                                       "Input Data",
                                                       batchDataGui=False,
                                                       force5d=True)

        opData = self.dataSelectionApplet.topLevelOperator
        opData.DatasetRoles.setValue(['Raw Data', 'Prediction Maps'])
        self._applets.append(self.dataSelectionApplet)

        self.thresholdingApplet = ThresholdTwoLevelsApplet(self, "Threshold & Size Filter", "ThresholdTwoLevels")
        self._applets.append(self.thresholdingApplet)

    def connectInputs(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTwoLevelThreshold = self.thresholdingApplet.topLevelOperator.getLane(laneIndex)

        op5raw = Op5ifyer(parent=self)
        op5predictions = Op5ifyer(parent=self)

        if self.fillMissing:
            opFillMissingSlices = self.fillMissingSlicesApplet.topLevelOperator.getLane(laneIndex)
            opFillMissingSlices.Input.connect(opData.ImageGroup[0])
            rawslot = opFillMissingSlices.Output
        else:
            rawslot = opData.ImageGroup[0]

        op5raw.input.connect(rawslot)
        op5predictions.input.connect(opData.ImageGroup[1])

        opTwoLevelThreshold.RawInput.connect(op5raw.output)
        opTwoLevelThreshold.InputImage.connect(op5predictions.output)

        op5Binary = Op5ifyer(parent=self)

        op5Binary.input.connect(opTwoLevelThreshold.CachedOutput)

        return op5raw.output, op5Binary.output
