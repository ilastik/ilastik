from lazyflow.graph import Graph
from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.tracking.conservation.conservationTrackingApplet import ConservationTrackingApplet
from ilastik.applets.objectClassification.objectClassificationApplet import ObjectClassificationApplet
#from ilastik.applets.opticalTranslation.opticalTranslationApplet import OpticalTranslationApplet
from ilastik.applets.thresholdTwoLevels.thresholdTwoLevelsApplet import ThresholdTwoLevelsApplet
from lazyflow.operators.opReorderAxes import OpReorderAxes
from ilastik.applets.trackingFeatureExtraction.trackingFeatureExtractionApplet import TrackingFeatureExtractionApplet
from ilastik.applets.trackingFeatureExtraction import config
from lazyflow.operators.opReorderAxes import OpReorderAxes
from ilastik.applets.tracking.base.trackingBaseDataExportApplet import TrackingBaseDataExportApplet

class ConservationTrackingWorkflowBase( Workflow ):
    workflowName = "Automatic Tracking Workflow (Conservation Tracking) BASE"

    def __init__( self, shell, headless, workflow_cmdline_args, *args, **kwargs ):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs: del kwargs['graph']
        # if 'withOptTrans' in kwargs:
        #     self.withOptTrans = kwargs['withOptTrans']
        # if 'fromBinary' in kwargs:
        #     self.fromBinary = kwargs['fromBinary']
        super(ConservationTrackingWorkflowBase, self).__init__(shell, headless, graph=graph, *args, **kwargs)

        data_instructions = 'Use the "Raw Data" tab to load your intensity image(s).\n\n'
        if self.fromBinary:
            data_instructions += 'Use the "Binary Image" tab to load your segmentation image(s).'
        else:
            data_instructions += 'Use the "Prediction Maps" tab to load your pixel-wise probability image(s).'

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
        if self.fromBinary:
            opDataSelection.DatasetRoles.setValue( ['Raw Data', 'Binary Image'] )
        else:
            opDataSelection.DatasetRoles.setValue( ['Raw Data', 'Prediction Maps'] )
                
        if not self.fromBinary:
            self.thresholdTwoLevelsApplet = ThresholdTwoLevelsApplet( self, 
                                                                  "Threshold and Size Filter", 
                                                                  "ThresholdTwoLevels" )        
        if self.withOptTrans:
            self.opticalTranslationApplet = OpticalTranslationApplet(workflow=self)
                                                                   
        self.objectExtractionApplet = TrackingFeatureExtractionApplet(workflow=self, interactive=False,
                                                                      name="Object Feature Computation")                                                                      
        
        self.divisionDetectionApplet = ObjectClassificationApplet(workflow=self,
                                                                     name="Division Detection (optional)",
                                                                     projectFileGroupName="DivisionDetection")
        
        self.cellClassificationApplet = ObjectClassificationApplet(workflow=self,
                                                                     name="Object Count Classification (optional)",
                                                                     projectFileGroupName="CountClassification")
                
        self.trackingApplet = ConservationTrackingApplet( workflow=self )
        opTracking = self.trackingApplet.topLevelOperator

        self.dataExportApplet = TrackingBaseDataExportApplet(self, "Tracking Result Export")
        self.dataExportApplet.set_exporting_operator(opTracking)
        
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.SelectionNames.setValue( ['Tracking Result', 'Merger Result', 'Object Identities'] )
        opDataExport.WorkingDirectory.connect( opDataSelection.WorkingDirectory )
        
        self._applets = []                
        self._applets.append(self.dataSelectionApplet)
        if not self.fromBinary:
            self._applets.append(self.thresholdTwoLevelsApplet)
        if self.withOptTrans:
            self._applets.append(self.opticalTranslationApplet)
        self._applets.append(self.objectExtractionApplet)
        self._applets.append(self.divisionDetectionApplet)
        self._applets.append(self.cellClassificationApplet)
        self._applets.append(self.trackingApplet)
        self._applets.append(self.dataExportApplet)
        
    @property
    def applets(self):
        return self._applets
    
    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName
    
    def connectLane(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        if not self.fromBinary:
            opTwoLevelThreshold = self.thresholdTwoLevelsApplet.topLevelOperator.getLane(laneIndex)
        if self.withOptTrans:
            opOptTranslation = self.opticalTranslationApplet.topLevelOperator.getLane(laneIndex)
        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)    
        opDivDetection = self.divisionDetectionApplet.topLevelOperator.getLane(laneIndex)
        opCellClassification = self.cellClassificationApplet.topLevelOperator.getLane(laneIndex)
        opTracking = self.trackingApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)
        
        op5Raw = OpReorderAxes(parent=self)
        op5Raw.AxisOrder.setValue("txyzc")
        op5Raw.Input.connect(opData.ImageGroup[0])
        
        if not self.fromBinary:
            opTwoLevelThreshold.InputImage.connect(opData.ImageGroup[1])
            opTwoLevelThreshold.RawInput.connect(opData.ImageGroup[0])  # Used for display only
            # opTwoLevelThreshold.Channel.setValue(1)
            binarySrc = opTwoLevelThreshold.CachedOutput
        else:
            binarySrc = opData.ImageGroup[1]
        
        # Use Op5ifyers for both input datasets such that they are guaranteed to 
        # have the same axis order after thresholding
        op5Binary = OpReorderAxes(parent=self)         
        op5Binary.AxisOrder.setValue("txyzc")
        op5Binary.Input.connect(binarySrc)
        
        if self.withOptTrans:
            opOptTranslation.RawImage.connect(op5Raw.Output)
            opOptTranslation.BinaryImage.connect(op5Binary.Output)
        
        # # Connect operators ##       
        vigra_features = list((set(config.vigra_features)).union(config.selected_features_objectcount[config.features_vigra_name])) 
        feature_names_vigra = {}
        feature_names_vigra[config.features_vigra_name] = { name: {} for name in vigra_features }
        opObjExtraction.RawImage.connect(op5Raw.Output)
        opObjExtraction.BinaryImage.connect(op5Binary.Output)
        if self.withOptTrans:
            opObjExtraction.TranslationVectors.connect(opOptTranslation.TranslationVectors)
        opObjExtraction.FeatureNamesVigra.setValue(feature_names_vigra)
        feature_dict_division = {}
        feature_dict_division[config.features_division_name] = { name: {} for name in config.division_features }
        opObjExtraction.FeatureNamesDivision.setValue(feature_dict_division)
        
        
        selected_features_div = {}
        for plugin_name in config.selected_features_division.keys():
            selected_features_div[plugin_name] = { name: {} for name in config.selected_features_division[plugin_name] }
        # FIXME: do not hard code this
        for name in [ 'SquaredDistances_' + str(i) for i in range(config.n_best_successors) ]:
            selected_features_div[config.features_division_name][name] = {}
            
        opDivDetection.BinaryImages.connect( op5Binary.Output )
        opDivDetection.RawImages.connect( op5Raw.Output )        
        opDivDetection.LabelsAllowedFlags.connect(opData.AllowLabels)
        opDivDetection.SegmentationImages.connect(opObjExtraction.LabelImage)
        opDivDetection.ObjectFeatures.connect(opObjExtraction.RegionFeaturesAll)
        opDivDetection.ComputedFeatureNames.connect(opObjExtraction.ComputedFeatureNamesAll)
        opDivDetection.SelectedFeatures.setValue(selected_features_div)
        opDivDetection.LabelNames.setValue(['Not Dividing', 'Dividing'])        
        opDivDetection.AllowDeleteLabels.setValue(False)
        opDivDetection.AllowAddLabel.setValue(False)
        opDivDetection.EnableLabelTransfer.setValue(False)
        
        selected_features_objectcount = {}
        for plugin_name in config.selected_features_objectcount.keys():
            selected_features_objectcount[plugin_name] = { name: {} for name in config.selected_features_objectcount[plugin_name] }
        opCellClassification.BinaryImages.connect( op5Binary.Output )
        opCellClassification.RawImages.connect( op5Raw.Output )
        opCellClassification.LabelsAllowedFlags.connect(opData.AllowLabels)
        opCellClassification.SegmentationImages.connect(opObjExtraction.LabelImage)
        opCellClassification.ObjectFeatures.connect(opObjExtraction.RegionFeaturesVigra)
        opCellClassification.ComputedFeatureNames.connect(opObjExtraction.ComputedFeatureNamesVigra)
        opCellClassification.SelectedFeatures.setValue( selected_features_objectcount )        
        opCellClassification.SuggestedLabelNames.setValue( ['false detection',] + [str(i) + ' Objects' for i in range(1,10) ] )
        opCellClassification.AllowDeleteLastLabelOnly.setValue(True)
        opCellClassification.EnableLabelTransfer.setValue(False)
        
        opTracking.RawImage.connect( op5Raw.Output )
        opTracking.LabelImage.connect( opObjExtraction.LabelImage )
        opTracking.ObjectFeatures.connect( opObjExtraction.RegionFeaturesVigra )
        opTracking.ObjectFeaturesWithDivFeatures.connect( opObjExtraction.RegionFeaturesAll)
        opTracking.ComputedFeatureNames.connect( opObjExtraction.ComputedFeatureNamesVigra )
        opTracking.ComputedFeatureNamesWithDivFeatures.connect( opObjExtraction.ComputedFeatureNamesAll )
        opTracking.DivisionProbabilities.connect( opDivDetection.Probabilities )
        opTracking.DetectionProbabilities.connect( opCellClassification.Probabilities )
        opTracking.NumLabels.connect( opCellClassification.NumLabels )
    
        opDataExport.Inputs.resize(3)
        opDataExport.Inputs[0].connect( opTracking.Output )
        opDataExport.Inputs[1].connect( opTracking.MergerOutput )
        opDataExport.Inputs[2].connect( opTracking.LabelImage )
        opDataExport.RawData.connect( op5Raw.Output )
        opDataExport.RawDatasetInfo.connect( opData.DatasetGroup[0] )

    def _inputReady(self, nRoles):
        slot = self.dataSelectionApplet.topLevelOperator.ImageGroup
        if len(slot) > 0:
            input_ready = True
            for sub in slot:
                input_ready = input_ready and \
                    all([sub[i].ready() for i in range(nRoles)])
        else:
            input_ready = False

        return input_ready

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.statusUpdateSignal`
        """
        # If no data, nothing else is ready.
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        input_ready = self._inputReady(2) and not self.dataSelectionApplet.busy

        if not self.fromBinary:
            opThresholding = self.thresholdTwoLevelsApplet.topLevelOperator
            thresholdingOutput = opThresholding.CachedOutput
            thresholding_ready = input_ready and \
                           len(thresholdingOutput) > 0
        else:
            thresholding_ready = True and input_ready

        opObjectExtraction = self.objectExtractionApplet.topLevelOperator
        objectExtractionOutput = opObjectExtraction.ComputedFeatureNamesAll
        features_ready = thresholding_ready and \
                         len(objectExtractionOutput) > 0

        objectCountClassifier_ready = features_ready

        opTracking = self.trackingApplet.topLevelOperator
        tracking_ready = objectCountClassifier_ready and \
                           len(opTracking.EventsVector) > 0
                           

        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= self.trackingApplet.busy
        busy |= self.dataExportApplet.busy
        self._shell.enableProjectChanges( not busy )

        self._shell.setAppletEnabled(self.dataSelectionApplet, not busy)
        if not self.fromBinary:
            self._shell.setAppletEnabled(self.thresholdTwoLevelsApplet, input_ready and not busy)
        self._shell.setAppletEnabled(self.objectExtractionApplet, thresholding_ready and not busy)
        self._shell.setAppletEnabled(self.cellClassificationApplet, features_ready and not busy)
        self._shell.setAppletEnabled(self.divisionDetectionApplet, features_ready and not busy)
        self._shell.setAppletEnabled(self.trackingApplet, objectCountClassifier_ready and not busy)
        self._shell.setAppletEnabled(self.dataExportApplet, tracking_ready and not busy and \
                                    self.dataExportApplet.topLevelOperator.Inputs[0][0].ready() )
        


class ConservationTrackingWorkflowFromBinary( ConservationTrackingWorkflowBase ):
    workflowName = "Automatic Tracking Workflow (Conservation Tracking) from binary image"
    workflowDisplayName = "Automatic Tracking Workflow (Conservation Tracking) [Inputs: Raw Data, Binary Image]"

    withOptTrans = False
    fromBinary = True


class ConservationTrackingWorkflowFromPrediction( ConservationTrackingWorkflowBase ):
    workflowName = "Automatic Tracking Workflow (Conservation Tracking) from prediction image"
    workflowDisplayName = "Automatic Tracking Workflow (Conservation Tracking) [Inputs: Raw Data, Pixel Prediction Map]"

    withOptTrans = False
    fromBinary = False
