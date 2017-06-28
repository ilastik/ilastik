"""Shell container to store all normal ilastik stuff

"""

from ilastik.shell.shellAbc import ShellABC
from ilastik.shell.projectManager import ProjectManager

import logging


logger = logging.getLogger(__name__)


class ServerShell(object):
    """
    For now, this class is a stand-in for the GUI shell (used when running
    ilastik as a server application).
    """
    def __init__(self):
        self.workflow_options = None
        self.projectManager = None

    @property
    def workflow(self):
        return self.projectManager.workflow

    def currentImageIndex(self):
        raise NotImplementedError

    def createAndLoadNewProject(self, newProjectFilePath, workflow_class):
        """
        """
        hdf5File = ProjectManager.createBlankProjectFile(newProjectFilePath)
        readOnly = False

        self.projectManager = ProjectManager(
            self,
            workflow_class,
            headless=True,
            workflow_cmdline_args=self.workflow_options)
        self.projectManager._loadProject(hdf5File, newProjectFilePath, readOnly)
        self.projectManager.saveProject()

    def openProjectFile(self, projectFilePath, force_readonly=False):
        """
        # TODO give some feedback!
        """
        # Make sure all workflow sub-classes have been loaded,
        #  so we can detect the workflow type in the project.
        import ilastik.workflows
        try:
            # Open the project file
            hdf5File, workflow_class, readOnly = ProjectManager.openProjectFile(projectFilePath, force_readonly)

            # If there are any "creation-time" command-line args saved to the project file,
            #  load them so that the workflow can be instantiated with the same settings
            #  that were used when the project was first created.
            project_creation_args = []
            if "workflow_cmdline_args" in hdf5File.keys():
                if len(hdf5File["workflow_cmdline_args"]) > 0:
                    project_creation_args = map(str, hdf5File["workflow_cmdline_args"][...])

            if workflow_class is None:
                workflow_class = ilastik.workflows.pixelClassification.PixelClassificationWorkflow
                import warnings
                warnings.warn("Your project file ({}) does not specify a workflow type. "
                              "Assuming Pixel Classification".format(projectFilePath))

            # Create our project manager
            # This instantiates the workflow and applies all settings from the project.
            self.projectManager = ProjectManager(self,
                                                 workflow_class,
                                                 headless=True,
                                                 workflow_cmdline_args=self.workflow_options,
                                                 project_creation_args=project_creation_args)
            self.projectManager._loadProject(hdf5File, projectFilePath, readOnly)

        except ProjectManager.FileMissingError:
            logger.error("Couldn't find project file: {}".format(projectFilePath))
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
            self.projectManager = ProjectManager(self,
                                                 default_workflow,
                                                 headless=True,
                                                 workflow_cmdline_args=self.workflow_options,
                                                 project_creation_args=self.workflow_options)

            self.projectManager._importProject(oldProjectFilePath, hdf5File, projectFilePath)

    def setAppletEnabled(self, applet, enabled):
        pass

    def isAppletEnabled(self, applet):
        return False

    def enableProjectChanges(self, enabled):
        pass


assert issubclass(ServerShell, ShellABC), (
    "ServerShell does not satisfy the generic shell interface!")
