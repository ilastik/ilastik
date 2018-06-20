from __future__ import division
from __future__ import absolute_import
from builtins import range
import copy
import weakref
from collections import OrderedDict
import logging
logger = logging.getLogger(__name__)  # noqa

import numpy
import vigra
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
        role_names = self.dataSelectionApplet.topLevelOperator.DatasetRoles.value
        parsed_args, unused_args = DataSelectionApplet.parse_known_cmdline_args(
            cmdline_args, role_names)
        return parsed_args, unused_args

    def run_export_from_parsed_args(self, parsed_args):
        """
        Run the export for each dataset listed in parsed_args (we use the same parser as DataSelectionApplet).
        """
        role_names = self.dataSelectionApplet.topLevelOperator.DatasetRoles.value
        role_path_dict = self.dataSelectionApplet.role_paths_from_parsed_args(
            parsed_args, role_names)
        return self.run_export(role_path_dict, parsed_args.input_axes, sequence_axis=parsed_args.stack_along)

    def run_export(self, role_data_dict, input_axes=None, export_to_array=False, sequence_axis=None):
        """
        Run the export for each dataset listed in role_data_dict,
        which must be a dict of {role_index : path-list} OR {role_index : DatasetInfo-list}

        As shown above, you may pass either filepaths OR preconfigured DatasetInfo objects.
        The latter is useful if you are batch processing data that already exists in memory as a numpy array.
        (See DatasetInfo.preloaded_array for how to provide a numpy array instead of a filepath.)

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

        export_to_array: If True do NOT export to disk as usual.
                         Instead, export the results to a list of arrays, which is returned.
                         If False, return a list of the filenames we produced to.
        """
        results = []

        self.progressSignal(0)
        try:
            assert isinstance(role_data_dict, OrderedDict)

            template_infos = self._get_template_dataset_infos(input_axes, sequence_axis)
            # Invert dict from [role][batch_index] -> path to a list-of-tuples, indexed by batch_index:
            # [ (role-1-path, role-2-path, ...),
            #   (role-1-path, role-2-path,...) ]
            datas_by_batch_index = list(zip(*list(role_data_dict.values())))

            # Call customization hook
            self.dataExportApplet.prepare_for_entire_export()

            batch_lane_index = len(self.dataSelectionApplet.topLevelOperator)
            for batch_dataset_index, role_input_datas in enumerate(datas_by_batch_index):
                # Add a lane to the end of the workflow for batch processing
                # (Expanding OpDataSelection by one has the effect of expanding the whole workflow.)
                self.dataSelectionApplet.topLevelOperator.addLane(
                    batch_lane_index)
                try:
                    # The above setup can take a long time for a big workflow.
                    # If the user has ALREADY cancelled, quit now instead of waiting for the first request to begin.
                    Request.raise_if_cancelled()

                    def emit_progress(dataset_percent):
                        overall_progress = (
                            batch_dataset_index + dataset_percent / 100.0) / len(datas_by_batch_index)
                        self.progressSignal(100 * overall_progress)

                    # Now use the new lane to export the batch results for the current file.
                    result = self._run_export_with_empty_batch_lane(role_input_datas,
                                                                    batch_lane_index,
                                                                    template_infos,
                                                                    emit_progress,
                                                                    export_to_array=export_to_array)
                    if export_to_array:
                        assert isinstance(result, numpy.ndarray)
                    else:
                        assert isinstance(result, str)
                    results.append(result)
                finally:
                    # Remove the batch lane.  See docstring above for explanation.
                    try:
                        self.dataSelectionApplet.topLevelOperator.removeLane(
                            batch_lane_index, batch_lane_index)
                    except Request.CancellationException:
                        log_exception(logger)
                        # If you see this, something went wrong in a graph setup operation.
                        raise RuntimeError(
                            "Encountered an unexpected CancellationException while removing the batch lane.")
                    assert len(
                        self.dataSelectionApplet.topLevelOperator.DatasetGroup) == batch_lane_index

            # Call customization hook
            self.dataExportApplet.post_process_entire_export()

            return results
        finally:
            self.progressSignal(100)

    def _get_template_dataset_infos(self, input_axes=None, sequence_axis=None):
        """
        Sometimes the default settings for an input file are not suitable (e.g. the axistags need to be changed).
        We assume the LAST non-batch input in the workflow has settings that will work for all batch processing inputs.
        Here, we get the DatasetInfo objects from that lane and store them as 'templates' to modify for all batch-
        processing files.
        """
        template_infos = {}

        # If there isn't an available dataset to use as a template
        if len(self.dataSelectionApplet.topLevelOperator.DatasetGroup) == 0:
            num_roles = len(
                self.dataSelectionApplet.topLevelOperator.DatasetRoles.value)
            for role_index in range(num_roles):
                template_infos[role_index] = DatasetInfo()
                if input_axes:
                    template_infos[role_index].axistags = vigra.defaultAxistags(
                        input_axes)
                if sequence_axis:
                    template_infos[role_index].sequenceAxis = sequence_axis
            return template_infos

        # Use the LAST non-batch input file as our 'template' for DatasetInfo settings (e.g. axistags)
        template_lane = len(
            self.dataSelectionApplet.topLevelOperator.DatasetGroup) - 1
        opDataSelectionTemplateView = self.dataSelectionApplet.topLevelOperator.getLane(
            template_lane)

        for role_index, info_slot in enumerate(opDataSelectionTemplateView.DatasetGroup):
            if info_slot.ready():
                template_infos[role_index] = info_slot.value
            else:
                template_infos[role_index] = DatasetInfo()
            if input_axes:
                # Support the --input_axes arg to override input axis order, same as DataSelection applet.
                template_infos[role_index].axistags = vigra.defaultAxistags(
                    input_axes)
            if sequence_axis:
                template_infos[role_index].sequenceAxis = sequence_axis
        return template_infos

    def _run_export_with_empty_batch_lane(self, role_input_datas, batch_lane_index, template_infos, progress_callback,
                                          export_to_array):
        """
        Configure the fresh batch lane with the given input files, and export the results.

        role_input_datas: A list of str or DatasetInfo, one item for each dataset-role.
                          (For example, a workflow might have two roles: Raw Data and Binary Segmentation.)

        batch_lane_index: The lane index used as the batch export lane.

        template_infos: A dict of DatasetInfo objects.
                        Settings like axistags, etc. that cannot be automatically inferred
                        from the filepath will be copied from these template objects.
                        (See explanation in _get_template_dataset_infos(), above.)

        progress_callback: Export progress for the current lane is reported via this callback.
        """
        assert role_input_datas[
            0], "At least one file must be provided for each dataset (the first role)."
        opDataSelectionBatchLaneView = self.dataSelectionApplet.topLevelOperator.getLane(
            batch_lane_index)

        # Apply new settings for each role
        for role_index, data_for_role in enumerate(role_input_datas):
            if not data_for_role:
                continue

            if isinstance(data_for_role, DatasetInfo):
                # Caller provided a pre-configured DatasetInfo instead of a just a path
                info = data_for_role
            else:
                # Copy the template info, but override filepath, etc.
                template_info = template_infos[role_index]
                info = DatasetInfo.from_file_path(template_info, data_for_role)

            # Force real data source when in headless mode.
            # If raw data doesn't exist in headless mode, we use fake data reader
            # (datasetInfo.realDataSource = False). Now we need to ensure that
            # the flag is set to True for new image lanes.
            info.realDataSource = True
            # Apply to the data selection operator
            opDataSelectionBatchLaneView.DatasetGroup[role_index].setValue(info)

        # Make sure nothing went wrong
        opDataExportBatchlaneView = self.dataExportApplet.topLevelOperator.getLane(
            batch_lane_index)
        # New lanes were added.
        # Give the workflow a chance to restore anything that was unecessarily invalidated (e.g. classifiers)
        self.workflow().handleNewLanesAdded()

        assert opDataExportBatchlaneView.ImageToExport.ready()
        assert opDataExportBatchlaneView.ExportPath.ready()

        # Call customization hook
        self.dataExportApplet.prepare_lane_for_export(batch_lane_index)

        # Finally, run the export
        opDataExportBatchlaneView.progressSignal.subscribe(progress_callback)

        if export_to_array:
            logger.info("Exporting to in-memory array.")
            result = opDataExportBatchlaneView.run_export_to_array()
        else:
            logger.info("Exporting to {}".format(
                opDataExportBatchlaneView.ExportPath.value))
            opDataExportBatchlaneView.run_export()
            result = opDataExportBatchlaneView.ExportPath.value

        # Call customization hook
        self.dataExportApplet.post_process_lane_export(batch_lane_index)

        return result
