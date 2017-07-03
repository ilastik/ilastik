"""Mediates between ilastikServerShell and ilastikServerAPI"""
from __future__ import print_function, division
import logging

import numpy

from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
from ilastik.shell.server.ilastikServerShell import ServerShell
from ilastik.applets.batchProcessing.batchProcessingApplet import BatchProcessingApplet
import collections

logger = logging.getLogger(__name__)


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
        batch_processing_applet = self._batch_applet
        batch_data_info = batch_processing_applet._get_template_dataset_infos()
        return collections.OrderedDict(
            (role_names[k], v) for k, v in batch_data_info.iteritems())

    @property
    def _batch_applet(self):
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
        batch_processing_applet = self._batch_applet

        role_data_dict = collections.OrderedDict({'Raw Input': data_info})
        ret_data = batch_processing_applet.run_export(role_data_dict, export_to_array=True)
        if is_single:
            return ret_data[0]
        else:
            return ret_data

    # --------------------------------------------------------------------------
    # NOT SURE YET:
    def get_applet_information(self, applet_index):
        """Generates a dict with applet-information
        """
        workflow = self._server_shell.workflow
        applet = workflow.applets[applet_index]
