import copy
import argparse
from collections import OrderedDict
import logging
logger = logging.getLogger(__name__)

from ilastik.applets.base.applet import Applet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.dataSelection.opDataSelection import DatasetInfo, OpMultiLaneDataSelectionGroup
from ilastik.applets.dataExport.opDataExport import OpDataExport

class BatchProcessingApplet( Applet ):
    """
    This applet can be appended to a workflow to provide batch-processing support.
    It has no 'top-level operator'.  Instead, it manipulates the workflow's DataSelection and DataExport operators. 
    """
    def __init__( self, workflow, title, dataSelectionApplet, dataExportApplet):
        Applet.__init__( self, "Batch Processing" )
        self.workflow = workflow
        self.dataSelectionApplet = dataSelectionApplet
        self.dataExportApplet = dataExportApplet
        self._gui = None # Created on first access

        assert isinstance(self.dataSelectionApplet.topLevelOperator, OpMultiLaneDataSelectionGroup)

    def getMultiLaneGui(self):
        if self._gui is None:
            from batchProcessingGui import BatchProcessingGui
            self._gui = BatchProcessingGui(self)
        return self._gui

    @property
    def topLevelOperator(self):
        # This applet has no top-level operator
        return None

    @property
    def dataSerializers(self):
        # No serializers.
        # The list of batch-processed files is not stored to the project file.
        return []

    def parse_known_cmdline_args(self, cmdline_args):
        # We use the same parser as the DataSelectionApplet
        role_names = self.dataSelectionApplet.topLevelOperator.DatasetRoles.value
        parsed_args, unused_args = DataSelectionApplet.parse_known_cmdline_args(cmdline_args, role_names)
        return parsed_args, unused_args

    def run_export(self, parsed_args):
        """
        Run the export for each dataset listed parsed_args (we use the same parser as DataSelectionApplet).

        For each dataset:
            1. Append a lane to the workflow
            2. Configure the new lane's DataSelection inputs with the new file (or files, if there is more than one role).
            3. Export the results from the new lane
            4. Remove the lane from the workflow.
        
        By appending/removing the batch lane for EACH dataset we process, we trigger the workflow's usual 
        prepareForNewLane() and connectLane() logic, which ensures that we get a fresh new lane that's 
        ready to process data.
        """
        template_infos = self._get_template_dataset_infos()
        role_names = self.dataSelectionApplet.topLevelOperator.DatasetRoles.value
        role_path_dict = self.dataSelectionApplet.role_paths_from_parsed_args(parsed_args, role_names)
        assert isinstance(role_path_dict, OrderedDict)
        # Invert dict from [role][batch_index] -> path to a list-of-tuples, indexed by batch_index: 
        # [ (role-1-path, role-2-path, ...),
        #   (role-1-path, role-2-path,...) ]
        paths_by_batch_index = zip( *role_path_dict.values() )

        for batch_dataset_index, role_input_paths in enumerate(paths_by_batch_index):
            # Add a lane to the end of the workflow for batch processing
            # (Expanding OpDataSelection by one has the effect of expanding the whole workflow.)
            dataset_group_slot = self.dataSelectionApplet.topLevelOperator.DatasetGroup
            dataset_group_slot.resize( len(dataset_group_slot)+1 )
            batch_lane_index = len(dataset_group_slot)-1
            try:
                # Now use the new lane to export the batch results for the current file.
                self._run_export_with_empty_batch_lane(role_input_paths, batch_lane_index, template_infos)
            finally:
                # Remove the batch lane.  See docstring above for explanation.
                dataset_group_slot.resize( len(dataset_group_slot)-1 )

    def _get_template_dataset_infos(self):
        """
        Sometimes the default settings for an input file are not suitable (e.g. the axistags need to be changed).
        We assume the LAST non-batch input in the workflow has settings that will work for all batch processing inputs.
        Here, we get the DatasetInfo objects from that lane and store them as 'templates' to modify for all batch-processing files.
        """
        # Use the LAST non-batch input file as our 'template' for DatasetInfo settings (e.g. axistags)
        template_lane = len(self.dataSelectionApplet.topLevelOperator.DatasetGroup)-1
        opDataSelectionTemplateView = self.dataSelectionApplet.topLevelOperator.getLane(template_lane)
        template_infos = {}
        for role_index, info_slot in enumerate(opDataSelectionTemplateView.DatasetGroup):
            if info_slot.ready():
                template_infos[role_index] = info_slot.value
            else:
                template_infos[role_index] = None
        return template_infos
    
    def _run_export_with_empty_batch_lane(self, role_input_paths, batch_lane_index, template_infos):
        """
        Configure the fresh batch lane with the given input files, and export the results.
        """
        assert role_input_paths[0], "At least one file must be provided for each dataset (the first role)."
        opDataSelectionBatchLaneView = self.dataSelectionApplet.topLevelOperator.getLane( batch_lane_index )

        # Apply new settings for each role
        for role_index, path_for_role in enumerate(role_input_paths):
            if not path_for_role:
                continue

            if template_infos[role_index]:
                info = copy.copy(template_infos[role_index])
            else:
                info = DatasetInfo()

            # Override the template settings with the current filepath.
            default_info = DataSelectionApplet.create_default_headless_dataset_info(path_for_role)
            info.filePath = default_info.filePath
            info.location = default_info.location
            info.nickname = default_info.nickname

            # Apply to the data selection operator
            opDataSelectionBatchLaneView.DatasetGroup[role_index].setValue(info)

        # Make sure nothing went wrong
        opDataExportBatchlaneView = self.dataExportApplet.topLevelOperator.getLane( batch_lane_index )
        assert opDataExportBatchlaneView.ImageToExport.ready()
        assert opDataExportBatchlaneView.ExportPath.ready()
        
        # Finally, run the export
        logger.info("Exporting to {}".format( opDataExportBatchlaneView.ExportPath.value ))
        opDataExportBatchlaneView.run_export()
