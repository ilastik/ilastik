import os
import logging
logger = logging.getLogger(__name__)

from ilastik.shell.projectManager import ProjectManager

class HeadlessShell(object):
    """
    For now, this class is just a stand-in for the GUI shell (used when running from the command line).
    """
    
    def __init__(self, workflowClass):
        self._workflowClass = workflowClass
        self.projectManager = None

    @property
    def workflow(self):
        return self.projectManager.workflow

    def createBlankProjectFile(self, projectFilePath):
        hdf5File = ProjectManager.createBlankProjectFile(projectFilePath)
        readOnly = False
        self.projectManager = ProjectManager( self._workflowClass, hdf5File, projectFilePath, readOnly, headless=True )

    def openProjectPath(self, projectFilePath):
        try:
            # Open the project file
            hdf5File, readOnly = ProjectManager.openProjectFile(projectFilePath)
            
            # Create our project manager
            # This instantiates the workflow and applies all settings from the project.
            self.projectManager = ProjectManager( self._workflowClass, hdf5File, projectFilePath, readOnly, headless=True )

        except ProjectManager.ProjectVersionError:
            # Couldn't open project.  Try importing it.
            oldProjectFilePath = projectFilePath
            name, ext = os.path.splitext(oldProjectFilePath)
    
            # Create a brand new project file.
            projectFilePath = name + "_imported" + ext
            logger.info("Importing project as '" + projectFilePath + "'")
            hdf5File = ProjectManager.createBlankProjectFile(projectFilePath)

            # Create the project manager.
            # Here, we provide an additional parameter: the path of the project we're importing from. 
            self.projectManager = ProjectManager( self._workflowClass, hdf5File, projectFilePath, readOnly=False, importFromPath=oldProjectFilePath, headless=True )

