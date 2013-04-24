from lazyflow.graph import Graph

from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.objectExtraction import ObjectExtractionApplet
from ilastik.applets.objectClassification import ObjectClassificationApplet

class ObjectClassificationWorkflowBinary(Workflow):
    name = "Object Classification Workflow"

    def __init__( self, headless, *args, **kwargs ):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs: del kwargs['graph']
        super(ObjectClassificationWorkflowBinary, self).__init__(headless=headless, graph=graph, *args, **kwargs)

        ######################
        # Interactive workflow
        ######################

        ## Create applets
        self.dataSelectionApplet = DataSelectionApplet(self,
                                                       "Input Data",
                                                       "Input Data",
                                                       batchDataGui=False,
                                                       force5d=True)

        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ['Raw Data', 'Segmentation Image'] )

        self.objectExtractionApplet = ObjectExtractionApplet(workflow=self)
        self.objectClassificationApplet = ObjectClassificationApplet(workflow=self)

        self._applets = []
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.objectExtractionApplet)
        self._applets.append(self.objectClassificationApplet)

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def connectLane( self, laneIndex ):
        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)
        opObjClassification = self.objectClassificationApplet.topLevelOperator.getLane(laneIndex)

        # connect data -> extraction
        opObjExtraction.RawImage.connect(opData.ImageGroup[0])
        opObjExtraction.BinaryImage.connect(opData.ImageGroup[1])

        # connect data -> classification
        opObjClassification.RawImages.connect(opData.ImageGroup[0])
        opObjClassification.BinaryImages.connect(opData.ImageGroup[1])
        opObjClassification.LabelsAllowedFlags.connect(opData.AllowLabels)

        # connect extraction -> classification
        opObjClassification.SegmentationImages.connect(opObjExtraction.LabelImage)
        opObjClassification.ObjectFeatures.connect(opObjExtraction.RegionFeatures)
        opObjClassification.ComputedFeatureNames.connect(opObjExtraction.ComputedFeatureNames)
