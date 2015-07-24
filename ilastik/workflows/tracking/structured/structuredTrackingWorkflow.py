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
from ilastik.applets.trackingFeatureExtraction.trackingFeatureExtractionApplet import TrackingFeatureExtractionApplet

from lazyflow.operators.opReorderAxes import OpReorderAxes
from ilastik.applets.tracking.base.trackingBaseDataExportApplet import TrackingBaseDataExportApplet
from ilastik.applets.trackingFeatureExtraction.trackingFeatureExtractionApplet import TrackingFeatureExtractionApplet

class StructuredTrackingWorkflow( Workflow ):
    workflowName = "Structured Learning Tracking Workflow"
    workflowDisplayName = "Structured Learning Tracking Workflow [Inputs: Raw Data, Pixel Prediction Map]"
    workflowDescription = "Structured learning tracking of objects, based on Prediction Maps or (binary) Segmentation Images"

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__( self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs ):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs: del kwargs['graph']
        super(StructuredTrackingWorkflow, self).__init__(shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs)

        data_instructions = 'Use the "Raw Data" tab to load your intensity image(s).\n\n'\
                            'Use the "Prediction Maps" tab to load your pixel-wise probability image(s).'
        ## Create applets
        self.dataSelectionApplet = DataSelectionApplet(self,"Input Data","Input Data",batchDataGui=False,force5d=True,instructionText=data_instructions,max_lanes=1)
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ['Raw Data', 'Prediction Maps'] )

        self.thresholdTwoLevelsApplet = ThresholdTwoLevelsApplet( self,"Threshold and Size Filter","ThresholdTwoLevels" )

        self.divisionDetectionApplet = ObjectClassificationApplet(workflow=self,
                                                                     name="Division Detection (optional)",
                                                                     projectFileGroupName="DivisionDetection")

        self.cellClassificationApplet = ObjectClassificationApplet(workflow=self,
                                                                     name="Object Count Classification (optional)",
                                                                     projectFileGroupName="CountClassification")

        self.cropSelectionApplet = CropSelectionApplet(self,"Crop Selection","CropSelection")

        self.trackingFeatureExtractionApplet = TrackingFeatureExtractionApplet(name="Object Feature Computation",workflow=self, interactive=False)

        self.objectExtractionApplet = ObjectExtractionApplet(name="Object Feature Computation",workflow=self, interactive=False)

        self.annotationsApplet = AnnotationsApplet( name="Training", workflow=self )
        opAnnotations = self.annotationsApplet.topLevelOperator

        self.dataExportAnnotationsApplet = TrackingBaseDataExportApplet(self, "Training Export")
        opDataExportAnnotations = self.dataExportAnnotationsApplet.topLevelOperator
        opDataExportAnnotations.SelectionNames.setValue( ['Training', 'Object Identities'] )
        opDataExportAnnotations.WorkingDirectory.connect( opDataSelection.WorkingDirectory )

        self.trackingApplet = StructuredTrackingApplet( name="Tracking - Structured Learning", workflow=self )
        opStructuredTracking = self.trackingApplet.topLevelOperator

        self.dataExportTrackingApplet = TrackingBaseDataExportApplet(self, "Tracking Result Export")
        opDataExportTracking = self.dataExportTrackingApplet.topLevelOperator
        opDataExportTracking.SelectionNames.setValue( ['Tracking Result', 'Merger Result', 'Object Identities'] )
        opDataExportTracking.WorkingDirectory.connect( opDataSelection.WorkingDirectory )

        self._applets = []
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.thresholdTwoLevelsApplet)
        self._applets.append(self.trackingFeatureExtractionApplet)
        self._applets.append(self.divisionDetectionApplet)
        self._applets.append(self.cellClassificationApplet)
        self._applets.append(self.cropSelectionApplet)
        self._applets.append(self.objectExtractionApplet)
        self._applets.append(self.annotationsApplet)
        self._applets.append(self.dataExportAnnotationsApplet)
        self._applets.append(self.trackingApplet)
        self._applets.append(self.dataExportTrackingApplet)

    def connectLane(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)
        opTrackingFeatureExtraction = self.trackingFeatureExtractionApplet.topLevelOperator.getLane(laneIndex)

        opAnnotations = self.annotationsApplet.topLevelOperator.getLane(laneIndex)
        opTwoLevelThreshold = self.thresholdTwoLevelsApplet.topLevelOperator.getLane(laneIndex)
        opDataAnnotationsExport = self.dataExportAnnotationsApplet.topLevelOperator.getLane(laneIndex)

        opCropSelection = self.cropSelectionApplet.topLevelOperator.getLane(laneIndex)
        opStructuredTracking = self.trackingApplet.topLevelOperator.getLane(laneIndex)
        opDataTrackingExport = self.dataExportTrackingApplet.topLevelOperator.getLane(laneIndex)

        ## Connect operators ##
        op5Raw = OpReorderAxes(parent=self)
        op5Raw.AxisOrder.setValue("txyzc")
        op5Raw.Input.connect(opData.ImageGroup[0])

        opDivDetection = self.divisionDetectionApplet.topLevelOperator.getLane(laneIndex)
        opCellClassification = self.cellClassificationApplet.topLevelOperator.getLane(laneIndex)

        opTwoLevelThreshold.InputImage.connect( opData.ImageGroup[1] )
        opTwoLevelThreshold.RawInput.connect( opData.ImageGroup[0] ) # Used for display only

        opCropSelection.InputImage.connect( opData.ImageGroup[0] )
        opCropSelection.PredictionImage.connect( opData.ImageGroup[1] )

        # Use OpReorderAxis for both input datasets such that they are guaranteed to
        # have the same axis order after thresholding
        op5Binary = OpReorderAxes( parent=self )
        op5Binary.AxisOrder.setValue("txyzc")
        op5Binary.Input.connect( opTwoLevelThreshold.CachedOutput )

        opObjExtraction.RawImage.connect( op5Raw.Output )
        opObjExtraction.BinaryImage.connect( op5Binary.Output )

        opTrackingFeatureExtraction.RawImage.connect( op5Raw.Output )
        opTrackingFeatureExtraction.BinaryImage.connect( op5Binary.Output )

        vigra_features = list((set(config.vigra_features)).union(config.selected_features_objectcount[config.features_vigra_name]))
        feature_names_vigra = {}
        feature_names_vigra[config.features_vigra_name] = { name: {} for name in vigra_features }

        opTrackingFeatureExtraction.FeatureNamesVigra.setValue(feature_names_vigra)
        feature_dict_division = {}
        feature_dict_division[config.features_division_name] = { name: {} for name in config.division_features }
        opTrackingFeatureExtraction.FeatureNamesDivision.setValue(feature_dict_division)

        selected_features_div = {}
        for plugin_name in config.selected_features_division.keys():
            selected_features_div[plugin_name] = { name: {} for name in config.selected_features_division[plugin_name] }

        # FIXME: do not hard code this
        for name in [ 'SquaredDistances_' + str(i) for i in range(config.n_best_successors) ]:
            selected_features_div[config.features_division_name][name] = {}

        opDivDetection.BinaryImages.connect( op5Binary.Output )
        opDivDetection.RawImages.connect( op5Raw.Output )
        opDivDetection.LabelsAllowedFlags.connect(opData.AllowLabels)
        opDivDetection.SegmentationImages.connect(opTrackingFeatureExtraction.LabelImage)
        opDivDetection.ObjectFeatures.connect(opTrackingFeatureExtraction.RegionFeaturesAll)
        opDivDetection.ComputedFeatureNames.connect(opTrackingFeatureExtraction.ComputedFeatureNamesAll)
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
        opCellClassification.SegmentationImages.connect(opTrackingFeatureExtraction.LabelImage)
        opCellClassification.ObjectFeatures.connect(opTrackingFeatureExtraction.RegionFeaturesVigra)
        opCellClassification.ComputedFeatureNames.connect(opTrackingFeatureExtraction.ComputedFeatureNamesVigra)
        opCellClassification.SelectedFeatures.setValue( selected_features_objectcount )
        opCellClassification.SuggestedLabelNames.setValue( ['false detection',] + [str(i) + ' Objects' for i in range(1,10) ] )
        opCellClassification.AllowDeleteLastLabelOnly.setValue(True)
        opCellClassification.EnableLabelTransfer.setValue(False)

        opAnnotations.RawImage.connect( op5Raw.Output )
        opAnnotations.BinaryImage.connect( op5Binary.Output )
        opAnnotations.LabelImage.connect( opObjExtraction.LabelImage )
        opAnnotations.ObjectFeatures.connect( opObjExtraction.RegionFeatures )
        opAnnotations.Crops.connect( opCropSelection.Crops)

        opDataAnnotationsExport.Inputs.resize(2)
        opDataAnnotationsExport.Inputs[0].connect( opAnnotations.TrackImage )
        opDataAnnotationsExport.Inputs[1].connect( opAnnotations.LabelImage )
        opDataAnnotationsExport.RawData.connect( op5Raw.Output )
        opDataAnnotationsExport.RawDatasetInfo.connect( opData.DatasetGroup[0] )

        opStructuredTracking.RawImage.connect( op5Raw.Output )
        opStructuredTracking.LabelImage.connect( opObjExtraction.LabelImage )
        #opStructuredTracking.ObjectFeatures.connect( opObjExtraction.RegionFeaturesVigra )
        #opStructuredTracking.ComputedFeatureNames.connect( opObjExtraction.ComputedFeatureNamesVigra )
        opStructuredTracking.ObjectFeatures.connect( opTrackingFeatureExtraction.RegionFeaturesVigra )
        opStructuredTracking.ComputedFeatureNames.connect( opTrackingFeatureExtraction.ComputedFeatureNamesVigra )
        opStructuredTracking.DivisionProbabilities.connect( opDivDetection.Probabilities )
        opStructuredTracking.DetectionProbabilities.connect( opCellClassification.Probabilities )
        opStructuredTracking.NumLabels.connect( opCellClassification.NumLabels )
        opStructuredTracking.Crops.connect (opCropSelection.Crops)
        opStructuredTracking.Annotations.connect (opAnnotations.Annotations)
        opStructuredTracking.Labels.connect (opAnnotations.Labels)
        opStructuredTracking.Divisions.connect (opAnnotations.Divisions)
        opStructuredTracking.MaxNumObj.connect (opCellClassification.MaxNumObj)

        opDataTrackingExport.Inputs.resize(3)
        opDataTrackingExport.Inputs[0].connect( opStructuredTracking.Output )
        opDataTrackingExport.Inputs[1].connect( opStructuredTracking.MergerOutput )
        opDataTrackingExport.Inputs[2].connect( opStructuredTracking.LabelImage )
        opDataTrackingExport.RawData.connect( op5Raw.Output )
        opDataTrackingExport.RawDatasetInfo.connect( opData.DatasetGroup[0] )

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
        input_ready = self._inputReady(2) and not self.dataSelectionApplet.busy

        opThresholding = self.thresholdTwoLevelsApplet.topLevelOperator
        thresholdingOutput = opThresholding.CachedOutput
        thresholding_ready = input_ready and len(thresholdingOutput) > 0

        #features_ready = thresholding_ready and \
        #                 len(objectExtractionOutput) > 0

        opTrackingFeatureExtraction = self.trackingFeatureExtractionApplet.topLevelOperator
        trackingFeatureExtractionOutput = opTrackingFeatureExtraction.ComputedFeatureNamesAll
        tracking_features_ready = thresholding_ready and len(trackingFeatureExtractionOutput) > 0

        opCropSelection = self.cropSelectionApplet.topLevelOperator
        croppingOutput = opCropSelection.Crops
        cropping_ready = thresholding_ready and len(croppingOutput) > 0

        objectCountClassifier_ready = tracking_features_ready

        opObjectExtraction = self.objectExtractionApplet.topLevelOperator
        objectExtractionOutput = opObjectExtraction.ComputedFeatureNames
        features_ready = thresholding_ready and \
                         len(objectExtractionOutput) > 0

        opAnnotations = self.annotationsApplet.topLevelOperator
        annotations_ready = features_ready and \
                           len(opAnnotations.Labels) > 0 and \
                           opAnnotations.Labels.ready() and \
                           len(opAnnotations.Divisions) > 0 and \
                           opAnnotations.Divisions.ready() and \
                           opAnnotations.TrackImage.ready()

        opStructuredTracking = self.trackingApplet.topLevelOperator
        structured_tracking_ready = objectCountClassifier_ready and \
                           len(opStructuredTracking.EventsVector) > 0
        busy = False
        busy |= self.dataSelectionApplet.busy
        #busy |= self.thresholdTwoLevelsApplet.busy
        #busy |= self.trackingFeatureExtractionApplet.busy
        #busy |= self.divisionDetectionApplet.busy
        #busy |= self.cellClassificationApplet.busy
        #busy |= self.cropSelectionApplet.busy
        busy |= self.annotationsApplet.busy
        busy |= self.dataExportAnnotationsApplet.busy
        busy |= self.trackingApplet.busy

        self._shell.enableProjectChanges( not busy )

        self._shell.setAppletEnabled(self.dataSelectionApplet, not busy)
        self._shell.setAppletEnabled(self.thresholdTwoLevelsApplet, input_ready and not busy)
        self._shell.setAppletEnabled(self.trackingFeatureExtractionApplet, thresholding_ready and not busy)
        self._shell.setAppletEnabled(self.cellClassificationApplet, tracking_features_ready and not busy)
        self._shell.setAppletEnabled(self.divisionDetectionApplet, tracking_features_ready and not busy)
        self._shell.setAppletEnabled(self.cropSelectionApplet, thresholding_ready and not busy)
        self._shell.setAppletEnabled(self.objectExtractionApplet, not busy)
        self._shell.setAppletEnabled(self.annotationsApplet, features_ready and not busy)
        self._shell.setAppletEnabled(self.dataExportAnnotationsApplet, annotations_ready and not busy and \
                                        self.dataExportAnnotationsApplet.topLevelOperator.Inputs[0][0].ready() )
        self._shell.setAppletEnabled(self.trackingApplet, objectCountClassifier_ready and not busy)
        self._shell.setAppletEnabled(self.dataExportTrackingApplet, structured_tracking_ready and not busy and \
                                    self.dataExportTrackingApplet.topLevelOperator.Inputs[0][0].ready() )
