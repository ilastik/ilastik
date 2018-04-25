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
import sys
import argparse
import itertools
from lazyflow.graph import Graph, Operator, OperatorWrapper

from ilastik.workflow import Workflow

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
from ilastik.applets.counting import CountingApplet, CountingDataExportApplet
from ilastik.applets.counting.opCounting import OpPredictionPipeline
from ilastik.applets.batchProcessing import BatchProcessingApplet

from lazyflow.roi import TinyVector
from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators.generic import OpTransposeSlots, OpSelectSubslot

import logging
logger = logging.getLogger(__name__)

class CountingWorkflow(Workflow):
    workflowName = "Cell Density Counting"
    workflowDescription = "This is obviously self-explanatory."
    defaultAppletIndex = 0 # show DataSelection by default

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs: del kwargs['graph']
        super( CountingWorkflow, self ).__init__( shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs )
        self.stored_classifier = None

        # Parse workflow-specific command-line args
        parser = argparse.ArgumentParser()
        parser.add_argument("--csv-export-file", help="Instead of exporting prediction density images, export total counts to the given csv path.")
        self.parsed_counting_workflow_args, unused_args = parser.parse_known_args(workflow_cmdline_args)

        ######################
        # Interactive workflow
        ######################

        allowed_axis_orders = []
        for space in itertools.permutations('xyz', 2):
            allowed_axis_orders.append(''.join(space) + 'c')

        self.dataSelectionApplet = DataSelectionApplet(self,
                                                       "Input Data",
                                                       "Input Data",
                                                       forceAxisOrder=allowed_axis_orders)
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        role_names = ['Raw Data']
        opDataSelection.DatasetRoles.setValue( role_names )

        self.featureSelectionApplet = FeatureSelectionApplet(self,
                                                             "Feature Selection",
                                                             "FeatureSelections")

        self.countingApplet = CountingApplet(workflow=self)
        opCounting = self.countingApplet.topLevelOperator

        self.dataExportApplet = CountingDataExportApplet(self, "Density Export", opCounting)

        # Customization hooks
        self.dataExportApplet.prepare_for_entire_export = self.prepare_for_entire_export
        self.dataExportApplet.post_process_lane_export = self.post_process_lane_export
        self.dataExportApplet.post_process_entire_export = self.post_process_entire_export

        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.PmapColors.connect(opCounting.PmapColors)
        opDataExport.LabelNames.connect(opCounting.LabelNames)
        opDataExport.UpperBound.connect(opCounting.UpperBound)
        opDataExport.WorkingDirectory.connect(opDataSelection.WorkingDirectory)
        opDataExport.SelectionNames.setValue( ['Probabilities'] )

        self._applets = []
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.countingApplet)
        self._applets.append(self.dataExportApplet)

        self.batchProcessingApplet = BatchProcessingApplet( self,
                                                            "Batch Processing",
                                                            self.dataSelectionApplet,
                                                            self.dataExportApplet )
        self._applets.append(self.batchProcessingApplet)
        if unused_args:
            # We parse the export setting args first.  All remaining args are considered input files by the input applet.
            self._batch_export_args, unused_args = self.dataExportApplet.parse_known_cmdline_args( unused_args )
            self._batch_input_args, unused_args = self.batchProcessingApplet.parse_known_cmdline_args( unused_args )
        else:
            self._batch_input_args = None
            self._batch_export_args = None

        if unused_args:
            logger.warning("Unused command-line args: {}".format( unused_args ))


    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def prepareForNewLane(self, laneIndex):
        """
        Overridden from Workflow base class.
        Called immediately before a new lane is added to the workflow.
        """
        # When the new lane is added, dirty notifications will propagate throughout the entire graph.
        # This means the classifier will be marked 'dirty' even though it is still usable.
        # Before that happens, let's store the classifier, so we can restore it at the end of connectLane(), below.
        opCounting = self.countingApplet.topLevelOperator
        if opCounting.classifier_cache.Output.ready() and \
           not opCounting.classifier_cache._dirty:
            self.stored_classifier = opCounting.classifier_cache.Output.value
        else:
            self.stored_classifier = None

    def handleNewLanesAdded(self):
        """
        Overridden from Workflow base class.
        Called immediately after a new lane is added to the workflow and initialized.
        """
        # Restore classifier we saved in prepareForNewLane() (if any)
        if self.stored_classifier is not None:
            self.countingApplet.topLevelOperator.classifier_cache.forceValue(self.stored_classifier)
            # Release reference
            self.stored_classifier = None

    def connectLane(self, laneIndex):
        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)
        opCounting = self.countingApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)


        #### connect input image
        opTrainingFeatures.InputImage.connect(opData.Image)

        opCounting.InputImages.connect(opData.Image)
        opCounting.FeatureImages.connect(opTrainingFeatures.OutputImage)
        opCounting.CachedFeatureImages.connect( opTrainingFeatures.CachedOutputImage )
        #opCounting.UserLabels.connect(opClassify.LabelImages)
        #opCounting.ForegroundLabels.connect(opObjExtraction.LabelImage)
        opDataExport.Inputs.resize(1)
        opDataExport.Inputs[0].connect( opCounting.HeadlessPredictionProbabilities )
        opDataExport.RawData.connect( opData.ImageGroup[0] )
        opDataExport.RawDatasetInfo.connect( opData.DatasetGroup[0] )

    def onProjectLoaded(self, projectManager):
        """
        Overridden from Workflow base class.  Called by the Project Manager.

        If the user provided command-line arguments, use them to configure
        the workflow for batch mode and export all results.
        (This workflow's headless mode supports only batch mode for now.)
        """
        # Headless batch mode.
        if self._headless and self._batch_input_args and self._batch_export_args:
            self.dataExportApplet.configure_operator_with_parsed_args( self._batch_export_args )

            # If the user provided a csv_path via the command line,
            # overwrite the setting in the counting export operator.
            csv_path = self.parsed_counting_workflow_args.csv_export_file
            if csv_path:
                self.dataExportApplet.topLevelOperator.CsvFilepath.setValue(csv_path)

            if self.countingApplet.topLevelOperator.classifier_cache._dirty:
                logger.warning("Your project file has no classifier.  "
                            "A new classifier will be trained for this run.")

            logger.info("Beginning Batch Processing")
            self.batchProcessingApplet.run_export_from_parsed_args(self._batch_input_args)
            logger.info("Completed Batch Processing")

    def prepare_for_entire_export(self):
        """
        Customization hook for data export (including batch mode).
        """
        self.freeze_status = self.countingApplet.topLevelOperator.FreezePredictions.value
        self.countingApplet.topLevelOperator.FreezePredictions.setValue(False)
        # Create a new CSV file to write object counts into.
        self.csv_export_file = None
        if self.dataExportApplet.topLevelOperator.CsvFilepath.ready():
            csv_path = self.dataExportApplet.topLevelOperator.CsvFilepath.value
            logger.info("Exporting object counts to CSV: " + csv_path)
            self.csv_export_file = open(csv_path, 'w')

    def post_process_lane_export(self, lane_index):
        """
        Customization hook for data export (including batch mode).
        """
        # Write the object counts for this lane as a line in the CSV file.
        if self.csv_export_file:
            self.dataExportApplet.write_csv_results(self.csv_export_file, lane_index)

    def post_process_entire_export(self):
        """
        Customization hook for data export (including batch mode).
        """
        self.countingApplet.topLevelOperator.FreezePredictions.setValue(self.freeze_status)
        if self.csv_export_file:
            self.csv_export_file.close()

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.statusUpdateSignal`
        """
        # If no data, nothing else is ready.
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        input_ready = len(opDataSelection.ImageGroup) > 0 and not self.dataSelectionApplet.busy

        opFeatureSelection = self.featureSelectionApplet.topLevelOperator
        featureOutput = opFeatureSelection.OutputImage
        features_ready = input_ready and \
                         len(featureOutput) > 0 and  \
                         featureOutput[0].ready() and \
                         (TinyVector(featureOutput[0].meta.shape) > 0).all()

        opDataExport = self.dataExportApplet.topLevelOperator
        predictions_ready = features_ready and \
                            len(opDataExport.Inputs) > 0 and \
                            opDataExport.Inputs[0][0].ready() and \
                            (TinyVector(opDataExport.Inputs[0][0].meta.shape) > 0).all()

        self._shell.setAppletEnabled(self.featureSelectionApplet, input_ready)
        self._shell.setAppletEnabled(self.countingApplet, features_ready)
        self._shell.setAppletEnabled(self.dataExportApplet, predictions_ready and not self.dataExportApplet.busy)
        self._shell.setAppletEnabled(self.batchProcessingApplet, predictions_ready and not self.batchProcessingApplet.busy)

        # Lastly, check for certain "busy" conditions, during which we
        #  should prevent the shell from closing the project.
        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= self.featureSelectionApplet.busy
        busy |= self.dataExportApplet.busy
        busy |= self.batchProcessingApplet.busy
        self._shell.enableProjectChanges( not busy )
