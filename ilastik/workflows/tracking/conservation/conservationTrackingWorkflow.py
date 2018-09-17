from builtins import range
import os
from lazyflow.graph import Graph
from lazyflow.utility import PathComponents, make_absolute, format_known_keys
from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet, DatasetInfo
from ilastik.applets.tracking.conservation.conservationTrackingApplet import ConservationTrackingApplet
from ilastik.applets.objectClassification.objectClassificationApplet import ObjectClassificationApplet
from ilastik.applets.thresholdTwoLevels.thresholdTwoLevelsApplet import ThresholdTwoLevelsApplet
from lazyflow.operators.opReorderAxes import OpReorderAxes
from ilastik.applets.trackingFeatureExtraction.trackingFeatureExtractionApplet import TrackingFeatureExtractionApplet
from ilastik.applets.trackingFeatureExtraction import config
from ilastik.applets.tracking.conservation import config as configConservation
from lazyflow.operators.opReorderAxes import OpReorderAxes
from ilastik.applets.tracking.base.trackingBaseDataExportApplet import TrackingBaseDataExportApplet
from ilastik.applets.tracking.base.opTrackingBaseDataExport import OpTrackingBaseDataExport
from ilastik.applets.batchProcessing import BatchProcessingApplet
from ilastik.plugins import pluginManager
from ilastik.config import cfg as ilastik_config

import logging
logger = logging.getLogger(__name__)

class ConservationTrackingWorkflowBase( Workflow ):
    workflowName = "Automatic Tracking Workflow (Conservation Tracking) BASE"

    def __init__( self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs ):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs: del kwargs['graph']
        # if 'withOptTrans' in kwargs:
        #     self.withOptTrans = kwargs['withOptTrans']
        # if 'fromBinary' in kwargs:
        #     self.fromBinary = kwargs['fromBinary']
        super(ConservationTrackingWorkflowBase, self).__init__(shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs)

        data_instructions = 'Use the "Raw Data" tab to load your intensity image(s).\n\n'
        if self.fromBinary:
            data_instructions += 'Use the "Binary Image" tab to load your segmentation image(s).'
        else:
            data_instructions += 'Use the "Prediction Maps" tab to load your pixel-wise probability image(s).'

        # Variables to store division and cell classifiers to prevent retraining every-time batch processing runs
        self.stored_division_classifier = None
        self.stored_cell_classifier = None

        ## Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, 
                                                       "Input Data", 
                                                       "Input Data", 
                                                       forceAxisOrder=['txyzc'],
                                                       instructionText=data_instructions,
                                                       max_lanes=None
                                                       )
        
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        if self.fromBinary:
            opDataSelection.DatasetRoles.setValue( ['Raw Data', 'Segmentation Image'] )
        else:
            opDataSelection.DatasetRoles.setValue( ['Raw Data', 'Prediction Maps'] )
                
        if not self.fromBinary:
            self.thresholdTwoLevelsApplet = ThresholdTwoLevelsApplet( self, 
                                                                  "Threshold and Size Filter", 
                                                                  "ThresholdTwoLevels" )
                                                                   
        self.objectExtractionApplet = TrackingFeatureExtractionApplet(workflow=self, interactive=False,
                                                                      name="Object Feature Computation")                                                                     
        
        opObjectExtraction = self.objectExtractionApplet.topLevelOperator

        self.divisionDetectionApplet = self._createDivisionDetectionApplet(configConservation.selectedFeaturesDiv) # Might be None

        if self.divisionDetectionApplet:
            feature_dict_division = {}
            feature_dict_division[config.features_division_name] = { name: {} for name in config.division_features }
            opObjectExtraction.FeatureNamesDivision.setValue(feature_dict_division)
               
            selected_features_div = {}
            for plugin_name in list(config.selected_features_division.keys()):
                selected_features_div[plugin_name] = { name: {} for name in config.selected_features_division[plugin_name] }
            # FIXME: do not hard code this
            for name in [ 'SquaredDistances_' + str(i) for i in range(config.n_best_successors) ]:
                selected_features_div[config.features_division_name][name] = {}

            opDivisionDetection = self.divisionDetectionApplet.topLevelOperator
            opDivisionDetection.SelectedFeatures.setValue(configConservation.selectedFeaturesDiv)
            opDivisionDetection.LabelNames.setValue(['Not Dividing', 'Dividing'])        
            opDivisionDetection.AllowDeleteLabels.setValue(False)
            opDivisionDetection.AllowAddLabel.setValue(False)
            opDivisionDetection.EnableLabelTransfer.setValue(False)
                
        self.cellClassificationApplet = ObjectClassificationApplet(workflow=self,
                                                                     name="Object Count Classification",
                                                                     projectFileGroupName="CountClassification",
                                                                     selectedFeatures=configConservation.selectedFeaturesObjectCount)

        selected_features_objectcount = {}
        for plugin_name in list(config.selected_features_objectcount.keys()):
            selected_features_objectcount[plugin_name] = { name: {} for name in config.selected_features_objectcount[plugin_name] }

        opCellClassification = self.cellClassificationApplet.topLevelOperator 
        opCellClassification.SelectedFeatures.setValue(configConservation.selectedFeaturesObjectCount)
        opCellClassification.SuggestedLabelNames.setValue( ['False Detection',] + [str(1) + ' Object'] + [str(i) + ' Objects' for i in range(2,10) ] )
        opCellClassification.AllowDeleteLastLabelOnly.setValue(True)
        opCellClassification.EnableLabelTransfer.setValue(False)
                
        self.trackingApplet = ConservationTrackingApplet( workflow=self )

        self.default_export_filename = '{dataset_dir}/{nickname}-exported_data.csv'
        self.dataExportApplet = TrackingBaseDataExportApplet(self, 
                                                             "Tracking Result Export", 
                                                             default_export_filename=self.default_export_filename)

        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.SelectionNames.setValue( ['Object-Identities', 'Tracking-Result', 'Merger-Result'] )
        opDataExport.WorkingDirectory.connect( opDataSelection.WorkingDirectory )

        # Extra configuration for object export table (as CSV table or HDF5 table)
        opTracking = self.trackingApplet.topLevelOperator
        self.dataExportApplet.set_exporting_operator(opTracking)
        self.dataExportApplet.prepare_lane_for_export = self.prepare_lane_for_export
        self.dataExportApplet.post_process_lane_export = self.post_process_lane_export


        # configure export settings
        # settings = {'file path': self.default_export_filename, 'compression': {}, 'file type': 'csv'}
        # selected_features = ['Count', 'RegionCenter', 'RegionRadii', 'RegionAxes']                  
        # opTracking.ExportSettings.setValue( (settings, selected_features) )
        
        self._applets = []                
        self._applets.append(self.dataSelectionApplet)
        if not self.fromBinary:
            self._applets.append(self.thresholdTwoLevelsApplet)
        self._applets.append(self.objectExtractionApplet)

        if self.divisionDetectionApplet:
            self._applets.append(self.divisionDetectionApplet)
        
        self.batchProcessingApplet = BatchProcessingApplet(self, "Batch Processing", self.dataSelectionApplet, self.dataExportApplet)
            
        self._applets.append(self.cellClassificationApplet)
        self._applets.append(self.trackingApplet)
        self._applets.append(self.dataExportApplet)
        self._applets.append(self.batchProcessingApplet)
        
        # Parse export and batch command-line arguments for headless mode
        if workflow_cmdline_args:
            self._data_export_args, unused_args = self.dataExportApplet.parse_known_cmdline_args( workflow_cmdline_args )
            self._batch_input_args, unused_args = self.batchProcessingApplet.parse_known_cmdline_args( workflow_cmdline_args )

        else:
            unused_args = None
            self._data_export_args = None
            self._batch_input_args = None

        if unused_args:
            logger.warning("Unused command-line args: {}".format( unused_args ))
        
    @property
    def applets(self):
        return self._applets

    def _createDivisionDetectionApplet(self,selectedFeatures=dict()):
        return ObjectClassificationApplet(workflow=self,
                                          name="Division Detection (optional)",
                                          projectFileGroupName="DivisionDetection",
                                          selectedFeatures=selectedFeatures)
    
    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def prepareForNewLane(self, laneIndex):
        # Store division and cell classifiers
        if self.divisionDetectionApplet:
            opDivisionClassification = self.divisionDetectionApplet.topLevelOperator
            if opDivisionClassification.classifier_cache.Output.ready() and \
               not opDivisionClassification.classifier_cache._dirty:
                self.stored_division_classifier = opDivisionClassification.classifier_cache.Output.value
            else:
                self.stored_division_classifier = None
                
        opCellClassification = self.cellClassificationApplet.topLevelOperator
        if opCellClassification.classifier_cache.Output.ready() and \
           not opCellClassification.classifier_cache._dirty:
            self.stored_cell_classifier = opCellClassification.classifier_cache.Output.value
        else:
            self.stored_cell_classifier = None

    def handleNewLanesAdded(self):
        """
        If new lanes were added, then we invalidated our classifiers unecessarily.
        Here, we can restore the classifier so it doesn't need to be retrained.
        """
        
        # If we have stored division and cell classifiers, restore them into the workflow now.
        if self.stored_division_classifier:
            opDivisionClassification = self.divisionDetectionApplet.topLevelOperator
            opDivisionClassification.classifier_cache.forceValue(self.stored_division_classifier)
            # Release reference
            self.stored_division_classifier = None
        
        # If we have stored division and cell classifiers, restore them into the workflow now.
        if self.stored_cell_classifier:
            opCellClassification = self.cellClassificationApplet.topLevelOperator
            opCellClassification.classifier_cache.forceValue(self.stored_cell_classifier)
            # Release reference
            self.stored_cell_classifier = None
    
    def connectLane(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        if not self.fromBinary:
            opTwoLevelThreshold = self.thresholdTwoLevelsApplet.topLevelOperator.getLane(laneIndex)
        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)
        opObjExtraction.setDefaultFeatures(configConservation.allFeaturesObjectCount)

        if self.divisionDetectionApplet:
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

        # # Connect operators ##       
        opObjExtraction.RawImage.connect(op5Raw.Output)
        opObjExtraction.BinaryImage.connect(op5Binary.Output)

        if self.divisionDetectionApplet:            
            opDivDetection.BinaryImages.connect( op5Binary.Output )
            opDivDetection.RawImages.connect( op5Raw.Output )        
            opDivDetection.SegmentationImages.connect(opObjExtraction.LabelImage)
            opDivDetection.ObjectFeatures.connect(opObjExtraction.RegionFeaturesAll)
            opDivDetection.ComputedFeatureNames.connect(opObjExtraction.ComputedFeatureNamesAll)
        
        opCellClassification.BinaryImages.connect( op5Binary.Output )
        opCellClassification.RawImages.connect( op5Raw.Output )
        opCellClassification.SegmentationImages.connect(opObjExtraction.LabelImage)
        opCellClassification.ObjectFeatures.connect(opObjExtraction.RegionFeaturesVigra)
        opCellClassification.ComputedFeatureNames.connect(opObjExtraction.FeatureNamesVigra)
        
        if self.divisionDetectionApplet: 
            opTracking.ObjectFeaturesWithDivFeatures.connect( opObjExtraction.RegionFeaturesAll)
            opTracking.ComputedFeatureNamesWithDivFeatures.connect( opObjExtraction.ComputedFeatureNamesAll )
            opTracking.DivisionProbabilities.connect( opDivDetection.Probabilities ) 

        opTracking.RawImage.connect( op5Raw.Output )
        opTracking.LabelImage.connect( opObjExtraction.LabelImage )
        opTracking.ObjectFeatures.connect( opObjExtraction.RegionFeaturesVigra )
        opTracking.ComputedFeatureNames.connect( opObjExtraction.FeatureNamesVigra)
        opTracking.DetectionProbabilities.connect( opCellClassification.Probabilities )
        opTracking.NumLabels.connect( opCellClassification.NumLabels )
    
        opDataExport.Inputs.resize(3)
        opDataExport.Inputs[0].connect( opTracking.RelabeledImage )
        opDataExport.Inputs[1].connect( opTracking.Output )
        opDataExport.Inputs[2].connect( opTracking.MergerOutput )
        opDataExport.RawData.connect( op5Raw.Output )
        opDataExport.RawDatasetInfo.connect( opData.DatasetGroup[0] )
         
    def prepare_lane_for_export(self, lane_index):
        # Bypass cache on headless mode and batch processing mode
        self.objectExtractionApplet.topLevelOperator[lane_index].BypassModeEnabled.setValue(True)
        
        if not self.fromBinary:
            self.thresholdTwoLevelsApplet.topLevelOperator[lane_index].opCache.BypassModeEnabled.setValue(True)
            self.thresholdTwoLevelsApplet.topLevelOperator[lane_index].opSmootherCache.BypassModeEnabled.setValue(True)
         
        # Get axes info  
        maxt = self.trackingApplet.topLevelOperator[lane_index].RawImage.meta.shape[0] 
        maxx = self.trackingApplet.topLevelOperator[lane_index].RawImage.meta.shape[1] 
        maxy = self.trackingApplet.topLevelOperator[lane_index].RawImage.meta.shape[2] 
        maxz = self.trackingApplet.topLevelOperator[lane_index].RawImage.meta.shape[3] 
        time_enum = list(range(maxt))
        x_range = (0, maxx)
        y_range = (0, maxy)
        z_range = (0, maxz)

        ndim = 2
        if ( z_range[1] - z_range[0] ) > 1:
            ndim = 3
        
        parameters = self.trackingApplet.topLevelOperator.Parameters.value
        
        # Save state of axis ranges
        if 'time_range' in parameters:
            self.prev_time_range = parameters['time_range']
        else:
            self.prev_time_range = time_enum
            
        if 'x_range' in parameters:
            self.prev_x_range = parameters['x_range']
        else:
            self.prev_x_range = x_range
        
        if 'y_range' in parameters:
            self.prev_y_range = parameters['y_range']
        else:
            self.prev_y_range = y_range
            
        if 'z_range' in parameters:
            self.prev_z_range = parameters['z_range']
        else:
            self.prev_z_range = z_range

        if 'numFramesPerSplit' in parameters:
            numFramesPerSplit = parameters['numFramesPerSplit']
        else:
            numFramesPerSplit = 0

        self.trackingApplet.topLevelOperator[lane_index].track(
            time_range = time_enum,
            x_range = x_range,
            y_range = y_range,
            z_range = z_range,
            size_range = parameters['size_range'],
            x_scale = parameters['scales'][0],
            y_scale = parameters['scales'][1],
            z_scale = parameters['scales'][2],
            maxDist=parameters['maxDist'],         
            maxObj = parameters['maxObj'],               
            divThreshold=parameters['divThreshold'],
            avgSize=parameters['avgSize'],                
            withTracklets=parameters['withTracklets'], 
            sizeDependent=parameters['sizeDependent'],
            divWeight=parameters['divWeight'],
            transWeight=parameters['transWeight'],
            withDivisions=parameters['withDivisions'],
            withOpticalCorrection=parameters['withOpticalCorrection'],
            withClassifierPrior=parameters['withClassifierPrior'],
            ndim=ndim,
            withMergerResolution=parameters['withMergerResolution'],
            borderAwareWidth = parameters['borderAwareWidth'],
            withArmaCoordinates = parameters['withArmaCoordinates'],
            cplex_timeout = parameters['cplex_timeout'],
            appearance_cost = parameters['appearanceCost'],
            disappearance_cost = parameters['disappearanceCost'],
            max_nearest_neighbors = parameters['max_nearest_neighbors'],
            numFramesPerSplit = numFramesPerSplit,
            force_build_hypotheses_graph = False,
            withBatchProcessing = True
        )

    def post_process_lane_export(self, lane_index, checkOverwriteFiles=False):
        # `checkOverwriteFiles` parameter ensures we check only once for files that could be overwritten, pop up
        # the MessageBox and then don't export. For the next round we click the export button,
        # we really want it to export, so checkOverwriteFiles=False.
        
        # Plugin export if selected
        logger.info("Export source is: " + self.dataExportApplet.topLevelOperator.SelectedExportSource.value)

        if self.dataExportApplet.topLevelOperator.SelectedExportSource.value == OpTrackingBaseDataExport.PluginOnlyName:
            logger.info("Export source plugin selected!")
            selectedPlugin = self.dataExportApplet.topLevelOperator.SelectedPlugin.value
            additionalPluginArgumentsSlot = self.dataExportApplet.topLevelOperator.AdditionalPluginArguments

            exportPluginInfo = pluginManager.getPluginByName(selectedPlugin, category="TrackingExportFormats")
            if exportPluginInfo is None:
                logger.error("Could not find selected plugin %s" % exportPluginInfo)
            else:
                exportPlugin = exportPluginInfo.plugin_object
                logger.info("Exporting tracking result using %s" % selectedPlugin)
                name_format = self.dataExportApplet.topLevelOperator.getLane(lane_index).OutputFilenameFormat.value
                partially_formatted_name = self.getPartiallyFormattedName(lane_index, name_format)

                if exportPlugin.exportsToFile:
                    filename = partially_formatted_name
                    if os.path.basename(filename) == '':
                        filename = os.path.join(filename, 'pluginExport.txt')
                else:
                    filename = partially_formatted_name

                if filename is None or len(str(filename)) == 0:
                    logger.error("Cannot export from plugin with empty output filename")
                    return True

                self.dataExportApplet.progressSignal(-1)
                exportStatus = self.trackingApplet.topLevelOperator.getLane(lane_index).exportPlugin(
                    filename, exportPlugin, checkOverwriteFiles, additionalPluginArgumentsSlot)
                self.dataExportApplet.progressSignal(100)

                if not exportStatus:
                    return False
                logger.info("Export done")

            return True
        return True

    def getPartiallyFormattedName(self, lane_index, path_format_string):
        ''' Takes the format string for the output file, fills in the most important placeholders, and returns it '''
        raw_dataset_info = self.dataSelectionApplet.topLevelOperator.DatasetGroup[lane_index][0].value
        project_path = self.shell.projectManager.currentProjectPath
        project_dir = os.path.dirname(project_path)
        dataset_dir = PathComponents(raw_dataset_info.filePath).externalDirectory
        abs_dataset_dir = make_absolute(dataset_dir, cwd=project_dir)
        known_keys = {}
        known_keys['dataset_dir'] = abs_dataset_dir
        nickname = raw_dataset_info.nickname.replace('*', '')
        if os.path.pathsep in nickname:
            nickname = PathComponents(nickname.split(os.path.pathsep)[0]).fileNameBase
        known_keys['nickname'] = nickname
        known_keys['result_type'] = self.dataExportApplet.topLevelOperator.SelectedPlugin._value
        # use partial formatting to fill in non-coordinate name fields
        partially_formatted_name = format_known_keys(path_format_string, known_keys)
        return partially_formatted_name


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

    def onProjectLoaded(self, projectManager):
        """
        Overridden from Workflow base class.  Called by the Project Manager.
        
        If the user provided command-line arguments, use them to configure 
        the workflow inputs and output settings.
        """

        # Configure the data export operator.
        if self._data_export_args:
            self.dataExportApplet.configure_operator_with_parsed_args( self._data_export_args )

        # Configure headless mode.
        if self._headless and self._batch_input_args and self._data_export_args:
            logger.info("Beginning Batch Processing")
            self.batchProcessingApplet.run_export_from_parsed_args(self._batch_input_args)
            logger.info("Completed Batch Processing")

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
        tracking_ready = objectCountClassifier_ready                          

        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= self.trackingApplet.busy
        busy |= self.dataExportApplet.busy
        busy |= self.batchProcessingApplet.busy
        self._shell.enableProjectChanges( not busy )

        self._shell.setAppletEnabled(self.dataSelectionApplet, not busy)
        if not self.fromBinary:
            self._shell.setAppletEnabled(self.thresholdTwoLevelsApplet, input_ready and not busy)
            
        if self.divisionDetectionApplet:    
            self._shell.setAppletEnabled(self.divisionDetectionApplet, features_ready and not busy)
        
        self._shell.setAppletEnabled(self.objectExtractionApplet, thresholding_ready and not busy)
        self._shell.setAppletEnabled(self.cellClassificationApplet, features_ready and not busy)
        self._shell.setAppletEnabled(self.trackingApplet, objectCountClassifier_ready and not busy)
        self._shell.setAppletEnabled(self.dataExportApplet, tracking_ready and not busy and \
                                    self.dataExportApplet.topLevelOperator.Inputs[0][0].ready() )
        self._shell.setAppletEnabled(self.batchProcessingApplet, tracking_ready and not busy and \
                                    self.dataExportApplet.topLevelOperator.Inputs[0][0].ready() )
        


class ConservationTrackingWorkflowFromBinary( ConservationTrackingWorkflowBase ):
    workflowName = "Automatic Tracking Workflow (Conservation Tracking) from binary image"
    workflowDisplayName = "Tracking [Inputs: Raw Data, Binary Image]"

    withOptTrans = False
    fromBinary = True


class ConservationTrackingWorkflowFromPrediction( ConservationTrackingWorkflowBase ):
    workflowName = "Automatic Tracking Workflow (Conservation Tracking) from prediction image"
    workflowDisplayName = "Tracking [Inputs: Raw Data, Pixel Prediction Map]"

    withOptTrans = False
    fromBinary = False
