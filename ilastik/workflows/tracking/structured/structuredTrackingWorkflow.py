from __future__ import print_function
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
from builtins import range
import os
from lazyflow.graph import Graph
from lazyflow.utility import PathComponents, make_absolute, format_known_keys
from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.tracking.annotations.annotationsApplet import AnnotationsApplet
from ilastik.applets.tracking.structured.structuredTrackingApplet import StructuredTrackingApplet
from ilastik.applets.objectExtraction.objectExtractionApplet import ObjectExtractionApplet
from ilastik.applets.thresholdTwoLevels.thresholdTwoLevelsApplet import ThresholdTwoLevelsApplet
from ilastik.applets.objectClassification.objectClassificationApplet import ObjectClassificationApplet
from ilastik.applets.trackingFeatureExtraction import config
from ilastik.applets.tracking.conservation import config as configConservation


from lazyflow.operators.opReorderAxes import OpReorderAxes
from ilastik.applets.tracking.base.trackingBaseDataExportApplet import TrackingBaseDataExportApplet
from ilastik.applets.trackingFeatureExtraction.trackingFeatureExtractionApplet import TrackingFeatureExtractionApplet
from ilastik.applets.tracking.base.opTrackingBaseDataExport import OpTrackingBaseDataExport
from ilastik.applets.batchProcessing import BatchProcessingApplet
from ilastik.plugins import pluginManager

import logging
logger = logging.getLogger(__name__)

SOLVER = None
try:
    import multiHypoTracking_with_cplex as mht
    SOLVER = "CPLEX"
    logger.info("CPLEX found!")
except ImportError:
    try:
        import multiHypoTracking_with_gurobi as mht
        SOLVER = "GUROBI"
        logger.info("GUROBI found!")
    except ImportError:
        try:
            import dpct
            SOLVER = "DPCT"
            logger.warning("Could not find any learning solver. Tracking will use flow-based solver (DPCT). " + \
                           "Learning for tracking will be disabled!")
        except ImportError:
            raise ImportError("Could not find any solver.")

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
                                                                     selectedFeatures=configConservation.selectedFeaturesDiv)

        self.cellClassificationApplet = ObjectClassificationApplet(workflow=self,
                                                                     name="Object Count Classification",
                                                                     projectFileGroupName="CountClassification",
                                                                     selectedFeatures=configConservation.selectedFeaturesObjectCount)

        self.trackingFeatureExtractionApplet = TrackingFeatureExtractionApplet(name="Object Feature Computation",workflow=self, interactive=False)

        self.objectExtractionApplet = ObjectExtractionApplet(name="Object Feature Computation",workflow=self, interactive=False)

        self.annotationsApplet = AnnotationsApplet( name="Training", workflow=self )
        opAnnotations = self.annotationsApplet.topLevelOperator

        self.trackingApplet = StructuredTrackingApplet( name="Tracking - Structured Learning", workflow=self )
        opStructuredTracking = self.trackingApplet.topLevelOperator

        if SOLVER=="CPLEX" or SOLVER=="GUROBI":
            self._solver="ILP"
        elif SOLVER=="DPCT":
            self._solver="Flow-based"
        else:
            self._solver=None
        opStructuredTracking._solver = self._solver

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
        self._applets.append(self.objectExtractionApplet)
        self._applets.append(self.annotationsApplet)
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

            if '--testFullAnnotations' in workflow_cmdline_args:
                self.testFullAnnotations = True
            else:
                self.testFullAnnotations = False

            self._data_export_args, unused_args = self.dataExportTrackingApplet.parse_known_cmdline_args( workflow_cmdline_args )
            self._batch_input_args, unused_args = self.batchProcessingApplet.parse_known_cmdline_args( workflow_cmdline_args )
        else:
            unused_args = None
            self._data_export_args = None
            self._batch_input_args = None
            self.testFullAnnotations = False

        if unused_args:
            logger.warning("Unused command-line args: {}".format( unused_args ))

    def connectLane(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)
        opTrackingFeatureExtraction = self.trackingFeatureExtractionApplet.topLevelOperator.getLane(laneIndex)

        opAnnotations = self.annotationsApplet.topLevelOperator.getLane(laneIndex)
        if not self.fromBinary:
            opTwoLevelThreshold = self.thresholdTwoLevelsApplet.topLevelOperator.getLane(laneIndex)

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

        opObjExtraction.RawImage.connect( op5Raw.Output )
        opObjExtraction.BinaryImage.connect( op5Binary.Output )

        opTrackingFeatureExtraction.RawImage.connect( op5Raw.Output )
        opTrackingFeatureExtraction.BinaryImage.connect( op5Binary.Output )

        opTrackingFeatureExtraction.setDefaultFeatures(configConservation.allFeaturesObjectCount)
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
        opAnnotations.DivisionProbabilities.connect( opDivDetection.Probabilities )
        opAnnotations.DetectionProbabilities.connect( opCellClassification.Probabilities )
        opAnnotations.MaxNumObj.connect (opCellClassification.MaxNumObj)

        opStructuredTracking.RawImage.connect( op5Raw.Output )
        opStructuredTracking.LabelImage.connect( opTrackingFeatureExtraction.LabelImage )
        opStructuredTracking.ObjectFeatures.connect( opTrackingFeatureExtraction.RegionFeaturesVigra )
        opStructuredTracking.ComputedFeatureNames.connect( opTrackingFeatureExtraction.FeatureNamesVigra )

        if self.divisionDetectionApplet:
            opStructuredTracking.ObjectFeaturesWithDivFeatures.connect( opTrackingFeatureExtraction.RegionFeaturesAll)
            opStructuredTracking.ComputedFeatureNamesWithDivFeatures.connect( opTrackingFeatureExtraction.ComputedFeatureNamesAll )
            opStructuredTracking.DivisionProbabilities.connect( opDivDetection.Probabilities )

        opStructuredTracking.DetectionProbabilities.connect( opCellClassification.Probabilities )
        opStructuredTracking.NumLabels.connect( opCellClassification.NumLabels )
        opStructuredTracking.Annotations.connect (opAnnotations.Annotations)
        opStructuredTracking.Labels.connect (opAnnotations.Labels)
        opStructuredTracking.Divisions.connect (opAnnotations.Divisions)
        opStructuredTracking.Appearances.connect (opAnnotations.Appearances)
        opStructuredTracking.Disappearances.connect (opAnnotations.Disappearances)
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

        # batch processing starts a new lane, so training data needs to be copied from the lane that loaded the project
        loaded_project_lane_index=0
        self.annotationsApplet.topLevelOperator[lane_index].Annotations.setValue(
            self.trackingApplet.topLevelOperator[loaded_project_lane_index].Annotations.value)

        def runLearningAndTracking(withMergerResolution=True):
            if self.testFullAnnotations:
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
            result = self.trackingApplet.topLevelOperator[lane_index].track(
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
                withMergerResolution=withMergerResolution,
                borderAwareWidth = parameters['borderAwareWidth'],
                withArmaCoordinates = parameters['withArmaCoordinates'],
                cplex_timeout = parameters['cplex_timeout'],
                appearance_cost = parameters['appearanceCost'],
                disappearance_cost = parameters['disappearanceCost'],
                force_build_hypotheses_graph = False,
                withBatchProcessing = True
            )

            return result

        if self.testFullAnnotations:

            self.result = runLearningAndTracking(withMergerResolution=False)

            hypothesesGraph = self.trackingApplet.topLevelOperator[lane_index].LearningHypothesesGraph.value
            hypothesesGraph.insertSolution(self.result)
            hypothesesGraph.computeLineage()
            solution = hypothesesGraph.getSolutionDictionary()
            annotations = self.trackingApplet.topLevelOperator[lane_index].Annotations.value

            self.trackingApplet.topLevelOperator[lane_index].insertAnnotationsToHypothesesGraph(hypothesesGraph,annotations,misdetectionLabel=-1)
            hypothesesGraph.computeLineage()
            solutionFromAnnotations = hypothesesGraph.getSolutionDictionary()

            for key in list(solution.keys()):
                if key == 'detectionResults':
                    detectionFlag = True
                    for i in range(len(solution[key])):
                        flag = False
                        for j in range(len(solutionFromAnnotations[key])):
                            if solution[key][i]['id'] == solutionFromAnnotations[key][j]['id'] and \
                                solution[key][i]['value'] == solutionFromAnnotations[key][j]['value']:
                                flag = True
                                break
                        detectionFlag &= flag
                elif key == 'divisionResults':
                    divisionFlag = True
                    for i in range(len(solution[key])):
                        flag = False
                        for j in range(len(solutionFromAnnotations[key])):
                            if solution[key][i]['id'] == solutionFromAnnotations[key][j]['id'] and \
                                solution[key][i]['value'] == solutionFromAnnotations[key][j]['value']:
                                flag = True
                                break
                        divisionFlag &= flag
                elif key == 'linkingResults':
                    linkingFlag = True
                    for i in range(len(solution[key])):
                        flag = False
                        for j in range(len(solutionFromAnnotations[key])):
                            if solution[key][i]['dest'] == solutionFromAnnotations[key][j]['dest'] and \
                                solution[key][i]['src'] == solutionFromAnnotations[key][j]['src']:
                                if solution[key][i]['gap'] == solutionFromAnnotations[key][j]['gap'] and \
                                    solution[key][i]['value'] == solutionFromAnnotations[key][j]['value']:
                                    flag = True
                                    break
                        linkingFlag &= flag

            assert detectionFlag, "Detection results are NOT correct. They differ from your annotated detections."
            logger.info("Detection results are correct.")
            assert divisionFlag, "Division results are NOT correct. They differ from your annotated divisions."
            logger.info("Division results are correct.")
            assert linkingFlag, "Transition results are NOT correct. They differ from your annotated transitions."
            logger.info("Transition results are correct.")
        self.result = runLearningAndTracking(withMergerResolution=parameters['withMergerResolution'])

    def post_process_lane_export(self, lane_index, checkOverwriteFiles=False):
        # Plugin export if selected
        logger.info("Export source is: " + self.dataExportTrackingApplet.topLevelOperator.SelectedExportSource.value)

        print("in post_process_lane_export")
        if self.dataExportTrackingApplet.topLevelOperator.SelectedExportSource.value == OpTrackingBaseDataExport.PluginOnlyName:
            logger.info("Export source plugin selected!")
            selectedPlugin = self.dataExportTrackingApplet.topLevelOperator.SelectedPlugin.value
            additionalPluginArgumentsSlot = self.dataExportTrackingApplet.topLevelOperator.AdditionalPluginArguments

            exportPluginInfo = pluginManager.getPluginByName(selectedPlugin, category="TrackingExportFormats")
            if exportPluginInfo is None:
                logger.error("Could not find selected plugin %s" % exportPluginInfo)
            else:
                exportPlugin = exportPluginInfo.plugin_object
                logger.info("Exporting tracking result using %s" % selectedPlugin)
                name_format = self.dataExportTrackingApplet.topLevelOperator.getLane(lane_index).OutputFilenameFormat.value
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

                self.dataExportTrackingApplet.progressSignal(-1)
                exportStatus = self.trackingApplet.topLevelOperator.getLane(lane_index).exportPlugin(
                    filename, exportPlugin, checkOverwriteFiles, additionalPluginArgumentsSlot)
                self.dataExportTrackingApplet.progressSignal(100)

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
        known_keys['result_type'] = self.dataExportTrackingApplet.topLevelOperator.SelectedPlugin._value
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
        structured_tracking_ready = objectCountClassifier_ready

        withIlpSolver = (self._solver=="ILP")

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
        self._shell.setAppletEnabled(self.objectExtractionApplet, not busy)
        self._shell.setAppletEnabled(self.annotationsApplet, features_ready and not busy) # and withIlpSolver)
        # self._shell.setAppletEnabled(self.dataExportAnnotationsApplet, annotations_ready and not busy and \
        #                                 self.dataExportAnnotationsApplet.topLevelOperator.Inputs[0][0].ready() )
        self._shell.setAppletEnabled(self.trackingApplet, objectCountClassifier_ready and not busy)
        self._shell.setAppletEnabled(self.dataExportTrackingApplet, structured_tracking_ready and not busy and \
                                    self.dataExportTrackingApplet.topLevelOperator.Inputs[0][0].ready() )

class StructuredTrackingWorkflowFromBinary( StructuredTrackingWorkflowBase ):
    workflowName = "Structured Learning Tracking Workflow from binary image"
    workflowDisplayName = "Tracking with Learning [Inputs: Raw Data, Binary Image]"
    workflowDescription = "Structured learning tracking of objects, based on binary images."

    fromBinary = True

class StructuredTrackingWorkflowFromPrediction( StructuredTrackingWorkflowBase ):
    workflowName = "Structured Learning Tracking Workflow from prediction image"
    workflowDisplayName = "Tracking with Learning [Inputs: Raw Data, Pixel Prediction Map]"
    workflowDescription = "Structured learning tracking of objects, based on prediction maps."

    fromBinary = False

