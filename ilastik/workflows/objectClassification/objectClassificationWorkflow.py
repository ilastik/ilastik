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
    name = "Object Classification Workflow"
    defaultAppletIndex = 1 # show DataSelection by default

    def __init__(self, headless, *args, **kwargs):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs: del kwargs['graph']
        super(ObjectClassificationWorkflow, self).__init__(headless=headless, graph=graph, *args, **kwargs)

        ######################
        # Interactive workflow
        ######################

        self.projectMetadataApplet = ProjectMetadataApplet()

        self.dataSelectionApplet = DataSelectionApplet(self,
                                                       "Data Selection",
                                                       "DataSelection",
                                                       batchDataGui=False,
                                                       force5d=False)

        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ['Raw Data'] )

        self.featureSelectionApplet = FeatureSelectionApplet(self,
                                                             "Feature Selection",
                                                             "FeatureSelections")

        self.pcApplet = PixelClassificationApplet(self, "PixelClassification")
        self.thresholdingApplet = ThresholdTwoLevelsApplet(self, "Thresholding", "ThresholdTwoLevels")
        self.objectExtractionApplet = ObjectExtractionApplet(workflow=self)
        self.objectClassificationApplet = ObjectClassificationApplet(workflow=self)

        self._applets = []
        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.pcApplet)
        self._applets.append(self.thresholdingApplet)
        self._applets.append(self.objectExtractionApplet)
        self._applets.append(self.objectClassificationApplet)


    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def connectLane(self, laneIndex):
        op5raw = Op5ifyer(parent=self)
        op5prob = Op5ifyer(parent=self)
        op5threshold = Op5ifyer(parent=self)

        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)
        opClassify = self.pcApplet.topLevelOperator.getLane(laneIndex)
        opThreshold = self.thresholdingApplet.topLevelOperator.getLane(laneIndex)
        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)
        opObjClassification = self.objectClassificationApplet.topLevelOperator.getLane(laneIndex)

        # connect input image
        opTrainingFeatures.InputImage.connect(opData.Image)
        opClassify.InputImages.connect(opData.Image)

        op5raw.input.connect(opData.Image)

        opThreshold.RawInput.connect(op5raw.output)
        opObjExtraction.RawImage.connect(op5raw.output)
        opObjClassification.RawImages.connect(op5raw.output)

        # training flags
        opClassify.LabelsAllowedFlags.connect(opData.AllowLabels)
        opObjClassification.LabelsAllowedFlags.connect(opData.AllowLabels)

        # connect pixel features
        opClassify.FeatureImages.connect(opTrainingFeatures.OutputImage)
        opClassify.CachedFeatureImages.connect(opTrainingFeatures.CachedOutputImage)

        #we will cache thresholding output, no point in caching predictions
        op5prob.input.connect(opClassify.HeadlessPredictionProbabilities)
        opThreshold.InputImage.connect(op5prob.output)

        op5threshold.input.connect(opThreshold.CachedOutput)
        opObjExtraction.BinaryImage.connect(op5threshold.output)

        opObjClassification.BinaryImages.connect(opThreshold.CachedOutput)

        # connect object features
        opObjClassification.SegmentationImages.connect(opObjExtraction.LabelImage)
        opObjClassification.ObjectFeatures.connect(opObjExtraction.RegionFeatures)
        opObjClassification.ComputedFeatureNames.connect(opObjExtraction.ComputedFeatureNames)