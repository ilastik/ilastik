###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2023, the ilastik developers
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
#          http://ilastik.org/license.html
###############################################################################
import enum
import logging

from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.serverConfiguration.types import Device, ServerConfig
from ilastik.applets.trainableDomainAdaptation import TrainableDomainAdaptationApplet
from ilastik.applets.trainableDomainAdaptation.tdaDataExportApplet import TdaDataExportApplet
from ilastik.config import runtime_cfg
from ilastik.utility import SlotNameEnum
from ilastik.workflows.neuralNetwork._localLauncher import LocalServerLauncher
from ilastik.workflows.neuralNetwork._nnWorkflowBase import _NNWorkflowBase
from lazyflow.operators import tiktorch

# TODO (k-dominik): check if tinyvector is of any benefit here
from lazyflow.roi import TinyVector

logger = logging.getLogger(__name__)


class LocalTrainableDomainAdaptationWorkflow(_NNWorkflowBase):
    """
    This class provides workflow for a local tiktorch executable.
    It can be specified via "--tiktorch_executable" command line parameter.
    Furthermore, the ilastik app will try to find a tiktorch version
    (usually the case when bundled for distribution) if the parameter is not
    supplied. If it cannot be found, workflow is not available.
    """

    auto_register = True

    workflowName = "Trainable Domain Adaptation (Local)"
    workflowDisplayName = "Trainable Domain Adaptation (Local)"

    workflowDescription = "Allows to apply bioimage.io shallow2deep models on your data using bundled tiktorch"

    @enum.unique
    class ExportNames(SlotNameEnum):
        NN_PROBABILITIES = enum.auto()
        PROBABILITIES = enum.auto()
        LABELS = enum.auto()

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):
        tiktorch_exe_path = runtime_cfg.tiktorch_executable
        if not tiktorch_exe_path:
            raise RuntimeError("No tiktorch-executable specified")

        self._launcher = LocalServerLauncher(tiktorch_exe_path)
        super().__init__(shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs)

    def _createFeatureSelectionApplet(self):
        return FeatureSelectionApplet(self, "Feature Selection", "FeatureSelections")

    def _create_local_connection(self):
        conn_str = self._launcher.start()
        return conn_str

    def _createClassifierApplet(self, headless=False, conn_str=None):
        if not headless or not conn_str:
            conn_str = self._create_local_connection()

        self.featureSelectionApplet = self._createFeatureSelectionApplet()
        self.applets.append(self.featureSelectionApplet)
        srv_config = ServerConfig(id="auto", address=conn_str, devices=[Device(id="cpu", name="cpu", enabled=True)])
        connFactory = tiktorch.TiktorchConnectionFactory()
        conn = connFactory.ensure_connection(srv_config)
        device_id, device_name = super()._configure_device(conn)

        srv_config = srv_config.evolve(devices=[Device(id=device_id, name=device_name, enabled=True)])

        tda_appplet = TrainableDomainAdaptationApplet(self, "TrainableDomainAdaptation", connectionFactory=connFactory)
        opNNclassify = tda_appplet.topLevelOperator
        opNNclassify.ServerConfig.setValue(srv_config)

        self.nnClassificationApplet = tda_appplet
        self._applets.append(self.nnClassificationApplet)

    def _createDataExportApplet(self):
        self.dataExportApplet = TdaDataExportApplet(self, "Data Export")

        # Configure global DataExport settings
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opClassify = self.nnClassificationApplet.topLevelOperator
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.WorkingDirectory.connect(opDataSelection.WorkingDirectory)
        opDataExport.SelectionNames.setValue(self.ExportNames.asDisplayNameList())
        opDataExport.PmapColors.connect(opClassify.PmapColors)
        opDataExport.LabelNames.connect(opClassify.LabelNames)

        self.dataExportApplet.prepare_for_entire_export = self.prepare_for_entire_export
        self.dataExportApplet.post_process_entire_export = self.post_process_entire_export

        self._applets.append(self.dataExportApplet)

    def connectLane(self, laneIndex):
        """
        connects the operators for different lanes, each lane has a laneIndex starting at 0
        """
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opNNclassify = self.nnClassificationApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)
        opFeatures = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)

        opFeatures.InputImage.connect(opData.Image)
        # Feature Images -> Classification Op (for training, prediction)
        opNNclassify.FeatureImages.connect(opFeatures.OutputImage)
        opNNclassify.CachedFeatureImages.connect(opFeatures.CachedOutputImage)
        # Input Image ->  Classification Op (for display)
        opNNclassify.InputImages.connect(opData.Image)
        opNNclassify.OverlayImages.connect(opData.ImageGroup[self.DATA_ROLE_OVERLAY])
        # Data Export connections
        opDataExport.RawData.connect(opData.ImageGroup[self.DATA_ROLE_RAW])
        opDataExport.RawDatasetInfo.connect(opData.DatasetGroup[self.DATA_ROLE_RAW])
        opDataExport.Inputs.resize(len(self.ExportNames))
        opDataExport.Inputs[self.ExportNames.NN_PROBABILITIES].connect(opNNclassify.NNPredictionProbabilities)
        opDataExport.Inputs[self.ExportNames.PROBABILITIES].connect(opNNclassify.HeadlessPredictionProbabilities)
        opDataExport.Inputs[self.ExportNames.LABELS].connect(opNNclassify.LabelImages)

    def cleanUp(self):
        super().cleanUp()
        self.nnClassificationApplet.tiktorchController.closeSession()
        self._launcher.stop()

    def handleAppletStateUpdateRequested(self, upstream_ready=True):
        """
        Overridden from NN Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        # If no data, nothing else is ready.
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        input_ready = len(opDataSelection.ImageGroup) > 0 and not self.dataSelectionApplet.busy

        opFeatureSelection = self.featureSelectionApplet.topLevelOperator
        featureOutput = opFeatureSelection.OutputImage
        features_ready = (
            input_ready
            and len(featureOutput) > 0
            and featureOutput[0].ready()
            and (TinyVector(featureOutput[0].meta.shape) > 0).all()
        )
        opNNClassification = self.nnClassificationApplet.topLevelOperator

        opDataExport = self.dataExportApplet.topLevelOperator

        invalid_classifier = (
            opNNClassification.classifier_cache.fixAtCurrent.value
            and opNNClassification.classifier_cache.Output.ready()
            and opNNClassification.classifier_cache.Output.value is None
        )

        predictions_ready = (
            features_ready
            and not invalid_classifier
            and len(opDataExport.Inputs) > 0
            and opDataExport.Inputs[0][self.ExportNames.PROBABILITIES].ready()
            and (TinyVector(opDataExport.Inputs[0][self.ExportNames.PROBABILITIES].meta.shape) > 0).all()
        )

        nn_predictions_ready = (
            predictions_ready
            and opDataExport.Inputs[0][self.ExportNames.NN_PROBABILITIES].ready()
            and (TinyVector(opDataExport.Inputs[0][self.ExportNames.NN_PROBABILITIES].meta.shape) > 0).all()
        )

        # Problems can occur if the features or input data are changed during live update mode.
        # Don't let the user do that.
        live_update_active = not opNNClassification.FreezePredictions.value

        # The user isn't allowed to touch anything while batch processing is running.
        batch_processing_busy = self.batchProcessingApplet.busy

        self._shell.setAppletEnabled(
            self.dataSelectionApplet, not batch_processing_busy and not live_update_active and upstream_ready
        )
        self._shell.setAppletEnabled(
            self.featureSelectionApplet,
            not batch_processing_busy and not live_update_active and input_ready and upstream_ready,
        )

        self._shell.setAppletEnabled(
            self.nnClassificationApplet,
            input_ready and features_ready and not batch_processing_busy and upstream_ready,
        )

        self._shell.setAppletEnabled(
            self.dataExportApplet,
            predictions_ready
            and nn_predictions_ready
            and not batch_processing_busy
            and not live_update_active
            and upstream_ready,
        )
        if self.batchProcessingApplet is not None:
            self._shell.setAppletEnabled(
                self.batchProcessingApplet,
                predictions_ready and nn_predictions_ready and not batch_processing_busy and upstream_ready,
            )

        # Lastly, check for certain "busy" conditions, during which we
        #  should prevent the shell from closing the project.
        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= self.featureSelectionApplet.busy
        busy |= self.nnClassificationApplet.busy
        busy |= self.dataExportApplet.busy
        busy |= self.batchProcessingApplet.busy
        self._shell.enableProjectChanges(not busy)

    def prepare_for_entire_export(self):
        """
        Assigned to DataExportApplet.prepare_for_entire_export
        (See above.)
        """
        # While exporting results, the caches should not be "frozen"
        logger.debug("Unfreezing probability cache for export.")
        opNNClassification = self.nnClassificationApplet.topLevelOperator
        self._freeze_val = opNNClassification.FreezePredictions.value
        opNNClassification.FreezePredictions.setValue(False)

    def post_process_entire_export(self):
        """
        Assigned to DataExportApplet.post_process_entire_export
        (See above.)
        """
        # After export is finished, re-freeze the segmentation caches.
        logger.debug("Restoring probability cache freeze status for export.")
        opNNClassification = self.nnClassificationApplet.topLevelOperator
        opNNClassification.FreezePredictions.setValue(self._freeze_val)
        self._freeze_val = None


class LocalTrainableDomainAdaptationWorkflowLegacy(LocalTrainableDomainAdaptationWorkflow):
    """
    Compatibility class for projects files that were created with
    ilastik 1.4.1rc2 and lower.

    Note the different `workflowName` attribute.
    """

    auto_register = False

    workflowName = "Trainable Domain Adaptation (Local) (beta)"
    workflowDisplayName = "Trainable Domain Adaptation (Local) (beta)"
