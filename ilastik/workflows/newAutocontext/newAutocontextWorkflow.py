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
import sys
import copy
import argparse
import warnings
import itertools
import collections
import logging
from __builtin__ import False
from ilastik.applets.pixelClassification.opPixelClassification import OpPixelClassification
logger = logging.getLogger(__name__)

import numpy

from ilastik.config import cfg as ilastik_config
from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.pixelClassification import PixelClassificationApplet, PixelClassificationDataExportApplet

from lazyflow.graph import Graph
from lazyflow.roi import TinyVector, fullSlicing
from lazyflow.operators.generic import OpMultiArrayStacker

class NewAutocontextWorkflowBase(Workflow):
    
    workflowName = "New Autocontext Base"
    defaultAppletIndex = 0 # show DataSelection by default
    
    DATA_ROLE_RAW = 0
    DATA_ROLE_PREDICTION_MASK = 1
    
    EXPORT_NAMES = ['Probabilities', 'Simple Segmentation', 'Uncertainty', 'Features', 'Labels']
    
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

        # Parse the creation args: These were saved to the project file when this project was first created.
        parsed_creation_args, unused_args = parser.parse_known_args(project_creation_args)
        
        # Parse the cmdline args for the current session.
        parsed_args, unused_args = parser.parse_known_args(workflow_cmdline_args)
        
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

        self.dataExportApplet = PixelClassificationDataExportApplet(self, "Prediction Export")
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.PmapColors.connect( opFinalClassify.PmapColors )
        opDataExport.LabelNames.connect( opFinalClassify.LabelNames )
        opDataExport.WorkingDirectory.connect( opDataSelection.WorkingDirectory )
        opDataExport.SelectionNames.setValue( self.EXPORT_NAMES )        

        # Expose for shell
        self._applets.append(self.dataSelectionApplet)
        self._applets += itertools.chain(*zip(self.featureSelectionApplets, self.pcApplets))
        self._applets.append(self.dataExportApplet)
        
        self.dataExportApplet.prepare_for_entire_export = self.prepare_for_entire_export
        self.dataExportApplet.post_process_entire_export = self.post_process_entire_export

        if unused_args:
            logger.warn("Unused command-line args: {}".format( unused_args ))

    def createDataSelectionApplet(self):
        """
        Can be overridden by subclasses, if they want to use 
        special parameters to initialize the DataSelectionApplet.
        """
        data_instructions = "Select your input data using the 'Raw Data' tab shown on the right"
        return DataSelectionApplet( self,
                                    "Input Data",
                                    "Input Data",
                                    supportIlastik05Import=False,
                                    instructionText=data_instructions )

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
        opDataExport.Inputs[0].connect( opFinalClassify.HeadlessPredictionProbabilities )
        opDataExport.Inputs[1].connect( opFinalClassify.SimpleSegmentation )
        opDataExport.Inputs[2].connect( opFinalClassify.HeadlessUncertaintyEstimate )
        opDataExport.Inputs[3].connect( opFinalClassify.FeatureImages )
        opDataExport.Inputs[4].connect( opFinalClassify.LabelImages )
        for slot in opDataExport.Inputs:
            assert slot.partner is not None

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
        #batch_processing_busy = self.batchProcessingApplet.busy
        batch_processing_busy = False # FIXME
        
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
                                                   and not downstream_live_update \
                                                   and not batch_processing_busy)

        self._shell.setAppletEnabled(self.dataExportApplet, stage_flags[-1].predictions_ready and not batch_processing_busy)

#         if self.batchProcessingApplet is not None:
#             self._shell.setAppletEnabled(self.batchProcessingApplet, predictions_ready and not batch_processing_busy)
    
        # Lastly, check for certain "busy" conditions, during which we 
        #  should prevent the shell from closing the project.
        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= any(applet.busy for applet in self.featureSelectionApplets)
        busy |= self.dataExportApplet.busy
        #busy |= self.batchProcessingApplet.busy
        self._shell.enableProjectChanges( not busy )

    def onProjectLoaded(self, projectManager):
        """
        Overridden from Workflow base class.  Called by the Project Manager.
        
        If the user provided command-line arguments, use them to configure 
        the workflow for batch mode and export all results.
        (This workflow's headless mode supports only batch mode for now.)
        """
        pass

    def prepare_for_entire_export(self):
        self.freeze_statuses = []
        for pcApplet in self.pcApplets:
            self.freeze_statuses.append(pcApplet.topLevelOperator.FreezePredictions.value)
            pcApplet.topLevelOperator.FreezePredictions.setValue(False)

    def post_process_entire_export(self):
        for pcApplet, freeze_status in zip(self.pcApplets, self.freeze_statuses):
            pcApplet.topLevelOperator.FreezePredictions.setValue(freeze_status)


class AutocontextTwoStage(NewAutocontextWorkflowBase):
    workflowName = "AutocontextTwoStage"
    workflowDisplayName = "Autocontext (2-stage)"

    def __init__(self, *args, **kwargs):
        super(AutocontextTwoStage, self).__init__(*args, n_stages=2, **kwargs)

class AutocontextThreeStage(NewAutocontextWorkflowBase):
    workflowName = "AutocontextThreeStage"
    workflowDisplayName = "Autocontext (3-stage)"

    def __init__(self, *args, **kwargs):
        super(AutocontextThreeStage, self).__init__(*args, n_stages=3, **kwargs)

class AutocontextFourStage(NewAutocontextWorkflowBase):
    workflowName = "AutocontextFourStage"
    workflowDisplayName = "Autocontext (4-stage)"

    def __init__(self, *args, **kwargs):
        super(AutocontextFourStage, self).__init__(*args, n_stages=4, **kwargs)
