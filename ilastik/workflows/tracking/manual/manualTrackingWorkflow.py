from lazyflow.graph import Graph
from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.tracking.manual.manualTrackingApplet import ManualTrackingApplet
from ilastik.applets.objectExtraction.objectExtractionApplet import ObjectExtractionApplet

class ManualTrackingWorkflow( Workflow ):
    workflowName = "Tracking Workflow (Manual)"
    workflowDescription = "Manual tracking of objects."

    @property
    def applets(self):
        return self._applets
    
    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__( self, *args, **kwargs ):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs: del kwargs['graph']
        super(ManualTrackingWorkflow, self).__init__(graph=graph, *args, **kwargs)
        
        ## Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, 
                                                       "Input: Segmentation", 
                                                       "Input Segmentation", 
                                                       batchDataGui=False,
                                                       force5d=True)
        opSegDataSelection = self.dataSelectionApplet.topLevelOperator
        opSegDataSelection.DatasetRoles.setValue( ['Binary Segmentation'] )        

        self.rawDataSelectionApplet = DataSelectionApplet(self, 
                                                          "Input: Raw Data", 
                                                          "Input Raw", 
                                                          batchDataGui=False,
                                                          force5d=True)
        opRawDataSelection = self.rawDataSelectionApplet.topLevelOperator
        opRawDataSelection.DatasetRoles.setValue( ['Raw Data'] )
                                                                   
        self.objectExtractionApplet = ObjectExtractionApplet(workflow=self,
                                                                      name="Object Extraction")
        
        self.trackingApplet = ManualTrackingApplet( workflow=self )
        
        self._applets = []        
        self._applets.append(self.rawDataSelectionApplet)
        self._applets.append(self.dataSelectionApplet)        
        self._applets.append(self.objectExtractionApplet)        
        self._applets.append(self.trackingApplet)
            
    def connectLane(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opRawData = self.rawDataSelectionApplet.topLevelOperator.getLane(laneIndex)        
        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)            
        opTracking = self.trackingApplet.topLevelOperator.getLane(laneIndex)
                
        ## Connect operators ##        
        opObjExtraction.RawImage.connect( opRawData.Image )
        opObjExtraction.BinaryImage.connect( opData.Image )        
        
        opTracking.RawImage.connect( opRawData.Image )
        opTracking.LabelImage.connect( opObjExtraction.LabelImage )
        opTracking.BinaryImage.connect( opData.Image )        
        opTracking.ObjectFeatures.connect( opObjExtraction.RegionFeatures )
