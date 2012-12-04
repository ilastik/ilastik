import os
import copy
import h5py
import logging
logger = logging.getLogger(__name__)

import traceback

import ilastik
from ilastik import isVersionCompatible

class ProjectManager(object):

    #########################
    ## Error types
    #########################    

    class ProjectVersionError(RuntimeError):
        def __init__(self, projectVersion, expectedVersion):
            RuntimeError.__init__(self, "Incompatible project version: {} (Expected: {})".format(projectVersion, expectedVersion) )
            self.projectVersion = projectVersion
            self.expectedVersion = expectedVersion
    
    class FileMissingError(RuntimeError):
        pass

    class SaveError(RuntimeError):
        pass

    #########################
    ## Class methods
    #########################    
    
    @classmethod
    def createBlankProjectFile(cls, projectFilePath):
        """
        Create a new ilp file at the given path and initialize it with a project version.
        If a file already existed at that location, it will be overwritten with a blank project.
        """
        # Create the blank project file
        h5File = h5py.File(projectFilePath, "w")
        h5File.create_dataset("ilastikVersion", data=ilastik.__version__)
        
        return h5File

    @classmethod
    def openProjectFile(cls, projectFilePath):
        """
        Attempt to open the given path to an existing project file.
        If it doesn't exist, raise a ``ProjectManager.FileMissingError``.
        If its version is outdated, raise a ``ProjectManager.ProjectVersionError.``
        """
        logger.info("Opening Project: " + projectFilePath)

        if not os.path.exists(projectFilePath):
            raise ProjectManager.FileMissingError()

        # Open the file as an HDF5 file
        try:
            hdf5File = h5py.File(projectFilePath)
            readOnly = False
        except IOError:
            # Maybe the project is read-only
            hdf5File = h5py.File(projectFilePath, 'r')
            readOnly = True

        projectVersion = "0.5"
        if "ilastikVersion" in hdf5File.keys():
            projectVersion = hdf5File["ilastikVersion"].value

        # FIXME: version comparison
        if not isVersionCompatible(projectVersion):
            # Must use _importProject() for old project files.
            raise ProjectManager.ProjectVersionError(projectVersion, ilastik.__version__)
        
        return (hdf5File, readOnly)

    #########################
    ## Public methods
    #########################    

    def __init__(self, workflowClass, hdf5File, projectFilePath, readOnly, importFromPath=None, headless=False):
        """
        Constructor.
        
        :param workflowClass: A subclass of ilastik.workflow.Workflow (the class, not an instance).
        :param hdf5File: An already-open h5py.File, usually created via ``ProjectManager.createBlankProjectFile``
        :param projectFilePath: The path to the file represented in the ``hdf5File`` parameter.
        :param readOnly: Set to True if the project file should NOT be modified.
        :param importFromPath: If the project should be overwritten using data imported from a different project, set this parameter to the other project's filepath.
        """
        # Instantiate the workflow.
        self.workflow = workflowClass(headless=headless)

        self.currentProjectFile = None
        self.currentProjectPath = None
        self.currentProjectIsReadOnly = False

        if importFromPath is None:
            # Normal load        
            self._loadProject(hdf5File, projectFilePath, readOnly)
        else:
            assert not readOnly, "Can't import into a read-only file."
            self._importProject(importFromPath, hdf5File, projectFilePath)

    def __del__(self):
        try:
            self._closeCurrentProject()
        except Exception,e:
            traceback.print_exc()
            raise e


    def getDirtyAppletNames(self):
        """
        Check all serializable items in our workflow if they have any unsaved data.
        """
        if self.currentProjectFile is None:
            return []

        dirtyAppletNames = []
        for applet in self._applets:
            for item in applet.dataSerializers:
                if item.isDirty():
                    dirtyAppletNames.append(applet.name)
        return dirtyAppletNames

    def saveProject(self):
        logger.debug("Save Project triggered")
        assert self.currentProjectFile != None
        assert self.currentProjectPath != None
        assert not self.currentProjectIsReadOnly, "Can't save a read-only project"

        # Minor GUI nicety: Pre-activate the progress signals for dirty applets so
        #  the progress manager treats these tasks as a group instead of several sequential jobs.
        for aplt in self._applets:
            for ser in aplt.dataSerializers:
                if ser.isDirty():
                    aplt.progressSignal.emit(0)
        try:
            # Applet serializable items are given the whole file (root group) for now
            for aplt in self._applets:
                for item in aplt.dataSerializers:
                    assert item.base_initialized, "AppletSerializer subclasses must call AppletSerializer.__init__ upon construction."
                    if item.isDirty():
                        item.serializeToHdf5(self.currentProjectFile, self.currentProjectPath)
        except Exception, err:
            logger.error("Project Save Action failed due to the following exception:")
            traceback.print_exc()
            raise ProjectManager.SaveError( str(err) )
        finally:
            # Flush any changes we made to disk, but don't close the file.
            self.currentProjectFile.flush()
            
            for applet in self._applets:
                applet.progressSignal.emit(100)

    def saveProjectSnapshot(self, snapshotPath):
        """
        Copy the project file as it is, then serialize any dirty state into the copy.
        Original serializers and project file should not be touched.
        """
        with h5py.File(snapshotPath, 'w') as snapshotFile:
            # Minor GUI nicety: Pre-activate the progress signals for dirty applets so
            #  the progress manager treats these tasks as a group instead of several sequential jobs.
            for aplt in self._applets:
                for ser in aplt.dataSerializers:
                    if ser.isDirty():
                        aplt.progressSignal.emit(0)

            # Start by copying the current project state into the file
            # This should be faster than serializing everything from scratch
            for key in self.currentProjectFile.keys():
                snapshotFile.copy(self.currentProjectFile[key], key)

            try:
                # Applet serializable items are given the whole file (root group) for now
                for aplt in self._applets:
                    for item in aplt.dataSerializers:
                        assert item.base_initialized, "AppletSerializer subclasses must call AppletSerializer.__init__ upon construction."

                        if item.isDirty():
                            # Use a COPY of the serializer, so the original serializer doesn't forget it's dirty state
                            itemCopy = copy.copy(item)
                            itemCopy.serializeToHdf5(snapshotFile, snapshotPath)
            except Exception, err:
                logger.error("Project Save Snapshot Action failed due to the following exception:")
                traceback.print_exc()
                raise ProjectManager.SaveError(str(err))
            finally:
                # Flush any changes we made to disk, but don't close the file.
                snapshotFile.flush()
                
                for applet in self._applets:
                    applet.progressSignal.emit(100)
                    
    def saveProjectAs(self, newPath):
        """
        Implement "Save As"
        Equivalent to the following (but done without closing the current project file):
        1) rename Old.ilp -> New.ilp
        2) touch Old.ilp
        3) copycontents New.ilp -> Old.ilp
        4) Save current applet state to current project (New.ilp)
        
        Postconditions: - Original project state is saved to a new file with the original name.
                        - Current project file is still open, but has a new name.
                        - Current project file has been saved (it is in sync with the applet states)
        """
        # If our project is read-only, we can't be efficient.
        # We have to take a snapshot, then close our current project and open the snapshot
        if self.currentProjectIsReadOnly:
            self._takeSnapshotAndLoadIt(newPath)
            return

        oldPath = self.currentProjectPath
        try:
            os.rename( oldPath, newPath )
        except OSError, err:
            msg = 'Could not rename your project file to:\n'
            msg += newPath + '\n'
            msg += 'One common cause for this is that the new location is on a different disk.\n'
            msg += 'Please try "Take Snapshot" instead.'
            msg += '(Error was: ' + str(err) + ')'
            logger.error(msg)
            raise ProjectManager.SaveError(msg)

        # The file has been renamed
        self.currentProjectPath = newPath

        # Copy the contents of the current project file to a newly-created file (with the old name)        
        with h5py.File(oldPath, 'w') as oldFile:
            for key in self.currentProjectFile.keys():
                oldFile.copy(self.currentProjectFile[key], key)

        # Save the current project state
        self.saveProject()
        
    #########################
    ## Private methods
    #########################    

    @property
    def _applets(self):
        return self.workflow.applets

    def _loadProject(self, hdf5File, projectFilePath, readOnly):
        """
        Load the data from the given hdf5File (which should already be open).
        """
        assert self.currentProjectFile is None

        # Minor GUI nicety: Pre-activate the progress signals for all applets so
        #  the progress manager treats these tasks as a group instead of several sequential jobs.
        for aplt in self._applets:
            aplt.progressSignal.emit(0)

        # Save this as the current project
        self.currentProjectFile = hdf5File
        self.currentProjectPath = projectFilePath
        self.currentProjectIsReadOnly = readOnly
        try:
            # Applet serializable items are given the whole file (root group)
            for aplt in self._applets:
                for item in aplt.dataSerializers:
                    assert item.base_initialized, "AppletSerializer subclasses must call AppletSerializer.__init__ upon construction."
                    item.deserializeFromHdf5(self.currentProjectFile, projectFilePath)
        except Exception, e:
            logger.error("Project could not be loaded due to the following exception:")
            traceback.print_exc()
            logger.error("Aborting Project Open Action")
            self._closeCurrentProject()

            raise e
        finally:
            for aplt in self._applets:
                aplt.progressSignal.emit(100)

    def _takeSnapshotAndLoadIt(self, newPath):
        """
        This is effectively a "save as", but is slower because the operators are totally re-loaded.
        All caches, etc. will be lost.
        """
        self.saveProjectSnapshot( newPath )
        hdf5File, readOnly = ProjectManager.openProjectFile( newPath )
        self._loadProject(hdf5File, newPath, readOnly)

    def _importProject(self, importedFilePath, newProjectFile, newProjectFilePath):
        """
        Load the data from a project and save it to a different project file.
        
        importedFilePath - The path to a (not open) .ilp file to import data from
        newProjectFile - An hdf5 handle to a new .ilp to load data into (must be open already)
        newProjectFilePath - The path to the new .ilp we're loading.
        """
        importedFilePath = os.path.abspath(importedFilePath)
        
        # Open and load the original project file
        try:
            importedFile = h5py.File(importedFilePath, 'r')
        except:
            logger.error("Error opening file: " + importedFilePath)
            raise

        # Load the imported project into the workflow state
        self._loadProject(importedFile, importedFilePath, True)
        
        # Export the current workflow state to the new file.
        # (Somewhat hacky: We temporarily swap the new file object as our current one during the save.)
        origProjectFile = self.currentProjectFile
        self.currentProjectFile = newProjectFile
        self.currentProjectPath = newProjectFilePath
        self.currentProjectIsReadOnly = False
        self.saveProject()
        self.currentProjectFile = origProjectFile

        # Close the original project
        self._closeCurrentProject()

        # Discard the old workflow and make a new one
        self.workflow = self.workflow.__class__()

        # Load the new file.
        self._loadProject(newProjectFile, newProjectFilePath, False)

    def _closeCurrentProject(self):
        self.workflow.cleanUp()
        self.workflow = None
        if self.currentProjectFile is not None:
            self.currentProjectFile.close()
            self.currentProjectFile = None
            self.currentProjectPath = None
            self.currentProjectIsReadOnly = False
