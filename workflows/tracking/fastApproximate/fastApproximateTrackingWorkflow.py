from lazyflow.graph import Graph
from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.tracking.fastApproximate.fastApproximateTrackingApplet import FastApproximateTrackingApplet
from ilastik.applets.objectExtractionMultiClass.objectExtractionMultiClassApplet import ObjectExtractionMultiClassApplet

class FastApproximateTrackingWorkflow( Workflow ):
    name = "Fast Approximate Tracking Workflow"
    
    def __init__( self, headless, *args, **kwargs ):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs: del kwargs['graph']
        super(FastApproximateTrackingWorkflow, self).__init__(headless=headless, graph=graph, *args, **kwargs)
        
        ## Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, "Input: Segmentation", "Input Segmentation", batchDataGui=False)
        self.rawDataSelectionApplet = DataSelectionApplet(self, "Input: Raw Data", "Input Raw", batchDataGui=False)
        self.objectExtractionApplet = ObjectExtractionMultiClassApplet( name="Object Extraction Multi-Class", workflow=self )
        self.trackingApplet = FastApproximateTrackingApplet( workflow=self )
        
        self._applets = []        
        self._applets.append(self.rawDataSelectionApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.objectExtractionApplet)
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
        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)    
        opTracking = self.trackingApplet.topLevelOperator.getLane(laneIndex)
        
        ## Connect operators ##
        opObjExtraction.RawImage.connect( opRawData.Image )                
        opObjExtraction.Images.connect( opData.Image )        
        
        opTracking.RawImage.connect( opRawData.Image )
        opTracking.LabelImage.connect( opObjExtraction.LabelImage )
        opTracking.ObjectFeatures.connect( opObjExtraction.RegionFeatures )
        opTracking.ClassMapping.connect( opObjExtraction.ClassMapping )
#        opTracking.RegionLocalCenters.connect( opObjExtraction.RegionLocalCenters )

        
        
        