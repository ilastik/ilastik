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
from functools import partial
import numpy as np

from ilastik.workflow import Workflow

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.wsdt import WsdtApplet
from ilastik.applets.edgeTraining import EdgeTrainingApplet
from ilastik.applets.multicut import MulticutApplet
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet
from ilastik.applets.batchProcessing import BatchProcessingApplet

from lazyflow.graph import Graph
from lazyflow.operators import OpSimpleStacker
from lazyflow.operators.generic import OpConvertDtype
from lazyflow.operators.valueProviders import OpPrecomputedInput

import logging
logger = logging.getLogger(__name__)

class MulticutWorkflow(Workflow):
    workflowName = "Multicut"
    workflowDescription = "A workflow based around training a classifier for merging superpixels and joining them via multicut."
    defaultAppletIndex = 0 # show DataSelection by default

    DATA_ROLE_RAW = 0
    DATA_ROLE_PROBABILITIES = 1
    DATA_ROLE_SUPERPIXELS = 2
    DATA_ROLE_GROUNDTRUTH = 3
    ROLE_NAMES = ['Raw Data', 'Probabilities', 'Superpixels', 'Groundtruth']
    EXPORT_NAMES = ['Multicut Segmentation']

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_workflow, *args, **kwargs):
        self.stored_classifier = None
        
        # Create a graph to be shared by all operators
        graph = Graph()

        super(MulticutWorkflow, self).__init__( shell, headless, workflow_cmdline_args, project_creation_workflow, graph=graph, *args, **kwargs)
        self._applets = []

        # -- DataSelection applet
        #
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", forceAxisOrder=['zyxc', 'yxc'])

        # Dataset inputs
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( self.ROLE_NAMES )

        # -- Watershed applet
        #
        self.wsdtApplet = WsdtApplet(self, "DT Watershed", "DT Watershed")

        # -- Edge training applet
        # 
        self.edgeTrainingApplet = EdgeTrainingApplet(self, "Edge Training", "Edge Training")
        opEdgeTraining = self.edgeTrainingApplet.topLevelOperator
        DEFAULT_FEATURES = { self.ROLE_NAMES[self.DATA_ROLE_RAW]: ['standard_edge_mean'] }
        opEdgeTraining.FeatureNames.setValue( DEFAULT_FEATURES )

        # -- Multicut applet
        #
        self.multicutApplet = MulticutApplet(self, "Multicut Segmentation", "Multicut Segmentation")

        # -- DataExport applet
        #
        self.dataExportApplet = DataExportApplet(self, "Data Export")
        self.dataExportApplet.prepare_for_entire_export = self.prepare_for_entire_export
        self.dataExportApplet.post_process_entire_export = self.post_process_entire_export

        # Configure global DataExport settings
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.WorkingDirectory.connect( opDataSelection.WorkingDirectory )
        opDataExport.SelectionNames.setValue( self.EXPORT_NAMES )

        # -- BatchProcessing applet
        #
        self.batchProcessingApplet = BatchProcessingApplet(self,
                                                           "Batch Processing",
                                                           self.dataSelectionApplet,
                                                           self.dataExportApplet)

        # -- Expose applets to shell
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.wsdtApplet)
        self._applets.append(self.edgeTrainingApplet)
        self._applets.append(self.multicutApplet)
        self._applets.append(self.dataExportApplet)
        self._applets.append(self.batchProcessingApplet)

        # -- Parse command-line arguments
        #    (Command-line args are applied in onProjectLoaded(), below.)
        if workflow_cmdline_args:
            self._data_export_args, unused_args = self.dataExportApplet.parse_known_cmdline_args( workflow_cmdline_args )
            self._batch_input_args, unused_args = self.batchProcessingApplet.parse_known_cmdline_args( unused_args )
        else:
            unused_args = None
            self._batch_input_args = None
            self._data_export_args = None

        if unused_args:
            logger.warning("Unused command-line args: {}".format( unused_args ))
        
        if not self._headless:
            shell.currentAppletChanged.connect( self.handle_applet_changed )

    def prepareForNewLane(self, laneIndex):
        """
        Overridden from Workflow base class.
        Called immediately before a new lane is added to the workflow.
        """
        opEdgeTraining = self.edgeTrainingApplet.topLevelOperator
        opClassifierCache = opEdgeTraining.opClassifierCache

        # When the new lane is added, dirty notifications will propagate throughout the entire graph.
        # This means the classifier will be marked 'dirty' even though it is still usable.
        # Before that happens, let's store the classifier, so we can restore it in handleNewLanesAdded(), below.
        if opClassifierCache.Output.ready() and \
           not opClassifierCache._dirty:
            self.stored_classifier = opClassifierCache.Output.value
        else:
            self.stored_classifier = None
        
    def connectLane(self, laneIndex):
        """
        Override from base class.
        """
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opWsdt = self.wsdtApplet.topLevelOperator.getLane(laneIndex)
        opEdgeTraining = self.edgeTrainingApplet.topLevelOperator.getLane(laneIndex)
        opMulticut = self.multicutApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)

        opConvertRaw = OpConvertDtype( parent=self )
        opConvertRaw.ConversionDtype.setValue( np.float32 )
        opConvertRaw.Input.connect( opDataSelection.ImageGroup[self.DATA_ROLE_RAW] )

        opConvertProbabilities = OpConvertDtype( parent=self )
        opConvertProbabilities.ConversionDtype.setValue( np.float32 )
        opConvertProbabilities.Input.connect( opDataSelection.ImageGroup[self.DATA_ROLE_PROBABILITIES] )

        # watershed inputs
        opWsdt.RawData.connect( opDataSelection.ImageGroup[self.DATA_ROLE_RAW] )
        opWsdt.Input.connect( opDataSelection.ImageGroup[self.DATA_ROLE_PROBABILITIES] )

        # Actual computation is done with both RawData and Probabilities
        opStackRawAndVoxels = OpSimpleStacker( parent=self )
        opStackRawAndVoxels.Images.resize(2)
        opStackRawAndVoxels.Images[0].connect( opConvertRaw.Output )
        opStackRawAndVoxels.Images[1].connect( opConvertProbabilities.Output )
        opStackRawAndVoxels.AxisFlag.setValue('c')

        # If superpixels are available from a file, use it.
        opSuperpixelsSelect = OpPrecomputedInput( ignore_dirty_input=True, parent=self )
        opSuperpixelsSelect.PrecomputedInput.connect( opDataSelection.ImageGroup[self.DATA_ROLE_SUPERPIXELS] )
        opSuperpixelsSelect.SlowInput.connect( opWsdt.Superpixels )

        # If the superpixel file changes, then we have to remove the training labels from the image
        def handle_new_superpixels( *args ):
            opEdgeTraining.handle_dirty_superpixels( opEdgeTraining.Superpixels )
        opDataSelection.ImageGroup[self.DATA_ROLE_SUPERPIXELS].notifyReady( handle_new_superpixels )
        opDataSelection.ImageGroup[self.DATA_ROLE_SUPERPIXELS].notifyUnready( handle_new_superpixels )

        # edge training inputs
        opEdgeTraining.RawData.connect( opDataSelection.ImageGroup[self.DATA_ROLE_RAW] ) # Used for visualization only
        opEdgeTraining.VoxelData.connect( opStackRawAndVoxels.Output )
        opEdgeTraining.Superpixels.connect( opSuperpixelsSelect.Output )
        opEdgeTraining.GroundtruthSegmentation.connect( opDataSelection.ImageGroup[self.DATA_ROLE_GROUNDTRUTH] )

        # multicut inputs
        opMulticut.Superpixels.connect( opEdgeTraining.Superpixels )
        opMulticut.Rag.connect( opEdgeTraining.Rag )
        opMulticut.EdgeProbabilities.connect( opEdgeTraining.EdgeProbabilities )
        opMulticut.EdgeProbabilitiesDict.connect( opEdgeTraining.EdgeProbabilitiesDict )
        opMulticut.RawData.connect( opDataSelection.ImageGroup[self.DATA_ROLE_RAW] )

        # DataExport inputs
        opDataExport.RawData.connect( opDataSelection.ImageGroup[self.DATA_ROLE_RAW] )
        opDataExport.RawDatasetInfo.connect( opDataSelection.DatasetGroup[self.DATA_ROLE_RAW] )        
        opDataExport.Inputs.resize( len(self.EXPORT_NAMES) )
        opDataExport.Inputs[0].connect( opMulticut.Output )
        for slot in opDataExport.Inputs:
            assert slot.upstream_slot is not None

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
            # Make sure the watershed can be computed if necessary.
            opWsdt = self.wsdtApplet.topLevelOperator
            opWsdt.FreezeCache.setValue( False )

            # Error checks
            if (self._batch_input_args.raw_data
            and len(self._batch_input_args.probabilities) != len(self._batch_input_args.raw_data) ):
                msg = "Error: Your input file lists are malformed.\n"
                msg += "Usage: run_ilastik.sh --headless --raw_data <file1> <file2>... --probabilities <file1> <file2>..."
                sys.exit(msg)

            if  (self._batch_input_args.superpixels
            and (not self._batch_input_args.raw_data or len(self._batch_input_args.superpixels) != len(self._batch_input_args.raw_data) ) ):
                msg = "Error: Wrong number of superpixel file inputs."
                sys.exit(msg)

            logger.info("Beginning Batch Processing")
            self.batchProcessingApplet.run_export_from_parsed_args(self._batch_input_args)
            logger.info("Completed Batch Processing")

    def prepare_for_entire_export(self):
        """
        Assigned to DataExportApplet.prepare_for_entire_export
        (See above.)
        """
        # While exporting results, the segmentation cache should not be "frozen"
        self.freeze_status = self.edgeTrainingApplet.topLevelOperator.FreezeCache.value
        self.edgeTrainingApplet.topLevelOperator.FreezeCache.setValue(False)

    def post_process_entire_export(self):
        """
        Assigned to DataExportApplet.post_process_entire_export
        (See above.)
        """
        # After export is finished, re-freeze the segmentation cache.
        self.edgeTrainingApplet.topLevelOperator.FreezeCache.setValue(self.freeze_status)


    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opWsdt = self.wsdtApplet.topLevelOperator
        opEdgeTraining = self.edgeTrainingApplet.topLevelOperator
        opMulticut = self.multicutApplet.topLevelOperator
        opDataExport = self.dataExportApplet.topLevelOperator

        # If no data, nothing else is ready.
        input_ready = len(opDataSelection.ImageGroup) > 0 and not self.dataSelectionApplet.busy

        superpixels_available_from_file = False
        lane_index = self._shell.currentImageIndex
        if lane_index != -1:
            superpixels_available_from_file = opDataSelection.ImageGroup[lane_index][self.DATA_ROLE_SUPERPIXELS].ready()

        superpixels_ready = opEdgeTraining.Superpixels.ready()

        # The user isn't allowed to touch anything while batch processing is running.
        batch_processing_busy = self.batchProcessingApplet.busy

        self._shell.setAppletEnabled( self.dataSelectionApplet,   not batch_processing_busy )
        self._shell.setAppletEnabled( self.wsdtApplet,            not batch_processing_busy and input_ready and not superpixels_available_from_file )
        self._shell.setAppletEnabled( self.edgeTrainingApplet,    not batch_processing_busy and input_ready and superpixels_ready )
        self._shell.setAppletEnabled( self.multicutApplet,        not batch_processing_busy and input_ready and opEdgeTraining.EdgeProbabilities.ready() )
        self._shell.setAppletEnabled( self.dataExportApplet,      not batch_processing_busy and input_ready and opMulticut.Output.ready())
        self._shell.setAppletEnabled( self.batchProcessingApplet, not batch_processing_busy and input_ready )

        # Lastly, check for certain "busy" conditions, during which we
        #  should prevent the shell from closing the project.
        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= self.wsdtApplet.busy
        busy |= self.edgeTrainingApplet.busy
        busy |= self.multicutApplet.busy
        busy |= self.dataExportApplet.busy
        busy |= self.batchProcessingApplet.busy
        self._shell.enableProjectChanges( not busy )

    def handle_applet_changed(self, prev_index, current_index):
        if prev_index != current_index:
            # If the user is viewing an applet downstream of the WSDT applet,
            # make sure the superpixels are always up-to-date.
            opWsdt = self.wsdtApplet.topLevelOperator
            opWsdt.FreezeCache.setValue( self._shell.currentAppletIndex <= self.applets.index( self.wsdtApplet ) )

            # Same for the multicut segmentation
            opMulticut = self.multicutApplet.topLevelOperator
            opMulticut.FreezeCache.setValue( self._shell.currentAppletIndex <= self.applets.index( self.multicutApplet ) )
