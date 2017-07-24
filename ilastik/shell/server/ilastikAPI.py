"""Mediates between ilastikServerShell and ilastikServerAPI"""
from __future__ import print_function, division
import logging
import collections
import copy

from functools import partial

import numpy

from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
from ilastik.shell.server.ilastikServerShell import ServerShell
from ilastik.applets.batchProcessing.batchProcessingApplet import BatchProcessingApplet
from ilastik.applets.dataSelection.dataSelectionApplet import DataSelectionApplet

from lazyflow.graph import OperatorWrapper
from lazyflow.operators.opReorderAxes import OpReorderAxes


logger = logging.getLogger(__name__)

VoxelSourceState = collections.namedtuple(
    "VoxelSourceState", "name axes shape dtype version")


class SlotTracker(object):
    """Copied from voxel_server"""

    def __init__(self, image_name_multislot, multislots, forced_axes=None):
        self.image_name_multislot = image_name_multislot
        self._slot_versions = {}  # { dataset_name : { slot_name : [slot, version] } }

        self.multislot_names = [s.name for s in multislots]
        if forced_axes is None:
            self.multislots = multislots
        else:
            self.multislots = []
            for multislot in multislots:
                op = OperatorWrapper(
                    OpReorderAxes,
                    parent=multislot.getRealOperator().parent,
                    broadcastingSlotNames=['AxisOrder'])
                op.AxisOrder.setValue(forced_axes)
                op.Input.connect(multislot)
                self.multislots.append(op.Output)

    def get_dataset_names(self):
        names = []
        for lane_index, name_slot in enumerate(self.image_name_multislot):
            if name_slot.ready():
                name = name_slot.value
            else:
                name = "dataset-{}".format(lane_index)
            names.append(name)
        return names

    def get_slot_versions(self, dataset_name):
        found = False
        lane_index = None
        for lane_index, name_slot in enumerate(self.image_name_multislot):
            if name_slot.value == dataset_name:
                found = True
                break
        if not found:
            raise RuntimeError("Dataset name not found: {}".format(dataset_name))

        if dataset_name not in self._slot_versions:
            for multislot in self.multislots:
                slot = multislot[lane_index]
                # TODO: Unsubscribe to these signals on shutdown...
                slot.notifyDirty(partial(self._increment_version, dataset_name))
                slot.notifyMetaChanged(partial(self._increment_version, dataset_name))

            self._slot_versions[dataset_name] = {
                self.multislot_names[self.multislots.index(multislot)]: [multislot[lane_index], 0]
                for multislot in self.multislots}

        return self._slot_versions[dataset_name]

    def _increment_version(self, dataset_name, slot, *args):
        for name in self._slot_versions[dataset_name].keys():
            if self._slot_versions[dataset_name][name][0] == slot:
                self._slot_versions[dataset_name][name][1] += 1
                return
        assert False, "Couldn't find slot"

    def get_states(self, dataset_name):
        states = collections.OrderedDict()
        slot_versions = self.get_slot_versions(dataset_name)
        for slot_name, (slot, version) in slot_versions.items():
            axes = ''.join(slot.meta.getAxisKeys())
            states[slot_name] = VoxelSourceState(slot_name,
                                                 axes,
                                                 slot.meta.shape,
                                                 slot.meta.dtype.__name__,
                                                 version)
        return states

    def get_slot(self, dataset_name, slot_name):
        slot_versions = self.get_slot_versions(dataset_name)
        return slot_versions[slot_name][0]


class IlastikAPI(object):
    """Collection of user-friendly methods for interaction with ilastik
    """
    def __init__(self, workflow_type=None, project_path=None):
        """Initialize a new API object

        If `workflow_type` is given and `project_path` is None, an in-memory
        project is created.
        If `project_path` is given and `workflow_type` is not given, an existing
        project is assumed.
        If both `workflow_type` and `project_path` are given, a new project with
        the given project path is created on disc.

        Args:
            workflow_type (str): workflow type as string,
              e.g. `pixel_classification`. Valid workflow types:

              * pixel_classification
              * ...

            project_path (str): path to project
        """
        super(IlastikAPI, self).__init__()
        self._server_shell = ServerShell()
        self.slot_tracker = None
        if workflow_type is not None and project_path is not None:
            # create new project
            logger.warning('New pr')
        elif workflow_type is not None:
            # create in-memory project
            logger.warning('Creation of in-memory projects not yet implemented! '
                           'Instantiating empty API.')
        elif project_path is not None:
            # load project
            self.load_project_file(project_path)

    def __repr__(self):
        return type(self)

    def __str__(self):
        return "{type} at {address}".format(type=type(self), address=hex(id(self)))

    @property
    def workflow_name(self):
        """get the current workflow name

        Returns:
            str: workflow name
        """
        workflow = self._server_shell.workflow
        if workflow is not None:
            return workflow.workflowName
        else:
            return None

    def initialize_voxel_server(self):
        op = self._server_shell.workflow.pcApplet.topLevelOperator
        multislots = [op.InputImages,
                      #op.LabelImages,
                      op.PredictionProbabilities]

        image_name_multislot = self._server_shell.workflow.dataSelectionApplet.topLevelOperator.ImageName
        # forcing to neuroglancer axisorder
        self.slot_tracker = SlotTracker(image_name_multislot, multislots, forced_axes='tczyx')

    def create_project(self, workflow_type='pixel_classification', project_path=None):
        """Create a new project

        TODO: memory-only project

        Args:
            project_path (str): path to project file, will be overwritten
              without warning.
            workflow_type (str): workflow type as string,
              e.g. `pixel_classification`. Valid workflow types:

              * pixel_classification
              * ...

        Raises:
            ValueError: if an unsupported `workflow_type` is given
        """
        if project_path is None:
            raise NotImplementedError('memory-only projects have to be implemented')
        from ilastik.workflows.pixelClassification import PixelClassificationWorkflow
        if workflow_type == 'pixel_classification':
            self._server_shell.createAndLoadNewProject(
                project_path,
                PixelClassificationWorkflow
            )
        else:
            raise ValueError('ProjectType needs to be PixelClassification for now')

    def load_project_file(self, project_file_path):
        """Load project file from disk (local)

        Args:
          project_file_path (str): path of `.ilp` file
        """
        self._server_shell.openProjectFile(project_file_path)

    def get_workflow_status(self):
        """Collects information about all applets into a dictionary
        """
        workflow = self._server_shell.workflow
        return workflow

    def get_applet_names(self):
        """Convenience property, get the list of applet names

        Returns:
            list: List of string with workflow names
        """
        workflow = self._server_shell.workflow
        applet_names = None
        if workflow is not None:
            applet_names = [applet.name for applet in workflow.applets]
        return applet_names

    @property
    def applets(self):
        """Get info on all applets in the current workflow

        Returns:
            list: list of applets of the current workflow
        """
        workflow = self._server_shell.workflow
        applets = None
        if workflow is not None:
            applets = workflow.applets
        return applets

    def get_batch_info(self):
        """Information about what info needs to be supplied for batch processing

        Returns:
            OrderedDict: role - dataset info pairs
        """
        workflow = self._server_shell.workflow
        # should this be the one accessed?
        role_names = workflow.ROLE_NAMES
        batch_data_info = self._get_template_dataset_infos()
        return collections.OrderedDict(
            (role_names[k], v) for k, v in batch_data_info.items())

    def get_batch_applet(self):
        """Get the batch applet from the workflow applets
        """
        applets = self.applets
        batch_processing_applets = [applet for applet in applets
                                    if isinstance(applet, BatchProcessingApplet)]
        assert len(batch_processing_applets) == 1, (
            "Expected only a single batch processing applet per workflow.")
        batch_processing_applet = batch_processing_applets[0]
        return batch_processing_applet

    def process_data(self, data):
        """Process data with the loaded projectk

        TODO: proper check if project is ready to process data.
        TODO: check whether return type might depend on the workflow.

        Args:
            data (ndarray, or list of ndarrays): ndarrays to process with the
              loaded ilastik project.

        Returns:
            ndarray or list of ndarrays:  depending on the input argument,

        """
        is_single = False
        if not isinstance(data, collections.Sequence):
            data = [data]
            is_single = True

        if not all(isinstance(d, numpy.ndarray) for d in data):
            raise ValueError("data has to be numpy.ndarray type")
        inputs = self.get_batch_info()
        raw_info = inputs['Raw Data']
        data_info = [DatasetInfo(preloaded_array=d) for d in data]
        for dinfo in data_info:
            dinfo.axistags = raw_info.axistags
        batch_processing_applet = self.get_batch_applet()

        role_data_dict = collections.OrderedDict({'Raw Input': data_info})
        ret_data = batch_processing_applet.run_export(role_data_dict, export_to_array=True)
        if is_single:
            return ret_data[0]
        else:
            return ret_data

    def get_applet(self, applet_type):
        """
        Args:
            applet_type (BaseApplet or derived): the actual class one is looking
              for.

        Returns:
            Applet
        """
        applets = self.applets
        selected_applet = [applet for applet in applets
                           if isinstance(applet, applet_type)]
        assert len(selected_applet) == 1, (
            "Expected only a single batch processing applet per workflow.")
        selected_applet = selected_applet[0]
        return selected_applet

    def get_structured_info(self):
        if self.slot_tracker is None:
            self.initialize_voxel_server()
        dataset_names = self.slot_tracker.get_dataset_names()
        json_states = []
        for lane_number, dataset_name in enumerate(dataset_names):
            states = self.slot_tracker.get_states(dataset_name)
            lane_states = []
            for source_name, state in states.items():
                tmp = collections.OrderedDict(zip(state._fields, state))
                tmp['lane_number'] = lane_number
                tmp['dataset_name'] = dataset_name
                tmp['source_name'] = source_name
                lane_states.append(tmp)
            json_states.append(lane_states)
        return (dataset_names, json_states)

    def get_input_info(self):
        """Gather information about inputs to the current workflow"""
        data_selection_applet = self.get_applet(DataSelectionApplet)
        return data_selection_applet

    def add_dataset(self, file_name):
        """Convenience method to add an image lane with the supplied data

        Args:
            file_name: path to image file to add.

        TODO: proper check if project is ready to process data.
        TODO: this only works for pixel classification

        Returns
            (int) lane index
        """
        is_single = False
        input_axes = None
        if not isinstance(file_name, (list, tuple)):
            data = [file_name]
            is_single = True

        data_selection_applet = self.get_applet(DataSelectionApplet)
        # add a new lane
        opDataSelection = data_selection_applet.topLevelOperator

        # configure roles
        if not is_single:
            raise NotImplementedError("Didn't have time to do that yet...")

        # HACK: just to get it working with pixel classification quickly

        template_infos = self._get_template_dataset_infos(input_axes)
        # Invert dict from [role][batch_index] -> path to a list-of-tuples, indexed by batch_index:
        # [ (role-1-path, role-2-path, ...),
        #   (role-1-path, role-2-path,...) ]
        # datas_by_batch_index = zip( *role_data_dict.values() )

        role_input_datas = list(zip(*collections.OrderedDict({'Raw Input': data}).values()))[0]
        existing_lanes = len(opDataSelection.DatasetGroup)
        opDataSelection.DatasetGroup.resize(existing_lanes + 1)
        lane_index = existing_lanes
        for role_index, data_for_role in enumerate(role_input_datas):
            if not data_for_role:
                continue

            if isinstance(data_for_role, DatasetInfo):
                # Caller provided a pre-configured DatasetInfo instead of a just a path
                info = data_for_role
            else:
                # Copy the template info, but override filepath, etc.
                default_info = DatasetInfo(data_for_role)
                info = copy.copy(template_infos[role_index])
                info.filePath = default_info.filePath
                info.location = default_info.location
                info.nickname = default_info.nickname

            # Apply to the data selection operator
            opDataSelection.DatasetGroup[lane_index][role_index].setValue(info)

    # --------------------------------------------------------------------------
    # NOT SURE YET:
    def get_applet_information(self, applet_index):
        """Generates a dict with applet-information
        """
        workflow = self._server_shell.workflow
        applet = workflow.applets[applet_index]


    # --------------------------------------------------------------------------
    # MIRRORED:

    # From batchprocessing applet
    def _get_template_dataset_infos(self, input_axes=None):
        """
        Sometimes the default settings for an input file are not suitable (e.g. the axistags need to be changed).
        We assume the LAST non-batch input in the workflow has settings that will work for all batch processing inputs.
        Here, we get the DatasetInfo objects from that lane and store them as 'templates' to modify for all batch-processing files.
        """
        template_infos = {}
        data_selection_applet = self.get_applet(DataSelectionApplet)
        # If there isn't an available dataset to use as a template
        if len(data_selection_applet.topLevelOperator.DatasetGroup) == 0:
            num_roles = len(data_selection_applet.topLevelOperator.DatasetRoles.value)
            for role_index in range(num_roles):
                template_infos[role_index] = DatasetInfo()
                if input_axes:
                    template_infos[role_index].axistags = vigra.defaultAxistags(input_axes)
            return template_infos

        # Use the LAST non-batch input file as our 'template' for DatasetInfo settings (e.g. axistags)
        template_lane = len(data_selection_applet.topLevelOperator.DatasetGroup) - 1
        opDataSelectionTemplateView = data_selection_applet.topLevelOperator.getLane(template_lane)

        for role_index, info_slot in enumerate(opDataSelectionTemplateView.DatasetGroup):
            if info_slot.ready():
                template_infos[role_index] = info_slot.value
            else:
                template_infos[role_index] = DatasetInfo()
            if input_axes:
                # Support the --input_axes arg to override input axis order, same as DataSelection applet.
                template_infos[role_index].axistags = vigra.defaultAxistags(input_axes)
        return template_infos
