from __future__ import division
from __future__ import absolute_import
from builtins import range
import copy
import weakref
from collections import OrderedDict
from typing import List
import logging
logger = logging.getLogger(__name__)  # noqa

import numpy
import vigra
from vigra.vigranumpycore import AxisTags
from lazyflow.request import Request
from ilastik.utility import log_exception
from ilastik.applets.base.applet import Applet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.dataSelection.opDataSelection import DatasetInfo, OpMultiLaneDataSelectionGroup


class BatchProcessingApplet(Applet):
    """
    This applet can be appended to a workflow to provide batch-processing support.
    It has no 'top-level operator'.  Instead, it manipulates the workflow's DataSelection and DataExport operators.
    """

    def __init__(self, workflow, title, dataSelectionApplet, dataExportApplet):
        super(BatchProcessingApplet, self).__init__(
            "Batch Processing", syncWithImageIndex=False)
        self.workflow = weakref.ref(workflow)
        self.dataSelectionApplet = dataSelectionApplet
        self.dataExportApplet = dataExportApplet
        assert isinstance(
            self.dataSelectionApplet.topLevelOperator, OpMultiLaneDataSelectionGroup)
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
        results = []
        for role_input_paths in zip(*role_path_dict.values()): #FIXME progress signals
            result = self.run_export(role_input_paths, parsed_args.input_axes, sequence_axis=parsed_args.stack_along)
            results.append(result)

    def get_previous_axes_tags(self) -> List[AxisTags]:
        if self.num_lanes == 0:
            return [None] * len(self.role_names)

        infos = []
        for role_index, _ in enumerate(self.role_names):
            info_slot = self.dataSelectionApplet.topLevelOperator.DatasetGroup[self.num_lanes - 1][role_index]
            infos.append(info_slot.value.axistags if info_slot.ready() else None)
        return infos

    def run_export(self, role_input_paths:List[str], input_axes:str=None, export_to_array:bool=False, sequence_axis:str=None):
        """
        Configures a lane using the paths specified in the paths from role_input_paths and runs the workflow.

        input_axes: specifies how to reinterpret the axes of the data sources
        sequence_axis: specifies the axis along which a collection of input files is stacked
        export_to_array: If True do NOT export to disk as usual.
                         Instead, export the results to a list of arrays, which is returned.
                         If False, return a list of the filenames we produced to.
        """

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
                    role_info = DatasetInfo.default(
                        role_input_path,
                        axistags=vigra.defaultAxistags(input_axes) if input_axes else role_axis_tags,
                        sequence_axis=sequence_axis
                    )
                    batch_lane.DatasetGroup[role_index].setValue(role_info)
            self.workflow().handleNewLanesAdded()
            # Call customization hook
            self.dataExportApplet.prepare_lane_for_export(self.num_lanes - 1)
            opDataExport = self.dataExportApplet.topLevelOperator.getLane(self.num_lanes - 1)
            if export_to_array:
                logger.info("Exporting to in-memory array.")
                result = opDataExport.run_export_to_array()
            else:
                logger.info("Exporting to {}".format(opDataExport.ExportPath.value))
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
    def role_names(self) -> int:
        return self.dataSelectionApplet.topLevelOperator.DatasetRoles.value

    def get_template_info(self, role_index:int) -> DatasetInfo:
        if self.num_lanes == 0:
            return DatasetInfo
