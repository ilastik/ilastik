import logging
import weakref
from typing import Callable, Dict, List, Optional, Union
import numpy
from ndstructs import Slice5D
from functools import partial
import argparse
import ast
import textwrap

from ilastik.applets.base.applet import Applet
from ilastik.applets.dataExport.opDataExport import OpDataExport
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.dataSelection.opDataSelection import DatasetInfo, OpMultiLaneDataSelectionGroup

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

        default_block_roi = Slice5D.all(x=slice(0, 256), y=slice(0, 256), z=slice(0, 256), t=slice(0, 1))

        def parse_distributed_block_roi(value: str) -> Slice5D:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, dict):
                if not set(parsed.keys()).issubset("xyztc"):
                    raise ValueError(f"Bad keys for distributed-block-roi: {value}")
                if not all(isinstance(v, (int, None.__class__)) for v in parsed.values()):
                    raise ValueError(f"Bad values for distributed-block-roi: {value}")
                overrides = {k: slice(0, int(v)) for k, v in parsed.items()}
            elif isinstance(parsed, int):
                overrides = {k: slice(0, parsed) for k in "xyz"}
            else:
                raise TypeError(f"Could not convert value {value} into a Slice5D")

            return Slice5D(**{**default_block_roi.to_dict(), **overrides})

        parser.add_argument(
            "--distributed_block_roi",
            "--distributed-block-roi",
            help=textwrap.dedent(
                """
                Determines the dimensions of the blocks used to split the data in distributed mode.
                Values can be either:"
                    An integer, which will be interpreted as if the following dict was passed in:
                    {'x': value, 'y': value, 'z': value, 't': 1, 'c': None}

                    or a literal python Dict[str, Optional[int]], with keys in 'xyztc'.
                    Missing keys will default like so:
                    {'x': 256, 'y': 256, 'z': 256, 't': 1, 'c': None}
                    Use None anywhere in the dict to mean "the whole dimension".
                """
            ),
            type=parse_distributed_block_roi,
            default=default_block_roi,
        )

        parsed_args, unused_args = parser.parse_known_args(cmdline_args)
        return parsed_args, unused_args

    def run_export_from_parsed_args(self, parsed_args: argparse.Namespace):
        "Run the export for each dataset listed in parsed_args as interpreted by DataSelectionApplet."
        if parsed_args.distributed:
            export_function = partial(self.do_distributed_export, block_roi=parsed_args.distributed_block_roi)
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
        if not export_function:
            export_function = self.do_export_to_array if export_to_array else self.do_normal_export
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

    def do_distributed_export(self, opDataExport, *, block_roi: Slice5D):
        logger.info("Running ilastik distributed...")
        return opDataExport.run_distributed_export(block_roi=block_roi)

    def export_dataset(
        self,
        lane_config: Dict[str, DatasetInfo],
        export_function: Optional[Callable[[OpDataExport], Union[str, numpy.array]]] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Union[str, numpy.array]:
        """
        Configures a lane using the paths specified in the paths from role_inputs and runs the workflow.
        """
        export_function = export_function or self.do_normal_export

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
            self.dataSelectionApplet.dropLastLane()
