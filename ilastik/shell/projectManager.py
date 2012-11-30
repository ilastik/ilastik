import os
import copy
import h5py
import logging
logger = logging.getLogger(__name__)

import traceback

import ilastik
from ilastik import isVersionCompatible

class ProjectManager(object):
    
    class ProjectVersionError(RuntimeError):
        def __init__(self, projectVersion, expectedVersion):
            RuntimeError.__init__(self, "Incompatible project version: {} (Expected: {})".format(projectVersion, expectedVersion) )
            self.projectVersion = projectVersion
            self.expectedVersion = expectedVersion
    
    class FileMissingError(RuntimeError):
        pass

    class SaveError(RuntimeError):
        pass
    
    def __init__(self, workflowClass):
        self.currentProjectFile = None
        self.currentProjectPath = None
        self.currentProjectIsReadOnly = False
        
        self._workflowClass = workflowClass
        self.workflow = workflowClass()

    @property
    def _applets(self):
        return self.workflow.applets

    def createBlankProjectFile(self, projectFilePath):
        """
        Create a new ilp file at the given path and initialize it with a project version.
        """
        # Create the blank project file
        h5File = h5py.File(projectFilePath, "w")
        h5File.create_dataset("ilastikVersion", data=ilastik.__version__)
        
        return h5File        

    def openProjectFile(self, projectFilePath):
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
            # Must use importProject() for old project files.
            raise ProjectManager.ProjectVersionError(projectVersion, ilastik.__version__)
        
        return (hdf5File, readOnly)

    def loadProject(self, hdf5File, projectFilePath, readOnly):
        """
        Load the data from the given hdf5File (which should already be open).
        """
        self.closeCurrentProject()

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
            logger.error("Project Open Action failed due to the following exception:")
            traceback.print_exc()
            logger.error("Aborting Project Open Action")
            self.closeCurrentProject()

            raise e
        finally:
            for aplt in self._applets:
                aplt.progressSignal.emit(100)

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
            self.takeSnapshotAndLoadIt(newPath)
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
        
    def takeSnapshotAndLoadIt(self, newPath):
        """
        This is effectively a "save as", but is slower because the operators are totally re-loaded.
        All caches, etc. will be lost.
        """
        self.saveProjectSnapshot( newPath )
        hdf5File, readOnly = self.openProjectFile( newPath )
        self.loadProject(hdf5File, newPath, readOnly)

    def importProject(self, importedFilePath, newProjectFile, newProjectFilePath):
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

        self.loadProject(importedFile, importedFilePath, True)
        
        # Export the current workflow state to the new file.
        # (Somewhat hacky: We temporarily swap the new file object as our current one during the save.)
        origProjectFile = self.currentProjectFile
        self.currentProjectFile = newProjectFile
        self.currentProjectPath = newProjectFilePath
        self.currentProjectIsReadOnly = False
        self.saveProject()
        self.currentProjectFile = origProjectFile

        # Close the original project
        self.closeCurrentProject()

        # Reload the workflow from the new file
        self.loadProject(newProjectFile, newProjectFilePath, False)

    def closeCurrentProject(self):
        self.unloadAllApplets()
        if self.currentProjectFile is not None:
            self.currentProjectFile.close()
            self.currentProjectFile = None
            self.currentProjectPath = None
            self.currentProjectIsReadOnly = False

    def unloadAllApplets(self):
        """
        Unload all applets into a blank state.
        """
        for applet in self._applets:
            # Unload the project data
            for item in applet.dataSerializers:
                item.unload()

    def isProjectDataDirty(self):
        """
        Check all serializable items in our workflow if they have any unsaved data.
        """
        if self.currentProjectFile is None:
            return False

        unSavedDataExists = False
        for applet in self._applets:
            for item in applet.dataSerializers:
                if unSavedDataExists:
                    break
                else:
                    unSavedDataExists = item.isDirty()
        return unSavedDataExists
