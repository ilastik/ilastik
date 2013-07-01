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
        self.projectManager = ProjectManager( workflow_class,
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
            
            # Create our project manager
            # This instantiates the workflow and applies all settings from the project.
            self.projectManager = ProjectManager( workflow_class,
                                                  headless=True,
                                                  workflow_cmdline_args=self._workflow_cmdline_args )
            self.projectManager._loadProject(hdf5File, projectFilePath, readOnly = False)
            
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
            self.projectManager = ProjectManager( default_workflow,
                                                  importFromPath=oldProjectFilePath,
                                                  headless=True )
            self.projectManager._importProject(oldProjectFilePath, hdf5File, projectFilePath,readOnly = False)

    def closeCurrentProject(self):
        self.projectManager._closeCurrentProject()
        self.projectManager.cleanUp()
        self.projectManager = None

assert issubclass( HeadlessShell, ShellABC ), "HeadlessShell does not satisfy the generic shell interface!"

