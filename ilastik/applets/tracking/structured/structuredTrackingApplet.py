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

from opStructuredTracking import OpStructuredTracking
from structuredTrackingSerializer import StructuredTrackingSerializer

class StructuredTrackingApplet(StandardApplet):
    def __init__( self, name="Structured Tracking", workflow=None, projectFileGroupName="StructuredTracking" ):
        super(StructuredTrackingApplet, self).__init__( name=name, workflow=workflow )
        self._serializableItems = [ StructuredTrackingSerializer(self.topLevelOperator, projectFileGroupName) ]
        self.busy = False

    @property
    def singleLaneOperatorClass( self ):
        return OpStructuredTracking

    @property
    def broadcastingSlots( self ):
        return []

    @property
    def singleLaneGuiClass( self ):
        from structuredTrackingGui import StructuredTrackingGui
        return StructuredTrackingGui

    @property
    def dataSerializers(self):
        return self._serializableItems
