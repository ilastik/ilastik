###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2017, the ilastik developers
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
import sys
import os
import warnings
import argparse
import csv

import numpy
import h5py

from ilastik.workflow import Workflow
from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet, DatasetInfo
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.pixelClassification import PixelClassificationApplet
from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
from ilastik.applets.pixelClassification.opPixelClassification import OpPredictionPipeline
from ilastik.applets.thresholdTwoLevels import ThresholdTwoLevelsApplet, OpThresholdTwoLevels
from ilastik.applets.objectExtraction import ObjectExtractionApplet
from ilastik.applets.objectClassification import ObjectClassificationApplet, ObjectClassificationDataExportApplet
from ilastik.applets.fillMissingSlices import FillMissingSlicesApplet
from ilastik.applets.fillMissingSlices.opFillMissingSlices import OpFillMissingSlicesNoCache
from ilastik.applets.blockwiseObjectClassification import BlockwiseObjectClassificationApplet, OpBlockwiseObjectClassification
from ilastik.applets.batchProcessing import BatchProcessingApplet
from ilastik.applets.seeds.seedsApplet import SeedsApplet
from ilastik.applets.watershedSegmentation.watershedSegmentationApplet import WatershedSegmentationApplet
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet

from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.operators.generic import OpTransposeSlots, OpSelectSubslot
from lazyflow.operators.valueProviders import OpAttributeSelector
from lazyflow.roi import TinyVector
from lazyflow.utility import PathComponents

import logging
logger = logging.getLogger(__name__)

EXPORT_SELECTION_PREDICTIONS = 0
EXPORT_SELECTION_PROBABILITIES = 1
EXPORT_SELECTION_BLOCKWISE_PREDICTIONS = 2
EXPORT_SELECTION_BLOCKWISE_PROBABILITIES = 3
EXPORT_SELECTION_PIXEL_PROBABILITIES = 4

'''
# Constants for pointcloud generation on cluster
CSV_FORMAT = { 'delimiter' : '\t', 'lineterminator' : '\n' }
OUTPUT_COLUMNS = ["x_px", "y_px", "z_px", 
                  "size_px", 
                  "min_x_px", "min_y_px", "min_z_px", 
                  "max_x_px", "max_y_px", "max_z_px"]
'''

#TODO:
# - add object classification for seeds
# - add applet to select the channel (channel selection) of the prediction for the different labels so that only one label is used
#   (for seeds or boundaries) and that there is only one channel


#class PixelObjectWatershed(ObjectClassificationWorkflow):
class PixelObjectWatershedWorkflow(Workflow):
    workflowName = "Pixel calssification on RawData for Boundaries and\
            Pixel Classification + Object Classification on Raw Data for Seeds; then WatershedSegmentation on it"
    workflowDisplayName = "Pixel Classification + Object Classification + Watershed ['Raw Data']"

    defaultAppletIndex = 0 # show DataSelection (first applet) by default

    # give your input data a number, so the group can be found for them
    DATA_ROLE_RAW           = 0
    #DATA_ROLE_BOUNDARIES    = 1
    #DATA_ROLE_SEEDS         = 2
    ROLE_NAMES = ['Raw Data']

    #define the names of the data, that can be exported in the DataExport Applet
    #TODO
    EXPORT_NAMES = ['Corrected Seeds', 'Watershed']

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_workflow, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()

        super(PixelObjectWatershedWorkflow, self).__init__( \
                shell, headless, workflow_cmdline_args, project_creation_workflow, graph=graph, *args, **kwargs)




        ############################################################
        # command line parser (taken from object classification workflow)
        ############################################################
        # Parse workflow-specific command-line args
        parser = argparse.ArgumentParser()
        parser.add_argument('--fillmissing', help="use 'fill missing' applet with chosen detection method", choices=['classic', 'svm', 'none'], default='none')
        parser.add_argument('--filter', help="pixel feature filter implementation.", choices=['Original', 'Refactored', 'Interpolated'], default='Original')
        parser.add_argument('--nobatch', help="do not append batch applets", action='store_true', default=False)
        
        parsed_creation_args, unused_args = parser.parse_known_args(project_creation_workflow)

        self.fillMissing = parsed_creation_args.fillmissing
        self.filter_implementation = parsed_creation_args.filter

        parsed_args, unused_args = parser.parse_known_args(workflow_cmdline_args)
        if parsed_args.fillmissing != 'none' and parsed_creation_args.fillmissing != parsed_args.fillmissing:
            logger.error( "Ignoring --fillmissing cmdline arg.  Can't specify a different fillmissing setting after the project has already been created." )
        
        if parsed_args.filter != 'Original' and parsed_creation_args.filter != parsed_args.filter:
            logger.error( "Ignoring --filter cmdline arg.  Can't specify a different filter setting after the project has already been created." )

        self.batch = not parsed_args.nobatch




        ############################################################
        # Init and add the applets, and expose to shell
        ############################################################
        self._applets = []

        # -- DataSelection applet
        #

        #self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", "Input Data")
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", forceAxisOrder=['txyzc'])

        # Dataset inputs
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( self.ROLE_NAMES )
        #opDataSelection.DatasetRoles.setValue(['Raw Data'])


        # array of feature selection applets (needed from pixelClassificationApplets)
        # OpPixelClassification0 takes the first element of this array = array[0] and so on
        self.featureSelectionApplets = []

        # -- FeatureSelection applet (for Boundaries)
        #
        self.featureSelectionAppletBoundaries = FeatureSelectionApplet(
            self,
            "Feature Selection Boundaries",
            "FeatureSelections",
            filter_implementation=self.filter_implementation
        )
        self.featureSelectionApplets.append(self.featureSelectionAppletBoundaries)

        # -- PixelClassification applet (for Boundaries)
        #
        self.pcAppletBoundaries = PixelClassificationApplet(
            self, "PixelClassification Boundaries")
        #done to use more than one feature selection applet, next one must be OpPixelClassification1
        self.pcAppletBoundaries.topLevelOperator.name = "OpPixelClassification0"
        # default is Training
        self.pcAppletBoundaries.name = "PixelClassification Boundaries"



        # -- FeatureSelection applet (for Seeds)
        #
        self.featureSelectionAppletSeeds = FeatureSelectionApplet(
            self,
            "Feature Selection Seeds",
            "FeatureSelections",
            filter_implementation=self.filter_implementation
        )
        self.featureSelectionApplets.append(self.featureSelectionAppletSeeds)

        # -- PixelClassification applet (for Seeds)
        #
        self.pcAppletSeeds = PixelClassificationApplet(
            self, "PixelClassification Seeds")
        #done to use more than one feature selection applet
        self.pcAppletSeeds.topLevelOperator.name = "OpPixelClassification1"
        # default is Training
        self.pcAppletSeeds.name = "PixelClassification Seeds"


        # -- ObjectClassification applet (for Seeds)
        #
        #TODO 




        # -- Seeds applet
        #
        self.seedsApplet = SeedsApplet(self, "Seeds", "SeedsGroup")

        # -- WatershedSegmentation applet
        #
        # ( workflow=self, guiName='', projectFileGroupName='' )
        self.watershedSegmentationApplet = WatershedSegmentationApplet(self, "Watershed", "WatershedSegmentation")

        # -- DataExport applet
        #
        self.dataExportApplet = DataExportApplet(self, "Data Export")

        # Configure global DataExport settings
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.WorkingDirectory.connect( opDataSelection.WorkingDirectory )
        #opDataExport.PmapColors.connect( opWatershedSegmentation.PmapColors )
        #opDataExport.LabelNames.connect( opWatershedSegmentation.LabelNames )
        opDataExport.SelectionNames.setValue( self.EXPORT_NAMES )





        # -- BatchProcessing applet
        #
        self.batchProcessingApplet = BatchProcessingApplet(self,
                                                           "Batch Processing",
                                                           self.dataSelectionApplet,
                                                           self.dataExportApplet)

        # -- Expose applets to shell
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionAppletBoundaries)
        self._applets.append(self.pcAppletBoundaries)
        self._applets.append(self.featureSelectionAppletSeeds)
        self._applets.append(self.pcAppletSeeds)
        self._applets.append(self.seedsApplet)
        self._applets.append(self.watershedSegmentationApplet)
        self._applets.append(self.dataExportApplet)
        self._applets.append(self.batchProcessingApplet)

        # -- Parse command-line arguments
        #    (Command-line args are applied in onProjectLoaded(), below.)
        if workflow_cmdline_args:
            self._data_export_args, unused_args = self.dataExportApplet.parse_known_cmdline_args( workflow_cmdline_args )
            self._batch_input_args, unused_args = self.dataSelectionApplet.parse_known_cmdline_args( unused_args, role_names )
        else:
            unused_args = None
            self._batch_input_args = None
            self._data_export_args = None

        if unused_args:
            logger.warn("Unused command-line args: {}".format( unused_args ))

    def connectLane(self, laneIndex):
        """
        Override from base class.
        Connect the output and the input of each applet with each other
        """

        """
        # reorder all input images to have the right axis order
        # prepare the reorderAxis operators here
        order           = "txyzc"
        op5rawdata      = OpReorderAxes(parent=self)
        op5rawdata      .AxisOrder.setValue(order)
        op5boundaries   = OpReorderAxes(parent=self)
        op5boundaries   .AxisOrder.setValue(order)
        op5seeds        = OpReorderAxes(parent=self)
        op5seeds        .AxisOrder.setValue(order)
        """


        # access applet operators
        # get the correct image-lane
        opDataSelection             = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opFeatureSelectionBoundaries= self.featureSelectionAppletBoundaries.topLevelOperator.getLane(laneIndex)
        opPCBoundaries              = self.pcAppletBoundaries.topLevelOperator.getLane(laneIndex)
        opFeatureSelectionSeeds     = self.featureSelectionAppletSeeds.topLevelOperator.getLane(laneIndex)
        opPCSeeds                   = self.pcAppletSeeds.topLevelOperator.getLane(laneIndex)
        opSeeds                     = self.seedsApplet.topLevelOperator.getLane(laneIndex)
        opWatershedSegmentation     = self.watershedSegmentationApplet.topLevelOperator.getLane(laneIndex)
        opDataExport                = self.dataExportApplet.topLevelOperator.getLane(laneIndex)

        # ReorderAxis the Inputs
        """
        op5rawdata.Input.connect(    opDataSelection.ImageGroup[self.DATA_ROLE_RAW] )
        op5boundaries.Input.connect( opDataSelection.ImageGroup[self.DATA_ROLE_BOUNDARIES] )
        op5seeds.Input.connect(      opDataSelection.ImageGroup[self.DATA_ROLE_SEEDS] )
        """


        # fill missing slices: Done for pixelClassification (don't know why)
        if self.fillMissing !='none':
            opFillMissingSlices = self.fillMissingSlicesApplet.topLevelOperator.getLane(laneIndex)
            opFillMissingSlices.Input.connect(    opDataSelection.ImageGroup[self.DATA_ROLE_RAW])
            rawslot = opFillMissingSlices.Output
        else:
            rawslot =     opDataSelection.ImageGroup[self.DATA_ROLE_RAW]

        # feature selection boundaries input
        opFeatureSelectionBoundaries.InputImage.connect(rawslot)

        # pixelclassification boundaries
        opPCBoundaries.InputImages.connect(rawslot)
        opPCBoundaries.FeatureImages.connect(opFeatureSelectionBoundaries.OutputImage)
        opPCBoundaries.CachedFeatureImages.connect(opFeatureSelectionBoundaries.CachedOutputImage)
        #TODO is reordering of axes necessary?
        #op5raw.Input.connect(rawslot)
        #op5pred.Input.connect(opClassify.PredictionProbabilities)


        # feature selection Seeds input
        opFeatureSelectionSeeds.InputImage.connect(rawslot)

        # pixelclassification Seeds
        opPCSeeds.InputImages.connect(rawslot)
        opPCSeeds.FeatureImages.connect(opFeatureSelectionSeeds.OutputImage)
        opPCSeeds.CachedFeatureImages.connect(opFeatureSelectionSeeds.CachedOutputImage)
        #TODO is reordering of axes necessary?
        #op5raw.Input.connect(rawslot)
        #op5pred.Input.connect(opClassify.PredictionProbabilities)


        #TODO Inputs of Seeds and Watersheds need to be adjusted (see var: rawdata)
        #TODO invent a new channel selection appelt (see workflow channel-selection named testWorkflow)
        # to choose the channel output in a new applet

        # seeds inputs
        """
        opSeeds.RawData.connect(    op5rawdata.Output)
        opSeeds.Boundaries.connect( op5boundaries.Output)
        opSeeds.Seeds.connect(      op5seeds.Output)
        """
        opSeeds.RawData.connect(    opDataSelection.ImageGroup[self.DATA_ROLE_RAW])
        #TODO
        opSeeds.Boundaries.connect( opDataSelection.ImageGroup[self.DATA_ROLE_RAW])
        opSeeds.Seeds.connect(      opDataSelection.ImageGroup[self.DATA_ROLE_RAW])

        # watershed inputs
        """
        opWatershedSegmentation.RawData.connect(    op5rawdata.Output )
        opWatershedSegmentation.Boundaries.connect( op5boundaries.Output )
        """
        opWatershedSegmentation.RawData.connect(    opDataSelection.ImageGroup[self.DATA_ROLE_RAW] )
        #TODO
        opWatershedSegmentation.Boundaries.connect( opDataSelection.ImageGroup[self.DATA_ROLE_RAW] )

        opWatershedSegmentation.SeedsExist.connect(         opSeeds.SeedsExist )
        #opWatershedSegmentation.Seeds.connect(              opSeeds.SeedsOut )
        #opWatershedSegmentation.CorrectedSeedsIn.connect(   opSeeds.SeedsOut )
        opWatershedSegmentation.Seeds.connect(              opSeeds.SeedsOutCached )
        opWatershedSegmentation.CorrectedSeedsIn.connect(   opSeeds.SeedsOutCached )


        # watershed parameter
        opWatershedSegmentation.WSMethod.connect(    opSeeds.WSMethod )

        # DataExport inputs for RawData layer
        #opDataExport.RawData.connect(       op5rawdata.Output )
        opDataExport.RawData.connect(       opDataSelection.ImageGroup[self.DATA_ROLE_RAW] )
        opDataExport.RawDatasetInfo.connect(opDataSelection.DatasetGroup[self.DATA_ROLE_RAW] )        


        # connect the output of the watershed-applet to the inputs of the data-export
        opDataExport.Inputs.resize( len(self.EXPORT_NAMES) )
        # 0. use the user manipulated seeds for this 
        # 1. use the cached output of the watershed algorithm, so that reloading the project 
        #    and exporting it will work without an additional calculation
        opDataExport.Inputs[0].connect( opWatershedSegmentation.CorrectedSeedsOut )
        opDataExport.Inputs[1].connect( opWatershedSegmentation.WSCCOCachedOutput )
        #opDataExport.Inputs[2].connect( opWatershedSegmentation.LabelNames )
        for slot in opDataExport.Inputs:
            assert slot.partner is not None
        #for more information, see ilastik.org/lazyflow/advanced.html OperatorWrapper class


    '''
    def connectInputs(self, laneIndex):
               
        op5raw = OpReorderAxes(parent=self)
        op5raw.AxisOrder.setValue("txyzc")
        op5pred = OpReorderAxes(parent=self)
        op5pred.AxisOrder.setValue("txyzc")
        op5threshold = OpReorderAxes(parent=self)
        op5threshold.AxisOrder.setValue("txyzc")
        
        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)
        opClassify = self.pcApplet.topLevelOperator.getLane(laneIndex)
        opThreshold = self.thresholdingApplet.topLevelOperator.getLane(laneIndex)

        if self.fillMissing !='none':
            opFillMissingSlices = self.fillMissingSlicesApplet.topLevelOperator.getLane(laneIndex)
            opFillMissingSlices.Input.connect(opData.Image)
            rawslot = opFillMissingSlices.Output
        else:
            rawslot = opData.Image

        opTrainingFeatures.InputImage.connect(rawslot)

        opClassify.InputImages.connect(rawslot)
        opClassify.FeatureImages.connect(opTrainingFeatures.OutputImage)
        opClassify.CachedFeatureImages.connect(opTrainingFeatures.CachedOutputImage)

        op5raw.Input.connect(rawslot)
        op5pred.Input.connect(opClassify.PredictionProbabilities)

        opThreshold.RawInput.connect(op5raw.Output)
        opThreshold.InputImage.connect(op5pred.Output)
        opThreshold.InputChannelColors.connect( opClassify.PmapColors )

        op5threshold.Input.connect(opThreshold.CachedOutput)

        return op5raw.Output, op5threshold.Output

    '''



        
    def onProjectLoaded(self, projectManager):
        """
        Overridden from Workflow base class.  Called by the Project Manager.
        
        If the user provided command-line arguments, use them to configure 
        the workflow inputs and output settings.
        """
        # Configure the data export operator.
        if self._data_export_args:
            self.dataExportApplet.configure_operator_with_parsed_args( self._data_export_args )

        if self._headless and self._batch_input_args and self._data_export_args:
            logger.info("Beginning Batch Processing")
            self.batchProcessingApplet.run_export_from_parsed_args(self._batch_input_args)
            logger.info("Completed Batch Processing")

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class.
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`.

        Handles that the applet can be seen and used in the gui.
        """
        opDataSelection             = self.dataSelectionApplet.topLevelOperator
        opDataExport                = self.dataExportApplet.topLevelOperator
        opFeatureSelectionBoundaries= self.featureSelectionAppletBoundaries.topLevelOperator
        opPCBoundaries              = self.pcAppletBoundaries.topLevelOperator
        opFeatureSelectionSeeds     = self.featureSelectionAppletSeeds.topLevelOperator
        opPCSeeds                   = self.pcAppletSeeds.topLevelOperator
        opSeeds                     = self.seedsApplet.topLevelOperator
        opWatershedSegmentation     = self.watershedSegmentationApplet.topLevelOperator

        # If no data, nothing else is ready.
        input_ready = len(opDataSelection.ImageGroup) > 0 and not self.dataSelectionApplet.busy

        # The user isn't allowed to touch anything while batch processing is running.
        batch_processing_busy = self.batchProcessingApplet.busy

        # Note: do not disable the seeds and the watershedapplet here, 
        # because otherwise propagate dirty of the seeds won't work
        # and the resetLabelsToSlot() won't be executed when seeds changed in the watershedSegmentationGui 

        # import
        self._shell.setAppletEnabled( self.dataSelectionApplet,\
                not batch_processing_busy )
        # seeds
        self._shell.setAppletEnabled( self.seedsApplet,\
                not batch_processing_busy and input_ready)# and opSeeds.Boundaries.ready())
        # watershed
        self._shell.setAppletEnabled( self.watershedSegmentationApplet,\
                not batch_processing_busy and input_ready)# and opSeeds.WSMethod.ready()
                #and opSeeds.SeedsOutCached.ready() and opSeeds.SeedsOut.ready())
        # export
        self._shell.setAppletEnabled( self.dataExportApplet,\
                not batch_processing_busy and input_ready )#and opSeeds.WSMethod.ready()) #TODO (add the watershedSegementation here)
                #and opWatershedSegmentation.Superpixels.ready())
        # batch processing
        self._shell.setAppletEnabled( self.batchProcessingApplet,\
                not batch_processing_busy and input_ready )


        # feature selection and pixel classification Boundaries
        cumulated_readyness = input_ready

        cumulated_readyness &= not self.batchProcessingApplet.busy # Nothing can be touched while batch mode is executing.

        featureOutput = opFeatureSelectionBoundaries.OutputImage
        features_ready = len(featureOutput) > 0 and  \
            featureOutput[0].ready() and \
            (TinyVector(featureOutput[0].meta.shape) > 0).all()
        cumulated_readyness = cumulated_readyness and features_ready
        self._shell.setAppletEnabled(self.pcAppletBoundaries, cumulated_readyness)

        slot = self.pcAppletBoundaries.topLevelOperator.PredictionProbabilities
        predictions_ready = len(slot) > 0 and \
            slot[0].ready() and \
            (TinyVector(slot[0].meta.shape) > 0).all()

        cumulated_readyness = cumulated_readyness and predictions_ready
        #TODO maybe following applets need to wait for the readyness of the PCBoundaries
        #self._shell.setAppletEnabled(self.thresholdingApplet, cumulated_readyness)

        # Problems can occur if the features or input data are changed during live update mode.
        # Don't let the user do that.
        live_update_active = not opPCBoundaries.FreezePredictions.value

        self._shell.setAppletEnabled(self.dataSelectionApplet, not live_update_active)
        self._shell.setAppletEnabled(self.featureSelectionAppletBoundaries, input_ready and not live_update_active)



        # feature selection and pixel classification Seeds
        cumulated_readyness = input_ready

        cumulated_readyness &= not self.batchProcessingApplet.busy # Nothing can be touched while batch mode is executing.

        featureOutput = opFeatureSelectionSeeds.OutputImage
        features_ready = len(featureOutput) > 0 and  \
            featureOutput[0].ready() and \
            (TinyVector(featureOutput[0].meta.shape) > 0).all()
        cumulated_readyness = cumulated_readyness and features_ready
        self._shell.setAppletEnabled(self.pcAppletSeeds, cumulated_readyness)

        slot = self.pcAppletSeeds.topLevelOperator.PredictionProbabilities
        predictions_ready = len(slot) > 0 and \
            slot[0].ready() and \
            (TinyVector(slot[0].meta.shape) > 0).all()

        cumulated_readyness = cumulated_readyness and predictions_ready
        #TODO maybe following applets need to wait for the readyness of the PCSeeds
        #self._shell.setAppletEnabled(self.thresholdingApplet, cumulated_readyness)

        # Problems can occur if the features or input data are changed during live update mode.
        # Don't let the user do that.
        live_update_active = not opPCSeeds.FreezePredictions.value

        self._shell.setAppletEnabled(self.dataSelectionApplet, not live_update_active)
        self._shell.setAppletEnabled(self.featureSelectionAppletSeeds, input_ready and not live_update_active)




        # Lastly, check for certain "busy" conditions, during which we
        #  should prevent the shell from closing the project.
        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= self.featureSelectionAppletBoundaries.busy
        busy |= self.pcAppletBoundaries.busy
        busy |= self.featureSelectionAppletSeeds.busy
        busy |= self.pcAppletSeeds.busy
        busy |= self.seedsApplet.busy
        busy |= self.watershedSegmentationApplet.busy
        busy |= self.dataExportApplet.busy
        busy |= self.batchProcessingApplet.busy
        self._shell.enableProjectChanges( not busy )






'''
class ObjectClassificationWorkflow(Workflow):
    workflowName = "Object Classification Workflow Base"
    defaultAppletIndex = 1 # show DataSelection by default

    def __init__(self, shell, headless,
                 workflow_cmdline_args,
                 project_creation_args,
                 *args, **kwargs):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs:
            del kwargs['graph']
        super(ObjectClassificationWorkflow, self).__init__(shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs)
        self.stored_pixel_classifier = None
        self.stored_object_classifier = None

        # Parse workflow-specific command-line args
        parser = argparse.ArgumentParser()
        parser.add_argument('--fillmissing', help="use 'fill missing' applet with chosen detection method", choices=['classic', 'svm', 'none'], default='none')
        parser.add_argument('--filter', help="pixel feature filter implementation.", choices=['Original', 'Refactored', 'Interpolated'], default='Original')
        parser.add_argument('--nobatch', help="do not append batch applets", action='store_true', default=False)
        
        parsed_creation_args, unused_args = parser.parse_known_args(project_creation_args)

        self.fillMissing = parsed_creation_args.fillmissing
        self.filter_implementation = parsed_creation_args.filter

        parsed_args, unused_args = parser.parse_known_args(workflow_cmdline_args)
        if parsed_args.fillmissing != 'none' and parsed_creation_args.fillmissing != parsed_args.fillmissing:
            logger.error( "Ignoring --fillmissing cmdline arg.  Can't specify a different fillmissing setting after the project has already been created." )
        
        if parsed_args.filter != 'Original' and parsed_creation_args.filter != parsed_args.filter:
            logger.error( "Ignoring --filter cmdline arg.  Can't specify a different filter setting after the project has already been created." )

        self.batch = not parsed_args.nobatch

        self._applets = []

        self.pcApplet = None
        self.projectMetadataApplet = ProjectMetadataApplet()
        self._applets.append(self.projectMetadataApplet)

        self.setupInputs()
        
        if self.fillMissing != 'none':
            self.fillMissingSlicesApplet = FillMissingSlicesApplet(
                self, "Fill Missing Slices", "Fill Missing Slices", self.fillMissing)
            self._applets.append(self.fillMissingSlicesApplet)

        if isinstance(self, ObjectClassificationWorkflowPixel):
            self.input_types = 'raw'
        elif isinstance(self, ObjectClassificationWorkflowBinary):
            self.input_types = 'raw+binary'
        elif isinstance( self, ObjectClassificationWorkflowPrediction ):
            self.input_types = 'raw+pmaps'
        
        # our main applets
        self.objectExtractionApplet = ObjectExtractionApplet(workflow=self, name = "Object Feature Selection")
        self.objectClassificationApplet = ObjectClassificationApplet(workflow=self)
        self.dataExportApplet = ObjectClassificationDataExportApplet(self, "Object Information Export")
        self.dataExportApplet.set_exporting_operator(self.objectClassificationApplet.topLevelOperator)

        # Customization hooks
        self.dataExportApplet.prepare_for_entire_export = self.prepare_for_entire_export
        #self.dataExportApplet.prepare_lane_for_export = self.prepare_lane_for_export
        self.dataExportApplet.post_process_lane_export = self.post_process_lane_export
        self.dataExportApplet.post_process_entire_export = self.post_process_entire_export
        
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.WorkingDirectory.connect( self.dataSelectionApplet.topLevelOperator.WorkingDirectory )
        
        # See EXPORT_SELECTION_PREDICTIONS and EXPORT_SELECTION_PROBABILITIES, above
        export_selection_names = ['Object Predictions',
                                  'Object Probabilities',
                                  'Blockwise Object Predictions',
                                  'Blockwise Object Probabilities']
        if self.input_types == 'raw':
            # Re-configure to add the pixel probabilities option
            # See EXPORT_SELECTION_PIXEL_PROBABILITIES, above
            export_selection_names.append( 'Pixel Probabilities' )
        opDataExport.SelectionNames.setValue( export_selection_names )

        self._batch_export_args = None
        self._batch_input_args = None
        self._export_args = None
        self.batchProcessingApplet = None
        if self.batch:
            self.batchProcessingApplet = BatchProcessingApplet(self, 
                                                               "Batch Processing", 
                                                               self.dataSelectionApplet, 
                                                               self.dataExportApplet)
    
            if unused_args:
                # Additional export args (specific to the object classification workflow)
                export_arg_parser = argparse.ArgumentParser()
                export_arg_parser.add_argument( "--table_filename", help="The location to export the object feature/prediction CSV file.", required=False )
                export_arg_parser.add_argument( "--export_object_prediction_img", action="store_true" )
                export_arg_parser.add_argument( "--export_object_probability_img", action="store_true" )
                export_arg_parser.add_argument( "--export_pixel_probability_img", action="store_true" )
                
                # TODO: Support this, too, someday?
                #export_arg_parser.add_argument( "--export_object_label_img", action="store_true" )
                
                    
                self._export_args, unused_args = export_arg_parser.parse_known_args(unused_args)
                if self.input_types != 'raw' and self._export_args.export_pixel_probability_img:
                    raise RuntimeError("Invalid command-line argument: \n"\
                                       "--export_pixel_probability_img' can only be used with the combined "\
                                       "'Pixel Classification + Object Classification' workflow.")

                if sum([self._export_args.export_object_prediction_img,
                        self._export_args.export_object_probability_img,
                        self._export_args.export_pixel_probability_img]) > 1:
                    raise RuntimeError("Invalid command-line arguments: Only one type classification output can be exported at a time.")

                # We parse the export setting args first.  All remaining args are considered input files by the input applet.
                self._batch_export_args, unused_args = self.dataExportApplet.parse_known_cmdline_args( unused_args )
                self._batch_input_args, unused_args = self.batchProcessingApplet.parse_known_cmdline_args( unused_args )

                # For backwards compatibility, translate these special args into the standard syntax
                if self._export_args.export_object_prediction_img:
                    self._batch_input_args.export_source = "Object Predictions"
                if self._export_args.export_object_probability_img:
                    self._batch_input_args.export_source = "Object Probabilities"
                if self._export_args.export_pixel_probability_img:
                    self._batch_input_args.export_source = "Pixel Probabilities"


        self.blockwiseObjectClassificationApplet = BlockwiseObjectClassificationApplet(
            self, "Blockwise Object Classification", "Blockwise Object Classification")

        self._applets.append(self.objectExtractionApplet)
        self._applets.append(self.objectClassificationApplet)
        self._applets.append(self.dataExportApplet)
        if self.batchProcessingApplet:
            self._applets.append(self.batchProcessingApplet)
        self._applets.append(self.blockwiseObjectClassificationApplet)

        if unused_args:
            logger.warn("Unused command-line args: {}".format( unused_args ))

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def prepareForNewLane(self, laneIndex):
        if self.pcApplet:
            opPixelClassification = self.pcApplet.topLevelOperator
            if opPixelClassification.classifier_cache.Output.ready() and \
               not opPixelClassification.classifier_cache._dirty:
                self.stored_pixel_classifier = opPixelClassification.classifier_cache.Output.value
            else:
                self.stored_pixel_classifier = None
        
        opObjectClassification = self.objectClassificationApplet.topLevelOperator
        if opObjectClassification.classifier_cache.Output.ready() and \
           not opObjectClassification.classifier_cache._dirty:
            self.stored_object_classifier = opObjectClassification.classifier_cache.Output.value
        else:
            self.stored_object_classifier = None

    def handleNewLanesAdded(self):
        """
        If new lanes were added, then we invalidated our classifiers unecessarily.
        Here, we can restore the classifier so it doesn't need to be retrained.
        """
        # If we have stored classifiers, restore them into the workflow now.
        if self.stored_pixel_classifier:
            opPixelClassification = self.pcApplet.topLevelOperator
            opPixelClassification.classifier_cache.forceValue(self.stored_pixel_classifier)
            # Release reference
            self.stored_pixel_classifier = None

        if self.stored_object_classifier:
            opObjectClassification = self.objectClassificationApplet.topLevelOperator
            opObjectClassification.classifier_cache.forceValue(self.stored_object_classifier)
            # Release reference
            self.stored_object_classifier = None

    def connectLane(self, laneIndex):
        rawslot, binaryslot = self.connectInputs(laneIndex)

        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)

        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)
        opObjClassification = self.objectClassificationApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)
        opBlockwiseObjectClassification = self.blockwiseObjectClassificationApplet.topLevelOperator.getLane(laneIndex)

        opObjExtraction.RawImage.connect(rawslot)
        opObjExtraction.BinaryImage.connect(binaryslot)

        opObjClassification.RawImages.connect(rawslot)
        opObjClassification.BinaryImages.connect(binaryslot)

        opObjClassification.SegmentationImages.connect(opObjExtraction.LabelImage)
        opObjClassification.ObjectFeatures.connect(opObjExtraction.RegionFeatures)
        opObjClassification.ComputedFeatureNames.connect(opObjExtraction.Features)

        # Data Export connections
        opDataExport.RawData.connect( opData.ImageGroup[0] )
        opDataExport.RawDatasetInfo.connect( opData.DatasetGroup[0] )
        opDataExport.Inputs.resize(4)
        opDataExport.Inputs[EXPORT_SELECTION_PREDICTIONS].connect( opObjClassification.UncachedPredictionImages )
        opDataExport.Inputs[EXPORT_SELECTION_PROBABILITIES].connect( opObjClassification.ProbabilityChannelImage )
        opDataExport.Inputs[EXPORT_SELECTION_BLOCKWISE_PREDICTIONS].connect( opBlockwiseObjectClassification.PredictionImage )
        opDataExport.Inputs[EXPORT_SELECTION_BLOCKWISE_PROBABILITIES].connect( opBlockwiseObjectClassification.ProbabilityChannelImage )
        
        if self.input_types == 'raw':
            # Append the prediction probabilities to the list of slots that can be exported.
            opDataExport.Inputs.resize(5)
            # Pull from this slot since the data has already been through the Op5 operator
            # (All data in the export operator must have matching spatial dimensions.)
            opThreshold = self.thresholdingApplet.topLevelOperator.getLane(laneIndex)
            opDataExport.Inputs[EXPORT_SELECTION_PIXEL_PROBABILITIES].connect( opThreshold.InputImage )

        opObjClassification = self.objectClassificationApplet.topLevelOperator.getLane(laneIndex)
        opBlockwiseObjectClassification = self.blockwiseObjectClassificationApplet.topLevelOperator.getLane(laneIndex)

        opBlockwiseObjectClassification.RawImage.connect(opObjClassification.RawImages)
        opBlockwiseObjectClassification.BinaryImage.connect(opObjClassification.BinaryImages)
        opBlockwiseObjectClassification.Classifier.connect(opObjClassification.Classifier)
        opBlockwiseObjectClassification.LabelsCount.connect(opObjClassification.NumLabels)
        opBlockwiseObjectClassification.SelectedFeatures.connect(opObjClassification.SelectedFeatures)
        
    def onProjectLoaded(self, projectManager):
        if not self._headless:
            return
        
        if not (self._batch_input_args and self._batch_export_args):
            logger.warn("Was not able to understand the batch mode command-line arguments.")
        
        # Check for problems: Is the project file ready to use?
        opObjClassification = self.objectClassificationApplet.topLevelOperator
        if not opObjClassification.Classifier.ready():
            logger.error( "Can't run batch prediction.\n"
                          "Couldn't obtain a classifier from your project file: {}.\n"
                          "Please make sure your project is fully configured with a trained classifier."
                          .format(projectManager.currentProjectPath) )
            return

        # Configure the data export operator.
        if self._batch_export_args:
            self.dataExportApplet.configure_operator_with_parsed_args( self._batch_export_args )

        if self._export_args:        
            csv_filename = self._export_args.table_filename
            if csv_filename:
                # The user wants to override the csv export location via 
                #  the command-line arguments. Apply the new setting to the operator.
                settings, selected_features = self.objectClassificationApplet.topLevelOperator.get_table_export_settings()
                if settings is None:
                    raise RuntimeError("You can't export the CSV object table unless you configure it in the GUI first.")
                assert 'file path' in settings, "Expected settings dict to contain a 'file path' key.  Did you rename that key?"
                settings['file path'] = csv_filename
                self.objectClassificationApplet.topLevelOperator.configure_table_export_settings( settings, selected_features )

        # Configure the batch data selection operator.
        if self._batch_input_args and self._batch_input_args.raw_data:
            logger.info("Beginning Batch Processing")
            self.batchProcessingApplet.run_export_from_parsed_args(self._batch_input_args)
            logger.info("Completed Batch Processing")

    def prepare_for_entire_export(self):
        # Un-freeze the workflow so we don't just get a bunch of zeros from the caches when we ask for results
        if self.pcApplet:
            self.pc_freeze_status = self.pcApplet.topLevelOperator.FreezePredictions.value
            self.pcApplet.topLevelOperator.FreezePredictions.setValue(False)
        self.oc_freeze_status = self.objectClassificationApplet.topLevelOperator.FreezePredictions.value
        self.objectClassificationApplet.topLevelOperator.FreezePredictions.setValue(False)

    def post_process_entire_export(self):
        # Unfreeze.
        if self.pcApplet:
            self.pcApplet.topLevelOperator.FreezePredictions.setValue(self.pc_freeze_status)
        self.objectClassificationApplet.topLevelOperator.FreezePredictions.setValue(self.oc_freeze_status)

    def post_process_lane_export(self, lane_index):
        # FIXME: This probably only works for the non-blockwise export slot.
        #        We should assert that the user isn't using the blockwise slot.
        settings, selected_features = self.objectClassificationApplet.topLevelOperator.get_table_export_settings()
        if settings:
            raw_dataset_info = self.dataSelectionApplet.topLevelOperator.DatasetGroup[lane_index][0].value
            if raw_dataset_info.location == DatasetInfo.Location.FileSystem:
                filename_suffix = raw_dataset_info.nickname
            else:
                filename_suffix = str(lane_index)
            req = self.objectClassificationApplet.topLevelOperator.export_object_data(
                        lane_index, 
                        # FIXME: Even in non-headless mode, we can't show the gui because we're running in a non-main thread.
                        #        That's not a huge deal, because there's still a progress bar for the overall export.
                        show_gui=False, 
                        filename_suffix=filename_suffix)
            req.wait()
         
    def getHeadlessOutputSlot(self, slotId):
        if slotId == "BatchPredictionImage":
            return self.opBatchClassify.PredictionImage
        raise Exception("Unknown headless output slot")

    def handleAppletStateUpdateRequested(self, upstream_ready=False):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        
        This method will be called by the child classes with the result of their
        own applet readyness findings as keyword argument.
        """

        # all workflows have these applets in common:

        # object feature selection
        # object classification
        # object prediction export
        # blockwise classification
        # batch input
        # batch prediction export

        self._shell.setAppletEnabled(self.dataSelectionApplet, not self.batchProcessingApplet.busy)

        cumulated_readyness = upstream_ready
        cumulated_readyness &= not self.batchProcessingApplet.busy # Nothing can be touched while batch mode is executing.

        self._shell.setAppletEnabled(self.objectExtractionApplet, cumulated_readyness)

        object_features_ready = ( self.objectExtractionApplet.topLevelOperator.Features.ready()
                                  and len(self.objectExtractionApplet.topLevelOperator.Features.value) > 0 )
        cumulated_readyness = cumulated_readyness and object_features_ready
        self._shell.setAppletEnabled(self.objectClassificationApplet, cumulated_readyness)

        opObjectClassification = self.objectClassificationApplet.topLevelOperator
        invalid_classifier = opObjectClassification.classifier_cache.fixAtCurrent.value and \
                             opObjectClassification.classifier_cache.Output.ready() and\
                             opObjectClassification.classifier_cache.Output.value is None

        invalid_classifier |= not opObjectClassification.NumLabels.ready() or \
                              opObjectClassification.NumLabels.value < 2

        object_classification_ready = object_features_ready and not invalid_classifier

        cumulated_readyness = cumulated_readyness and object_classification_ready
        self._shell.setAppletEnabled(self.dataExportApplet, cumulated_readyness)

        if self.batch:
            object_prediction_ready = True  # TODO is that so?
            cumulated_readyness = cumulated_readyness and object_prediction_ready

            self._shell.setAppletEnabled(self.blockwiseObjectClassificationApplet, cumulated_readyness)
            self._shell.setAppletEnabled(self.batchProcessingApplet, cumulated_readyness)

        # Lastly, check for certain "busy" conditions, during which we 
        # should prevent the shell from closing the project.
        #TODO implement
        busy = False
        self._shell.enableProjectChanges( not busy )

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

    def postprocessClusterSubResult(self, roi, result, blockwise_fileset):
        """
        This function is only used by special cluster scripts.
        
        When the batch-processing mechanism was rewritten, this function broke.
        It could probably be fixed with minor changes.
        """
        assert sys.version_info.major == 2, "Alert! This function has not been " \
        "tested under python 3. Please remove this assertion, and be wary of any " \
        "strange behavior you encounter"

        # TODO: Here, we hard-code to select from the first lane only.
        opBatchClassify = self.opBatchClassify[0]
        
        from lazyflow.utility.io_uti.blockwiseFileset import vectorized_pickle_dumps
        # Assume that roi always starts as a multiple of the blockshape
        block_shape = opBatchClassify.get_blockshape()
        assert all(block_shape == blockwise_fileset.description.sub_block_shape), "block shapes don't match"
        assert all((roi[0] % block_shape) == 0), "Sub-blocks must exactly correspond to the blockwise object classification blockshape"
        sub_block_index = roi[0] // blockwise_fileset.description.sub_block_shape

        sub_block_start = sub_block_index
        sub_block_stop = sub_block_start + 1
        sub_block_roi = (sub_block_start, sub_block_stop)
        
        # FIRST, remove all objects that lie outside the block (i.e. remove the ones in the halo)
        region_features = opBatchClassify.BlockwiseRegionFeatures( *sub_block_roi ).wait()
        region_features_dict = region_features.flat[0]
        region_centers = region_features_dict['Default features']['RegionCenter']

        opBlockPipeline = opBatchClassify._blockPipelines[ tuple(roi[0]) ]

        # Compute the block offset within the image coordinates
        halo_roi = opBlockPipeline._halo_roi

        translated_region_centers = region_centers + halo_roi[0][1:-1]

        # TODO: If this is too slow, vectorize this
        mask = numpy.zeros( region_centers.shape[0], dtype=numpy.bool_ )
        for index, translated_region_center in enumerate(translated_region_centers):
            # FIXME: Here we assume t=0 and c=0
            mask[index] = opBatchClassify.is_in_block( roi[0], (0,) + tuple(translated_region_center) + (0,) )
        
        # Always exclude the first object (it's the background??)
        mask[0] = False
        
        # Remove all 'negative' predictions, emit only 'positive' predictions
        # FIXME: Don't hardcode this?
        POSITIVE_LABEL = 2
        objectwise_predictions = opBlockPipeline.ObjectwisePredictions([]).wait()[0]
        assert objectwise_predictions.shape == mask.shape
        mask[objectwise_predictions != POSITIVE_LABEL] = False

        filtered_features = {}
        for feature_group, feature_dict in region_features_dict.items():
            filtered_group = filtered_features[feature_group] = {}
            for feature_name, feature_array in feature_dict.items():
                filtered_group[feature_name] = feature_array[mask]

        # SECOND, translate from block-local coordinates to global (file) coordinates.
        # Unfortunately, we've got multiple translations to perform here:
        # Coordinates in the region features are relative to their own block INCLUDING HALO,
        #  so we need to add the start of the block-with-halo as an offset.
        # BUT the image itself may be offset relative to the BlockwiseFileset coordinates
        #  (due to the view_origin setting), so we also need to add an offset for that, too

        # Get the image offset relative to the file coordinates
        image_offset = blockwise_fileset.description.view_origin
        
        total_offset_5d = halo_roi[0] + image_offset
        total_offset_3d = total_offset_5d[1:-1]

        filtered_features["Default features"]["RegionCenter"] += total_offset_3d
        filtered_features["Default features"]["Coord<Minimum>"] += total_offset_3d
        filtered_features["Default features"]["Coord<Maximum>"] += total_offset_3d

        # Finally, write the features to hdf5
        h5File = blockwise_fileset.getOpenHdf5FileForBlock( roi[0] )
        if 'pickled_region_features' in h5File:
            del h5File['pickled_region_features']

        # Must use str dtype
        dtype = h5py.new_vlen(str)
        dataset = h5File.create_dataset( 'pickled_region_features', shape=(1,), dtype=dtype )
        pickled_features = vectorized_pickle_dumps(numpy.array((filtered_features,)))
        dataset[0] = pickled_features

        object_centers_xyz = filtered_features["Default features"]["RegionCenter"].astype(int)
        object_min_coords_xyz = filtered_features["Default features"]["Coord<Minimum>"].astype(int)
        object_max_coords_xyz = filtered_features["Default features"]["Coord<Maximum>"].astype(int)
        object_sizes = filtered_features["Default features"]["Count"][:,0].astype(int)

        # Also, write out selected features as a 'point cloud' csv file.
        # (Store the csv file next to this block's h5 file.)
        dataset_directory = blockwise_fileset.getDatasetDirectory(roi[0])
        pointcloud_path = os.path.join( dataset_directory, "block-pointcloud.csv" )
        
        logger.info("Writing to csv: {}".format( pointcloud_path ))
        with open(pointcloud_path, "w") as fout:
            csv_writer = csv.DictWriter(fout, OUTPUT_COLUMNS, **CSV_FORMAT)
            csv_writer.writeheader()
        
            for obj_id in range(len(object_sizes)):
                fields = {}
                fields["x_px"], fields["y_px"], fields["z_px"], = object_centers_xyz[obj_id]
                fields["min_x_px"], fields["min_y_px"], fields["min_z_px"], = object_min_coords_xyz[obj_id]
                fields["max_x_px"], fields["max_y_px"], fields["max_z_px"], = object_max_coords_xyz[obj_id]
                fields["size_px"] = object_sizes[obj_id]

                csv_writer.writerow( fields )
                #fout.flush()
        
        logger.info("FINISHED csv export")

'''
'''

class ObjectClassificationWorkflowPixel(ObjectClassificationWorkflow):
    workflowName = "Pixel calssification on RawData for Boundaries and\
            Pixel Classification + Object Classification on Raw Data for Seeds; then WatershedSegmentation on it"
    workflowDisplayName = "Pixel Classification + Object Classification + Watershed"

    def setupInputs(self):
        data_instructions = 'Use the "Raw Data" tab on the right to load your intensity image(s).'
        
        self.dataSelectionApplet = DataSelectionApplet( self, 
                                                        "Input Data", 
                                                        "Input Data", 
                                                        batchDataGui=False,
                                                        forceAxisOrder=None, 
                                                        instructionText=data_instructions )
        opData = self.dataSelectionApplet.topLevelOperator
        opData.DatasetRoles.setValue(['Raw Data'])

        self.featureSelectionApplet = FeatureSelectionApplet(
            self,
            "Feature Selection",
            "FeatureSelections",
            filter_implementation=self.filter_implementation
        )

        self.pcApplet = PixelClassificationApplet(
            self, "PixelClassification")
        self.thresholdingApplet = ThresholdTwoLevelsApplet(
            self, "Thresholding", "ThresholdTwoLevels")

        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.pcApplet)
        self._applets.append(self.thresholdingApplet)


    def connectInputs(self, laneIndex):
               
        op5raw = OpReorderAxes(parent=self)
        op5raw.AxisOrder.setValue("txyzc")
        op5pred = OpReorderAxes(parent=self)
        op5pred.AxisOrder.setValue("txyzc")
        op5threshold = OpReorderAxes(parent=self)
        op5threshold.AxisOrder.setValue("txyzc")
        
        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)
        opClassify = self.pcApplet.topLevelOperator.getLane(laneIndex)
        opThreshold = self.thresholdingApplet.topLevelOperator.getLane(laneIndex)

        if self.fillMissing !='none':
            opFillMissingSlices = self.fillMissingSlicesApplet.topLevelOperator.getLane(laneIndex)
            opFillMissingSlices.Input.connect(opData.Image)
            rawslot = opFillMissingSlices.Output
        else:
            rawslot = opData.Image

        opTrainingFeatures.InputImage.connect(rawslot)

        opClassify.InputImages.connect(rawslot)
        opClassify.FeatureImages.connect(opTrainingFeatures.OutputImage)
        opClassify.CachedFeatureImages.connect(opTrainingFeatures.CachedOutputImage)

        op5raw.Input.connect(rawslot)
        op5pred.Input.connect(opClassify.PredictionProbabilities)

        opThreshold.RawInput.connect(op5raw.Output)
        opThreshold.InputImage.connect(op5pred.Output)
        opThreshold.InputChannelColors.connect( opClassify.PmapColors )

        op5threshold.Input.connect(opThreshold.CachedOutput)

        return op5raw.Output, op5threshold.Output

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        input_ready = self._inputReady(1)
        cumulated_readyness = input_ready

        cumulated_readyness &= not self.batchProcessingApplet.busy # Nothing can be touched while batch mode is executing.

        opFeatureSelection = self.featureSelectionApplet.topLevelOperator
        featureOutput = opFeatureSelection.OutputImage
        features_ready = len(featureOutput) > 0 and  \
            featureOutput[0].ready() and \
            (TinyVector(featureOutput[0].meta.shape) > 0).all()
        cumulated_readyness = cumulated_readyness and features_ready
        self._shell.setAppletEnabled(self.pcApplet, cumulated_readyness)

        slot = self.pcApplet.topLevelOperator.PredictionProbabilities
        predictions_ready = len(slot) > 0 and \
            slot[0].ready() and \
            (TinyVector(slot[0].meta.shape) > 0).all()

        cumulated_readyness = cumulated_readyness and predictions_ready
        self._shell.setAppletEnabled(self.thresholdingApplet, cumulated_readyness)

        # Problems can occur if the features or input data are changed during live update mode.
        # Don't let the user do that.
        opPixelClassification = self.pcApplet.topLevelOperator
        live_update_active = not opPixelClassification.FreezePredictions.value

        self._shell.setAppletEnabled(self.dataSelectionApplet, not live_update_active)
        self._shell.setAppletEnabled(self.featureSelectionApplet, input_ready and not live_update_active)

        super(ObjectClassificationWorkflowPixel, self).handleAppletStateUpdateRequested(upstream_ready=cumulated_readyness)
'''

'''

class ObjectClassificationWorkflowBinary(ObjectClassificationWorkflow):
    workflowName = "Object Classification (from binary image)"
    workflowDisplayName = "Object Classification [Inputs: Raw Data, Segmentation]"

    def setupInputs(self):
        data_instructions = 'Use the "Raw Data" tab to load your intensity image(s).\n\n'\
                            'Use the "Segmentation Image" tab to load your binary mask image(s).'

        self.dataSelectionApplet = DataSelectionApplet( self,
                                                        "Input Data",
                                                        "Input Data",
                                                        batchDataGui=False,
                                                        forceAxisOrder=['txyzc'],
                                                        instructionText=data_instructions )

        opData = self.dataSelectionApplet.topLevelOperator
        opData.DatasetRoles.setValue(['Raw Data', 'Segmentation Image'])
        self._applets.append(self.dataSelectionApplet)

    def connectInputs(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        if self.fillMissing != 'none':
            opFillMissingSlices = self.fillMissingSlicesApplet.topLevelOperator.getLane(laneIndex)
            opFillMissingSlices.Input.connect(opData.ImageGroup[0])
            rawslot = opFillMissingSlices.Output
        else:
            rawslot = opData.ImageGroup[0]

        return rawslot, opData.ImageGroup[1]

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        input_ready = self._inputReady(2)

        super(ObjectClassificationWorkflowBinary, self).handleAppletStateUpdateRequested(upstream_ready=input_ready)

'''
'''

class ObjectClassificationWorkflowPrediction(ObjectClassificationWorkflow):
    workflowName = "Object Classification (from prediction image)"
    workflowDisplayName = "Object Classification [Inputs: Raw Data, Pixel Prediction Map]"

    def setupInputs(self):
        data_instructions = 'Use the "Raw Data" tab to load your intensity image(s).\n\n'\
                            'Use the "Prediction Maps" tab to load your pixel-wise probability image(s).'
        
        self.dataSelectionApplet = DataSelectionApplet( self,
                                                        "Input Data",
                                                        "Input Data",
                                                        batchDataGui=False,
                                                        forceAxisOrder=['txyzc'],
                                                        instructionText=data_instructions )

        opData = self.dataSelectionApplet.topLevelOperator
        opData.DatasetRoles.setValue(['Raw Data', 'Prediction Maps'])
        self._applets.append(self.dataSelectionApplet)

        self.thresholdingApplet = ThresholdTwoLevelsApplet(self, "Threshold and Size Filter", "ThresholdTwoLevels")
        self._applets.append(self.thresholdingApplet)

    def connectInputs(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTwoLevelThreshold = self.thresholdingApplet.topLevelOperator.getLane(laneIndex)

        op5raw = OpReorderAxes(parent=self)
        op5raw.AxisOrder.setValue("txyzc")
        op5predictions = OpReorderAxes(parent=self)
        op5predictions.AxisOrder.setValue("txyzc")

        if self.fillMissing != 'none':
            opFillMissingSlices = self.fillMissingSlicesApplet.topLevelOperator.getLane(laneIndex)
            opFillMissingSlices.Input.connect(opData.ImageGroup[0])
            rawslot = opFillMissingSlices.Output
        else:
            rawslot = opData.ImageGroup[0]

        op5raw.Input.connect(rawslot)
        op5predictions.Input.connect(opData.ImageGroup[1])

        opTwoLevelThreshold.RawInput.connect(op5raw.Output)
        opTwoLevelThreshold.InputImage.connect(op5predictions.Output)

        op5Binary = OpReorderAxes(parent=self)
        op5Binary.AxisOrder.setValue("txyzc")
        op5Binary.Input.connect(opTwoLevelThreshold.CachedOutput)

        return op5raw.Output, op5Binary.Output

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        input_ready = self._inputReady(2)
        cumulated_readyness = input_ready
        cumulated_readyness &= not self.batchProcessingApplet.busy # Nothing can be touched while batch mode is executing.
        self._shell.setAppletEnabled(self.thresholdingApplet, cumulated_readyness)

        thresholding_ready = True  # is that so?
        cumulated_readyness = cumulated_readyness and thresholding_ready
        super(ObjectClassificationWorkflowPrediction, self).handleAppletStateUpdateRequested(upstream_ready=cumulated_readyness)
'''


if __name__ == "__main__":
    from sys import argv
    w = PixelObjectWatershedWorkflow(True, argv)
