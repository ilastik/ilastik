import h5py
import logging
logger = logging.getLogger(__name__)

class HeadlessShell(object):
    def __init__(self):
        self.currentProjectFile = None
        self.currentProjectPath = None
        self._applets = []
        self.currentImageIndex = -1

    def addApplet(self, app):
        self._applets.append(app)

    def openProjectFile(self, projectFilePath):
        logger.info("Opening Project: " + projectFilePath)

        # Open the file as an HDF5 file
        hdf5File = h5py.File(projectFilePath)
        self.loadProject(hdf5File, projectFilePath)

    def loadProject(self, hdf5File, projectFilePath):
        """
        Load the data from the given hdf5File (which should already be open).
        """
        self.closeCurrentProject()

        assert self.currentProjectFile is None

        # Save this as the current project
        self.currentProjectFile = hdf5File
        self.currentProjectPath = projectFilePath
        # Applet serializable items are given the whole file (root group)
        for applet in self._applets:
            for item in applet.dataSerializers:
                assert item.base_initialized, "AppletSerializer subclasses must call AppletSerializer.__init__ upon construction."
                item.deserializeFromHdf5(self.currentProjectFile, projectFilePath)

    def saveProject(self):
        logger.debug("Save Project triggered")

        assert self.currentProjectFile != None
        assert self.currentProjectPath != None

        # Applet serializable items are given the whole file (root group) for now
        for applet in self._applets:
            for item in applet.dataSerializers:
                assert item.base_initialized, "AppletSerializer subclasses must call AppletSerializer.__init__ upon construction."
                if item.isDirty():
                    item.serializeToHdf5(self.currentProjectFile, self.currentProjectPath)

        # Flush any changes we made to disk, but don't close the file.
        self.currentProjectFile.flush()

    def closeCurrentProject(self):
        self.unloadAllApplets()
        if self.currentProjectFile is not None:
            self.currentProjectFile.close()
            self.currentProjectFile = None

    def unloadAllApplets(self):
        """
        Unload all applets into a blank state.
        """
        for applet in self._applets:
            # Unload the project data
            for item in applet.dataSerializers:
                item.unload()

    def changeCurrentInputImageIndex(self, newImageIndex):
        if newImageIndex != self.currentImageIndex:
            # Alert each central widget and viewer control widget that the image selection changed
            for i in range( len(self._applets) ):
                self._applets[i].gui.setImageIndex(newImageIndex)
                
            self.currentImageIndex = newImageIndex

