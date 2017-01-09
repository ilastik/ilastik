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
#           http://ilastik.org/license.html
###############################################################################
from ilastik.applets.base.standardApplet import StandardApplet

from opWatershedSegmentation import OpCachedWatershedSegmentation
from watershedSegmentationSerializer import WatershedSegmentationSerializer

class WatershedSegmentationApplet( StandardApplet ):
    """
    Distance-transform-based watershed applet
    """
    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(WatershedSegmentationApplet, self).__init__(guiName, workflow)
        self._serializableItems = [ WatershedSegmentationSerializer(self.topLevelOperator, projectFileGroupName) ]

    @property
    def singleLaneOperatorClass(self):
        return OpCachedWatershedSegmentation

    @property
    def broadcastingSlots(self):
        return [ 'FreezeCache',
                 'ChannelSelection',
                 'Pmin',
                 'MinMembraneSize',
                 'MinSegmentSize',
                 'SigmaMinima',
                 'SigmaWeights',
                 'GroupSeeds' ]

    @property
    def singleLaneGuiClass(self):
        from watershedSegmentationGui import WatershedSegmentationGui
        return WatershedSegmentationGui

    @property
    def dataSerializers(self):
        return self._serializableItems
