###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
import os
from lazyflow.graph import Graph
from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.tracking.annotations.annotationsApplet import AnnotationsApplet
from ilastik.applets.tracking.structured.structuredTrackingApplet import StructuredTrackingApplet
from ilastik.applets.objectExtraction.objectExtractionApplet import ObjectExtractionApplet
from ilastik.applets.thresholdTwoLevels.thresholdTwoLevelsApplet import ThresholdTwoLevelsApplet
from ilastik.applets.objectClassification.objectClassificationApplet import ObjectClassificationApplet
from ilastik.applets.cropping.cropSelectionApplet import CropSelectionApplet
from ilastik.applets.trackingFeatureExtraction import config
from ilastik.applets.tracking.conservation import config as configConservation
from ilastik.applets.tracking.structured import config as configStructured

from lazyflow.operators.opReorderAxes import OpReorderAxes
from ilastik.applets.tracking.base.trackingBaseDataExportApplet import TrackingBaseDataExportApplet
from ilastik.applets.trackingFeatureExtraction.trackingFeatureExtractionApplet import TrackingFeatureExtractionApplet
from ilastik.applets.batchProcessing import BatchProcessingApplet

import logging
logger = logging.getLogger(__name__)

class StructuredTrackingWorkflowBase( Workflow ):
    workflowName = "Structured Learning Tracking Workflow BASE"

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__( self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs ):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs: del kwargs['graph']

        super(StructuredTrackingWorkflowBase, self).__init__(shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs)

        data_instructions = 'Use the "Raw Data" tab to load your intensity image(s).\n\n'
        if self.fromBinary:
            data_instructions += 'Use the "Binary Image" tab to load your segmentation image(s).'
        else:
            data_instructions += 'Use the "Prediction Maps" tab to load your pixel-wise probability image(s).'

        # Create applets
        self.dataSelectionApplet = DataSelectionApplet(self,
            "Input Data",
            "Input Data",
            batchDataGui=False,
            forceAxisOrder=['txyzc'],
            instructionText=data_instructions,
            max_lanes=1)

        opDataSelection = self.dataSelectionApplet.topLevelOperator
        if self.fromBinary:
            opDataSelection.DatasetRoles.setValue( ['Raw Data', 'Binary Image'] )
        else:
            opDataSelection.DatasetRoles.setValue( ['Raw Data', 'Prediction Maps'] )

        if not self.fromBinary:
            self.thresholdTwoLevelsApplet = ThresholdTwoLevelsApplet( self,"Threshold and Size Filter","ThresholdTwoLevels" )

        self.divisionDetectionApplet = ObjectClassificationApplet(workflow=self,
                                                                     name="Division Detection (optional)",
                                                                     projectFileGroupName="DivisionDetection",
                                                                     selectedFeatures=configStructured.selectedFeaturesDiv)

        self.cellClassificationApplet = ObjectClassificationApplet(workflow=self,
                                                                     name="Object Count Classification",
                                                                     projectFileGroupName="CountClassification",
                                                                     selectedFeatures=configStructured.selectedFeaturesObjectCount)

        self.cropSelectionApplet = CropSelectionApplet(self,"Crop Selection","CropSelection")

        self.trackingFeatureExtractionApplet = TrackingFeatureExtractionApplet(name="Object Feature Computation",workflow=self, interactive=False)

        self.objectExtractionApplet = ObjectExtractionApplet(name="Object Feature Computation",workflow=self, interactive=False)

        self.annotationsApplet = AnnotationsApplet( name="Training", workflow=self )
        opAnnotations = self.annotationsApplet.topLevelOperator

        # self.default_training_export_filename = '{dataset_dir}/{nickname}-training_exported_data.csv'
        # self.dataExportAnnotationsApplet = TrackingBaseDataExportApplet(self, "Training Export",default_export_filename=self.default_training_export_filename)
        # opDataExportAnnotations = self.dataExportAnnotationsApplet.topLevelOperator
        # opDataExportAnnotations.SelectionNames.setValue( ['User Training for Tracking', 'Object Identities'] )
        # opDataExportAnnotations.WorkingDirectory.connect( opDataSelection.WorkingDirectory )
        # self.dataExportAnnotationsApplet.set_exporting_operator(opAnnotations)

        self.trackingApplet = StructuredTrackingApplet( name="Tracking - Structured Learning", workflow=self )
        opStructuredTracking = self.trackingApplet.topLevelOperator

        self.default_tracking_export_filename = '{dataset_dir}/{nickname}-tracking_exported_data.csv'
        self.dataExportTrackingApplet = TrackingBaseDataExportApplet(self, "Tracking Result Export",default_export_filename=self.default_tracking_export_filename)
        opDataExportTracking = self.dataExportTrackingApplet.topLevelOperator
        opDataExportTracking.SelectionNames.setValue( ['Tracking-Result', 'Merger-Result', 'Object-Identities'] )
        opDataExportTracking.WorkingDirectory.connect( opDataSelection.WorkingDirectory )
        self.dataExportTrackingApplet.set_exporting_operator(opStructuredTracking)
        self.dataExportTrackingApplet.prepare_lane_for_export = self.prepare_lane_for_export
        self.dataExportTrackingApplet.post_process_lane_export = self.post_process_lane_export

        # configure export settings
        settings = {'file path': self.default_tracking_export_filename, 'compression': {}, 'file type': 'h5'}
        selected_features = ['Count', 'RegionCenter', 'RegionRadii', 'RegionAxes']
        opStructuredTracking.ExportSettings.setValue( (settings, selected_features) )

        self._applets = []
        self._applets.append(self.dataSelectionApplet)
        if not self.fromBinary:
            self._applets.append(self.thresholdTwoLevelsApplet)
        self._applets.append(self.trackingFeatureExtractionApplet)
        self._applets.append(self.divisionDetectionApplet)

        self.batchProcessingApplet = BatchProcessingApplet(self, "Batch Processing", self.dataSelectionApplet, self.dataExportTrackingApplet)

        self._applets.append(self.cellClassificationApplet)
        self._applets.append(self.cropSelectionApplet)
        self._applets.append(self.objectExtractionApplet)
        self._applets.append(self.annotationsApplet)
        # self._applets.append(self.dataExportAnnotationsApplet)
        self._applets.append(self.trackingApplet)
        self._applets.append(self.dataExportTrackingApplet)

        if self.divisionDetectionApplet:
            opDivDetection = self.divisionDetectionApplet.topLevelOperator
            opDivDetection.SelectedFeatures.setValue(configConservation.selectedFeaturesDiv)
            opDivDetection.LabelNames.setValue(['Not Dividing', 'Dividing'])
            opDivDetection.AllowDeleteLabels.setValue(False)
            opDivDetection.AllowAddLabel.setValue(False)
            opDivDetection.EnableLabelTransfer.setValue(False)

        opCellClassification = self.cellClassificationApplet.topLevelOperator
        opCellClassification.SelectedFeatures.setValue(configConservation.selectedFeaturesObjectCount )
        opCellClassification.SuggestedLabelNames.setValue( ['False Detection',] + [str(1) + ' Object'] + [str(i) + ' Objects' for i in range(2,10) ] )
        opCellClassification.AllowDeleteLastLabelOnly.setValue(True)
        opCellClassification.EnableLabelTransfer.setValue(False)

        if workflow_cmdline_args:
            self._data_export_args, unused_args = self.dataExportTrackingApplet.parse_known_cmdline_args( workflow_cmdline_args )
            self._batch_input_args, unused_args = self.batchProcessingApplet.parse_known_cmdline_args( workflow_cmdline_args )
        else:
            unused_args = None
            self._data_export_args = None
            self._batch_input_args = None

        if unused_args:
            logger.warn("Unused command-line args: {}".format( unused_args ))

    def connectLane(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)
        opTrackingFeatureExtraction = self.trackingFeatureExtractionApplet.topLevelOperator.getLane(laneIndex)

        opAnnotations = self.annotationsApplet.topLevelOperator.getLane(laneIndex)
        if not self.fromBinary:
            opTwoLevelThreshold = self.thresholdTwoLevelsApplet.topLevelOperator.getLane(laneIndex)
        # opDataAnnotationsExport = self.dataExportAnnotationsApplet.topLevelOperator.getLane(laneIndex)

        opCropSelection = self.cropSelectionApplet.topLevelOperator.getLane(laneIndex)
        opStructuredTracking = self.trackingApplet.topLevelOperator.getLane(laneIndex)
        opDataTrackingExport = self.dataExportTrackingApplet.topLevelOperator.getLane(laneIndex)

        ## Connect operators ##
        op5Raw = OpReorderAxes(parent=self)
        op5Raw.AxisOrder.setValue("txyzc")
        op5Raw.Input.connect(opData.ImageGroup[0])

        opDivDetection = self.divisionDetectionApplet.topLevelOperator.getLane(laneIndex)
        opCellClassification = self.cellClassificationApplet.topLevelOperator.getLane(laneIndex)

        if not self.fromBinary:
            opTwoLevelThreshold.InputImage.connect( opData.ImageGroup[1] )
            opTwoLevelThreshold.RawInput.connect( opData.ImageGroup[0] ) # Used for display only
            binarySrc = opTwoLevelThreshold.CachedOutput
        else:
            binarySrc = opData.ImageGroup[1]
        # Use Op5ifyers for both input datasets such that they are guaranteed to
        # have the same axis order after thresholding
        op5Binary = OpReorderAxes(parent=self)
        op5Binary.AxisOrder.setValue("txyzc")
        op5Binary.Input.connect(binarySrc)

        opCropSelection.InputImage.connect( opData.ImageGroup[0] )
        opCropSelection.PredictionImage.connect( opData.ImageGroup[1] )

        opObjExtraction.RawImage.connect( op5Raw.Output )
        opObjExtraction.BinaryImage.connect( op5Binary.Output )

        opTrackingFeatureExtraction.RawImage.connect( op5Raw.Output )
        opTrackingFeatureExtraction.BinaryImage.connect( op5Binary.Output )

        # vigra_features = list((set(config.vigra_features)).union(config.selected_features_objectcount[config.features_vigra_name]))
        # feature_names_vigra = {}
        # feature_names_vigra[config.features_vigra_name] = { name: {} for name in vigra_features }

        opTrackingFeatureExtraction.FeatureNamesVigra.setValue(configConservation.allFeaturesObjectCount)
        feature_dict_division = {}
        feature_dict_division[config.features_division_name] = { name: {} for name in config.division_features }
        opTrackingFeatureExtraction.FeatureNamesDivision.setValue(feature_dict_division)

        if self.divisionDetectionApplet:
            opDivDetection.BinaryImages.connect( op5Binary.Output )
            opDivDetection.RawImages.connect( op5Raw.Output )
            opDivDetection.SegmentationImages.connect(opTrackingFeatureExtraction.LabelImage)
            opDivDetection.ObjectFeatures.connect(opTrackingFeatureExtraction.RegionFeaturesAll)
            opDivDetection.ComputedFeatureNames.connect(opTrackingFeatureExtraction.ComputedFeatureNamesAll)

        opCellClassification.BinaryImages.connect( op5Binary.Output )
        opCellClassification.RawImages.connect( op5Raw.Output )
        opCellClassification.SegmentationImages.connect(opTrackingFeatureExtraction.LabelImage)
        opCellClassification.ObjectFeatures.connect(opTrackingFeatureExtraction.RegionFeaturesAll)
        opCellClassification.ComputedFeatureNames.connect(opTrackingFeatureExtraction.ComputedFeatureNamesNoDivisions)

        opAnnotations.RawImage.connect( op5Raw.Output )
        opAnnotations.BinaryImage.connect( op5Binary.Output )
        opAnnotations.LabelImage.connect( opObjExtraction.LabelImage )
        opAnnotations.ObjectFeatures.connect( opObjExtraction.RegionFeatures )
        opAnnotations.ComputedFeatureNames.connect(opObjExtraction.Features)
        opAnnotations.Crops.connect( opCropSelection.Crops)
        opAnnotations.DivisionProbabilities.connect( opDivDetection.Probabilities )
        opAnnotations.DetectionProbabilities.connect( opCellClassification.Probabilities )
        opAnnotations.MaxNumObj.connect (opCellClassification.MaxNumObj)

        # opDataAnnotationsExport.Inputs.resize(2)
        # opDataAnnotationsExport.Inputs[0].connect( opAnnotations.TrackImage )
        # opDataAnnotationsExport.Inputs[1].connect( opAnnotations.LabelImage )
        # opDataAnnotationsExport.RawData.connect( op5Raw.Output )
        # opDataAnnotationsExport.RawDatasetInfo.connect( opData.DatasetGroup[0] )

        opStructuredTracking.RawImage.connect( op5Raw.Output )
        opStructuredTracking.LabelImage.connect( opTrackingFeatureExtraction.LabelImage )
        opStructuredTracking.ObjectFeatures.connect( opTrackingFeatureExtraction.RegionFeaturesVigra )
        opStructuredTracking.ComputedFeatureNames.connect( opTrackingFeatureExtraction.FeatureNamesVigra )

        if self.divisionDetectionApplet:
            opStructuredTracking.ObjectFeaturesWithDivFeatures.connect( opTrackingFeatureExtraction.RegionFeaturesAll)
            opStructuredTracking.ComputedFeatureNamesWithDivFeatures.connect( opTrackingFeatureExtraction.ComputedFeatureNamesAll )
            opStructuredTracking.DivisionProbabilities.connect( opDivDetection.Probabilities )

        # configure tracking export settings
        settings = {'file path': self.default_tracking_export_filename, 'compression': {}, 'file type': 'csv'}
        selected_features = ['Count', 'RegionCenter']
        opStructuredTracking.configure_table_export_settings(settings, selected_features)

        opStructuredTracking.DetectionProbabilities.connect( opCellClassification.Probabilities )
        opStructuredTracking.NumLabels.connect( opCellClassification.NumLabels )
        opStructuredTracking.Crops.connect (opCropSelection.Crops)
        opStructuredTracking.Annotations.connect (opAnnotations.Annotations)
        opStructuredTracking.Labels.connect (opAnnotations.Labels)
        opStructuredTracking.Divisions.connect (opAnnotations.Divisions)
        opStructuredTracking.MaxNumObj.connect (opCellClassification.MaxNumObj)

        opDataTrackingExport.Inputs.resize(3)
        opDataTrackingExport.Inputs[0].connect( opStructuredTracking.RelabeledImage )
        opDataTrackingExport.Inputs[1].connect( opStructuredTracking.MergerOutput )
        opDataTrackingExport.Inputs[2].connect( opStructuredTracking.LabelImage )
        opDataTrackingExport.RawData.connect( op5Raw.Output )
        opDataTrackingExport.RawDatasetInfo.connect( opData.DatasetGroup[0] )

    def prepare_lane_for_export(self, lane_index):
        import logging
        logger = logging.getLogger(__name__)

        maxt = self.trackingApplet.topLevelOperator[lane_index].RawImage.meta.shape[0]
        maxx = self.trackingApplet.topLevelOperator[lane_index].RawImage.meta.shape[1]
        maxy = self.trackingApplet.topLevelOperator[lane_index].RawImage.meta.shape[2]
        maxz = self.trackingApplet.topLevelOperator[lane_index].RawImage.meta.shape[3]
        time_enum = range(maxt)
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

        # batch processing starts a new lane, so training data needs to be copied from the lane that loaded the project
        loaded_project_lane_index=0
        self.annotationsApplet.topLevelOperator[lane_index].Annotations.setValue(
            self.trackingApplet.topLevelOperator[loaded_project_lane_index].Annotations.value)

        self.cropSelectionApplet.topLevelOperator[lane_index].Crops.setValue(
            self.trackingApplet.topLevelOperator[loaded_project_lane_index].Crops.value)

        logger.info("Test: Structured Learning")
        weights = self.trackingApplet.topLevelOperator[lane_index]._runStructuredLearning(
            z_range,
            parameters['maxObj'],
            parameters['max_nearest_neighbors'],
            parameters['maxDist'],
            parameters['divThreshold'],
            [parameters['scales'][0],parameters['scales'][1],parameters['scales'][2]],
            parameters['size_range'],
            parameters['withDivisions'],
            parameters['borderAwareWidth'],
            parameters['withClassifierPrior'],
            withBatchProcessing=True)
        logger.info("weights: {}".format(weights))

        logger.info("Test: Tracking")
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
            detWeight=parameters['detWeight'],
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
            force_build_hypotheses_graph = False,
            withBatchProcessing = True
        )

    def post_process_lane_export(self, lane_index):
        # FIXME: This probably only works for the non-blockwise export slot.
        #        We should assert that the user isn't using the blockwise slot.
        settings, selected_features = self.trackingApplet.topLevelOperator.getLane(lane_index).get_table_export_settings()
        from lazyflow.utility import PathComponents, make_absolute, format_known_keys

        if settings:
            self.dataExportTrackingApplet.progressSignal.emit(-1)
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

            # use partial formatting to fill in non-coordinate name fields
            name_format = settings['file path']
            partially_formatted_name = format_known_keys( name_format, known_keys )
            settings['file path'] = partially_formatted_name

            req = self.trackingApplet.topLevelOperator.getLane(lane_index).export_object_data(
                        lane_index,
                        # FIXME: Even in non-headless mode, we can't show the gui because we're running in a non-main thread.
                        #        That's not a huge deal, because there's still a progress bar for the overall export.
                        show_gui=False)

            req.wait()
            self.dataExportTrackingApplet.progressSignal.emit(100)

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
            self.dataExportTrackingApplet.configure_operator_with_parsed_args( self._data_export_args )

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
        input_ready = self._inputReady(2) and not self.dataSelectionApplet.busy

        if not self.fromBinary:
            opThresholding = self.thresholdTwoLevelsApplet.topLevelOperator
            thresholdingOutput = opThresholding.CachedOutput
            thresholding_ready = input_ready and len(thresholdingOutput) > 0
        else:
            thresholding_ready = input_ready

        opTrackingFeatureExtraction = self.trackingFeatureExtractionApplet.topLevelOperator
        trackingFeatureExtractionOutput = opTrackingFeatureExtraction.ComputedFeatureNamesAll
        tracking_features_ready = thresholding_ready and len(trackingFeatureExtractionOutput) > 0

        opCropSelection = self.cropSelectionApplet.topLevelOperator
        croppingOutput = opCropSelection.Crops
        cropping_ready = thresholding_ready and len(croppingOutput) > 0

        objectCountClassifier_ready = tracking_features_ready

        opObjectExtraction = self.objectExtractionApplet.topLevelOperator
        objectExtractionOutput = opObjectExtraction.RegionFeatures
        features_ready = thresholding_ready and \
                         len(objectExtractionOutput) > 0

        opAnnotations = self.annotationsApplet.topLevelOperator
        annotations_ready = features_ready and \
                           len(opAnnotations.Labels) > 0 and \
                           opAnnotations.Labels.ready() and \
                           opAnnotations.TrackImage.ready()

        opStructuredTracking = self.trackingApplet.topLevelOperator
        structured_tracking_ready = objectCountClassifier_ready and \
                           len(opStructuredTracking.EventsVector) > 0
        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= self.annotationsApplet.busy
        # busy |= self.dataExportAnnotationsApplet.busy
        busy |= self.trackingApplet.busy
        busy |= self.dataExportTrackingApplet.busy

        self._shell.enableProjectChanges( not busy )

        self._shell.setAppletEnabled(self.dataSelectionApplet, not busy)
        if not self.fromBinary:
            self._shell.setAppletEnabled(self.thresholdTwoLevelsApplet, input_ready and not busy)
        self._shell.setAppletEnabled(self.trackingFeatureExtractionApplet, thresholding_ready and not busy)
        self._shell.setAppletEnabled(self.cellClassificationApplet, tracking_features_ready and not busy)
        self._shell.setAppletEnabled(self.divisionDetectionApplet, tracking_features_ready and not busy)
        self._shell.setAppletEnabled(self.cropSelectionApplet, thresholding_ready and not busy)
        self._shell.setAppletEnabled(self.objectExtractionApplet, not busy)
        self._shell.setAppletEnabled(self.annotationsApplet, features_ready and not busy)
        # self._shell.setAppletEnabled(self.dataExportAnnotationsApplet, annotations_ready and not busy and \
        #                                 self.dataExportAnnotationsApplet.topLevelOperator.Inputs[0][0].ready() )
        self._shell.setAppletEnabled(self.trackingApplet, objectCountClassifier_ready and not busy)
        self._shell.setAppletEnabled(self.dataExportTrackingApplet, structured_tracking_ready and not busy and \
                                    self.dataExportTrackingApplet.topLevelOperator.Inputs[0][0].ready() )

class StructuredTrackingWorkflowFromBinary( StructuredTrackingWorkflowBase ):
    workflowName = "Structured Learning Tracking Workflow from binary image"
    workflowDisplayName = "(BETA) Tracking with Learning [Inputs: Raw Data, Binary Image]"
    workflowDescription = "Structured learning tracking of objects, based on binary images."

    fromBinary = True

class StructuredTrackingWorkflowFromPrediction( StructuredTrackingWorkflowBase ):
    workflowName = "Structured Learning Tracking Workflow from prediction image"
    workflowDisplayName = "(BETA) Tracking with Learning [Inputs: Raw Data, Pixel Prediction Map]"
    workflowDescription = "Structured learning tracking of objects, based on prediction maps."

    fromBinary = False

