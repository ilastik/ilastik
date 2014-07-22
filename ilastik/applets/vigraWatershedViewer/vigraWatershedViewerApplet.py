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

from opVigraWatershedViewer import OpVigraWatershedViewer
from vigraWatershedViewerSerializer import VigraWatershedViewerSerializer

class VigraWatershedViewerApplet( StandardApplet ):
    """
    Viewer for watershed results, with minimal configuration controls.
    """
    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(VigraWatershedViewerApplet, self).__init__(guiName, workflow)
        self._serializableItems = [ VigraWatershedViewerSerializer(self.topLevelOperator, projectFileGroupName) ]
        
    @property
    def singleLaneOperatorClass(self):
        return OpVigraWatershedViewer

    @property
    def broadcastingSlots(self):
        return ['InputChannelIndexes', 'WatershedPadding', 'FreezeCache', 'CacheBlockShape', 'SeedThresholdValue', 'MinSeedSize' ]
    
    @property
    def singleLaneGuiClass(self):
        from vigraWatershedViewerGui import VigraWatershedViewerGui
        return VigraWatershedViewerGui

    @property
    def dataSerializers(self):
        return self._serializableItems
