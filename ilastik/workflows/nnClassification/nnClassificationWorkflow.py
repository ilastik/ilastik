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
from __future__ import division
import argparse
import logging

import numpy

from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.networkClassification import NNClassApplet, NNClassificationDataExportApplet
from ilastik.applets.batchProcessing import BatchProcessingApplet

from lazyflow.classifiers import TikTorchLazyflowClassifier
from lazyflow.operators.opReorderAxes import OpReorderAxes

from lazyflow.graph import Graph


logger = logging.getLogger(__name__)

class NNClassificationWorkflow(Workflow):
    """
    Workflow for the Neural Network Classification Applet
    """
    workflowName = "Neural Network Classification"
    workflowDescription = "This is obviously self-explanatory."
    defaultAppletIndex = 0 # show DataSelection by default

    DATA_ROLE_RAW = 0
    ROLE_NAMES = ['Raw Data']
    EXPORT_NAMES = ['Probabilities']

    @property
    def applets(self):
        """
        Return the list of applets that are owned by this workflow
        """
        return self._applets

    @property
    def imageNameListSlot(self):
        """
        Return the "image name list" slot, which lists the names of
        all image lanes (i.e. files) currently loaded by the workflow
        """
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):

        # Create a graph to be shared by all operators
        graph = Graph()
        super(NNClassificationWorkflow, self).__init__(shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs)
        self._applets = []
        self._workflow_cmdline_args = workflow_cmdline_args

        # Parse workflow-specific command-line args
        parser = argparse.ArgumentParser()
        parser.add_argument('--batch-size', help="choose the prefered batch size", type=int)
        parser.add_argument('--halo-size', help="choose the prefered halo size", type=int)
        parser.add_argument('--model-path', help="the neural network model for prediction")

        # Parse the creation args: These were saved to the project file when this project was first created.
        parsed_creation_args, unused_args = parser.parse_known_args(project_creation_args)

        # Parse the cmdline args for the current session.
        self.parsed_args, unused_args = parser.parse_known_args(workflow_cmdline_args)

        ######################
        # Interactive workflow
        ######################

        data_instructions = "Select your input data using the 'Raw Data' tab shown on the right.\n\n"\
                            "Power users: Optionally use the 'Prediction Mask' tab to supply a binary image that tells ilastik where it should avoid computations you don't need."

        # Applets for training (interactive) workflow
        self.dataSelectionApplet = self.createDataSelectionApplet()
        opDataSelection = self.dataSelectionApplet.topLevelOperator

        # see role constants, above
        opDataSelection.DatasetRoles.setValue(NNClassificationWorkflow.ROLE_NAMES)

        self.nnClassificationApplet = NNClassApplet(self, "NNClassApplet")

        self.dataExportApplet = NNClassificationDataExportApplet(self, 'Data Export')

        # Configure global DataExport settings
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.WorkingDirectory.connect(opDataSelection.WorkingDirectory)
        opDataExport.SelectionNames.setValue(self.EXPORT_NAMES)

        # self.dataExportApplet.prepare_for_entire_export = self.prepare_for_entire_export
        # self.dataExportApplet.post_process_entire_export = self.post_process_entire_export

        self.batchProcessingApplet = BatchProcessingApplet(self,
                                                           "Batch Processing",
                                                           self.dataSelectionApplet,
                                                           self.dataExportApplet)

        # Expose for shell
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.nnClassificationApplet)
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
            logger.warn("Unused command-line args: {}".format(unused_args))

    def createDataSelectionApplet(self):
        """
        Can be overridden by subclasses, if they want to use
        special parameters to initialize the DataSelectionApplet.
        """
        data_instructions = "Select your input data using the 'Raw Data' tab shown on the right"
        return DataSelectionApplet(self,
                                   "Input Data",
                                   "Input Data",
                                   supportIlastik05Import=True,
                                   instructionText=data_instructions)


    def connectLane(self, laneIndex):
        """
        connects the operators for different lanes, each lane has a laneIndex starting at 0
        """
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opNNclassify = self.nnClassificationApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)

        # Input Image -> Feature Op
        #         and -> Classification Op (for display)
        opNNclassify.InputImage.connect(opData.Image)

        #ReorderAxes is needed for specifying the original_shape meta tag , hack!
        op5Pred = OpReorderAxes(parent=self)
        op5Pred.AxisOrder.setValue("txyzc")
        op5Pred.Input.connect(opNNclassify.CachedPredictionProbabilities)

        # Data Export connections
        opDataExport.RawData.connect(opData.ImageGroup[self.DATA_ROLE_RAW] )
        opDataExport.RawDatasetInfo.connect(opData.DatasetGroup[self.DATA_ROLE_RAW])
        opDataExport.Inputs.resize(len(self.EXPORT_NAMES))
        opDataExport.Inputs[0].connect(op5Pred.Output)
        # for slot in opDataExport.Inputs:
        #     assert slot.upstream_slot is not None

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        # If no data, nothing else is ready.
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        input_ready = len(opDataSelection.ImageGroup) > 0 and not self.dataSelectionApplet.busy

        opNNClassification = self.nnClassificationApplet.topLevelOperator

        opDataExport = self.dataExportApplet.topLevelOperator

        predictions_ready = input_ready and \
                            len(opDataExport.Inputs) > 0
                            # opDataExport.Inputs[0][0].ready()
                            # (TinyVector(opDataExport.Inputs[0][0].meta.shape) > 0).all()

        # Problems can occur if the features or input data are changed during live update mode.
        # Don't let the user do that.
        live_update_active = not opNNClassification.FreezePredictions.value

        # The user isn't allowed to touch anything while batch processing is running.
        batch_processing_busy = self.batchProcessingApplet.busy

        self._shell.setAppletEnabled(self.dataSelectionApplet, not batch_processing_busy)
        self._shell.setAppletEnabled(self.nnClassificationApplet, input_ready and not batch_processing_busy)
        self._shell.setAppletEnabled(self.dataExportApplet, predictions_ready and not batch_processing_busy and not live_update_active)

        if self.batchProcessingApplet is not None:
            self._shell.setAppletEnabled(self.batchProcessingApplet, predictions_ready and not batch_processing_busy)

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
            self.dataExportApplet.configure_operator_with_parsed_args(self._batch_export_args)

            batch_size = self.parsed_args.batch_size
            halo_size = self.parsed_args.halo_size
            model_path = self.parsed_args.model_path

            if batch_size and model_path:

                model = TikTorchLazyflowClassifier(None, model_path,
                                                   halo_size, batch_size)

                input_shape = self.getBlockShape(model, halo_size)

                self.nnClassificationApplet.topLevelOperator.BlockShape.setValue(input_shape)
                self.nnClassificationApplet.topLevelOperator.NumClasses.setValue(model._tiktorch_net.get('num_output_channels'))

                self.nnClassificationApplet.topLevelOperator.Classifier.setValue(model)

            logger.info("Beginning Batch Processing")
            self.batchProcessingApplet.run_export_from_parsed_args(self._batch_input_args)
            logger.info("Completed Batch Processing")


    # def prepare_for_entire_export(self):
    #     """
    #     Assigned to DataExportApplet.prepare_for_entire_export
    #     (See above.)
    #     """
    #     print("prepare_for_entire_export")
    #     self.freeze_status = self.nnClassificationApplet.topLevelOperator.FreezePredictions.value
    #     self.nnClassificationApplet.topLevelOperator.FreezePredictions.setValue(False)


    # def post_process_entire_export(self):
    #     """
    #     Assigned to DataExportApplet.post_process_entire_export
    #     (See above.)
    #     """
    #     print("post_process_entire_export")
    #     self.nnClassificationApplet.topLevelOperator.FreezePredictions.setValue(self.freeze_status)


    def getBlockShape(self, model, halo_size):
        """
        calculates the input Block shape
        """
        expected_input_shape = model._tiktorch_net.expected_input_shape
        input_shape = numpy.array(expected_input_shape)

        if not halo_size:
            if 'output_size' in model._tiktorch_net._configuration:
                #if the ouputsize of the model is smaller as the expected input shape
                #the halo needs to be changed
                output_shape = model._tiktorch_net.get('output_size')
                if (output_shape != input_shape):
                    self.halo_size = int((input_shape[1] - output_shape[1])/2)
                    model.HALO_SIZE = self.halo_size
                    print(self.halo_size)


        if len(model._tiktorch_net.get('window_size')) == 2:
            input_shape = numpy.append(input_shape, None)
        else:

            input_shape = input_shape[1:]
            input_shape = numpy.append(input_shape, None)

        input_shape[1:3] -= 2 * self.halo_size

        return input_shape







