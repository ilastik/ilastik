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
#           http://ilastik.org/license.html
###############################################################################
from builtins import range
import sys
import copy
import argparse
import warnings
import itertools
import collections
from functools import partial
import logging
from ilastik.applets.pixelClassification.opPixelClassification import OpPixelClassification
logger = logging.getLogger(__name__)

import numpy as np

from ilastik.config import cfg as ilastik_config
from ilastik.workflow import Workflow
from ilastik.applets.base.applet import DatasetConstraintError
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.pixelClassification import PixelClassificationApplet, PixelClassificationDataExportApplet
from ilastik.applets.batchProcessing import BatchProcessingApplet

from lazyflow.graph import Graph
from lazyflow.roi import TinyVector, sliceToRoi, roiToSlice
from lazyflow.operators.generic import OpMultiArrayStacker
from lazyflow.operators.valueProviders import OpMetadataInjector

class NewAutocontextWorkflowBase(Workflow):
    
    workflowName = "New Autocontext Base"
    defaultAppletIndex = 0 # show DataSelection by default
    
    DATA_ROLE_RAW = 0
    DATA_ROLE_PREDICTION_MASK = 1
    
    # First export names must match these for the export GUI, because we re-use the ordinary PC gui
    # (See PixelClassificationDataExportGui.)
    EXPORT_NAMES_PER_STAGE = ['Probabilities', 'Simple Segmentation', 'Uncertainty', 'Features', 'Labels', 'Input']
    
    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, n_stages, *args, **kwargs):
        """
        n_stages: How many iterations of feature selection and pixel classification should be inserted into the workflow.
        
        All other params are just as in PixelClassificationWorkflow
        """
        # Create a graph to be shared by all operators
        graph = Graph()
        super( NewAutocontextWorkflowBase, self ).__init__( shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs )
        self.stored_classifers = []
        self._applets = []
        self._workflow_cmdline_args = workflow_cmdline_args

        # Parse workflow-specific command-line args
        parser = argparse.ArgumentParser()
        parser.add_argument('--retrain', help="Re-train the classifier based on labels stored in project file, and re-save.", action="store_true")

        # Parse the creation args: These were saved to the project file when this project was first created.
        parsed_creation_args, unused_args = parser.parse_known_args(project_creation_args)
        
        # Parse the cmdline args for the current session.
        parsed_args, unused_args = parser.parse_known_args(workflow_cmdline_args)
        self.retrain = parsed_args.retrain
        
        data_instructions = "Select your input data using the 'Raw Data' tab shown on the right.\n\n"\
                            "Power users: Optionally use the 'Prediction Mask' tab to supply a binary image that tells ilastik where it should avoid computations you don't need."

        self.dataSelectionApplet = self.createDataSelectionApplet()
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        
        # see role constants, above
        role_names = ['Raw Data', 'Prediction Mask']
        opDataSelection.DatasetRoles.setValue( role_names )

        self.featureSelectionApplets = []
        self.pcApplets = []
        for i in range(n_stages):
            self.featureSelectionApplets.append( self.createFeatureSelectionApplet(i) )
            self.pcApplets.append( self.createPixelClassificationApplet(i) )
        opFinalClassify = self.pcApplets[-1].topLevelOperator

        # If *any* stage enters 'live update' mode, make sure they all enter live update mode.
        def sync_freeze_predictions_settings( slot, *args ):
            freeze_predictions = slot.value
            for pcApplet in self.pcApplets:
                pcApplet.topLevelOperator.FreezePredictions.setValue( freeze_predictions )
        for pcApplet in self.pcApplets:
            pcApplet.topLevelOperator.FreezePredictions.notifyDirty( sync_freeze_predictions_settings )

        self.dataExportApplet = PixelClassificationDataExportApplet(self, "Prediction Export")
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.PmapColors.connect( opFinalClassify.PmapColors )
        opDataExport.LabelNames.connect( opFinalClassify.LabelNames )
        opDataExport.WorkingDirectory.connect( opDataSelection.WorkingDirectory )

        self.EXPORT_NAMES = []
        for stage_index in reversed(list(range(n_stages))):
            self.EXPORT_NAMES += ["{} Stage {}".format( name, stage_index+1 ) for name in self.EXPORT_NAMES_PER_STAGE]
        
        # And finally, one last item for *all* probabilities from all stages.
        self.EXPORT_NAMES += ["Probabilities All Stages"]
        opDataExport.SelectionNames.setValue( self.EXPORT_NAMES )

        # Expose for shell
        self._applets.append(self.dataSelectionApplet)
        self._applets += itertools.chain(*list(zip(self.featureSelectionApplets, self.pcApplets)))
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

        return DataSelectionApplet( self,
                                    "Input Data",
                                    "Input Data",
                                    supportIlastik05Import=False,
                                    instructionText=data_instructions,
                                    forceAxisOrder=c_at_end)

    def createFeatureSelectionApplet(self, index):
        """
        Can be overridden by subclasses, if they want to return their own type of FeatureSelectionApplet.
        NOTE: The applet returned here must have the same interface as the regular FeatureSelectionApplet.
              (If it looks like a duck...)
        """
        # Make the first one compatible with the pixel classification workflow,
        # in case the user uses "Import Project"
        hdf5_group_name = 'FeatureSelections'
        if index > 0:
            hdf5_group_name = "FeatureSelections{index:02d}".format(index=index)
        applet = FeatureSelectionApplet(self, "Feature Selection", hdf5_group_name)
        applet.topLevelOperator.name += '{}'.format(index)
        return applet

    def createPixelClassificationApplet(self, index=0):
        """
        Can be overridden by subclasses, if they want to return their own type of PixelClassificationApplet.
        NOTE: The applet returned here must have the same interface as the regular PixelClassificationApplet.
              (If it looks like a duck...)
        """
        # Make the first one compatible with the pixel classification workflow,
        # in case the user uses "Import Project"
        hdf5_group_name = 'PixelClassification'
        if index > 0:
            hdf5_group_name = "PixelClassification{index:02d}".format(index=index)
        applet = PixelClassificationApplet( self, hdf5_group_name )
        applet.topLevelOperator.name += '{}'.format(index)
        return applet


    def prepareForNewLane(self, laneIndex):
        """
        Overridden from Workflow base class.
        Called immediately before a new lane is added to the workflow.
        """
        # When the new lane is added, dirty notifications will propagate throughout the entire graph.
        # This means the classifier will be marked 'dirty' even though it is still usable.
        # Before that happens, let's store the classifier, so we can restore it at the end of connectLane(), below.
        self.stored_classifers = []
        for pcApplet in self.pcApplets:
            opPixelClassification = pcApplet.topLevelOperator
            if opPixelClassification.classifier_cache.Output.ready() and \
               not opPixelClassification.classifier_cache._dirty:
                self.stored_classifers.append(opPixelClassification.classifier_cache.Output.value)
            else:
                self.stored_classifers = []
        
    def handleNewLanesAdded(self):
        """
        Overridden from Workflow base class.
        Called immediately after a new lane is added to the workflow and initialized.
        """
        # Restore classifier we saved in prepareForNewLane() (if any)
        if self.stored_classifers:
            for pcApplet, classifier in zip(self.pcApplets, self.stored_classifers):
                pcApplet.topLevelOperator.classifier_cache.forceValue(classifier)

            # Release references
            self.stored_classifers = []

    def connectLane(self, laneIndex):
        # Get a handle to each operator
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opFirstFeatures = self.featureSelectionApplets[0].topLevelOperator.getLane(laneIndex)
        opFirstClassify = self.pcApplets[0].topLevelOperator.getLane(laneIndex)
        opFinalClassify = self.pcApplets[-1].topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)
        
        def checkConstraints(*_):
            if opData.Image.meta.dtype != np.uint8:
                msg = "The Autocontext Workflow only supports 8-bit images (UINT8 pixel type).\n"\
                      "Your image has a pixel type of {}.  Please convert your data to UINT8 and try again."\
                      .format( str(np.dtype(opData.Image.meta.dtype)) )
                raise DatasetConstraintError( "Autocontext Workflow", msg, unfixable=True )
                
        opData.Image.notifyReady( checkConstraints )
        
        # Input Image -> Feature Op
        #         and -> Classification Op (for display)
        opFirstFeatures.InputImage.connect( opData.Image )
        opFirstClassify.InputImages.connect( opData.Image )

        # Feature Images -> Classification Op (for training, prediction)
        opFirstClassify.FeatureImages.connect( opFirstFeatures.OutputImage )
        opFirstClassify.CachedFeatureImages.connect( opFirstFeatures.CachedOutputImage )

        upstreamPcApplets = self.pcApplets[0:-1]
        downstreamFeatureApplets = self.featureSelectionApplets[1:]
        downstreamPcApplets = self.pcApplets[1:]

        for ( upstreamPcApplet,
              downstreamFeaturesApplet,
              downstreamPcApplet ) in zip( upstreamPcApplets, 
                                           downstreamFeatureApplets, 
                                           downstreamPcApplets ):
            
            opUpstreamClassify = upstreamPcApplet.topLevelOperator.getLane(laneIndex)
            opDownstreamFeatures = downstreamFeaturesApplet.topLevelOperator.getLane(laneIndex)
            opDownstreamClassify = downstreamPcApplet.topLevelOperator.getLane(laneIndex)

            # Connect label inputs (all are connected together).
            #opDownstreamClassify.LabelInputs.connect( opUpstreamClassify.LabelInputs )
            
            # Connect data path
            #assert opData.Image.meta.dtype == numpy.uint8, "Raw Data must be uint8, not {}".format( opData.Image.meta.dtype )
            opStacker = OpMultiArrayStacker(parent=self)
            opStacker.Images.resize(2)
            opStacker.Images[0].connect( opData.Image )
            opStacker.Images[1].connect( opUpstreamClassify.PredictionProbabilitiesUint8 )
            opStacker.AxisFlag.setValue('c')
            
            opDownstreamFeatures.InputImage.connect( opStacker.Output )
            opDownstreamClassify.InputImages.connect( opStacker.Output )
            opDownstreamClassify.FeatureImages.connect( opDownstreamFeatures.OutputImage )
            opDownstreamClassify.CachedFeatureImages.connect( opDownstreamFeatures.CachedOutputImage )

        # Data Export connections
        opDataExport.RawData.connect( opData.ImageGroup[self.DATA_ROLE_RAW] )
        opDataExport.RawDatasetInfo.connect( opData.DatasetGroup[self.DATA_ROLE_RAW] )
        opDataExport.ConstraintDataset.connect( opData.ImageGroup[self.DATA_ROLE_RAW] )

        opDataExport.Inputs.resize( len(self.EXPORT_NAMES) )
        for reverse_stage_index, (stage_index, pcApplet) in enumerate(reversed(list(enumerate(self.pcApplets)))):
            opPc = pcApplet.topLevelOperator.getLane(laneIndex)
            num_items_per_stage = len(self.EXPORT_NAMES_PER_STAGE)
            opDataExport.Inputs[num_items_per_stage*reverse_stage_index+0].connect( opPc.HeadlessPredictionProbabilities )
            opDataExport.Inputs[num_items_per_stage*reverse_stage_index+1].connect( opPc.SimpleSegmentation )
            opDataExport.Inputs[num_items_per_stage*reverse_stage_index+2].connect( opPc.HeadlessUncertaintyEstimate )
            opDataExport.Inputs[num_items_per_stage*reverse_stage_index+3].connect( opPc.FeatureImages )
            opDataExport.Inputs[num_items_per_stage*reverse_stage_index+4].connect( opPc.LabelImages )
            opDataExport.Inputs[num_items_per_stage*reverse_stage_index+5].connect( opPc.InputImages ) # Input must come last due to an assumption in PixelClassificationDataExportGui

        # One last export slot for all probabilities, all stages
        opAllStageStacker = OpMultiArrayStacker(parent=self)
        opAllStageStacker.Images.resize( len(self.pcApplets) )
        for stage_index, pcApplet in enumerate(self.pcApplets):
            opPc = pcApplet.topLevelOperator.getLane(laneIndex)
            opAllStageStacker.Images[stage_index].connect(opPc.HeadlessPredictionProbabilities)
            opAllStageStacker.AxisFlag.setValue('c')

        # The ideal_blockshape metadata field will be bogus, so just eliminate it
        # (Otherwise, the channels could be split up in an unfortunate way.)
        opMetadataOverride = OpMetadataInjector(parent=self)
        opMetadataOverride.Input.connect( opAllStageStacker.Output )
        opMetadataOverride.Metadata.setValue( {'ideal_blockshape' : None } )
        
        opDataExport.Inputs[-1].connect( opMetadataOverride.Output )
        
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

        # First, determine various 'ready' states for each pixel classification stage (features+prediction)
        StageFlags = collections.namedtuple("StageFlags", 'input_ready features_ready invalid_classifier predictions_ready live_update_active')
        stage_flags = []
        for stage_index, (featureSelectionApplet, pcApplet) in enumerate(zip(self.featureSelectionApplets, self.pcApplets)):
            if stage_index == 0:
                input_ready = len(opDataSelection.ImageGroup) > 0 and not self.dataSelectionApplet.busy
            else:
                input_ready = stage_flags[stage_index-1].predictions_ready

            opFeatureSelection = featureSelectionApplet.topLevelOperator
            featureOutput = opFeatureSelection.OutputImage
            features_ready = input_ready and \
                             len(featureOutput) > 0 and  \
                             featureOutput[0].ready() and \
                             (TinyVector(featureOutput[0].meta.shape) > 0).all()

            opPixelClassification = pcApplet.topLevelOperator
            invalid_classifier = opPixelClassification.classifier_cache.fixAtCurrent.value and \
                                 opPixelClassification.classifier_cache.Output.ready() and\
                                 opPixelClassification.classifier_cache.Output.value is None
    
            predictions_ready = features_ready and \
                                not invalid_classifier and \
                                len(opPixelClassification.HeadlessPredictionProbabilities) > 0 and \
                                opPixelClassification.HeadlessPredictionProbabilities[0].ready() and \
                                (TinyVector(opPixelClassification.HeadlessPredictionProbabilities[0].meta.shape) > 0).all()

            live_update_active = not opPixelClassification.FreezePredictions.value
            
            stage_flags += [ StageFlags(input_ready, features_ready, invalid_classifier, predictions_ready, live_update_active) ]



        opDataExport = self.dataExportApplet.topLevelOperator
        opPixelClassification = self.pcApplets[0].topLevelOperator

        # Problems can occur if the features or input data are changed during live update mode.
        # Don't let the user do that.
        any_live_update = any(flags.live_update_active for flags in stage_flags)
        
        # The user isn't allowed to touch anything while batch processing is running.
        batch_processing_busy = self.batchProcessingApplet.busy
        
        self._shell.setAppletEnabled(self.dataSelectionApplet, not any_live_update and not batch_processing_busy)

        for stage_index, (featureSelectionApplet, pcApplet) in enumerate(zip(self.featureSelectionApplets, self.pcApplets)):
            upstream_live_update = any(flags.live_update_active for flags in stage_flags[:stage_index])
            this_stage_live_update = stage_flags[stage_index].live_update_active
            downstream_live_update = any(flags.live_update_active for flags in stage_flags[stage_index+1:])
            
            self._shell.setAppletEnabled(featureSelectionApplet, stage_flags[stage_index].input_ready \
                                                                 and not this_stage_live_update \
                                                                 and not downstream_live_update \
                                                                 and not batch_processing_busy)
            
            self._shell.setAppletEnabled(pcApplet, stage_flags[stage_index].features_ready \
                                                   #and not downstream_live_update \ # Not necessary because live update modes are synced -- labels can't be added in live update.
                                                   and not batch_processing_busy)

        self._shell.setAppletEnabled(self.dataExportApplet, stage_flags[-1].predictions_ready and not batch_processing_busy)
        self._shell.setAppletEnabled(self.batchProcessingApplet, predictions_ready and not batch_processing_busy)
    
        # Lastly, check for certain "busy" conditions, during which we 
        #  should prevent the shell from closing the project.
        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= any(applet.busy for applet in self.featureSelectionApplets)
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
        if self._headless:
            # In headless mode, let's see the messages from the training operator.
            logging.getLogger("lazyflow.operators.classifierOperators").setLevel(logging.DEBUG)

        if self.retrain:
            self._force_retrain_classifiers(projectManager)
        
        # Configure the data export operator.
        if self._batch_export_args:
            self.dataExportApplet.configure_operator_with_parsed_args( self._batch_export_args )

        if self._batch_input_args:
            for pcApplet in self.pcApplets:
                if pcApplet.topLevelOperator.classifier_cache._dirty:
                    logger.warning("At least one of your classifiers is not yet trained.  "
                                "A new classifier will be trained for this run.")
                    break

        if self._headless and self._batch_input_args and self._batch_export_args:
            logger.info("Beginning Batch Processing")
            self.batchProcessingApplet.run_export_from_parsed_args(self._batch_input_args)
            logger.info("Completed Batch Processing")

    def prepare_for_entire_export(self):
        # While exporting, we don't want to cache any data.
        export_selection_index = self.dataExportApplet.topLevelOperator.InputSelection.value
        export_selection_name = self.dataExportApplet.topLevelOperator.SelectionNames.value[ export_selection_index ]
        if 'all stages' in export_selection_name.lower():
            # UNLESS we're exporting from more than one stage at a time.
            # In that case, the caches help avoid unnecessary work (except for the last stage)
            self.featureSelectionApplets[-1].topLevelOperator.BypassCache.setValue(True)
        else:
            for featureSeletionApplet in self.featureSelectionApplets:
                featureSeletionApplet.topLevelOperator.BypassCache.setValue(True)
            
        # Unfreeze the classifier caches (ensure that we're exporting based on up-to-date labels)
        self.freeze_statuses = []
        for pcApplet in self.pcApplets:
            self.freeze_statuses.append(pcApplet.topLevelOperator.FreezePredictions.value)
            pcApplet.topLevelOperator.FreezePredictions.setValue(False)

    def post_process_entire_export(self):
        # While exporting, we disabled caches, but now we can enable them again.
        for featureSeletionApplet in self.featureSelectionApplets:
            featureSeletionApplet.topLevelOperator.BypassCache.setValue(False)

        # Re-freeze classifier caches (if necessary)
        for pcApplet, freeze_status in zip(self.pcApplets, self.freeze_statuses):
            pcApplet.topLevelOperator.FreezePredictions.setValue(freeze_status)

    def _force_retrain_classifiers(self, projectManager):
        # Cause the FIRST classifier to be dirty so it is forced to retrain.
        # (useful if the stored labels were changed outside ilastik)
        self.pcApplets[0].topLevelOperator.opTrain.ClassifierFactory.setDirty()
        
        # Unfreeze all classifier caches.
        for pcApplet in self.pcApplets:
            pcApplet.topLevelOperator.FreezePredictions.setValue(False)

        # Request the LAST classifier, which forces training
        _ = self.pcApplets[-1].topLevelOperator.Classifier.value

        # store new classifiers to project file
        projectManager.saveProject(force_all_save=False)

    def menus(self):
        """
        Overridden from Workflow base class
        """
        from PyQt5.QtWidgets import QMenu
        autocontext_menu = QMenu("Autocontext Utilities")
        distribute_action = autocontext_menu.addAction("Distribute Labels...")
        distribute_action.triggered.connect( self.distribute_labels_from_current_stage )

        self._autocontext_menu = autocontext_menu # Must retain here as a member or else reference disappears and the menu is deleted.
        return [self._autocontext_menu]
        
    def distribute_labels_from_current_stage(self):
        """
        Distrubute labels from the currently viewed stage across all other stages.
        """
        # Late import.
        # (Don't import PyQt in headless mode.)
        from PyQt5.QtWidgets import QMessageBox
        current_applet = self._applets[self.shell.currentAppletIndex]
        if current_applet not in self.pcApplets:
            QMessageBox.critical(self.shell, "Wrong page selected", "The currently active page isn't a Training page.")
            return
        
        current_stage_index = self.pcApplets.index(current_applet)
        destination_stage_indexes, partition = self.get_label_distribution_settings( current_stage_index,
                                                                                     num_stages=len(self.pcApplets))
        if destination_stage_indexes is None:
            return # User cancelled
        
        current_applet = self._applets[self.shell.currentAppletIndex]
        opCurrentPixelClassification = current_applet.topLevelOperator
        num_current_stage_classes = len(opCurrentPixelClassification.LabelNames.value)

        # Before we get started, make sure the destination stages have the necessary label classes
        for stage_index in destination_stage_indexes:
            # Get this stage's OpPixelClassification
            opPc = self.pcApplets[stage_index].topLevelOperator
    
            # Copy Label Colors
            current_stage_label_colors = opCurrentPixelClassification.LabelColors.value
            new_label_colors = list(opPc.LabelColors.value)
            new_label_colors[:num_current_stage_classes] = current_stage_label_colors[:num_current_stage_classes]
            opPc.LabelColors.setValue(new_label_colors)
            
            # Copy PMap colors
            current_stage_pmap_colors = opCurrentPixelClassification.PmapColors.value
            new_pmap_colors = list(opPc.PmapColors.value)
            new_pmap_colors[:num_current_stage_classes] = current_stage_pmap_colors[:num_current_stage_classes]
            opPc.PmapColors.setValue(new_pmap_colors)
    
            # Copy Label Names                    
            current_stage_label_names = opCurrentPixelClassification.LabelNames.value
            new_label_names = list(opPc.LabelNames.value)
            new_label_names[:num_current_stage_classes] = current_stage_label_names[:num_current_stage_classes]
            opPc.LabelNames.setValue(new_label_names)

        # For each lane, copy over the labels from the source stage to the destination stages 
        for lane_index in range(len(opCurrentPixelClassification.InputImages)):
            opPcLane = opCurrentPixelClassification.getLane(lane_index)

            # Gather all the labels for this lane
            blockwise_labels = {}
            nonzero_slicings = opPcLane.NonzeroLabelBlocks.value
            for block_slicing in nonzero_slicings:
                # Convert from slicing to roi-tuple so we can hash it in a dict key
                block_roi = sliceToRoi( block_slicing, opPcLane.InputImages.meta.shape )
                block_roi = tuple(map(tuple, block_roi))
                blockwise_labels[block_roi] = opPcLane.LabelImages[block_slicing].wait()

            if partition and current_stage_index in destination_stage_indexes:
                # Clear all labels in the current lane, since we'll be overwriting it with a subset of labels
                # FIXME: We could implement a fast function for this in OpCompressedUserLabelArray...
                for label_value in range(1,num_current_stage_classes+1,):
                    opPcLane.opLabelPipeline.opLabelArray.clearLabel(label_value)

            # Now redistribute those labels across all lanes
            for block_roi, block_labels in list(blockwise_labels.items()):
                nonzero_coords = block_labels.nonzero()

                if partition:
                    num_labels = len(nonzero_coords[0])
                    destination_stage_map = np.random.choice(destination_stage_indexes, (num_labels,))
                
                for stage_index in destination_stage_indexes:
                    if not partition:
                        this_stage_block_labels = block_labels
                    else:
                        # Divide into disjoint partitions
                        # Find the coordinates labels destined for this stage
                        this_stage_coords = np.transpose(nonzero_coords)[destination_stage_map == stage_index]
                        this_stage_coords = tuple(this_stage_coords.transpose())

                        # Extract only the labels destined for this stage
                        this_stage_block_labels = np.zeros_like(block_labels)
                        this_stage_block_labels[this_stage_coords] = block_labels[this_stage_coords]

                    # Get the current lane's view of this stage's OpPixelClassification
                    opPc = self.pcApplets[stage_index].topLevelOperator.getLane(lane_index)

                    # Inject
                    opPc.LabelInputs[roiToSlice(*block_roi)] = this_stage_block_labels
    
    @staticmethod
    def get_label_distribution_settings(source_stage_index, num_stages):
        # Late import.
        # (Don't import PyQt in headless mode.)
        from PyQt5.QtWidgets import QDialog, QVBoxLayout
        class LabelDistributionOptionsDlg( QDialog ):
            """
            A little dialog to let the user specify how the labels should be
            distributed from the current stages to the other stages.
            """
            def __init__(self, source_stage_index, num_stages, *args, **kwargs):
                super(LabelDistributionOptionsDlg, self).__init__(*args, **kwargs)

                from PyQt5.QtCore import Qt
                from PyQt5.QtWidgets import QGroupBox, QCheckBox, QRadioButton, QDialogButtonBox
            
                self.setWindowTitle("Distributing from Stage {}".format(source_stage_index+1))

                self.stage_checkboxes = []
                for stage_index in range(1, num_stages+1):
                    self.stage_checkboxes.append( QCheckBox("Stage {}".format( stage_index )) )
                
                # By default, send labels back into the current stage, at least.
                self.stage_checkboxes[source_stage_index].setChecked(True)
                
                stage_selection_layout = QVBoxLayout()
                for checkbox in self.stage_checkboxes:
                    stage_selection_layout.addWidget( checkbox )

                stage_selection_groupbox = QGroupBox("Send labels from Stage {} to:".format( source_stage_index+1 ), self)
                stage_selection_groupbox.setLayout(stage_selection_layout)
                
                self.copy_button = QRadioButton("Copy", self)
                self.partition_button = QRadioButton("Partition", self)
                self.partition_button.setChecked(True)
                distribution_mode_layout = QVBoxLayout()
                distribution_mode_layout.addWidget(self.copy_button)
                distribution_mode_layout.addWidget(self.partition_button)
                
                distribution_mode_group = QGroupBox("Distribution Mode", self)
                distribution_mode_group.setLayout(distribution_mode_layout)
                
                buttonbox = QDialogButtonBox( Qt.Horizontal, parent=self )
                buttonbox.setStandardButtons( QDialogButtonBox.Ok | QDialogButtonBox.Cancel )
                buttonbox.accepted.connect( self.accept )
                buttonbox.rejected.connect( self.reject )
                
                dlg_layout = QVBoxLayout()
                dlg_layout.addWidget(stage_selection_groupbox)
                dlg_layout.addWidget(distribution_mode_group)
                dlg_layout.addWidget(buttonbox)
                self.setLayout(dlg_layout)

            def distribution_mode(self):
                if self.copy_button.isChecked():
                    return "copy"
                if self.partition_button.isChecked():
                    return "partition"
                assert False, "Shouldn't get here."
            
            def destination_stages(self):
                """
                Return the list of stage_indexes (0-based) that the user checked.
                """
                return [ i for i,box in enumerate(self.stage_checkboxes) if box.isChecked() ]

        dlg = LabelDistributionOptionsDlg( source_stage_index, num_stages )
        if dlg.exec_() == QDialog.Rejected:
            return (None, None)
        
        destination_stage_indexes = dlg.destination_stages()
        partition = (dlg.distribution_mode() == "partition")
        return (destination_stage_indexes, partition)

        
class AutocontextTwoStage(NewAutocontextWorkflowBase):
    workflowName = "AutocontextTwoStage"
    workflowDisplayName = "Autocontext (2-stage)"

    def __init__(self, *args, **kwargs):
        super(AutocontextTwoStage, self).__init__(*args, n_stages=2, **kwargs)

import ilastik.config
if ilastik.config.cfg.getboolean('ilastik', 'debug'):
    class AutocontextThreeStage(NewAutocontextWorkflowBase):
        workflowName = "AutocontextThreeStage"
        workflowDisplayName = "Autocontext (3-stage)"

        def __init__(self, *args, **kwargs):
            super(AutocontextThreeStage, self).__init__(*args, n_stages=3, **kwargs)

import ilastik.config
if ilastik.config.cfg.getboolean('ilastik', 'debug'):
    class AutocontextFourStage(NewAutocontextWorkflowBase):
        workflowName = "AutocontextFourStage"
        workflowDisplayName = "Autocontext (4-stage)"
     
        def __init__(self, *args, **kwargs):
            super(AutocontextFourStage, self).__init__(*args, n_stages=4, **kwargs)
