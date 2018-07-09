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
from builtins import range
import sys
import copy
import argparse
import itertools
import logging
logger = logging.getLogger(__name__)

import numpy

from ilastik.config import cfg as ilastik_config
from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.pixelClassification import PixelClassificationApplet, PixelClassificationDataExportApplet
from ilastik.applets.batchProcessing import BatchProcessingApplet

from lazyflow.graph import Graph
from lazyflow.roi import TinyVector, fullSlicing

class PixelClassificationWorkflow(Workflow):

    workflowName = "Pixel Classification"
    workflowDescription = "This is obviously self-explanatory."
    defaultAppletIndex = 0 # show DataSelection by default

    DATA_ROLE_RAW = 0
    DATA_ROLE_PREDICTION_MASK = 1
    ROLE_NAMES = ['Raw Data', 'Prediction Mask']
    EXPORT_NAMES = ['Probabilities', 'Simple Segmentation', 'Uncertainty', 'Features', 'Labels']

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()
        super( PixelClassificationWorkflow, self ).__init__( shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs )
        self.stored_classifier = None
        self._applets = []
        self._workflow_cmdline_args = workflow_cmdline_args
        # Parse workflow-specific command-line args
        parser = argparse.ArgumentParser()
        parser.add_argument('--print-labels-by-slice', help="Print the number of labels for each Z-slice of each image.", action="store_true")
        parser.add_argument('--label-search-value', help="If provided, only this value is considered when using --print-labels-by-slice", default=0, type=int)
        parser.add_argument('--generate-random-labels', help="Add random labels to the project file.", action="store_true")
        parser.add_argument('--random-label-value', help="The label value to use injecting random labels", default=1, type=int)
        parser.add_argument('--random-label-count', help="The number of random labels to inject via --generate-random-labels", default=2000, type=int)
        parser.add_argument('--retrain', help="Re-train the classifier based on labels stored in project file, and re-save.", action="store_true")
        parser.add_argument('--tree-count', help='Number of trees for Vigra RF classifier.', type=int)
        parser.add_argument('--variable-importance-path', help='Location of variable-importance table.', type=str)
        parser.add_argument('--label-proportion', help='Proportion of feature-pixels used to train the classifier.', type=float)

        # Parse the creation args: These were saved to the project file when this project was first created.
        parsed_creation_args, unused_args = parser.parse_known_args(project_creation_args)

        # Parse the cmdline args for the current session.
        parsed_args, unused_args = parser.parse_known_args(workflow_cmdline_args)
        self.print_labels_by_slice = parsed_args.print_labels_by_slice
        self.label_search_value = parsed_args.label_search_value
        self.generate_random_labels = parsed_args.generate_random_labels
        self.random_label_value = parsed_args.random_label_value
        self.random_label_count = parsed_args.random_label_count
        self.retrain = parsed_args.retrain
        self.tree_count = parsed_args.tree_count
        self.variable_importance_path = parsed_args.variable_importance_path
        self.label_proportion = parsed_args.label_proportion

        data_instructions = "Select your input data using the 'Raw Data' tab shown on the right.\n\n"\
                            "Power users: Optionally use the 'Prediction Mask' tab to supply a binary image that tells ilastik where it should avoid computations you don't need."

        # Applets for training (interactive) workflow
        self.dataSelectionApplet = self.createDataSelectionApplet()
        opDataSelection = self.dataSelectionApplet.topLevelOperator

        # see role constants, above
        opDataSelection.DatasetRoles.setValue( PixelClassificationWorkflow.ROLE_NAMES )

        self.featureSelectionApplet = self.createFeatureSelectionApplet()

        self.pcApplet = self.createPixelClassificationApplet()
        opClassify = self.pcApplet.topLevelOperator

        self.dataExportApplet = PixelClassificationDataExportApplet(self, "Prediction Export")
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.PmapColors.connect( opClassify.PmapColors )
        opDataExport.LabelNames.connect( opClassify.LabelNames )
        opDataExport.WorkingDirectory.connect( opDataSelection.WorkingDirectory )
        opDataExport.SelectionNames.setValue( self.EXPORT_NAMES )

        # Expose for shell
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.pcApplet)
        self._applets.append(self.dataExportApplet)

        self.dataExportApplet.prepare_for_entire_export = self.prepare_for_entire_export
        self.dataExportApplet.post_process_entire_export = self.post_process_entire_export

        self.batchProcessingApplet = BatchProcessingApplet(self,
                                                           "Batch Processing",
                                                           self.dataSelectionApplet,
                                                           self.dataExportApplet)

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

    def createDataSelectionApplet(self):
        """
        Can be overridden by subclasses, if they want to use
        special parameters to initialize the DataSelectionApplet.
        """
        data_instructions = "Select your input data using the 'Raw Data' tab shown on the right"
        c_at_end = ['yxc', 'xyc']
        for perm in itertools.permutations('tzyx', 3):
            c_at_end.append(''.join(perm) + 'c')
        for perm in itertools.permutations('tzyx', 4):
            c_at_end.append(''.join(perm) + 'c')

        return DataSelectionApplet(self,
                                   "Input Data",
                                   "Input Data",
                                   supportIlastik05Import=True,
                                   instructionText=data_instructions,
                                   forceAxisOrder=c_at_end)

    def createFeatureSelectionApplet(self):
        """
        Can be overridden by subclasses, if they want to return their own type of FeatureSelectionApplet.
        NOTE: The applet returned here must have the same interface as the regular FeatureSelectionApplet.
              (If it looks like a duck...)
        """
        return FeatureSelectionApplet(self, "Feature Selection", "FeatureSelections")

    def createPixelClassificationApplet(self):
        """
        Can be overridden by subclasses, if they want to return their own type of PixelClassificationApplet.
        NOTE: The applet returned here must have the same interface as the regular PixelClassificationApplet.
              (If it looks like a duck...)
        """
        return PixelClassificationApplet( self, "PixelClassification" )

    def prepareForNewLane(self, laneIndex):
        """
        Overridden from Workflow base class.
        Called immediately before a new lane is added to the workflow.
        """
        # When the new lane is added, dirty notifications will propagate throughout the entire graph.
        # This means the classifier will be marked 'dirty' even though it is still usable.
        # Before that happens, let's store the classifier, so we can restore it in handleNewLanesAdded(), below.
        opPixelClassification = self.pcApplet.topLevelOperator
        if opPixelClassification.classifier_cache.Output.ready() and \
           not opPixelClassification.classifier_cache._dirty:
            self.stored_classifier = opPixelClassification.classifier_cache.Output.value
        else:
            self.stored_classifier = None

    def handleNewLanesAdded(self):
        """
        Overridden from Workflow base class.
        Called immediately after a new lane is added to the workflow and initialized.
        """
        # Restore classifier we saved in prepareForNewLane() (if any)
        if self.stored_classifier:
            self.pcApplet.topLevelOperator.classifier_cache.forceValue(self.stored_classifier)
            # Release reference
            self.stored_classifier = None

    def connectLane(self, laneIndex):
        # Get a handle to each operator
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)
        opClassify = self.pcApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)

        # Input Image -> Feature Op
        #         and -> Classification Op (for display)
        opTrainingFeatures.InputImage.connect( opData.Image )
        opClassify.InputImages.connect( opData.Image )

        if ilastik_config.getboolean('ilastik', 'debug'):
            opClassify.PredictionMasks.connect( opData.ImageGroup[self.DATA_ROLE_PREDICTION_MASK] )

        # Feature Images -> Classification Op (for training, prediction)
        opClassify.FeatureImages.connect( opTrainingFeatures.OutputImage )
        opClassify.CachedFeatureImages.connect( opTrainingFeatures.CachedOutputImage )

        # Data Export connections
        opDataExport.RawData.connect( opData.ImageGroup[self.DATA_ROLE_RAW] )
        opDataExport.RawDatasetInfo.connect( opData.DatasetGroup[self.DATA_ROLE_RAW] )
        opDataExport.ConstraintDataset.connect( opData.ImageGroup[self.DATA_ROLE_RAW] )
        opDataExport.Inputs.resize( len(self.EXPORT_NAMES) )
        opDataExport.Inputs[0].connect( opClassify.HeadlessPredictionProbabilities )
        opDataExport.Inputs[1].connect( opClassify.SimpleSegmentation )
        opDataExport.Inputs[2].connect( opClassify.HeadlessUncertaintyEstimate )
        opDataExport.Inputs[3].connect( opClassify.FeatureImages )
        opDataExport.Inputs[4].connect( opClassify.LabelImages )
        for slot in opDataExport.Inputs:
            assert slot.upstream_slot is not None

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
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
        opPixelClassification = self.pcApplet.topLevelOperator

        invalid_classifier = opPixelClassification.classifier_cache.fixAtCurrent.value and \
                             opPixelClassification.classifier_cache.Output.ready() and\
                             opPixelClassification.classifier_cache.Output.value is None

        predictions_ready = features_ready and \
                            not invalid_classifier and \
                            len(opDataExport.Inputs) > 0 and \
                            opDataExport.Inputs[0][0].ready() and \
                            (TinyVector(opDataExport.Inputs[0][0].meta.shape) > 0).all()

        # Problems can occur if the features or input data are changed during live update mode.
        # Don't let the user do that.
        live_update_active = not opPixelClassification.FreezePredictions.value

        # The user isn't allowed to touch anything while batch processing is running.
        batch_processing_busy = self.batchProcessingApplet.busy

        self._shell.setAppletEnabled(self.dataSelectionApplet, not live_update_active and not batch_processing_busy)
        self._shell.setAppletEnabled(self.featureSelectionApplet, input_ready and not live_update_active and not batch_processing_busy)
        self._shell.setAppletEnabled(self.pcApplet, features_ready and not batch_processing_busy)
        self._shell.setAppletEnabled(self.dataExportApplet, predictions_ready and not batch_processing_busy)

        if self.batchProcessingApplet is not None:
            self._shell.setAppletEnabled(self.batchProcessingApplet, predictions_ready and not batch_processing_busy)

        # Lastly, check for certain "busy" conditions, during which we
        #  should prevent the shell from closing the project.
        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= self.featureSelectionApplet.busy
        busy |= self.dataExportApplet.busy
        busy |= self.batchProcessingApplet.busy
        self._shell.enableProjectChanges( not busy )

    def onProjectLoaded(self, projectManager):
        """
        Overridden from Workflow base class.  Called by the Project Manager.

        If the user provided command-line arguments, use them to configure
        the workflow for batch mode and export all results.
        (This workflow's headless mode supports only batch mode for now.)
        """
        if self.generate_random_labels:
            self._generate_random_labels(self.random_label_count, self.random_label_value)
            logger.info("Saving project...")
            self._shell.projectManager.saveProject()
            logger.info("Done.")

        if self.print_labels_by_slice:
            self._print_labels_by_slice( self.label_search_value )

        if self._headless:
            # In headless mode, let's see the messages from the training operator.
            logging.getLogger("lazyflow.operators.classifierOperators").setLevel(logging.DEBUG)

        if self.variable_importance_path:
            classifier_factory = self.pcApplet.topLevelOperator.opTrain.ClassifierFactory.value
            classifier_factory.set_variable_importance_path( self.variable_importance_path )

        if self.tree_count:
            classifier_factory = self.pcApplet.topLevelOperator.opTrain.ClassifierFactory.value
            classifier_factory.set_num_trees( self.tree_count )

        if self.label_proportion:
            classifier_factory = self.pcApplet.topLevelOperator.opTrain.ClassifierFactory.value
            classifier_factory.set_label_proportion( self.label_proportion )

        if self.tree_count or self.label_proportion:
            self.pcApplet.topLevelOperator.ClassifierFactory.setDirty()

        if self.retrain:
            self._force_retrain_classifier(projectManager)

        # Configure the data export operator.
        if self._batch_export_args:
            self.dataExportApplet.configure_operator_with_parsed_args( self._batch_export_args )

        if self._batch_input_args and self.pcApplet.topLevelOperator.classifier_cache._dirty:
            logger.warning("Your project file has no classifier.  A new classifier will be trained for this run.")

        if self._headless and self._batch_input_args and self._batch_export_args:
            logger.info("Beginning Batch Processing")
            self.batchProcessingApplet.run_export_from_parsed_args(self._batch_input_args)
            logger.info("Completed Batch Processing")

    def prepare_for_entire_export(self):
        """
        Assigned to DataExportApplet.prepare_for_entire_export
        (See above.)
        """
        self.freeze_status = self.pcApplet.topLevelOperator.FreezePredictions.value
        self.pcApplet.topLevelOperator.FreezePredictions.setValue(False)

    def post_process_entire_export(self):
        """
        Assigned to DataExportApplet.post_process_entire_export
        (See above.)
        """
        self.pcApplet.topLevelOperator.FreezePredictions.setValue(self.freeze_status)

    def _force_retrain_classifier(self, projectManager):
        # Cause the classifier to be dirty so it is forced to retrain.
        # (useful if the stored labels were changed outside ilastik)
        self.pcApplet.topLevelOperator.opTrain.ClassifierFactory.setDirty()

        # Request the classifier, which forces training
        self.pcApplet.topLevelOperator.FreezePredictions.setValue(False)
        _ = self.pcApplet.topLevelOperator.Classifier.value

        # store new classifier to project file
        projectManager.saveProject(force_all_save=False)

    def _print_labels_by_slice(self, search_value):
        """
        Iterate over each label image in the project and print the number of labels present on each Z-slice of the image.
        (This is a special feature requested by the FlyEM proofreaders.)
        """
        opTopLevelClassify = self.pcApplet.topLevelOperator
        project_label_count = 0
        for image_index, label_slot in enumerate(opTopLevelClassify.LabelImages):
            tagged_shape = label_slot.meta.getTaggedShape()
            if 'z' not in tagged_shape:
                logger.error("Can't print label counts by Z-slices.  Image #{} has no Z-dimension.".format(image_index))
            else:
                logger.info("Label counts in Z-slices of Image #{}:".format( image_index ))
                slicing = [slice(None)] * len(tagged_shape)
                blank_slices = []
                image_label_count = 0
                for z in range(tagged_shape['z']):
                    slicing[list(tagged_shape.keys()).index('z')] = slice(z, z+1)
                    label_slice = label_slot[slicing].wait()
                    if search_value:
                        count = (label_slice == search_value).sum()
                    else:
                        count = (label_slice != 0).sum()
                    if count > 0:
                        logger.info("Z={}: {}".format( z, count ))
                        image_label_count += count
                    else:
                        blank_slices.append( z )
                project_label_count += image_label_count
                if len(blank_slices) > 20:
                    # Don't list the blank slices if there were a lot of them.
                    logger.info("Image #{} has {} blank slices.".format( image_index, len(blank_slices) ))
                elif len(blank_slices) > 0:
                    logger.info( "Image #{} has {} blank slices: {}".format( image_index, len(blank_slices), blank_slices ) )
                else:
                    logger.info( "Image #{} has no blank slices.".format( image_index ) )
                logger.info( "Total labels for Image #{}: {}".format( image_index, image_label_count ) )
        logger.info( "Total labels for project: {}".format( project_label_count ) )


    def _generate_random_labels(self, labels_per_image, label_value):
        """
        Inject random labels into the project file.
        (This is a special feature requested by the FlyEM proofreaders.)
        """
        logger.info( "Injecting {} labels of value {} into all images.".format( labels_per_image, label_value ) )
        opTopLevelClassify = self.pcApplet.topLevelOperator

        label_names = copy.copy(opTopLevelClassify.LabelNames.value)
        while len(label_names) < label_value:
            label_names.append( "Label {}".format( len(label_names)+1 ) )

        opTopLevelClassify.LabelNames.setValue( label_names )

        for image_index in range(len(opTopLevelClassify.LabelImages)):
            logger.info( "Injecting labels into image #{}".format( image_index ) )
            # For reproducibility of label generation
            SEED = 1
            numpy.random.seed([SEED, image_index])

            label_input_slot = opTopLevelClassify.LabelInputs[image_index]
            label_output_slot = opTopLevelClassify.LabelImages[image_index]

            shape = label_output_slot.meta.shape
            random_labels = numpy.zeros( shape=shape, dtype=numpy.uint8 )
            num_pixels = len(random_labels.flat)
            current_progress = -1
            for sample_index in range(labels_per_image):
                flat_index = numpy.random.randint(0,num_pixels)
                # Don't overwrite existing labels
                # Keep looking until we find a blank pixel
                while random_labels.flat[flat_index]:
                    flat_index = numpy.random.randint(0,num_pixels)
                random_labels.flat[flat_index] = label_value

                # Print progress every 10%
                progress = float(sample_index) // labels_per_image
                progress = 10 * (int(100*progress)//10)
                if progress != current_progress:
                    current_progress = progress
                    sys.stdout.write( "{}% ".format( current_progress ) )
                    sys.stdout.flush()

            sys.stdout.write( "100%\n" )
            # Write into the operator
            label_input_slot[fullSlicing(shape)] = random_labels

        logger.info( "Done injecting labels" )


    def getHeadlessOutputSlot(self, slotId):
        """
        Not used by the regular app.
        Only used for special cluster scripts.
        """
        # "Regular" (i.e. with the images that the user selected as input data)
        if slotId == "Predictions":
            return self.pcApplet.topLevelOperator.HeadlessPredictionProbabilities
        elif slotId == "PredictionsUint8":
            return self.pcApplet.topLevelOperator.HeadlessUint8PredictionProbabilities
        # "Batch" (i.e. with the images that the user selected as batch inputs).
        elif slotId == "BatchPredictions":
            return self.opBatchPredictionPipeline.HeadlessPredictionProbabilities
        if slotId == "BatchPredictionsUint8":
            return self.opBatchPredictionPipeline.HeadlessUint8PredictionProbabilities

        raise Exception("Unknown headless output slot")


