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
import copy
import argparse
import logging
logger = logging.getLogger(__name__)

import numpy

from ilastik.config import cfg as ilastik_config

from ilastik.workflow import Workflow

from ilastik.applets.pixelClassification import PixelClassificationApplet, PixelClassificationDataExportApplet
from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet

from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelectionNoCache
from ilastik.applets.pixelClassification.opPixelClassification import OpPredictionPipelineNoCache

from lazyflow.roi import TinyVector, fullSlicing
from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators.generic import OpTransposeSlots, OpSelectSubslot

class PixelClassificationWorkflow(Workflow):
    
    workflowName = "Pixel Classification"
    workflowDescription = "This is obviously self-explanatory."
    defaultAppletIndex = 1 # show DataSelection by default
    
    DATA_ROLE_RAW = 0
    DATA_ROLE_PREDICTION_MASK = 1
    
    EXPORT_NAMES = ['Probabilities', 'Simple Segmentation', 'Uncertainty', 'Features']
    
    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, appendBatchOperators=True, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()
        super( PixelClassificationWorkflow, self ).__init__( shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs )
        self._applets = []
        self._workflow_cmdline_args = workflow_cmdline_args

        data_instructions = "Select your input data using the 'Raw Data' tab shown on the right"

        # Parse workflow-specific command-line args
        parser = argparse.ArgumentParser()
        parser.add_argument('--filter', help="pixel feature filter implementation.", choices=['Original', 'Refactored', 'Interpolated'], default='Original')
        parser.add_argument('--print-labels-by-slice', help="Print the number of labels for each Z-slice of each image.", action="store_true")
        parser.add_argument('--label-search-value', help="If provided, only this value is considered when using --print-labels-by-slice", default=0, type=int)
        parser.add_argument('--generate-random-labels', help="Add random labels to the project file.", action="store_true")
        parser.add_argument('--random-label-value', help="The label value to use injecting random labels", default=1, type=int)
        parser.add_argument('--random-label-count', help="The number of random labels to inject via --generate-random-labels", default=2000, type=int)
        parser.add_argument('--retrain', help="Re-train the classifier based on labels stored in project file, and re-save.", action="store_true")

        # Parse the creation args: These were saved to the project file when this project was first created.
        parsed_creation_args, unused_args = parser.parse_known_args(project_creation_args)
        self.filter_implementation = parsed_creation_args.filter
        
        # Parse the cmdline args for the current session.
        parsed_args, unused_args = parser.parse_known_args(workflow_cmdline_args)
        self.print_labels_by_slice = parsed_args.print_labels_by_slice
        self.label_search_value = parsed_args.label_search_value
        self.generate_random_labels = parsed_args.generate_random_labels
        self.random_label_value = parsed_args.random_label_value
        self.random_label_count = parsed_args.random_label_count
        self.retrain = parsed_args.retrain

        if parsed_args.filter and parsed_args.filter != parsed_creation_args.filter:
            logger.error("Ignoring new --filter setting.  Filter implementation cannot be changed after initial project creation.")
        
        # Applets for training (interactive) workflow 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet( self,
                                                        "Input Data",
                                                        "Input Data",
                                                        supportIlastik05Import=True,
                                                        batchDataGui=False,
                                                        instructionText=data_instructions )
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        
        if ilastik_config.getboolean('ilastik', 'debug'):
            # see role constants, above
            role_names = ['Raw Data', 'Prediction Mask']
            opDataSelection.DatasetRoles.setValue( role_names )
        else:
            role_names = ['Raw Data']
            opDataSelection.DatasetRoles.setValue( role_names )

        self.featureSelectionApplet = FeatureSelectionApplet(self, "Feature Selection", "FeatureSelections", self.filter_implementation)

        self.pcApplet = PixelClassificationApplet( self, "PixelClassification" )
        opClassify = self.pcApplet.topLevelOperator

        self.dataExportApplet = PixelClassificationDataExportApplet(self, "Prediction Export")
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.PmapColors.connect( opClassify.PmapColors )
        opDataExport.LabelNames.connect( opClassify.LabelNames )
        opDataExport.WorkingDirectory.connect( opDataSelection.WorkingDirectory )
        opDataExport.SelectionNames.setValue( self.EXPORT_NAMES )        

        # Expose for shell
        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.pcApplet)
        self._applets.append(self.dataExportApplet)

        self._batch_input_args = None
        self._batch_export_args = None

        self.batchInputApplet = None
        self.batchResultsApplet = None
        if appendBatchOperators:
            # Create applets for batch workflow
            self.batchInputApplet = DataSelectionApplet(self, "Batch Prediction Input Selections", "Batch Inputs", supportIlastik05Import=False, batchDataGui=True)
            self.batchResultsApplet = PixelClassificationDataExportApplet(self, "Batch Prediction Output Locations", isBatch=True)
    
            # Expose in shell        
            self._applets.append(self.batchInputApplet)
            self._applets.append(self.batchResultsApplet)
    
            # Connect batch workflow (NOT lane-based)
            self._initBatchWorkflow()

            if unused_args:
                # We parse the export setting args first.  All remaining args are considered input files by the input applet.
                self._batch_export_args, unused_args = self.batchResultsApplet.parse_known_cmdline_args( unused_args )
                self._batch_input_args, unused_args = self.batchInputApplet.parse_known_cmdline_args( unused_args )
    
        if unused_args:
            logger.warn("Unused command-line args: {}".format( unused_args ))

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
        
        # Training flags -> Classification Op (for GUI restrictions)
        opClassify.LabelsAllowedFlags.connect( opData.AllowLabels )

        # Data Export connections
        opDataExport.RawData.connect( opData.ImageGroup[self.DATA_ROLE_RAW] )
        opDataExport.RawDatasetInfo.connect( opData.DatasetGroup[self.DATA_ROLE_RAW] )
        opDataExport.ConstraintDataset.connect( opData.ImageGroup[self.DATA_ROLE_RAW] )
        opDataExport.Inputs.resize( len(self.EXPORT_NAMES) )
        opDataExport.Inputs[0].connect( opClassify.HeadlessPredictionProbabilities )
        opDataExport.Inputs[1].connect( opClassify.SimpleSegmentation )
        opDataExport.Inputs[2].connect( opClassify.HeadlessUncertaintyEstimate )
        opDataExport.Inputs[3].connect( opClassify.FeatureImages )
        for slot in opDataExport.Inputs:
            assert slot.partner is not None

    def _initBatchWorkflow(self):
        """
        Connect the batch-mode top-level operators to the training workflow and to each other.
        """
        # Access applet operators from the training workflow
        opTrainingDataSelection = self.dataSelectionApplet.topLevelOperator
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator
        opClassify = self.pcApplet.topLevelOperator
        
        # Access the batch operators
        opBatchInputs = self.batchInputApplet.topLevelOperator
        opBatchResults = self.batchResultsApplet.topLevelOperator
        
        opBatchInputs.DatasetRoles.connect( opTrainingDataSelection.DatasetRoles )
        
        opSelectFirstLane = OperatorWrapper( OpSelectSubslot, parent=self )
        opSelectFirstLane.Inputs.connect( opTrainingDataSelection.ImageGroup )
        opSelectFirstLane.SubslotIndex.setValue(0)
        
        opSelectFirstRole = OpSelectSubslot( parent=self )
        opSelectFirstRole.Inputs.connect( opSelectFirstLane.Output )
        opSelectFirstRole.SubslotIndex.setValue(self.DATA_ROLE_RAW)
        
        opBatchResults.ConstraintDataset.connect( opSelectFirstRole.Output )
        
        ## Create additional batch workflow operators
        opBatchFeatures = OperatorWrapper( OpFeatureSelectionNoCache, operator_kwargs={'filter_implementation': self.filter_implementation}, parent=self, promotedSlotNames=['InputImage'] )
        opBatchPredictionPipeline = OperatorWrapper( OpPredictionPipelineNoCache, parent=self )
        
        ## Connect Operators ##
        opTranspose = OpTransposeSlots( parent=self )
        opTranspose.OutputLength.setValue(2) # There are 2 roles
        opTranspose.Inputs.connect( opBatchInputs.DatasetGroup )
        opTranspose.name = "batchTransposeInputs"
        
        # Provide dataset paths from data selection applet to the batch export applet
        opBatchResults.RawDatasetInfo.connect( opTranspose.Outputs[self.DATA_ROLE_RAW] )
        opBatchResults.WorkingDirectory.connect( opBatchInputs.WorkingDirectory )
        
        # Connect (clone) the feature operator inputs from 
        #  the interactive workflow's features operator (which gets them from the GUI)
        opBatchFeatures.Scales.connect( opTrainingFeatures.Scales )
        opBatchFeatures.FeatureIds.connect( opTrainingFeatures.FeatureIds )
        opBatchFeatures.SelectionMatrix.connect( opTrainingFeatures.SelectionMatrix )
        
        # Classifier and NumClasses are provided by the interactive workflow
        opBatchPredictionPipeline.Classifier.connect( opClassify.Classifier )
        opBatchPredictionPipeline.NumClasses.connect( opClassify.NumClasses )
        
        # Provide these for the gui
        opBatchResults.RawData.connect( opBatchInputs.Image )
        opBatchResults.PmapColors.connect( opClassify.PmapColors )
        opBatchResults.LabelNames.connect( opClassify.LabelNames )
        
        # Connect Image pathway:
        # Input Image -> Features Op -> Prediction Op -> Export
        opBatchFeatures.InputImage.connect( opBatchInputs.Image )
        opBatchPredictionPipeline.PredictionMask.connect( opBatchInputs.Image1 )
        opBatchPredictionPipeline.FeatureImages.connect( opBatchFeatures.OutputImage )

        opBatchResults.SelectionNames.setValue( self.EXPORT_NAMES )        
        # opBatchResults.Inputs is indexed by [lane][selection],
        # Use OpTranspose to allow connection.
        opTransposeBatchInputs = OpTransposeSlots( parent=self )
        opTransposeBatchInputs.name = "opTransposeBatchInputs"
        opTransposeBatchInputs.OutputLength.setValue(0)
        opTransposeBatchInputs.Inputs.resize( len(self.EXPORT_NAMES) )
        opTransposeBatchInputs.Inputs[0].connect( opBatchPredictionPipeline.HeadlessPredictionProbabilities ) # selection 0
        opTransposeBatchInputs.Inputs[1].connect( opBatchPredictionPipeline.SimpleSegmentation ) # selection 1
        opTransposeBatchInputs.Inputs[2].connect( opBatchPredictionPipeline.HeadlessUncertaintyEstimate ) # selection 2
        opTransposeBatchInputs.Inputs[3].connect( opBatchPredictionPipeline.FeatureImages ) # selection 3
        for slot in opTransposeBatchInputs.Inputs:
            assert slot.partner is not None
        
        # Now opTransposeBatchInputs.Outputs is level-2 indexed by [lane][selection]
        opBatchResults.Inputs.connect( opTransposeBatchInputs.Outputs )

        # We don't actually need the cached path in the batch pipeline.
        # Just connect the uncached features here to satisfy the operator.
        #opBatchPredictionPipeline.CachedFeatureImages.connect( opBatchFeatures.OutputImage )

        self.opBatchFeatures = opBatchFeatures
        self.opBatchPredictionPipeline = opBatchPredictionPipeline

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
        
        self._shell.setAppletEnabled(self.dataSelectionApplet, not live_update_active)
        self._shell.setAppletEnabled(self.featureSelectionApplet, input_ready and not live_update_active)
        self._shell.setAppletEnabled(self.pcApplet, features_ready)
        self._shell.setAppletEnabled(self.dataExportApplet, predictions_ready)

        if self.batchInputApplet is not None:
            # Training workflow must be fully configured before batch can be used
            self._shell.setAppletEnabled(self.batchInputApplet, predictions_ready)
    
            opBatchDataSelection = self.batchInputApplet.topLevelOperator
            batch_input_ready = predictions_ready and \
                                len(opBatchDataSelection.ImageGroup) > 0
            self._shell.setAppletEnabled(self.batchResultsApplet, batch_input_ready)
            
        # Lastly, check for certain "busy" conditions, during which we 
        #  should prevent the shell from closing the project.
        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= self.featureSelectionApplet.busy
        busy |= self.dataExportApplet.busy
        self._shell.enableProjectChanges( not busy )

    def getHeadlessOutputSlot(self, slotId):
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

        # Configure the batch data selection operator.
        if self._batch_input_args and (self._batch_input_args.input_files or self._batch_input_args.raw_data):
            self.batchInputApplet.configure_operator_with_parsed_args( self._batch_input_args )
        
        # Configure the data export operator.
        if self._batch_export_args:
            self.batchResultsApplet.configure_operator_with_parsed_args( self._batch_export_args )

        if self._batch_input_args and self.pcApplet.topLevelOperator.classifier_cache._dirty:
            logger.warn("Your project file has no classifier.  A new classifier will be trained for this run.")

        # Let's see the messages from the training operator.
        logging.getLogger("lazyflow.operators.classifierOperators").setLevel(logging.DEBUG)
        
        if self.retrain:
            # Cause the classifier to be dirty so it is forced to retrain.
            # (useful if the stored labels were changed outside ilastik)
            self.pcApplet.topLevelOperator.opTrain.ClassifierFactory.setDirty()
            
            # Request the classifier, which forces training
            self.pcApplet.topLevelOperator.FreezePredictions.setValue(False)
            _ = self.pcApplet.topLevelOperator.Classifier.value

            # store new classifier to project file
            projectManager.saveProject(force_all_save=False)

        if self._headless and self._batch_input_args and self._batch_export_args:
            # Make sure we're using the up-to-date classifier.
            self.pcApplet.topLevelOperator.FreezePredictions.setValue(False)
        
            # Now run the batch export and report progress....
            opBatchDataExport = self.batchResultsApplet.topLevelOperator
            for i, opExportDataLaneView in enumerate(opBatchDataExport):
                logger.info( "Exporting result {} to {}".format(i, opExportDataLaneView.ExportPath.value) )
    
                sys.stdout.write( "Result {}/{} Progress: ".format( i, len( opBatchDataExport ) ) )
                sys.stdout.flush()
                def print_progress( progress ):
                    sys.stdout.write( "{} ".format( progress ) )
                    sys.stdout.flush()
    
                # If the operator provides a progress signal, use it.
                slotProgressSignal = opExportDataLaneView.progressSignal
                slotProgressSignal.subscribe( print_progress )
                opExportDataLaneView.run_export()
                
                # Finished.
                sys.stdout.write("\n")


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
                    slicing[tagged_shape.keys().index('z')] = slice(z, z+1)
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
                progress = float(sample_index) / labels_per_image
                progress = 10 * (int(100*progress)/10)
                if progress != current_progress:
                    current_progress = progress
                    sys.stdout.write( "{}% ".format( current_progress ) )
                    sys.stdout.flush()

            sys.stdout.write( "100%\n" )
            # Write into the operator
            label_input_slot[fullSlicing(shape)] = random_labels
        
        logger.info( "Done injecting labels" )

