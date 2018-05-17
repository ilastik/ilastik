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
import argparse
import numpy as np

from ilastik.workflow import Workflow

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.wsdt import WsdtApplet
from ilastik.applets.edgeTrainingWithMulticut import EdgeTrainingWithMulticutApplet
from ilastik.applets.edgeTrainingWithMulticut.opEdgeTrainingWithMulticut import OpEdgeTrainingWithMulticut
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet
from ilastik.applets.batchProcessing import BatchProcessingApplet

from lazyflow.graph import Graph
from lazyflow.operators import OpRelabelConsecutive, OpBlockedArrayCache, OpSimpleStacker
from lazyflow.operators.generic import OpConvertDtype, OpPixelOperator
from lazyflow.operators.valueProviders import OpPrecomputedInput

import logging
logger = logging.getLogger(__name__)

class EdgeTrainingWithMulticutWorkflow(Workflow):
    workflowName = "Edge Training With Multicut"
    workflowDisplayName = "Boundary-based Segmentation with Multicut"

    workflowDescription = "Segment images based on boundary information: train an edge classifier and apply multicut to the results."
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

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):
        self.stored_classifier = None

        # Create a graph to be shared by all operators
        graph = Graph()

        super(EdgeTrainingWithMulticutWorkflow, self).__init__( shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs)
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

        # -- Edge training AND Multicut applet
        # 
        self.edgeTrainingWithMulticutApplet = EdgeTrainingWithMulticutApplet(self, "Training and Multicut", "Training and Multicut")
        opEdgeTrainingWithMulticut = self.edgeTrainingWithMulticutApplet.topLevelOperator
        DEFAULT_FEATURES = { self.ROLE_NAMES[self.DATA_ROLE_RAW]: ["standard_edge_mean"] }
        opEdgeTrainingWithMulticut.FeatureNames.setValue( DEFAULT_FEATURES )

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
        self._applets.append(self.edgeTrainingWithMulticutApplet)
        self._applets.append(self.dataExportApplet)
        self._applets.append(self.batchProcessingApplet)

        # -- Parse command-line arguments
        #    (Command-line args are applied in onProjectLoaded(), below.)
        # Parse workflow-specific command-line args
        parser = argparse.ArgumentParser()
        parser.add_argument('--retrain', help="Re-train the classifier based on labels stored in the project file, and re-save.", action="store_true")
        self.parsed_workflow_args, unused_args = parser.parse_known_args(workflow_cmdline_args)
        if unused_args:
            # Parse batch export/input args.
            self._data_export_args, unused_args = self.dataExportApplet.parse_known_cmdline_args( unused_args )
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
        opEdgeTrainingWithMulticut = self.edgeTrainingWithMulticutApplet.topLevelOperator
        opClassifierCache = opEdgeTrainingWithMulticut.opEdgeTraining.opClassifierCache

        # When the new lane is added, dirty notifications will propagate throughout the entire graph.
        # This means the classifier will be marked 'dirty' even though it is still usable.
        # Before that happens, let's store the classifier, so we can restore it in handleNewLanesAdded(), below.
        if opClassifierCache.Output.ready() and \
           not opClassifierCache._dirty:
            self.stored_classifier = opClassifierCache.Output.value
        else:
            self.stored_classifier = None
        
    def handleNewLanesAdded(self):
        """
        Overridden from Workflow base class.
        Called immediately after a new lane is added to the workflow and initialized.
        """
        opEdgeTrainingWithMulticut = self.edgeTrainingWithMulticutApplet.topLevelOperator
        opClassifierCache = opEdgeTrainingWithMulticut.opEdgeTraining.opClassifierCache

        # Restore classifier we saved in prepareForNewLane() (if any)
        if self.stored_classifier:
            opClassifierCache.forceValue(self.stored_classifier)
            # Release reference
            self.stored_classifier = None

    def connectLane(self, laneIndex):
        """
        Override from base class.
        """
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opWsdt = self.wsdtApplet.topLevelOperator.getLane(laneIndex)
        opEdgeTrainingWithMulticut = self.edgeTrainingWithMulticutApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)

        # RAW DATA: Convert to float32
        opConvertRaw = OpConvertDtype( parent=self )
        opConvertRaw.ConversionDtype.setValue( np.float32 )
        opConvertRaw.Input.connect( opDataSelection.ImageGroup[self.DATA_ROLE_RAW] )

        # PROBABILITIES: Convert to float32
        opConvertProbabilities = OpConvertDtype( parent=self )
        opConvertProbabilities.ConversionDtype.setValue( np.float32 )
        opConvertProbabilities.Input.connect( opDataSelection.ImageGroup[self.DATA_ROLE_PROBABILITIES] )

        # PROBABILITIES: Normalize drange to [0.0, 1.0]
        opNormalizeProbabilities = OpPixelOperator(parent=self)

        def normalize_inplace(a):
            drange = opConvertProbabilities.Output.meta.drange
            if drange is None or (drange[0] == 0.0 and drange[1] == 1.0):
                return a
            a[:] -= drange[0]
            a[:] = a[:] / float((drange[1] - drange[0]))
            return a

        opNormalizeProbabilities.Input.connect( opConvertProbabilities.Output )
        opNormalizeProbabilities.Function.setValue( normalize_inplace )

        # GROUNDTRUTH: Convert to uint32, relabel, and cache
        opConvertGroundtruth = OpConvertDtype( parent=self )
        opConvertGroundtruth.ConversionDtype.setValue( np.uint32 )
        opConvertGroundtruth.Input.connect( opDataSelection.ImageGroup[self.DATA_ROLE_GROUNDTRUTH] )

        opRelabelGroundtruth = OpRelabelConsecutive( parent=self )
        opRelabelGroundtruth.Input.connect( opConvertGroundtruth.Output )
        
        opGroundtruthCache = OpBlockedArrayCache( parent=self )
        opGroundtruthCache.CompressionEnabled.setValue(True)
        opGroundtruthCache.Input.connect( opRelabelGroundtruth.Output )

        # watershed inputs
        opWsdt.RawData.connect( opDataSelection.ImageGroup[self.DATA_ROLE_RAW] )
        opWsdt.Input.connect( opNormalizeProbabilities.Output )

        # Actual computation is done with both RawData and Probabilities
        opStackRawAndVoxels = OpSimpleStacker( parent=self )
        opStackRawAndVoxels.Images.resize(2)
        opStackRawAndVoxels.Images[0].connect( opConvertRaw.Output )
        opStackRawAndVoxels.Images[1].connect( opNormalizeProbabilities.Output )
        opStackRawAndVoxels.AxisFlag.setValue('c')

        # If superpixels are available from a file, use it.
        opSuperpixelsSelect = OpPrecomputedInput( ignore_dirty_input=True, parent=self )
        opSuperpixelsSelect.PrecomputedInput.connect( opDataSelection.ImageGroup[self.DATA_ROLE_SUPERPIXELS] )
        opSuperpixelsSelect.SlowInput.connect( opWsdt.Superpixels )

        # If the superpixel file changes, then we have to remove the training labels from the image
        opEdgeTraining = opEdgeTrainingWithMulticut.opEdgeTraining
        def handle_new_superpixels( *args ):
            opEdgeTraining.handle_dirty_superpixels( opEdgeTraining.Superpixels )
        opDataSelection.ImageGroup[self.DATA_ROLE_SUPERPIXELS].notifyReady( handle_new_superpixels )
        opDataSelection.ImageGroup[self.DATA_ROLE_SUPERPIXELS].notifyUnready( handle_new_superpixels )

        # edge training inputs
        opEdgeTrainingWithMulticut.RawData.connect( opDataSelection.ImageGroup[self.DATA_ROLE_RAW] ) # Used for visualization only
        opEdgeTrainingWithMulticut.VoxelData.connect( opStackRawAndVoxels.Output )
        opEdgeTrainingWithMulticut.Superpixels.connect( opSuperpixelsSelect.Output )
        opEdgeTrainingWithMulticut.GroundtruthSegmentation.connect( opGroundtruthCache.Output )

        # DataExport inputs
        opDataExport.RawData.connect( opDataSelection.ImageGroup[self.DATA_ROLE_RAW] )
        opDataExport.RawDatasetInfo.connect( opDataSelection.DatasetGroup[self.DATA_ROLE_RAW] )        
        opDataExport.Inputs.resize( len(self.EXPORT_NAMES) )
        opDataExport.Inputs[0].connect( opEdgeTrainingWithMulticut.Output )
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

        # Retrain the classifier?
        if self.parsed_workflow_args.retrain:
            self._force_retrain_classifier(projectManager)

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

    def _force_retrain_classifier(self, projectManager):
        logger.info("Retraining edge classifier...")
        op = self.edgeTrainingWithMulticutApplet.topLevelOperator

        # Cause the classifier to be dirty so it is forced to retrain.
        # (useful if the stored labels or features were changed outside ilastik)
        op.FeatureNames.setDirty()
        
        # Request the classifier, which forces training
        new_classifier = op.opEdgeTraining.opClassifierCache.Output.value
        if new_classifier is None:
            raise RuntimeError("Classifier could not be trained! Check your labels and features.")

        # store new classifier to project file
        projectManager.saveProject(force_all_save=False)

    def prepare_for_entire_export(self):
        """
        Assigned to DataExportApplet.prepare_for_entire_export
        (See above.)
        """
        # While exporting results, the caches should not be "frozen"
        opWsdt = self.wsdtApplet.topLevelOperator
        self.wsdt_frozen = opWsdt.FreezeCache.value
        opWsdt.FreezeCache.setValue(False)

        opTraining = self.edgeTrainingWithMulticutApplet.topLevelOperator
        self.freeze_classifier_status = opTraining.FreezeClassifier.value
        self.freeze_cache_status = opTraining.FreezeCache.value
        opTraining.FreezeClassifier.setValue(False)
        opTraining.FreezeCache.setValue(False)

    def post_process_entire_export(self):
        """
        Assigned to DataExportApplet.post_process_entire_export
        (See above.)
        """
        # After export is finished, re-freeze the segmentation caches.
        opWsdt = self.wsdtApplet.topLevelOperator
        opWsdt.FreezeCache.setValue(self.wsdt_frozen)
        
        opTraining = self.edgeTrainingWithMulticutApplet.topLevelOperator
        opTraining.FreezeClassifier.setValue(self.freeze_classifier_status)
        opTraining.FreezeCache.setValue(self.freeze_cache_status)

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
    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opWsdt = self.wsdtApplet.topLevelOperator
        opEdgeTrainingWithMulticut = self.edgeTrainingWithMulticutApplet.topLevelOperator
        opDataExport = self.dataExportApplet.topLevelOperator

        # If no data, nothing else is ready.
        input_ready = self._inputReady(2) and not self.dataSelectionApplet.busy
        superpixels_available_from_file = False
        lane_index = self._shell.currentImageIndex
        if lane_index != -1:
            superpixels_available_from_file = opDataSelection.ImageGroup[lane_index][self.DATA_ROLE_SUPERPIXELS].ready()

        superpixels_ready = opWsdt.Superpixels.ready()

        # The user isn't allowed to touch anything while batch processing is running.
        batch_processing_busy = self.batchProcessingApplet.busy

        self._shell.setAppletEnabled( self.dataSelectionApplet,             not batch_processing_busy )
        self._shell.setAppletEnabled( self.wsdtApplet,                      not batch_processing_busy and input_ready and not superpixels_available_from_file )
        self._shell.setAppletEnabled( self.edgeTrainingWithMulticutApplet,  not batch_processing_busy and input_ready and superpixels_ready )
        self._shell.setAppletEnabled( self.dataExportApplet,                not batch_processing_busy and input_ready and opEdgeTrainingWithMulticut.Output.ready())
        self._shell.setAppletEnabled( self.batchProcessingApplet,           not batch_processing_busy and input_ready )

        # Lastly, check for certain "busy" conditions, during which we
        #  should prevent the shell from closing the project.
        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= self.wsdtApplet.busy
        busy |= self.edgeTrainingWithMulticutApplet.busy
        busy |= self.dataExportApplet.busy
        busy |= self.batchProcessingApplet.busy
        self._shell.enableProjectChanges( not busy )

    def handle_applet_changed(self, prev_index, current_index):
        if prev_index != current_index:
            # If the user is viewing an applet downstream of the WSDT applet,
            # make sure the superpixels are always up-to-date.
            opWsdt = self.wsdtApplet.topLevelOperator
            opWsdt.FreezeCache.setValue( self._shell.currentAppletIndex <= self.applets.index( self.wsdtApplet ) )

            # Same for training and multicut
            opMulticut = self.edgeTrainingWithMulticutApplet.topLevelOperator
            opMulticut.FreezeClassifier.setValue( self._shell.currentAppletIndex <= self.applets.index( self.edgeTrainingWithMulticutApplet ) )
            opMulticut.FreezeCache.setValue( self._shell.currentAppletIndex <= self.applets.index( self.edgeTrainingWithMulticutApplet ) )
            
