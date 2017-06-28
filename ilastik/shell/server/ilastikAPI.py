"""Mediates between ilastikServerShell and ilastikServerAPI"""
from __future__ import print_function, division
import logging
import os

from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
from ilastik.shell.server.ilastikServerShell import ServerShell
from ilastik.shell.projectManager import ProjectManager
from ilastik.applets.batchProcessing.batchProcessingApplet import BatchProcessingApplet
import collections

logger = logging.getLogger(__name__)

CONFIG = {
    'projects_path': os.path.expanduser('~/temp/ilastikserver')
}


class IlastikAPI(object):
    def __init__(self):
        super(IlastikAPI, self).__init__()
        self._server_shell = ServerShell()

    def get_current_workflow_name(self):
        workflow = self._server_shell.workflow
        if workflow is not None:
            return workflow.workflowName
        else:
            return None

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
        workflow = self._server_shell.workflow
        applet_names = [applet.name for applet in workflow.applets]
        return applet_names

    def get_applets(self):
        """Get info on all applets in the current workflow"""
        workflow = self._server_shell.workflow
        applets = workflow.applets
        return applets

    def get_applet_information(self, applet_index):
        """Generates a dict with applet-information
        """
        workflow = self._server_shell.workflow
        applet = workflow.applets[applet_index]

    def process_image(self, input_dict):
        """Process one or more image physical image files

        Args:
          input_dict (dict, or list of dicts): dictionary in the form
            {
               "role_name_a": "image_path",
               "role_name_b": "image_path",
               # optional:21
            }

        TODO: find out which inputs are optional; from dataSelectionApplet:
        # As far as this parser is concerned, all roles except the first are optional.
        # (Workflows that require the other roles are responsible for raising an error themselves.)
        """
        if isinstance(input_dict, collections.Sequence):
            # do the processing of multiple images
            pass
        else:
            # process a single image
            pass

    def get_batch_info(self):
        """Information about what info needs to be supplied for batch processing

        Returns an ordered dict role - dataset info pairs
        """
        workflow = self._server_shell.workflow
        role_names = workflow.ROLE_NAMES
        batch_processing_applet = self._get_batch_applet()
        batch_data_info = batch_processing_applet._get_template_dataset_infos()
        return collections.OrderedDict(
            (role_names[k], v) for k, v in batch_data_info.iteritems())

    def _get_batch_applet(self):
        applets = self.get_applets()
        batch_processing_applets = [applet for applet in applets
                                    if isinstance(applet, BatchProcessingApplet)]
        assert len(batch_processing_applets) == 1, (
            "Expected only a single batch processing applet per workflow.")
        batch_processing_applet = batch_processing_applets[0]
        return batch_processing_applet

    def process_data(self, data):
        inputs = self.get_batch_info()
        raw_info = inputs['Raw Data']
        data_info = DatasetInfo(preloaded_array=data)
        data_info.axistags = raw_info.axistags
        batch_processing_applet = self._get_batch_applet()

        role_data_dict = collections.OrderedDict({'Raw Input': [data_info]})
        ret_data = batch_processing_applet.run_export(role_data_dict, export_to_array=True)

        return ret_data

    def create_project(self, project_path, project_type='pixel_classification'):
        """Create a project at

        Args:
            project_path (TYPE): Description
            project_type (str, optional): Description

        Raises:
            ValueError: Description
        """
        from ilastik.workflows.pixelClassification import PixelClassificationWorkflow
        if project_type == 'pixel_classification':
            self._server_shell.createAndLoadNewProject(
                project_path,
                PixelClassificationWorkflow
            )
        else:
            raise ValueError('ProjectType needs to be PixelClassification for now')

    def __repr__(self):
        return type(self)

    def __str__(self):
        return "{type} at {address}".format(type=type(self), address=hex(id(self)))
