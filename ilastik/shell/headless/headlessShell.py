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
import re
import logging
logger = logging.getLogger(__name__)

from lazyflow.utility import isUrl
from ilastik.shell.shellAbc import ShellABC
from ilastik.shell.projectManager import ProjectManager

class HeadlessShell(object):
    """
    For now, this class is just a stand-in for the GUI shell (used when running from the command line).
    """

    def __init__(self, workflow_cmdline_args=None):
        self._workflow_cmdline_args = workflow_cmdline_args or []
        self.projectManager = None

    @property
    def workflow(self):
        if self.projectManager is not None:
            return self.projectManager.workflow

    @property
    def currentImageIndex(self):
        return -1

    def createAndLoadNewProject(self, newProjectFilePath, workflow_class):
        hdf5File = ProjectManager.createBlankProjectFile(newProjectFilePath)
        readOnly = False
        self.projectManager = ProjectManager( self,
                                              workflow_class,
                                              headless=True,
                                              workflow_cmdline_args=self._workflow_cmdline_args  )
        self.projectManager._loadProject(hdf5File, newProjectFilePath, readOnly)
        self.projectManager.saveProject()

    @classmethod
    def downloadProjectFromDvid(cls, dvid_key_url):
        dvid_key_url = str(dvid_key_url)
        
        # By convention, command-line users specify the location of the project 
        # keyvalue data using the same format that the DVID API itself uses.
        url_format = "^protocol://hostname/api/node/uuid/kv_instance_name(/key/keyname)?"
        for field in ['protocol', 'hostname', 'uuid', 'kv_instance_name', 'keyname']:
            url_format = url_format.replace( field, '(?P<' + field + '>[^?/]+)' )

        match = re.match( url_format, dvid_key_url )
        if not match:
            # DVID is the only url-based format we support right now.
            # So if it looks like the user gave a URL that isn't a valid DVID node, then error.
            raise RuntimeError("Invalid URL format for DVID key-value data: {}".format(projectFilePath))

        fields = match.groupdict()            
        projectFilePath = ProjectManager.downloadProjectFromDvid( fields['hostname'],
                                                                  fields['uuid'],
                                                                  fields['kv_instance_name'],
                                                                  fields['keyname'] )
        return projectFilePath
        
    def openProjectFile(self, projectFilePath, force_readonly=False):
        # If the user gave a URL to a DVID key, then download the project file from dvid first.
        # (So far, DVID is the only type of URL access we support for project files.)
        if isUrl(projectFilePath):
            projectFilePath = HeadlessShell.downloadProjectFromDvid(projectFilePath)

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
            if "workflow_cmdline_args" in list(hdf5File.keys()):
                if len(hdf5File["workflow_cmdline_args"]) > 0:
                    project_creation_args = list(map(str, hdf5File["workflow_cmdline_args"][...]))

            if workflow_class is None:
                # If the project file has no known workflow, we assume pixel classification
                import ilastik.workflows
                workflow_class = ilastik.workflows.pixelClassification.PixelClassificationWorkflow
                import warnings
                warnings.warn( "Your project file ({}) does not specify a workflow type.  "
                               "Assuming Pixel Classification".format( projectFilePath ) )            
            
            # Create our project manager
            # This instantiates the workflow and applies all settings from the project.
            self.projectManager = ProjectManager( self,
                                                  workflow_class,
                                                  headless=True,
                                                  workflow_cmdline_args=self._workflow_cmdline_args,
                                                  project_creation_args=project_creation_args )
            self.projectManager._loadProject(hdf5File, projectFilePath, readOnly)

        except ProjectManager.FileMissingError:
            logger.error("Couldn't find project file: {}".format( projectFilePath ))
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
            self.projectManager = ProjectManager( self,
                                                  default_workflow,
                                                  headless=True,
                                                  workflow_cmdline_args=self._workflow_cmdline_args,
                                                  project_creation_args=self._workflow_cmdline_args )

            self.projectManager._importProject(oldProjectFilePath, hdf5File, projectFilePath)

    def setAppletEnabled(self, applet, enabled):
        """
        Provided here to satisfy the ShellABC.
        For now, HeadlessShell has no concept of "enabled" or "disabled" applets.
        """
        pass

    def isAppletEnabled(self, applet):
        return False

    def enableProjectChanges(self, enabled):
        """
        Provided here to satisfy the ShellABC.
        For now, HeadlessShell has no mechanism for closing projects.
        """
        pass

    def closeCurrentProject(self):
        if self.projectManager is not None:
            self.projectManager._closeCurrentProject()
            self.projectManager.cleanUp()
            self.projectManager = None


assert issubclass(HeadlessShell, ShellABC), "HeadlessShell does not satisfy the generic shell interface!"
