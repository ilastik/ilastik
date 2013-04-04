from lazyflow.graph import Graph
from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.tracking.conservation.conservationTrackingApplet import ConservationTrackingApplet
from ilastik.applets.divisionFeatureExtraction.divisionFeatureExtractionApplet import DivisionFeatureExtractionApplet
from ilastik.applets.objectClassification.objectClassificationApplet import ObjectClassificationApplet
from ilastik.applets.opticalTranslation.opticalTranslationApplet import OpticalTranslationApplet

class ConservationTrackingWorkflow( Workflow ):
    name = "Conservation Tracking Workflow"

    def __init__( self, headless, *args, **kwargs ):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs: del kwargs['graph']
        super(ConservationTrackingWorkflow, self).__init__(headless=headless, graph=graph, *args, **kwargs)
        
        ## Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, 
                                                       "Input: Segmentation", 
                                                       "Input Segmentation", 
                                                       batchDataGui=False,
                                                       force5d=True)
        
        self.rawDataSelectionApplet = DataSelectionApplet(self, 
                                                          "Input: Raw Data", 
                                                          "Input Raw", 
                                                          batchDataGui=False,
                                                          force5d=True)
        
        self.opticalTranslationApplet = OpticalTranslationApplet(workflow=self)
                                                                   
        self.objectExtractionApplet = DivisionFeatureExtractionApplet(workflow=self,
                                                                      name="Object Extraction")
        
        self.divisionDetectionApplet = ObjectClassificationApplet(workflow=self,
                                                                     name="Division Detection",
                                                                     projectFileGroupName="DivisionDetection")
        
        self.cellClassificationApplet = ObjectClassificationApplet(workflow=self,
                                                                     name="Cell Classification",
                                                                     projectFileGroupName="CellClassification")
                
        self.trackingApplet = ConservationTrackingApplet( workflow=self )
        
        self._applets = []        
        self._applets.append(self.rawDataSelectionApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.opticalTranslationApplet)
        self._applets.append(self.objectExtractionApplet)
        self._applets.append(self.divisionDetectionApplet)
        self._applets.append(self.cellClassificationApplet)
        self._applets.append(self.trackingApplet)
        
    @property
    def applets(self):
        return self._applets
    
    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName
    
    def connectLane(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opRawData = self.rawDataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opOptTranslation = self.opticalTranslationApplet.topLevelOperator.getLane(laneIndex)
        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)    
        opDivDetection = self.divisionDetectionApplet.topLevelOperator.getLane(laneIndex)
        opCellClassification = self.cellClassificationApplet.topLevelOperator.getLane(laneIndex)
        opTracking = self.trackingApplet.topLevelOperator.getLane(laneIndex)
        
        opOptTranslation.RawImage.connect( opRawData.Image )
        opOptTranslation.BinaryImage.connect( opData.Image )
        
        ## Connect operators ##        
        opObjExtraction.RawImage.connect( opRawData.Image )
        opObjExtraction.BinaryImage.connect( opData.Image )
        opObjExtraction.TranslationVectors.connect( opOptTranslation.TranslationVectors )
        
        opDivDetection.BinaryImages.connect(opData.Image)
        opDivDetection.RawImages.connect(opRawData.Image)
        opDivDetection.LabelsAllowedFlags.connect(opData.AllowLabels)
        opDivDetection.SegmentationImages.connect(opObjExtraction.LabelImage)
        opDivDetection.ObjectFeatures.connect(opObjExtraction.RegionFeatures)
        
        opCellClassification.BinaryImages.connect(opData.Image)
        opCellClassification.RawImages.connect(opRawData.Image)
        opCellClassification.LabelsAllowedFlags.connect(opData.AllowLabels)
        opCellClassification.SegmentationImages.connect(opObjExtraction.LabelImage)
        opCellClassification.ObjectFeatures.connect(opObjExtraction.RegionFeatures)
        
        opTracking.RawImage.connect( opRawData.Image )
        opTracking.LabelImage.connect( opObjExtraction.LabelImage )
        opTracking.ObjectFeatures.connect( opDivDetection.ObjectFeatures )
        opTracking.DivisionProbabilities.connect( opDivDetection.Probabilities )
#        opTracking.RegionLocalCenters.connect( opObjExtraction.RegionLocalCenters )        
    
