"""Shell container to store all normal ilastik stuff

"""

from ilastik.shell.shellAbc import ShellABC
from ilastik.shell.projectManager import ProjectManager
from lazyflow.utility import isUrl


class ServerShell(object):
    """
    For now, this class is a stand-in for the GUI shell (used when running
    ilastik as a server application).
    """
    def __init__(self, workflow_cmdline_args=None):

        self._workflow_cmdline_args = workflow_cmdline_args
        if self._workflow_cmdline_args is None:
            self._workflow_cmdline_args = []

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
            workflow_cmdline_args=self._workflow_cmdline_args)
        self.projectManager._loadProject(hdf5File, newProjectFilePath, readOnly)
        self.projectManager.saveProject()

    def openProjectFile(self, projectFilePath):
        """
        """
        raise NotImplementedError

    def setAppletEnabled(self, applet, enabled):
        pass

    def isAppletEnabled(self, applet):
        return False

    def enableProjectChanges(self, enabled):
        pass


assert issubclass(ServerShell, ShellABC), (
    "ServerShell does not satisfy the generic shell interface!")
