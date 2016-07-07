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
from ilastik.applets.base.standardApplet import StandardApplet

from opAnnotations import OpAnnotations
from annotationsSerializer import AnnotationsSerializer

class AnnotationsApplet(StandardApplet):
    def __init__( self, name="Annotations", workflow=None, projectFileGroupName="TrackingAnnotations" ):
        super(AnnotationsApplet, self).__init__( name=name, workflow=workflow )
        self._serializableItems = [ AnnotationsSerializer(self.topLevelOperator, projectFileGroupName) ]
        self.busy = False

    @property
    def singleLaneOperatorClass( self ):
        return OpAnnotations

    @property
    def broadcastingSlots( self ):
        return []

    @property
    def singleLaneGuiClass( self ):
        from annotationsGui import AnnotationsGui
        return AnnotationsGui

    @property
    def dataSerializers(self):
        return self._serializableItems
