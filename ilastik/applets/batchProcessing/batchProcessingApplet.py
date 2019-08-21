import logging
import weakref
from collections import OrderedDict
from typing import Callable, Dict, Hashable, List, Optional, Union, Mapping, Iterable
import numpy
import vigra
from vigra.vigranumpycore import AxisTags
from lazyflow.request import Request
from functools import partial

from ilastik.applets.base.applet import Applet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.dataSelection.opDataSelection import FilesystemDatasetInfo, OpMultiLaneDataSelectionGroup

logger = logging.getLogger(__name__)  # noqa


class BatchProcessingApplet(Applet):
    """
    This applet can be appended to a workflow to provide batch-processing support.
    It has no 'top-level operator'.  Instead, it manipulates the workflow's DataSelection and DataExport operators.
    """

    def __init__(self, workflow, title, dataSelectionApplet, dataExportApplet):
        super(BatchProcessingApplet, self).__init__("Batch Processing", syncWithImageIndex=False)
        self.workflow = weakref.ref(workflow)
        self.dataSelectionApplet = dataSelectionApplet
        self.dataExportApplet = dataExportApplet
        assert isinstance(self.dataSelectionApplet.topLevelOperator, OpMultiLaneDataSelectionGroup)
        self._gui = None  # Created on first access

    def getMultiLaneGui(self):
        if self._gui is None:
            from .batchProcessingGui import BatchProcessingGui

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
        parsed_args, unused_args = DataSelectionApplet.parse_known_cmdline_args(cmdline_args, self.role_names)
        return parsed_args, unused_args

    def run_export_from_parsed_args(self, parsed_args):
        """
        Run the export for each dataset listed in parsed_args (we use the same parser as DataSelectionApplet).
        """
        role_path_dict = self.dataSelectionApplet.role_paths_from_parsed_args(parsed_args)
        return self.run_export(role_path_dict, parsed_args.input_axes, sequence_axis=parsed_args.stack_along)

    def run_export(
        self,
        role_data_dict: Mapping[Hashable, Iterable[str]],
        input_axes: Optional[str] = None,
        export_to_array: bool = False,
        sequence_axis: Optional[str] = None,
    ) -> Union[List[str], List[numpy.array]]:
        """Run the export for each dataset listed in role_data_dict

        For each dataset:
                1. Append a lane to the workflow
                2. Configure the new lane's DataSelection inputs with the new file (or files, if there is more than one
                   role).
                3. Export the results from the new lane
                4. Remove the lane from the workflow.

            By appending/removing the batch lane for EACH dataset we process, we trigger the workflow's usual
            prepareForNewLane() and connectLane() logic, which ensures that we get a fresh new lane that's
            ready to process data.

            After each lane is processed, the given post-processing callback will be executed.
            signature: lane_postprocessing_callback(batch_lane_index)

        Args:
            role_data_dict: dict with role_name: list(paths) of data that should be processed.
            input_axes: axis description to override from the default role
            export_to_array: If True do NOT export to disk as usual.
              Instead, export the results to a list of arrays, which is returned.
              If False, return a list of the filenames we produced to.
            sequence_axis: stack along this axis, overrides setting from default role

        Returns:
            list containing either strings of paths to exported files,
              or numpy.arrays (depending on export_to_array)
        """
        self.progressSignal(0)
        batches = list(zip(*role_data_dict.values()))
        try:
            results = []
            for batch_dataset_index, role_input_paths in enumerate(batches):

                def emit_progress(dataset_index, dataset_percent):
                    overall_progress = (dataset_index + dataset_percent / 100.0) / len(batches)
                    self.progressSignal(100 * overall_progress)

                result = self.export_dataset(
                    role_input_paths,
                    input_axes=input_axes,
                    export_to_array=export_to_array,
                    sequence_axis=sequence_axis,
                    progress_callback=partial(emit_progress, batch_dataset_index),
                )
                results.append(result)
            return results
        finally:
            self.progressSignal(100)

    def get_previous_axes_tags(self) -> List[Optional[AxisTags]]:
        if self.num_lanes == 0:
            return [None] * len(self.role_names)

        infos = []
        for role_index, _ in enumerate(self.role_names):
            info_slot = self.dataSelectionApplet.topLevelOperator.DatasetGroup[self.num_lanes - 1][role_index]
            infos.append(info_slot.value.axistags if info_slot.ready() else None)
        return infos

    def export_dataset(
        self,
        role_input_paths: List[str],
        input_axes: Optional[str] = None,
        export_to_array: bool = False,
        sequence_axis: Optional[str] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Union[str, numpy.array]:
        """
        Configures a lane using the paths specified in the paths from role_input_paths and runs the workflow.
        """
        progress_callback = progress_callback or self.progressSignal
        original_num_lanes = self.num_lanes
        previous_axes_tags = self.get_previous_axes_tags()
        # Call customization hook
        self.dataExportApplet.prepare_for_entire_export()
        # Add a lane to the end of the workflow for batch processing
        # (Expanding OpDataSelection by one has the effect of expanding the whole workflow.)
        self.dataSelectionApplet.topLevelOperator.addLane(self.num_lanes)
        batch_lane = self.dataSelectionApplet.topLevelOperator.getLane(self.num_lanes - 1)
        try:
            for role_index, (role_input_path, role_axis_tags) in enumerate(zip(role_input_paths, previous_axes_tags)):
                if role_input_path:
                    role_info = FilesystemDatasetInfo(
                        filePath=role_input_path,
                        project_file=None,
                        axistags=vigra.defaultAxistags(input_axes) if input_axes else role_axis_tags,
                        sequence_axis=sequence_axis,
                        guess_tags_for_singleton_axes=True,  # FIXME: add cmd line param to negate this
                    )
                    batch_lane.DatasetGroup[role_index].setValue(role_info)
            self.workflow().handleNewLanesAdded()
            # Call customization hook
            self.dataExportApplet.prepare_lane_for_export(self.num_lanes - 1)
            opDataExport = self.dataExportApplet.topLevelOperator.getLane(self.num_lanes - 1)
            opDataExport.progressSignal.subscribe(progress_callback)
            if export_to_array:
                logger.info("Exporting to in-memory array.")
                result = opDataExport.run_export_to_array()
            else:
                logger.info(f"Exporting to {opDataExport.ExportPath.value}")
                opDataExport.run_export()
                result = opDataExport.ExportPath.value

            # Call customization hook
            self.dataExportApplet.post_process_lane_export(self.num_lanes - 1)
            self.dataExportApplet.post_process_entire_export()
            return result
        finally:
            self.dataSelectionApplet.topLevelOperator.removeLane(original_num_lanes, original_num_lanes)

    @property
    def num_lanes(self) -> int:
        return len(self.dataSelectionApplet.topLevelOperator.DatasetGroup)

    @property
    def role_names(self) -> List[str]:
        return self.dataSelectionApplet.topLevelOperator.DatasetRoles.value
