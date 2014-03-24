# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

import os
import logging
logger = logging.getLogger(__name__)

from ilastik.shell.shellAbc import ShellABC
from ilastik.shell.projectManager import ProjectManager

class HeadlessShell(object):
    """
    For now, this class is just a stand-in for the GUI shell (used when running from the command line).
    """
    
    def __init__(self, workflow_cmdline_args=None):
        self._workflow_cmdline_args = workflow_cmdline_args or []
        self.projectManager = None

    @property
    def workflow(self):
        return self.projectManager.workflow

    def createAndLoadNewProject(self, newProjectFilePath, workflow_class):
        hdf5File = ProjectManager.createBlankProjectFile(newProjectFilePath)
        readOnly = False
        self.projectManager = ProjectManager( self,
                                              workflow_class,
                                              headless=True,
                                              workflow_cmdline_args=self._workflow_cmdline_args  )
        self.projectManager._loadProject(hdf5File, newProjectFilePath, readOnly)
        
    def openProjectFile(self, projectFilePath):
        # Make sure all workflow sub-classes have been loaded,
        #  so we can detect the workflow type in the project.
        import ilastik.workflows
        try:
            # Open the project file
            hdf5File, workflow_class, _ = ProjectManager.openProjectFile(projectFilePath)

            if workflow_class is None:
                # If the project file has no known workflow, we assume pixel classification
                import ilastik.workflows
                workflow_class = ilastik.workflows.pixelClassification.PixelClassificationWorkflow
                import warnings
                warnings.warn( "Your project file ({}) does not specify a workflow type.  "
                               "Assuming Pixel Classification".format( projectFilePath ) )            
            
            # Create our project manager
            # This instantiates the workflow and applies all settings from the project.
            self.projectManager = ProjectManager( self,
                                                  workflow_class,
                                                  headless=True,
                                                  workflow_cmdline_args=self._workflow_cmdline_args )
            self.projectManager._loadProject(hdf5File, projectFilePath, readOnly = False)

        except ProjectManager.FileMissingError:
            logger.error("Couldn't find project file: {}".format( projectFilePath ))
            raise            
        except ProjectManager.ProjectVersionError:
            # Couldn't open project.  Try importing it.
            oldProjectFilePath = projectFilePath
            name, ext = os.path.splitext(oldProjectFilePath)
    
            # Create a brand new project file.
            projectFilePath = name + "_imported" + ext
            logger.info("Importing project as '" + projectFilePath + "'")
            hdf5File = ProjectManager.createBlankProjectFile(projectFilePath)

            # For now, we assume that any imported projects are pixel classification workflow projects.
            import ilastik.workflows
            default_workflow = ilastik.workflows.pixelClassification.PixelClassificationWorkflow

            # Create the project manager.
            # Here, we provide an additional parameter: the path of the project we're importing from. 
            self.projectManager = ProjectManager( self,
                                                  default_workflow,
                                                  importFromPath=oldProjectFilePath,
                                                  headless=True )
            self.projectManager._importProject(oldProjectFilePath, hdf5File, projectFilePath,readOnly = False)

    def setAppletEnabled(self, applet, enabled):
        """
        Provided here to satisfy the ShellABC.
        For now, HeadlessShell has no concept of "enabled" or "disabled" applets.
        """
        pass

    def enableProjectChanges(self, enabled):
        """
        Provided here to satisfy the ShellABC.
        For now, HeadlessShell has no mechanism for closing projects.
        """
        pass

    def closeCurrentProject(self):
        self.projectManager._closeCurrentProject()
        self.projectManager.cleanUp()
        self.projectManager = None

assert issubclass( HeadlessShell, ShellABC ), "HeadlessShell does not satisfy the generic shell interface!"

