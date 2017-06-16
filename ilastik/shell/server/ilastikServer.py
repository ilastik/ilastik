from ilastik.shell.shellAbc import ShellABC


class ServerShell(object):
    """
    For now, this class is a stand-in for the GUI shell (used when running
    ilastik as a server application).
    """
    def workflow(self):
        raise NotImplementedError

    def currentImageIndex(self):
        raise NotImplementedError

    def createAndLoadNewProject(self, newProjectFilePath, workflow_class):
        """
        """
        raise NotImplementedError

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
