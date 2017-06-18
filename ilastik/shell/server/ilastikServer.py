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

