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
from ilastik.applets.base.applet import Applet
from projectMetadataSerializer import ProjectMetadataSerializer, Ilastik05ProjectMetadataDeserializer
from projectMetadata import ProjectMetadata

class ProjectMetadataApplet( Applet ):
    """
    This applet allows the user to enter project metadata (e.g. Project name, labeler name, etc.).
    
    Note that this applet does not affect the processing pipeline and has no top-level operator.
    """
    def __init__( self ):
        Applet.__init__( self, "Project Metadata" )
        
        self._projectMetadata = ProjectMetadata()

        self._gui = None # Created on first acess

        self._serializableItems = [ ProjectMetadataSerializer(self._projectMetadata, "ProjectMetadata"),
                                    Ilastik05ProjectMetadataDeserializer(self._projectMetadata) ]

    def getMultiLaneGui(self):
        if self._gui is None:
            from projectMetadataGui import ProjectMetadataGui
            self._gui = ProjectMetadataGui(self._projectMetadata)
        return self._gui

    @property
    def topLevelOperator(self):
        # This applet provides a GUI and serializers, but does not affect the graph in any way.
        return None

    @property
    def dataSerializers(self):
        return self._serializableItems
