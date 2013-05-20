import os
import copy
import h5py
import logging
logger = logging.getLogger(__name__)

import traceback

import ilastik
from ilastik import isVersionCompatible

class ProjectManager(object):
    """
    This class manages creating, opening, importing, saving, and closing project files.
    It instantiates a workflow object and loads its applets with the settings from the 
    project file by using the applets' serializer objects.
    
    To open a project file, instantiate a ProjectManager object.
    To close the project file, delete the ProjectManager object.
    
    Once the project manager has been instantiated, clients can access its ``workflow``
    member for direct access to its applets and their top-level operators.
    """

    #########################
    ## Error types
    #########################    

    class ProjectVersionError(RuntimeError):
        """
        Raised if an attempt is made to open a project file that was generated with an old version of ilastik.
        """
        def __init__(self, projectVersion, expectedVersion):
            RuntimeError.__init__(self, "Incompatible project version: {} (Expected: {})".format(projectVersion, expectedVersion) )
            self.projectVersion = projectVersion
            self.expectedVersion = expectedVersion
    
    class FileMissingError(RuntimeError):
        """
        Raised if an attempt is made to open a project file that can't be found on disk.
        """
        pass

    class SaveError(RuntimeError):
        """
        Raised if saving the project results in an error of some kind.
        The project file will be in an UNKNOWN and potentially inconsistent state!
        """
        pass

    #########################
    ## Class methods
    #########################    
    
    @classmethod
    def createBlankProjectFile(cls, projectFilePath, workflow_class, workflow_cmdline_args):
        """
        Class method.
        Create a new ilp file at the given path and initialize it with a project version.
        If a file already existed at that location, it will be overwritten with a blank project.
        """
        # Create the blank project file
        h5File = h5py.File(projectFilePath, "w")
        h5File.create_dataset("ilastikVersion", data=ilastik.__version__)
        h5File.create_dataset("workflowName", data=workflow_class.__name__)
        if workflow_cmdline_args is not None:
            h5File.create_dataset("workflow_cmdline_args", data=workflow_cmdline_args)
        
        return h5File

    @classmethod
    def getWorkflowName(self, projectFile):
        return str( projectFile['workflowName'][()] )

    @classmethod
    def openProjectFile(cls, projectFilePath):
        """
        Class method.
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

    def __init__(self, workflowClass, headless=False, workflow_cmdline_args=None):
        """
        Constructor.
        
        :param workflowClass: A subclass of ilastik.workflow.Workflow (the class, not an instance).
        :param headless: A bool that is passed to the workflow constructor, 
                         indicating whether or not the workflow should be opened in 'headless' mode.
        :param workflow_cmdline_args: A list of strings from the command-line to configure the workflow.
        """
        if workflow_cmdline_args is None:
            workflow_cmdline_args = []

        # Init
        self.workflow = None
        self.currentProjectFile = None
        self.currentProjectPath = None
        self.currentProjectIsReadOnly = False

        # Instantiate the workflow.
        self._workflowClass = workflowClass
        self._workflow_cmdline_args = workflow_cmdline_args or []
        self._headless = headless
        
        #the workflow class has to be specified at this point
        assert workflowClass is not None
        self.workflow = workflowClass(headless, workflow_cmdline_args)
    
    
    def cleanUp(self):
        """
        Should be called when the Projectmanager is canceled. Closes the project file.
        """
        try:
            self._closeCurrentProject()
        except Exception,e:
            traceback.print_exc()
            raise e


    def getDirtyAppletNames(self):
        """
        Check the serializers for every applet in the workflow.
        If a serializer declares itself to be dirty (i.e. it is-out-of-sync with the applet's operator),
        then the applet's name is appended to the resulting list.
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
        """
        Update the project file with the state of the current workflow settings.
        Must not be called if the project file was opened in read-only mode.
        """
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
            
            #save the current workflow as standard workflow
            if "workflowName" in self.currentProjectFile:
                del self.currentProjectFile["workflowName"]
            self.currentProjectFile.create_dataset("workflowName",data = self.workflow.workflowName)

            if "workflow_cmdline_args" in self.currentProjectFile:
                del self.currentProjectFile["workflow_cmdline_args"]
            self.currentProjectFile.create_dataset(name='workflow_cmdline_args', data=self._workflow_cmdline_args)

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
        Equivalent to the following steps (but done without closing the current project file):

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
            self.currentProjectFile.close()
            if os.path.isfile(newPath):
                os.remove(newPath)
            os.rename( oldPath, newPath )
            self.currentProjectFile = h5py.File(newPath)
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
        with h5py.File(oldPath, 'a') as oldFile:
            for key in self.currentProjectFile.keys():
                oldFile.copy(self.currentProjectFile[key], key)
        
        for aplt in self._applets:
            for item in aplt.dataSerializers:
                item.updateWorkingDirectory(newPath,oldPath)
        
        # Save the current project state
        self.saveProject()
        
    #########################
    ## Private methods
    #########################    

    @property
    def _applets(self):
        if self.workflow is not None:
            return self.workflow.applets
        else:
            return []

    def _loadProject(self, hdf5File, projectFilePath, readOnly):
        """
        Load the data from the given hdf5File (which should already be open).
        
        :param hdf5File: An already-open h5py.File, usually created via ``ProjectManager.createBlankProjectFile``
        :param projectFilePath: The path to the file represented in the ``hdf5File`` parameter.
        :param readOnly: Set to True if the project file should NOT be modified.
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
                    item.ignoreDirty = True
                                        
                    if item.caresOfHeadless:
                        item.deserializeFromHdf5(self.currentProjectFile, projectFilePath, self._headless)
                    else:
                        item.deserializeFromHdf5(self.currentProjectFile, projectFilePath)

                    item.ignoreDirty = False
        except:
            logger.error("Project could not be loaded due to the following exception:")
            traceback.print_exc()
            logger.error("Aborting Project Open Action")
            self._closeCurrentProject()
            raise
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

        # Create brand new workflow to load from the new project file.
        self.workflow = self._workflowClass(self._headless, self._workflow_cmdline_args)

        # Load the new file.
        self._loadProject(newProjectFile, newProjectFilePath, False)

    def _closeCurrentProject(self):
        if self.workflow is not None:
            self.workflow.cleanUp()
        self.workflow = None
        if self.currentProjectFile is not None:
            self.currentProjectFile.close()
            self.currentProjectFile = None
            self.currentProjectPath = None
            self.currentProjectIsReadOnly = False
