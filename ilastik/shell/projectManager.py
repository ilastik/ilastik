###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
import os
import gc
import copy
import platform
import h5py
import logging
import time
import tempfile
logger = logging.getLogger(__name__)

import ilastik
from ilastik import isVersionCompatible
from ilastik.utility import log_exception
from ilastik.workflow import getWorkflowFromName
from lazyflow.utility.timer import Timer, timeLogged

try:
    import libdvid
    _has_dvid_support = True
except:
    _has_dvid_support = False

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
    def createBlankProjectFile(cls, projectFilePath, workflow_class=None, workflow_cmdline_args=None, h5_file_kwargs={}):
        """Create a new ilp file at the given path and initialize it with a project version.

        Class method. If a file already exists at the location, it
        will be overwritten with a blank project (i.e. the mode is
        fixed to 'w').

        :param projectFilePath: Full path of the new project (for instance '/tmp/MyProject.ilp').
        :param workflow_class: If not None, add dataset containing the name of the workflow_class.
        :param workflow_cmdline_args: If not None, add dataset containing the commandline arguments.
        :param h5_file_kwargs: Passed directly to h5py.File.__init__(); all standard params except 'mode' are allowed. 
        :rtype: h5py.File

        """
        # Create the blank project file
        if 'mode' in h5_file_kwargs:
            raise ValueError("ProjectManager.createBlankProjectFile(): 'mode' is not allowed as a h5py.File kwarg")
        os.makedirs(os.path.dirname(projectFilePath), exist_ok=True)
        h5File = h5py.File(projectFilePath, mode="w", **h5_file_kwargs)
        h5File.create_dataset("ilastikVersion", data=ilastik.__version__.encode('utf-8'))
        h5File.create_dataset("time", data = time.ctime().encode('utf-8'))
        if workflow_class is not None:
            h5File.create_dataset("workflowName", data=workflow_class.__name__.encode('utf-8'))
        if workflow_cmdline_args is not None and len(workflow_cmdline_args) > 0:
            h5File.create_dataset("workflow_cmdline_args", data=[arg.encode('utf-8') for arg in workflow_cmdline_args])
        
        return h5File

    @classmethod
    def getWorkflowName(self, projectFile):
        return str( projectFile['workflowName'][()].decode('utf-8') )

    @classmethod
    def openProjectFile(cls, projectFilePath, forceReadOnly=False):
        """
        Class method.
        Attempt to open the given path to an existing project file.
        If it doesn't exist, raise a ``ProjectManager.FileMissingError``.
        If its version is outdated, raise a ``ProjectManager.ProjectVersionError.``
        """
        projectFilePath = os.path.expanduser(projectFilePath)
        logger.info("Opening Project: " + projectFilePath)

        if not os.path.exists(projectFilePath):
            raise ProjectManager.FileMissingError(projectFilePath)

        # Open the file as an HDF5 file
        try:
            if forceReadOnly:
                mode = 'r'
            else:
                mode = 'r+'
            hdf5File = h5py.File(projectFilePath, mode)
        except IOError:
            # Maybe we tried 'r+', but the project is read-only
            hdf5File = h5py.File(projectFilePath, 'r')
        readOnly = (hdf5File.mode == 'r')

        projectVersion = "0.5"
        if "ilastikVersion" in list(hdf5File.keys()):
            projectVersion = hdf5File["ilastikVersion"].value.decode('utf-8')
        
        # FIXME: version comparison
        if not isVersionCompatible(projectVersion):
            # Must use _importProject() for old project files.
            raise ProjectManager.ProjectVersionError(projectVersion, ilastik.__version__)
        
        workflow_class = None
        if "workflowName" in list(hdf5File.keys()):
            #if workflow is found in file, take it
            workflowName = hdf5File["workflowName"].value.decode('utf-8')
            workflow_class = getWorkflowFromName(workflowName)
        
        return (hdf5File, workflow_class, readOnly)

    @classmethod
    def downloadProjectFromDvid(cls, hostname, node_uuid, keyvalue_name, project_key=None, local_filepath=None):
        """
        Download a file from a dvid keyvalue data instance and store it to the given local_filepath.
        If no local_filepath is given, create a new temporary file.
        Returns the path to the downloaded file.
        """
        node_service = libdvid.DVIDNodeService(hostname, node_uuid)
        keys = node_service.get_keys(keyvalue_name)
        
        if not project_key:
            if len(keys) == 1:
                # Only one key, so let's try it.
                project_key = keys[0]
            else:
                # Try to find a key that looks like a project file.
                possible_project_keys = [s for s in keys if s.endswith('.ilp')]
                if len(possible_project_keys) == 1:
                    project_key = possible_project_keys[0]
                else:
                    # Too many or too few keys ending with .ilp -- can't decide which one to use!
                    raise RuntimeError("Can't infer project key name from keys in key/value instance.")
        
        if project_key not in keys:
            raise ProjectManager.FileMissingError("Key/value instance does not have required key: {}".format(PROJECT_FILE_KEY))

        file_data = node_service.get(keyvalue_name, project_key)
        if local_filepath is None:
            tempdir = tempfile.mkdtemp()
            local_filepath = os.path.join(tempdir, project_key)
        
        with open(local_filepath, 'w') as local_file:
            local_file.write(file_data)
        
        return local_filepath

    #########################
    ## Public methods
    #########################    

    def __init__(self, shell, workflowClass, headless=False, workflow_cmdline_args=None, project_creation_args=None):
        """
        Constructor.
        
        :param workflowClass: A subclass of ilastik.workflow.Workflow (the class, not an instance).
        :param headless: A bool that is passed to the workflow constructor, 
                         indicating whether or not the workflow should be opened in 'headless' mode.
        :param workflow_cmdline_args: A list of strings from the command-line to configure the workflow.
        """
        # Init
        self.closed = True
        self._shell = shell
        self.workflow = None
        self.currentProjectFile = None
        self.currentProjectPath = None
        self.currentProjectIsReadOnly = False

        # Instantiate the workflow.
        self._workflowClass = workflowClass
        self._workflow_cmdline_args = workflow_cmdline_args or []
        self._project_creation_args = project_creation_args or []
        self._headless = headless
        
        #the workflow class has to be specified at this point
        assert workflowClass is not None
        self.workflow = workflowClass(shell, headless, self._workflow_cmdline_args, self._project_creation_args)
    
    
    def cleanUp(self):
        """
        Should be called when the Projectmanager is canceled. Closes the project file.
        """
        try:
            self._closeCurrentProject()
        except Exception as e:
            log_exception( logger )
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
            for serializer in applet.dataSerializers:
                if serializer.isDirty():
                    dirtyAppletNames.append(applet.name)
        return dirtyAppletNames

    def saveProject(self, force_all_save=False):
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
                    aplt.progressSignal(0)
        try:
            # Applet serializable items are given the whole file (root group) for now
            for aplt in self._applets:
                for serializer in aplt.dataSerializers:
                    assert serializer.base_initialized, "AppletSerializer subclasses must call AppletSerializer.__init__ upon construction."
                    if force_all_save or serializer.isDirty() or serializer.shouldSerialize(self.currentProjectFile):
                        serializer.serializeToHdf5(self.currentProjectFile, self.currentProjectPath)
            
            #save the current workflow as standard workflow
            if "workflowName" in self.currentProjectFile:
                del self.currentProjectFile["workflowName"]
            self.currentProjectFile.create_dataset("workflowName",data = self.workflow.workflowName.encode('utf-8'))

        except Exception as err:
            log_exception( logger, "Project Save Action failed due to the exception shown above." )
            raise ProjectManager.SaveError( str(err) )
        finally:
            # save current time
            if "time" in self.currentProjectFile:
                del self.currentProjectFile["time"]
            self.currentProjectFile.create_dataset("time", data = time.ctime().encode('utf-8'))
            # Flush any changes we made to disk, but don't close the file.
            self.currentProjectFile.flush()
            
            for applet in self._applets:
                applet.progressSignal(100)

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
                        aplt.progressSignal(0)

            # Start by copying the current project state into the file
            # This should be faster than serializing everything from scratch
            for key in list(self.currentProjectFile.keys()):
                snapshotFile.copy(self.currentProjectFile[key], key)

            try:
                # Applet serializable items are given the whole file (root group) for now
                for aplt in self._applets:
                    for serializer in aplt.dataSerializers:
                        assert serializer.base_initialized, "AppletSerializer subclasses must call AppletSerializer.__init__ upon construction."

                        if serializer.isDirty() or serializer.shouldSerialize(self.currentProjectFile):
                            # Use a COPY of the serializer, so the original serializer doesn't forget it's dirty state
                            serializerCopy = copy.copy(serializer)
                            serializerCopy.serializeToHdf5(snapshotFile, snapshotPath)
            except Exception as err:
                log_exception( logger, "Project Save Snapshot Action failed due to the exception printed above." )
                raise ProjectManager.SaveError(str(err))
            finally:
                # save current time
                if "time" in snapshotFile:
                    del snapshotFile["time"]
                snapshotFile.create_dataset("time", data = time.ctime().encode('utf-8'))

                # Flush any changes we made to disk, but don't close the file.
                snapshotFile.flush()
                
                for applet in self._applets:
                    applet.progressSignal(100)
                    
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
        # Furthermore, windows does not permit renaming an open file, so we must take this approach.
        if self.currentProjectIsReadOnly or platform.system() == 'Windows':
            self._takeSnapshotAndLoadIt(newPath)
            return

        oldPath = self.currentProjectPath
        try:
            os.rename( oldPath, newPath )
        except OSError as err:
            msg = 'Could not rename your project file to:\n'
            msg += newPath + '\n'
            msg += 'One common cause for this is that the new location is on a different disk.\n'
            msg += 'Please try "Save Copy As" instead.'
            msg += '(Error was: ' + str(err) + ')'
            logger.error(msg)
            raise ProjectManager.SaveError(msg)

        # The file has been renamed
        self.currentProjectPath = newPath
        
        # Copy the contents of the current project file to a newly-created file (with the old name)
        with h5py.File(oldPath, 'a') as oldFile:
            for key in list(self.currentProjectFile.keys()):
                oldFile.copy(self.currentProjectFile[key], key)
        
        for aplt in self._applets:
            for serializer in aplt.dataSerializers:
                serializer.updateWorkingDirectory(newPath,oldPath)
        
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

    @timeLogged(logger, logging.DEBUG)
    def _loadProject(self, hdf5File, projectFilePath, readOnly):
        """
        Load the data from the given hdf5File (which should already be open).
        
        :param hdf5File: An already-open h5py.File, usually created via ``ProjectManager.createBlankProjectFile``
        :param projectFilePath: The path to the file represented in the ``hdf5File`` parameter.
        :param readOnly: Set to True if the project file should NOT be modified.
        """
        # We are about to create a LOT of tiny objects.
        # Temporarily disable garbage collection while we do this.
        gc.disable()
        
        assert self.currentProjectFile is None

        # Minor GUI nicety: Pre-activate the progress signals for all applets so
        #  the progress manager treats these tasks as a group instead of several sequential jobs.
        for aplt in self._applets:
            aplt.progressSignal(0)

        # Save this as the current project
        self.currentProjectFile = hdf5File
        self.currentProjectPath = projectFilePath
        self.currentProjectIsReadOnly = readOnly
        try:
            # Applet serializable items are given the whole file (root group)
            for aplt in self._applets:
                with Timer() as timer:
                    for serializer in aplt.dataSerializers:
                        assert serializer.base_initialized, "AppletSerializer subclasses must call AppletSerializer.__init__ upon construction."
                        serializer.ignoreDirty = True

                        serializer.deserializeFromHdf5(self.currentProjectFile, projectFilePath, self._headless)

                        serializer.ignoreDirty = False
                logger.debug('Deserializing applet "{}" took {} seconds'.format( aplt.name, timer.seconds() ))
            

            self.closed = False
            # Call the workflow's custom post-load initialization (if any)
            self.workflow.onProjectLoaded( self )

            self.workflow.handleAppletStateUpdateRequested()            
        except:
            msg = "Project could not be loaded due to the exception shown above.\n"
            msg += "Aborting Project Open Action"
            log_exception( logger, msg )
            self._closeCurrentProject()
            raise
        finally:
            gc.enable()
            for aplt in self._applets:
                aplt.progressSignal(100)


    def _takeSnapshotAndLoadIt(self, newPath):
        """
        This is effectively a "save as", but is slower because the operators are totally re-loaded.
        All caches, etc. will be lost.
        """
        self.saveProjectSnapshot( newPath )
        hdf5File, workflowClass, readOnly = ProjectManager.openProjectFile( newPath )
        
        # Close the old project *file*, but don't destroy the workflow.
        assert self.currentProjectFile is not None
        self.currentProjectFile.close()
        self.currentProjectFile = None
        
        # Open the snapshot of the old project that we just made
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
        self.saveProject(force_all_save=True)
        self.currentProjectFile = origProjectFile

        # Close the original project
        self._closeCurrentProject()

        self.currentProjectFile = None

        # Create brand new workflow to load from the new project file.
        self.workflow = self._workflowClass(self._shell, self._headless, self._workflow_cmdline_args, self._project_creation_args)

        # Load the new file.
        self._loadProject(newProjectFile, newProjectFilePath, False)

    def _closeCurrentProject(self):
        if self.closed:
            return
        self.closed = True
        if self.workflow is not None:
            self.workflow.cleanUp()
        if self.currentProjectFile is not None:
            self.currentProjectFile.close()
