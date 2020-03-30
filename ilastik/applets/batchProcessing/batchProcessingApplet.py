import logging
import sys
from pathlib import Path
import weakref
from collections import OrderedDict
from typing import Callable, Dict, Hashable, List, Optional, Union, Mapping, Iterable
import numpy
import vigra
from vigra.vigranumpycore import AxisTags
from lazyflow.request import Request
from ndstructs import Shape5D
from functools import partial

from ilastik.applets.base.applet import Applet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.dataSelection.opDataSelection import (
    DatasetInfo,
    FilesystemDatasetInfo,
    OpMultiLaneDataSelectionGroup,
)

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
        parser = DataSelectionApplet.get_arg_parser(self.role_names)
        parser.add_argument(
            "--distributed",
            help="Distributed mode. Used for running ilastik on HPCs via SLURM/srun/mpirun",
            action="store_true",
        )
        parser.add_argument(
            "--distributed_block_size",
            help="The length of the side of the tiles used in distributed mode",
            type=int,
            default=256,
        )

        parsed_args, unused_args = parser.parse_known_args(cmdline_args)
        return parsed_args, unused_args

    def run_export_from_parsed_args(self, parsed_args):
        """
        Run the export for each dataset listed in parsed_args (we use the same parser as DataSelectionApplet).
        """
        if parsed_args.distributed:
            export_function = partial(self.do_distributed_export, block_size=parsed_args.distributed_block_size)
        else:
            export_function = self.do_normal_export

        role_path_dict = self.dataSelectionApplet.role_paths_from_parsed_args(parsed_args)
        return self.run_export(
            role_path_dict,
            input_axes=parsed_args.input_axes,
            sequence_axis=parsed_args.stack_along,
            export_function=export_function,
        )

    def run_export(
        self,
        role_data_dict: Mapping[Hashable, Iterable[Union[str, DatasetInfo]]],
        input_axes: Optional[str] = None,
        export_to_array: bool = False,
        sequence_axis: Optional[str] = None,
        export_function: Optional[Callable] = None,
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
        assert not (export_to_array and export_function)
        export_function = export_function or (self.do_export_to_array if export_to_array else self.do_normal_export)
        self.progressSignal(0)
        batches = list(zip(*role_data_dict.values()))
        try:
            results = []
            for batch_index, role_inputs in enumerate(batches):

                def lerpProgressSignal(a, b, p):
                    self.progressSignal((100 - p) * a + p * b)

                global_progress_start = batch_index / len(batches)
                global_progress_end = (batch_index + 1) / len(batches)

                result = self.export_dataset(
                    role_inputs,
                    input_axes=input_axes,
                    export_function=export_function,
                    sequence_axis=sequence_axis,
                    progress_callback=partial(lerpProgressSignal, global_progress_start, global_progress_end),
                )
                results.append(result)
            self.dataExportApplet.post_process_entire_export()
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

    def do_normal_export(self, opDataExport):
        logger.info(f"Exporting to {opDataExport.ExportPath.value}")
        opDataExport.run_export()
        return opDataExport.ExportPath.value

    def do_export_to_array(self, opDataExport):
        logger.info("Exporting to in-memory array.")
        return opDataExport.run_export_to_array()

    def do_distributed_export(self, opDataExport, *, block_size: int = 256):
        logger.info("Exporting to distributed command line...")
        return opDataExport.run_distributed_export(block_shape=Shape5D.hypercube(block_size))

    def export_dataset(
        self,
        role_inputs: List[Union[str, DatasetInfo]],
        export_function: Callable = None,
        input_axes: Optional[str] = None,
        sequence_axis: Optional[str] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Union[str, numpy.array]:
        """
        Configures a lane using the paths specified in the paths from role_inputs and runs the workflow.
        """
        export_function = export_function or self.do_normal_export
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
            for role_index, (role_input, role_axis_tags) in enumerate(zip(role_inputs, previous_axes_tags)):
                if not role_input:
                    continue
                if isinstance(role_input, DatasetInfo):
                    role_info = role_input
                else:
                    role_info = FilesystemDatasetInfo(
                        filePath=role_input,
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
            result = export_function(opDataExport)
            # Call customization hook
            self.dataExportApplet.post_process_lane_export(self.num_lanes - 1)
            return result
        finally:
            self.dataSelectionApplet.topLevelOperator.removeLane(original_num_lanes, original_num_lanes)

    @property
    def num_lanes(self) -> int:
        return len(self.dataSelectionApplet.topLevelOperator.DatasetGroup)

    @property
    def role_names(self) -> List[str]:
        return self.dataSelectionApplet.topLevelOperator.DatasetRoles.value
