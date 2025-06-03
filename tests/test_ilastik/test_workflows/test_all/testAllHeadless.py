###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2017, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#          http://ilastik.org/license.html
###############################################################################
"""Basic tests that can be applied to _all_ workflows in headless mode

This is meant as a sanity check to make sure that workflows can be at least
started after changes are committed.

Also this can be used as a basis for further headless-mode testing.
"""
import os
import sys
import tempfile

from ilastik import app
from ilastik.workflow import getAvailableWorkflows
from ilastik.shell.projectManager import ProjectManager

import logging
import pytest

logger = logging.getLogger(__name__)


WORKFLOW_LIST = list(getAvailableWorkflows())


def generate_project_file_name(temp_dir, workflow_name):
    project_file_name = os.path.join(temp_dir, f'test_project_{"_".join(workflow_name.split())}.ilp')
    return project_file_name


class TestHeadlessWorkflowStartupProjectCreation(object):
    """Start a headless shell and create a project for each workflow"""

    @pytest.mark.parametrize("workflow_class_tuple", WORKFLOW_LIST, ids=[x[1] for x in WORKFLOW_LIST])
    def test_workflow_creation_headless(self, workflow_class_tuple):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.start_workflow_create_project_headless(workflow_class_tuple, temp_dir)

    def start_workflow_create_project_headless(self, workflow_class_tuple, temp_dir):
        """Tests project file creation via the command line
        Args:
            workflow_class_tuple (tuple): tuple returned from getAvailableWorkflows
              with (workflow_class, workflow_name, workflow_class.workflowDisplayName)
        """
        workflow_class, workflow_name, display_name = workflow_class_tuple
        logger.debug(f"starting {workflow_name}")
        project_file = generate_project_file_name(temp_dir, workflow_name)

        args = ["--headless", f"--new_project={project_file}", f"--workflow={workflow_name}"]
        # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv = ["ilastik.py"]
        sys.argv.extend(args)

        # Start up the ilastik.py entry script as if we had launched it from the command line
        parsed_args, workflow_cmdline_args = app.parse_known_args()

        shell = app.main(parsed_args=parsed_args, workflow_cmdline_args=workflow_cmdline_args, init_logging=False)

        shell.closeCurrentProject()

        # now check if the project file has been created:
        assert os.path.exists(project_file), f"Project File {project_file} creation not successful"

    @pytest.mark.parametrize("workflow_class_tuple", WORKFLOW_LIST, ids=[x[1] for x in WORKFLOW_LIST])
    def test_workflow_loading_headless(self, workflow_class_tuple):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.start_workflow_load_project_headless(workflow_class_tuple, temp_dir)

    def create_project_file(self, workflow_class, project_file_name):
        newProjectFile = ProjectManager.createBlankProjectFile(project_file_name, workflow_class, [])
        newProjectFile.close()

    def start_workflow_load_project_headless(self, workflow_class_tuple, temp_dir):
        """Tests opening project files in headless mode via the command line
        Args:
            workflow_class_tuple (tuple): tuple returned from getAvailableWorkflows
              with (workflow_class, workflow_name, workflow_class.workflowDisplayName)
        """
        workflow_class, workflow_name, display_name = workflow_class_tuple
        logger.debug(f"starting {workflow_name}")
        project_file = generate_project_file_name(temp_dir, workflow_name)

        self.create_project_file(workflow_class, project_file)
        assert os.path.exists(project_file), f"Project File {project_file} creation not successful"

        args = ["--headless", f"--project={project_file}"]
        # Clear the existing commandline args so it looks like we're starting fresh.
        sys.argv = ["ilastik.py"]
        sys.argv.extend(args)

        # Start up the ilastik.py entry script as if we had launched it from the command line
        parsed_args, workflow_cmdline_args = app.parse_known_args()
        shell = app.main(parsed_args=parsed_args, workflow_cmdline_args=workflow_cmdline_args, init_logging=False)

        shell.closeCurrentProject()

        # no errors -> everything should be cool
