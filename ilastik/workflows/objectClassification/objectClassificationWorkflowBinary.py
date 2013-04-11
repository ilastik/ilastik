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
        self.rawDataSelectionApplet = DataSelectionApplet(self,
                                                       "Input: Raw",
                                                       "Input Raw",
                                                       batchDataGui=False,
                                                       force5d=True)
        
        self.dataSelectionApplet = DataSelectionApplet(self,
                                                       "Input: Segmentation",
                                                       "Input Segmentation",
                                                       batchDataGui=False,
                                                       force5d=True)
        
        self.objectExtractionApplet = ObjectExtractionApplet(workflow=self)
        self.objectClassificationApplet = ObjectClassificationApplet(workflow=self)

        self._applets = []
        self._applets.append(self.rawDataSelectionApplet)
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
        opRawData = self.rawDataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)
        opObjClassification = self.objectClassificationApplet.topLevelOperator.getLane(laneIndex)

        # connect data -> extraction
        opObjExtraction.RawImage.connect(opRawData.Image)
        opObjExtraction.BinaryImage.connect(opData.Image)

        # connect data -> classification
        opObjClassification.BinaryImages.connect(opData.Image)
        opObjClassification.RawImages.connect(opRawData.Image)
        opObjClassification.LabelsAllowedFlags.connect(opData.AllowLabels)

        # connect extraction -> classification
        opObjClassification.SegmentationImages.connect(opObjExtraction.LabelImage)
        opObjClassification.ObjectFeatures.connect(opObjExtraction.RegionFeatures)
    
        # bad things will happen if labels are created before feature selection took place   
        self.objectExtractionApplet.enableDownstream(False)

