from lazyflow.graph import Graph
from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.tracking.manual.manualTrackingApplet import ManualTrackingApplet
from ilastik.applets.objectExtraction.objectExtractionApplet import ObjectExtractionApplet
from ilastik.applets.thresholdTwoLevels.thresholdTwoLevelsApplet import ThresholdTwoLevelsApplet
from lazyflow.operators.opReorderAxes import OpReorderAxes
from ilastik.applets.tracking.base.trackingBaseDataExportApplet import TrackingBaseDataExportApplet

class ManualTrackingWorkflow( Workflow ):
    workflowName = "Manual Tracking Workflow"
    workflowDescription = "Manual tracking of objects, based on Prediction Maps or (binary) Segmentation Images"    

    @property
    def applets(self):
        return self._applets
    
    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__( self, shell, headless, workflow_cmdline_args, *args, **kwargs ):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs: del kwargs['graph']
        super(ManualTrackingWorkflow, self).__init__(shell, headless, graph=graph, *args, **kwargs)
        
        data_instructions = 'Use the "Raw Data" tab to load your intensity image(s).\n\n'\
                            'Use the "Prediction Maps" tab to load your pixel-wise probability image(s).'
        ## Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, 
                                                       "Input Data", 
                                                       "Input Data", 
                                                       batchDataGui=False,
                                                       force5d=True,
                                                       instructionText=data_instructions,
                                                       max_lanes=1
                                                       )
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ['Raw Data', 'Prediction Maps'] )                
        
        self.thresholdTwoLevelsApplet = ThresholdTwoLevelsApplet( self, 
                                                                  "Threshold and Size Filter", 
                                                                  "ThresholdTwoLevels" )
                     
        self.objectExtractionApplet = ObjectExtractionApplet(name="Object Feature Computation",
                                                             workflow=self, interactive=False)
        
        self.trackingApplet = ManualTrackingApplet( workflow=self )
        self.dataExportApplet = TrackingBaseDataExportApplet(self, "Tracking Result Export")
        
        self._applets = []        
        self._applets.append(self.dataSelectionApplet)        
        self._applets.append(self.thresholdTwoLevelsApplet)
        self._applets.append(self.objectExtractionApplet)        
        self._applets.append(self.trackingApplet)
        self._applets.append(self.dataExportApplet)
            
    def connectLane(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)        
        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)
        opTracking = self.trackingApplet.topLevelOperator.getLane(laneIndex)    
        opTwoLevelThreshold = self.thresholdTwoLevelsApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)
                        
        ## Connect operators ##
        op5Raw = OpReorderAxes(parent=self)
        op5Raw.AxisOrder.setValue("txyzc")
        op5Raw.Input.connect(opData.ImageGroup[0])
        
        opTwoLevelThreshold.InputImage.connect( opData.ImageGroup[1] )
        opTwoLevelThreshold.RawInput.connect( opData.ImageGroup[0] ) # Used for display only
        # Use OpReorderAxis for both input datasets such that they are guaranteed to 
        # have the same axis order after thresholding
        op5Binary = OpReorderAxes( parent=self )        
        op5Binary.AxisOrder.setValue("txyzc")
        op5Binary.Input.connect( opTwoLevelThreshold.CachedOutput )        
        
        opObjExtraction.RawImage.connect( op5Raw.Output )
        opObjExtraction.BinaryImage.connect( op5Binary.Output )
        
        opTracking.RawImage.connect( op5Raw.Output )
        opTracking.BinaryImage.connect( op5Binary.Output )
        opTracking.LabelImage.connect( opObjExtraction.LabelImage )
        opTracking.ObjectFeatures.connect( opObjExtraction.RegionFeatures )        
        
        opDataExport.WorkingDirectory.connect( self.dataSelectionApplet.topLevelOperator.WorkingDirectory )
        opDataExport.RawData.connect( op5Raw.Output )
        opDataExport.Input.connect( opTracking.TrackImage )
        opDataExport.RawDatasetInfo.connect( opData.DatasetGroup[0] )
        