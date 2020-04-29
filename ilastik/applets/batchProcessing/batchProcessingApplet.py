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
import argparse

from ilastik.applets.base.applet import Applet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.dataSelection.opDataSelection import (
    DatasetInfo,
    FilesystemDatasetInfo,
    UrlDatasetInfo,
    OpMultiLaneDataSelectionGroup,
)
from lazyflow.utility import isUrl

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
        parser = DataSelectionApplet.get_arg_parser(self.dataSelectionApplet.role_names)
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

    def run_export_from_parsed_args(self, parsed_args: argparse.Namespace):
        "Run the export for each dataset listed in parsed_args as interpreted by DataSelectionApplet."
        if parsed_args.distributed:
            export_function = partial(self.do_distributed_export, block_size=parsed_args.distributed_block_size)
        else:
            export_function = self.do_normal_export

        return self.run_export(
            lane_configs=self.dataSelectionApplet.lane_configs_from_parsed_args(parsed_args),
            export_function=export_function,
        )

    def run_export(
        self,
        lane_configs: List[Dict[str, Optional[DatasetInfo]]],
        export_to_array: bool = False,
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

        Args:
            lane_configs: A list of dicts with one dict of role_name -> DatasetInfo for each lane
            export_to_array: If True do NOT export to disk as usual.
              Instead, export the results to a list of arrays, which is returned.
              If False, return a list of the filenames we produced to.

        Returns:
            list containing either strings of paths to exported files,
              or numpy.arrays (depending on export_to_array)
        """
        assert not (export_to_array and export_function)
        export_function = export_function or (self.do_export_to_array if export_to_array else self.do_normal_export)
        self.progressSignal(0)
        try:
            results = []
            for batch_index, lane_config in enumerate(lane_configs):

                def lerpProgressSignal(a, b, p):
                    self.progressSignal((100 - p) * a + p * b)

                global_progress_start = batch_index / len(lane_configs)
                global_progress_end = (batch_index + 1) / len(lane_configs)

                result = self.export_dataset(
                    lane_config,
                    export_function=export_function,
                    progress_callback=partial(lerpProgressSignal, global_progress_start, global_progress_end),
                )
                results.append(result)
            self.dataExportApplet.post_process_entire_export()
            return results
        finally:
            self.progressSignal(100)

    def do_normal_export(self, opDataExport):
        logger.info(f"Exporting to {opDataExport.ExportPath.value}")
        opDataExport.run_export()
        return opDataExport.ExportPath.value

    def do_export_to_array(self, opDataExport):
        logger.info("Exporting to in-memory array.")
        return opDataExport.run_export_to_array()

    def do_distributed_export(self, opDataExport, *, block_size: int = 256):
        logger.info("Running ilastik distributed...")
        return opDataExport.run_distributed_export(block_shape=Shape5D.hypercube(block_size))

    def export_dataset(
        self,
        lane_config: Dict[str, DatasetInfo],
        export_function: Callable = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Union[str, numpy.array]:
        """
        Configures a lane using the paths specified in the paths from role_inputs and runs the workflow.
        """
        export_function = export_function or self.do_normal_export
        role_names = self.dataSelectionApplet.role_names

        # Call customization hook
        self.dataExportApplet.prepare_for_entire_export()
        self.dataSelectionApplet.pushLane(lane_config)
        try:
            # Call customization hook
            self.dataExportApplet.prepare_lane_for_export(self.dataSelectionApplet.num_lanes - 1)
            opDataExport = self.dataExportApplet.topLevelOperator.getLane(self.dataSelectionApplet.num_lanes - 1)
            opDataExport.progressSignal.subscribe(progress_callback or self.progressSignal)
            result = export_function(opDataExport)
            # Call customization hook
            self.dataExportApplet.post_process_lane_export(self.dataSelectionApplet.num_lanes - 1)
            return result
        finally:
            self.dataSelectionApplet.popLane()
