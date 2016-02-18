import os
from lazyflow.graph import Graph
from lazyflow.utility import PathComponents, make_absolute, format_known_keys
from ilastik.workflow import Workflow
from ilastik.workflows.tracking.conservation.conservationTrackingWorkflow import ConservationTrackingWorkflowBase 
from ilastik.applets.dataSelection import DataSelectionApplet, DatasetInfo
from ilastik.applets.tracking.conservation.conservationTrackingApplet import ConservationTrackingApplet
from ilastik.applets.objectClassification.objectClassificationApplet import ObjectClassificationApplet
#from ilastik.applets.opticalTranslation.opticalTranslationApplet import OpticalTranslationApplet
from ilastik.applets.thresholdTwoLevels.thresholdTwoLevelsApplet import ThresholdTwoLevelsApplet
from lazyflow.operators.opReorderAxes import OpReorderAxes
from ilastik.applets.trackingFeatureExtraction.trackingFeatureExtractionApplet import TrackingFeatureExtractionApplet
from ilastik.applets.trackingFeatureExtraction import config
from lazyflow.operators.opReorderAxes import OpReorderAxes
from ilastik.applets.tracking.base.trackingBaseDataExportApplet import TrackingBaseDataExportApplet


class AnimalConservationTrackingWorkflowBase( ConservationTrackingWorkflowBase ):
    workflowName = "Animal Conservation Tracking Workflow BASE"  
      
    def __init__( self, shell, headless, workflow_cmdline_args, *args, **kwargs ):
        # Set to true in order to disable divisions in ConservationTrackingWorkflow
        self.withAnimalTracking = True
          
        super(AnimalConservationTrackingWorkflowBase, self).__init__(shell, headless, workflow_cmdline_args, *args, **kwargs)
    
    def connectLane(self, laneIndex):        
        # Set animal tracking and disabled divisions in tracking op parameters
        opTracking = self.trackingApplet.topLevelOperator.getLane(laneIndex)
        opTracking.Parameters.value['withDivisions'] = False
        opTracking.Parameters.value['withAnimalTracking'] = self.withAnimalTracking     
           
        super(AnimalConservationTrackingWorkflowBase, self).connectLane(laneIndex) 
        
    def _createDivisionDetectionApplet(self,selectedFeatures=None):
        return None 


class AnimalConservationTrackingWorkflowFromBinary( AnimalConservationTrackingWorkflowBase ):
    workflowName = "Animal Conservation Tracking Workflow from Binary Image"
    workflowDisplayName = "Animal Conservation Tracking Workflow [Inputs: Raw Data, Binary Image]"

    withOptTrans = False
    fromBinary = True
    

class AnimalConservationTrackingWorkflowFromPrediction( AnimalConservationTrackingWorkflowBase ):
    workflowName = "Animal Conservation Tracking Workflow from Prediction Image"
    workflowDisplayName = "Animal Conservation Tracking Workflow [Inputs: Raw Data, Pixel Prediction Map]"

    withOptTrans = False
    fromBinary = False
