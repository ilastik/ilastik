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
import argparse
import logging
logger = logging.getLogger(__name__)

from ilastik.applets.batchProcessing import BatchProcessingApplet
from ilastik.applets.pixelClassification import PixelClassificationDataExportApplet
from ilastik.workflows.pixelClassification import PixelClassificationWorkflow

from slicApplet import SlicApplet
from voxelSegmentationApplet import VoxelSegmentationApplet


from lazyflow.graph import Graph

class VoxelSegmentationWorkflow(PixelClassificationWorkflow):
    workflowName = "Voxel Segmentation Workflow"
    workflowDescription = ""
    workflowDisplayName = workflowName
    defaultAppletIndex = 0  # show DataSelection by default

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):
        # Copy pasted from the pixel classification workflow class
        # Create a graph to be shared by all operators
        graph = Graph()
        super(PixelClassificationWorkflow, self).__init__(shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs)
        self.stored_classifier = None
        self._applets = []
        self._workflow_cmdline_args = workflow_cmdline_args
        # Parse workflow-specific command-line args
        parser = argparse.ArgumentParser()
        parser.add_argument('--filter', help="pixel feature filter implementation.", choices=['Original', 'Refactored', 'Interpolated'], default='Original')
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
        self.filter_implementation = parsed_creation_args.filter

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

        if parsed_args.filter and parsed_args.filter != parsed_creation_args.filter:
            logger.error("Ignoring new --filter setting.  Filter implementation cannot be changed after initial project creation.")

        data_instructions = "Select your input data using the 'Raw Data' tab shown on the right.\n\n"\
                            "Power users: Optionally use the 'Prediction Mask' tab to supply a binary image that tells ilastik where it should avoid computations you don't need."

        # Applet for SLIC segmentation
        self.slicApplet = self.createSlicApplet()

        # Applets for training (interactive) workflow 
        self.dataSelectionApplet = self.createDataSelectionApplet()
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        
        # see role constants, above
        opDataSelection.DatasetRoles.setValue( PixelClassificationWorkflow.ROLE_NAMES )

        self.featureSelectionApplet = self.createFeatureSelectionApplet()

        #TODO rename pcApplet
        self.pcApplet = self.createVoxelSegmentationApplet()
        opClassify = self.pcApplet.topLevelOperator

        self.dataExportApplet = PixelClassificationDataExportApplet(self, "Prediction Export")
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.PmapColors.connect( opClassify.PmapColors )
        opDataExport.LabelNames.connect( opClassify.LabelNames )
        opDataExport.WorkingDirectory.connect( opDataSelection.WorkingDirectory )
        opDataExport.SelectionNames.setValue( self.EXPORT_NAMES )        

        # Expose for shell
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.slicApplet)
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
            logger.warn("Unused command-line args: {}".format(unused_args))

    def connectLane(self, laneIndex):
        super(VoxelSegmentationWorkflow, self).connectLane(laneIndex)
        opSlic = self.slicApplet.topLevelOperator
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)

        opSlic.Input.connect(opData.Image)

    def createVoxelSegmentationApplet(self):
        return VoxelSegmentationApplet(self, "VoxelSegmentation")

    def createSlicApplet(self):
        return SlicApplet(self)