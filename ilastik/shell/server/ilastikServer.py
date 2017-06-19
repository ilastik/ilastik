"""Mediates between ilastikServerShell and ilastikServerAPI"""
from __future__ import print_function, division
import logging
import os

from ilastik.shell.server.ilastikServerShell import ServerShell

logger = logging.getLogger(__name__)

CONFIG = {
    'projects_path': os.path.expanduser('~/temp/ilastikserver')
}


class IlastikServer(object):
    def __init__(self):
        super(IlastikServer, self).__init__()
        self._server_shell = ServerShell()

    def get_current_workflow_name(self):
        workflow = self._server_shell.workflow
        if workflow is not None:
            return workflow.workflowName
        else:
            return None

    def get_workflow_status(self):
        """Collects information about all applets into a dictionary
        """
        workflow = self._server_shell.workflow
        return workflow

    def get_applet_names(self):
        workflow = self._server_shell.workflow
        applet_names = [applet.name for applet in workflow.applets]
        return applet_names

    def get_applet_information(self, applet_index):
        """Generates a dict with applet-information
        """
        workflow = self._server_shell.workflow
        applet = workflow.applets[applet_index]
        applet.


    def create_project(self, project_name, project_type='pixel_classification'):
        from ilastik.workflows.pixelClassification import PixelClassificationWorkflow
        if project_type == 'pixel_classification':
            self._server_shell.createAndLoadNewProject(
                os.path.join(
                    CONFIG['projects_path'],
                    "{project_name:s}.h5".format(project_name=project_name)),
                PixelClassificationWorkflow
            )
        else:
            raise ValueError('ProjectType needs to be PixelClassification for now')

    def __repr__(self):
        return type(self)

    def __str__(self):
        return "{type} at {address}".format(type=type(self), address=hex(id(self)))
