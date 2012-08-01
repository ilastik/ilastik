import os
import logging
logger = logging.getLogger(__name__)

from ilastik.shell.projectManager import ProjectManager

class HeadlessShell(object):
    """
    For now, this class is just a stand-in for the GUI shell (used when running from the command line).
    """
    
    def __init__(self):
        self._applets = []
        self.projectManager = ProjectManager()
        self.currentImageIndex = -1

    def addApplet(self, aplt):
        self._applets.append(aplt)
        self.projectManager.addApplet(aplt)
    
    def changeCurrentInputImageIndex(self, newImageIndex):
        if newImageIndex != self.currentImageIndex:
            # Alert each central widget and viewer control widget that the image selection changed
            for i in range( len(self._applets) ):
                self._applets[i].gui.setImageIndex(newImageIndex)
                
            self.currentImageIndex = newImageIndex

    def openProjectPath(self, projectFilePath):
        try:
            hdf5File = self.projectManager.openProjectFile(projectFilePath)
            self.projectManager.loadProject(hdf5File, projectFilePath)
        except ProjectManager.ProjectVersionError:
            # Couldn't open project.  Try importing it.
            oldProjectFilePath = projectFilePath
            name, ext = os.path.splitext(oldProjectFilePath)
            projectFilePath = name + "_imported" + ext
    
            logger.info("Importing project as '" + projectFilePath + "'")
            self.projectManager.importProject(oldProjectFilePath, projectFilePath)

