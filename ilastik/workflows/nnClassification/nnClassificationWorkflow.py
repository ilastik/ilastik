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
import logging
logger = logging.getLogger(__name__)

import numpy

from ilastik.config import cfg as ilastik_config
from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.networkClassification import NNClassApplet, NNClassificationDataExportApplet
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet
from ilastik.applets.batchProcessing import BatchProcessingApplet

from lazyflow.graph import Graph
from lazyflow.roi import TinyVector, fullSlicing

class NNClassificationWorkflow(Workflow):
    
    workflowName = "Neural Network Classification"
    workflowDescription = "This is obviously self-explanatory."
    defaultAppletIndex = 0 # show DataSelection by default
    
    DATA_ROLE_RAW = 0
    ROLE_NAMES = ['Raw Data']
    EXPORT_NAMES = ['Features', 'Probabilities']
    
    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()
        super( NNClassificationWorkflow, self ).__init__( shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs )
        self._applets = []
        self._workflow_cmdline_args = workflow_cmdline_args
        # Parse workflow-specific command-line args
        parser = argparse.ArgumentParser()
        # parser.add_argument('--print-labels-by-slice', help="Print the number of labels for each Z-slice of each image.", action="store_true")

        # Parse the creation args: These were saved to the project file when this project was first created.
        parsed_creation_args, unused_args = parser.parse_known_args(project_creation_args)

        # Parse the cmdline args for the current session.
        parsed_args, unused_args = parser.parse_known_args(workflow_cmdline_args)
        # self.print_labels_by_slice = parsed_args.print_labels_by_slice

        data_instructions = "Select your input data using the 'Raw Data' tab shown on the right.\n\n"\
                            "Power users: Optionally use the 'Prediction Mask' tab to supply a binary image that tells ilastik where it should avoid computations you don't need."

        # Applets for training (interactive) workflow 
        self.dataSelectionApplet = self.createDataSelectionApplet()
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        
        # see role constants, above
        opDataSelection.DatasetRoles.setValue( NNClassificationWorkflow.ROLE_NAMES )

        self.nnClassificationApplet = NNClassApplet(self, "NNClassApplet")
        opNNclassify = self.nnClassificationApplet.topLevelOperator

        self.dataExportApplet = DataExportApplet(self, "Data Export")
        self.dataExportApplet.prepare_for_entire_export = self.prepare_for_entire_export
        self.dataExportApplet.post_process_entire_export = self.post_process_entire_export      

        # Configure global DataExport settings
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.WorkingDirectory.connect( opDataSelection.WorkingDirectory )
        opDataExport.SelectionNames.setValue( self.EXPORT_NAMES )

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
            self._batch_export_args, unused_args = self.dataExportApplet.parse_known_cmdline_args( unused_args )
            self._batch_input_args, unused_args = self.batchProcessingApplet.parse_known_cmdline_args( unused_args )
        else:
            self._batch_input_args = None
            self._batch_export_args = None

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
                                    supportIlastik05Import=True,
                                    instructionText=data_instructions)

    # def prepareForNewLane(self, laneIndex):

    #     opNNClassification = self.nnClassificationApplet.topLevelOperator

    def connectLane(self, laneIndex):
        # Get a handle to each operator
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opNNclassify = self.nnClassificationApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)
        
        # Input Image -> Feature Op
        #         and -> Classification Op (for display)
        opNNclassify.InputImage.connect( opData.Image )
        
        # Data Export connections
        opDataExport.RawData.connect( opData.ImageGroup[self.DATA_ROLE_RAW])
        opDataExport.RawDatasetInfo.connect( opData.DatasetGroup[self.DATA_ROLE_RAW])
        # opDataExport.Inputs.resize( len(self.EXPORT_NAMES))
        opDataExport.Inputs.resize( 1 )
        # opDataExport.Inputs[0].connect(opNNclassify.InputImage)
        opDataExport.Inputs[0].connect(opNNclassify.CachedPredictionProbabilities)
        # for slot in opDataExport.Inputs:
        #     assert slot.partner is not None

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        # If no data, nothing else is ready.
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        input_ready = len(opDataSelection.ImageGroup) > 0 and not self.dataSelectionApplet.busy

        opNNClassification = self.nnClassificationApplet.topLevelOperator
        nnOutput = []

        opDataExport = self.dataExportApplet.topLevelOperator 

        predictions_ready = input_ready and \
                            len(opDataExport.Inputs) > 0 
                            # opDataExport.Inputs[0][0].ready()
                            # (TinyVector(opDataExport.Inputs[0][0].meta.shape) > 0).all()

        # Problems can occur if the features or input data are changed during live update mode.
        # Don't let the user do that.
        print ("liveupdate value", opNNClassification.FreezePredictions.value)
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


    def prepare_for_entire_export(self):
        """
        Assigned to DataExportApplet.prepare_for_entire_export
        (See above.)
        """
        print ('prepare_for_entire_export')
        self.freeze_status = self.nnClassificationApplet.topLevelOperator.FreezePredictions.value
        self.nnClassificationApplet.topLevelOperator.FreezePredictions.setValue(False)

    def post_process_entire_export(self):
        """
        Assigned to DataExportApplet.post_process_entire_export
        (See above.)
        """
        print('post_process_entire_export')
        self.nnClassificationApplet.topLevelOperator.FreezePredictions.setValue(self.freeze_status)





