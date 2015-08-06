import copy
import argparse
from collections import OrderedDict
import logging
logger = logging.getLogger(__name__)

from lazyflow.request import Request
from ilastik.utility import log_exception
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
        super(BatchProcessingApplet, self).__init__( "Batch Processing", syncWithImageIndex=False )
        self.workflow = workflow
        self.dataSelectionApplet = dataSelectionApplet
        self.dataExportApplet = dataExportApplet
        assert isinstance(self.dataSelectionApplet.topLevelOperator, OpMultiLaneDataSelectionGroup)
        self._gui = None # Created on first access

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

    def run_export_from_parsed_args(self, parsed_args):
        """
        Run the export for each dataset listed in parsed_args (we use the same parser as DataSelectionApplet).
        """
        role_names = self.dataSelectionApplet.topLevelOperator.DatasetRoles.value
        role_path_dict = self.dataSelectionApplet.role_paths_from_parsed_args(parsed_args, role_names)
        self.run_export(role_path_dict)

    def run_export(self, role_path_dict ):
        """
        Run the export for each dataset listed in role_path_dict, 
        which must be a dict of {role_index : path_list}.

        For each dataset:
            1. Append a lane to the workflow
            2. Configure the new lane's DataSelection inputs with the new file (or files, if there is more than one role).
            3. Export the results from the new lane
            4. Remove the lane from the workflow.
        
        By appending/removing the batch lane for EACH dataset we process, we trigger the workflow's usual 
        prepareForNewLane() and connectLane() logic, which ensures that we get a fresh new lane that's 
        ready to process data.
        
        After each lane is processed, the given post-processing callback will be executed.
        signature: lane_postprocessing_callback(batch_lane_index)
        """
        self.progressSignal.emit(0)
        try:
            assert isinstance(role_path_dict, OrderedDict)
            template_infos = self._get_template_dataset_infos()
            # Invert dict from [role][batch_index] -> path to a list-of-tuples, indexed by batch_index: 
            # [ (role-1-path, role-2-path, ...),
            #   (role-1-path, role-2-path,...) ]
            paths_by_batch_index = zip( *role_path_dict.values() )

            # Call customization hook
            self.dataExportApplet.prepare_for_entire_export()

            batch_lane_index = len(self.dataSelectionApplet.topLevelOperator)
            for batch_dataset_index, role_input_paths in enumerate(paths_by_batch_index):
                # Add a lane to the end of the workflow for batch processing
                # (Expanding OpDataSelection by one has the effect of expanding the whole workflow.)
                self.dataSelectionApplet.topLevelOperator.addLane( batch_lane_index )
                try:
                    # The above setup can take a long time for a big workflow.
                    # If the user has ALREADY cancelled, quit now instead of waiting for the first request to begin.
                    Request.raise_if_cancelled()
                    
                    def emit_progress(dataset_percent):
                        overall_progress = (batch_dataset_index + dataset_percent/100.0)/len(paths_by_batch_index)
                        self.progressSignal.emit(100*overall_progress)

                    # Now use the new lane to export the batch results for the current file.
                    self._run_export_with_empty_batch_lane( role_input_paths,
                                                            batch_lane_index,
                                                            template_infos,
                                                            emit_progress )
                finally:
                    # Remove the batch lane.  See docstring above for explanation.
                    try:
                        self.dataSelectionApplet.topLevelOperator.removeLane( batch_lane_index, batch_lane_index )
                    except Request.CancellationException:
                        log_exception(logger)
                        # If you see this, something went wrong in a graph setup operation.
                        raise RuntimeError("Encountered an unexpected CancellationException while removing the batch lane.")
                    assert len(self.dataSelectionApplet.topLevelOperator.DatasetGroup) == batch_lane_index

            # Call customization hook
            self.dataExportApplet.post_process_entire_export()
            
        finally:
            self.progressSignal.emit(100)

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
    
    def _run_export_with_empty_batch_lane(self, role_input_paths, batch_lane_index, template_infos, progress_callback):
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
        
        # New lanes were added.
        # Give the workflow a chance to restore anything that was unecessarily invalidated (e.g. classifiers)
        self.workflow.handleNewLanesAdded()
        
        # Call customization hook
        self.dataExportApplet.prepare_lane_for_export(batch_lane_index)

        # Finally, run the export
        logger.info("Exporting to {}".format( opDataExportBatchlaneView.ExportPath.value ))
        opDataExportBatchlaneView.progressSignal.subscribe(progress_callback)
        opDataExportBatchlaneView.run_export()

        # Call customization hook
        self.dataExportApplet.post_process_lane_export(batch_lane_index)
