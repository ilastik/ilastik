from lazyflow.graph import Graph

from ilastik.workflow import Workflow
from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.pixelClassification import PixelClassificationApplet
from ilastik.applets.thresholdTwoLevels import ThresholdTwoLevelsApplet
from ilastik.applets.objectExtraction import ObjectExtractionApplet
from ilastik.applets.objectClassification import ObjectClassificationApplet

from lazyflow.operators import OpSegmentation, Op5ifyer

class ObjectClassificationWorkflow(Workflow):
    workflowName = "Object Classification Workflow Base"
    defaultAppletIndex = 1 # show DataSelection by default

    def __init__(self, headless, *args, **kwargs):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs:
            del kwargs['graph']
        super(ObjectClassificationWorkflow, self).__init__(headless=headless, graph=graph, *args, **kwargs)

        self._applets = []

        self.projectMetadataApplet = ProjectMetadataApplet()
        self._applets.append(self.projectMetadataApplet)

        self.setupInputs()

        # our main applets
        self.objectExtractionApplet = ObjectExtractionApplet(workflow=self)
        self.objectClassificationApplet = ObjectClassificationApplet(workflow=self)
        self._applets.append(self.objectExtractionApplet)
        self._applets.append(self.objectClassificationApplet)


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


class ObjectClassificationWorkflowPixel(ObjectClassificationWorkflow):
    workflowName = "Object Classification (from pixel classification)"

    def setupInputs(self):
        self.dataSelectionApplet = DataSelectionApplet(self,
                                                       "Data Selection",
                                                       "DataSelection",
                                                       batchDataGui=False,
                                                       force5d=False)
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue(['Raw Data'])

        self.featureSelectionApplet = FeatureSelectionApplet(self,
                                                             "Feature Selection",
                                                             "FeatureSelections")

        self.pcApplet = PixelClassificationApplet(self, "PixelClassification")
        self.thresholdingApplet = ThresholdTwoLevelsApplet(self, "Thresholding", "ThresholdTwoLevels")

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

        opTrainingFeatures.InputImage.connect(opData.Image)

        opClassify.InputImages.connect(opData.Image)
        opClassify.LabelsAllowedFlags.connect(opData.AllowLabels)
        opClassify.FeatureImages.connect(opTrainingFeatures.OutputImage)
        opClassify.CachedFeatureImages.connect(opTrainingFeatures.CachedOutputImage)

        opThreshold.RawInput.connect(op5raw.output)
        opThreshold.InputImage.connect(op5pred.output)

        op5raw.input.connect(opData.Image)
        op5pred.input.connect(opClassify.HeadlessPredictionProbabilities)
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

        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue(['Raw Data', 'Segmentation Image'])
        self._applets.append(self.dataSelectionApplet)

    def connectInputs(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        return opData.ImageGroup[0], opData.ImageGroup[1]


class ObjectClassificationWorkflowPrediction(ObjectClassificationWorkflow):
    workflowName = "Object Classification (from prediction image)"

    def setupInputs(self):
        self.dataSelectionApplet = DataSelectionApplet(self,
                                                       "Input Data",
                                                       "Input Data",
                                                       batchDataGui=False,
                                                       force5d=True)

        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue(['Raw Data', 'Prediction Maps'])
        self._applets.append(self.dataSelectionApplet)

        self.thresholdTwoLevelsApplet = ThresholdTwoLevelsApplet(self, "Threshold & Size Filter", "ThresholdTwoLevels")
        self._applets.append(self.thresholdTwoLevelsApplet)

    def connectInputs(self, laneIndex):
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTwoLevelThreshold = self.thresholdTwoLevelsApplet.topLevelOperator.getLane(laneIndex)

        op5Raw = Op5ifyer(parent=self)
        op5Raw.input.connect(opDataSelection.ImageGroup[0])

        op5Predictions = Op5ifyer(parent=self)
        op5Predictions.input.connect(opDataSelection.ImageGroup[1])

        opTwoLevelThreshold.InputImage.connect(op5Predictions.output)
        opTwoLevelThreshold.RawInput.connect(op5Raw.output)

        op5Binary = Op5ifyer(parent=self)

        op5Binary.input.connect(opTwoLevelThreshold.CachedOutput)

        return op5Raw.output, op5Predictions.output
