import argparse
import logging

import numpy

from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.neuralNetwork import NNClassificationDataExportApplet
from ilastik.applets.batchProcessing import BatchProcessingApplet

from lazyflow.graph import Graph


logger = logging.getLogger(__name__)


class _NNWorkflowBase(Workflow):
    """
    This class provides workflow for a remote tiktorch server
    It has special server configuration applets allowing user to
    connect to remotely running tiktorch server managed by user
    """

    auto_register = False
    workflowName = "Neural Network Classification (BASE)"
    workflowDescription = "Base class for NN Classification workflows"

    DATA_ROLE_RAW = 0
    ROLE_NAMES = ["Raw Data"]
    EXPORT_NAMES = ["Probabilities", "Labels"]

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        """
        Return the "image name list" slot, which lists the names of
        all image lanes (i.e. files) currently loaded by the workflow
        """
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):
        graph = Graph()
        super().__init__(shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs)

        self._applets = []
        self._workflow_cmdline_args = workflow_cmdline_args

        # Parse workflow-specific command-line args
        parser = argparse.ArgumentParser()
        parser.add_argument("--batch-size", help="choose the preferred batch size", type=int)
        parser.add_argument("--halo-size", help="choose the preferred halo size", type=int)
        parser.add_argument("--model-path", help="the neural network model for prediction")

        # Parse the creation args: These were saved to the project file when this project was first created.
        parsed_creation_args, unused_args = parser.parse_known_args(project_creation_args)

        # Parse the cmdline args for the current session.
        self.parsed_args, unused_args = parser.parse_known_args(workflow_cmdline_args)

        # Functions are supposed to expose applets to shell (add to self._applets)
        self.createInputAndConfigApplets()
        self.createClassifierApplet()

        self.dataExportApplet = NNClassificationDataExportApplet(self, "Data Export")

        # Configure global DataExport settings
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opClassify = self.nnClassificationApplet.topLevelOperator
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.WorkingDirectory.connect(opDataSelection.WorkingDirectory)
        opDataExport.SelectionNames.setValue(self.EXPORT_NAMES)
        opDataExport.PmapColors.connect(opClassify.PmapColors)
        opDataExport.LabelNames.connect(opClassify.LabelNames)

        self.batchProcessingApplet = BatchProcessingApplet(
            self, "Batch Processing", self.dataSelectionApplet, self.dataExportApplet
        )

        # Expose for shell
        self._applets.append(self.dataExportApplet)
        self._applets.append(self.batchProcessingApplet)

        if unused_args:
            # We parse the export setting args first.  All remaining args are considered input files by the input applet.
            self._batch_export_args, unused_args = self.dataExportApplet.parse_known_cmdline_args(unused_args)
            self._batch_input_args, unused_args = self.batchProcessingApplet.parse_known_cmdline_args(unused_args)
        else:
            self._batch_input_args = None
            self._batch_export_args = None

        if unused_args:
            logger.warning("Unused command-line args: {}".format(unused_args))

    def createClassifierApplet(self):
        # Override in child class
        raise NotImplemented

    def createInputAndConfigApplets(self):
        self.dataSelectionApplet = self.createDataSelectionApplet()
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue(self.ROLE_NAMES)
        self._applets.append(self.dataSelectionApplet)

    def createDataSelectionApplet(self):
        """
        Can be overridden by subclasses, if they want to use
        special parameters to initialize the DataSelectionApplet.
        """
        data_instructions = "Select your input data using the 'Raw Data' tab shown on the right"
        return DataSelectionApplet(self, "Input Data", "Input Data", instructionText=data_instructions)

    def connectLane(self, laneIndex):
        """
        connects the operators for different lanes, each lane has a laneIndex starting at 0
        """
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opNNclassify = self.nnClassificationApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)

        # Input Image ->  Classification Op (for display)
        opNNclassify.InputImages.connect(opData.Image)
        # Data Export connections
        opDataExport.RawData.connect(opData.ImageGroup[self.DATA_ROLE_RAW])
        opDataExport.RawDatasetInfo.connect(opData.DatasetGroup[self.DATA_ROLE_RAW])
        opDataExport.Inputs.resize(len(self.EXPORT_NAMES))
        opDataExport.Inputs[0].connect(opNNclassify.PredictionProbabilities)
        opDataExport.Inputs[1].connect(opNNclassify.LabelImages)

    def handleAppletStateUpdateRequested(self, upstream_ready=True):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        # If no data, nothing else is ready.
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        input_ready = len(opDataSelection.ImageGroup) > 0 and not self.dataSelectionApplet.busy

        opNNClassification = self.nnClassificationApplet.topLevelOperator

        opDataExport = self.dataExportApplet.topLevelOperator

        predictions_ready = input_ready and len(opDataExport.Inputs) > 0

        # Problems can occur if the features or input data are changed during live update mode.
        # Don't let the user do that.
        live_update_active = not opNNClassification.FreezePredictions.value

        # The user isn't allowed to touch anything while batch processing is running.
        batch_processing_busy = self.batchProcessingApplet.busy

        self._shell.setAppletEnabled(self.dataSelectionApplet, not batch_processing_busy and upstream_ready)

        self._shell.setAppletEnabled(
            self.nnClassificationApplet, input_ready and not batch_processing_busy and upstream_ready
        )
        self._shell.setAppletEnabled(
            self.dataExportApplet,
            predictions_ready and not batch_processing_busy and not live_update_active and upstream_ready,
        )

        if self.batchProcessingApplet is not None:
            self._shell.setAppletEnabled(
                self.batchProcessingApplet, predictions_ready and not batch_processing_busy and upstream_ready
            )

        # Lastly, check for certain "busy" conditions, during which we
        #  should prevent the shell from closing the project.
        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= self.nnClassificationApplet.busy
        busy |= self.dataExportApplet.busy
        busy |= self.batchProcessingApplet.busy
        self._shell.enableProjectChanges(not busy)

    def onProjectLoaded(self, projectManager):
        """
        Overridden from Workflow base class.  Called by the Project Manager.

        If the user provided command-line arguments, use them to configure
        the workflow for batch mode and export all results.
        (This workflow's headless mode supports only batch mode for now.)
        """
        # Headless batch mode.
        if self._headless and self._batch_input_args and self._batch_export_args:
            raise NotImplementedError("headless networkclassification not implemented yet!")
            self.dataExportApplet.configure_operator_with_parsed_args(self._batch_export_args)

            batch_size = self.parsed_args.batch_size
            halo_size = self.parsed_args.halo_size
            model_path = self.parsed_args.model_path

            if batch_size and model_path:

                model = TikTorchLazyflowClassifier(None, model_path, halo_size, batch_size)

                input_shape = self.getBlockShape(model, halo_size)

                self.nnClassificationApplet.topLevelOperator.BlockShape.setValue(input_shape)
                self.nnClassificationApplet.topLevelOperator.NumClasses.setValue(
                    model._tiktorch_net.get("num_output_channels")
                )

                self.nnClassificationApplet.topLevelOperator.Classifier.setValue(model)

            logger.info("Beginning Batch Processing")
            self.batchProcessingApplet.run_export_from_parsed_args(self._batch_input_args)
            logger.info("Completed Batch Processing")

    def getBlockShape(self, model, halo_size):
        """
        calculates the input Block shape
        """
        expected_input_shape = model._tiktorch_net.expected_input_shape
        input_shape = numpy.array(expected_input_shape)

        if not halo_size:
            if "output_size" in model._tiktorch_net._configuration:
                # if the ouputsize of the model is smaller as the expected input shape
                # the halo needs to be changed
                output_shape = model._tiktorch_net.get("output_size")
                if output_shape != input_shape:
                    self.halo_size = int((input_shape[1] - output_shape[1]) / 2)
                    model.HALO_SIZE = self.halo_size
                    print(self.halo_size)

        if len(model._tiktorch_net.get("window_size")) == 2:
            input_shape = numpy.append(input_shape, None)
        else:

            input_shape = input_shape[1:]
            input_shape = numpy.append(input_shape, None)

        input_shape[1:3] -= 2 * self.halo_size

        return input_shape

    def cleanUp(self):
        self.nnClassificationApplet.cleanUp()
