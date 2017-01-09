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

#from opWatershedSegmentation import OpCachedWatershedSegmentation
from opWatershedSegmentation import OpWatershedSegmentation
from watershedSegmentationSerializer import WatershedSegmentationSerializer

class WatershedSegmentationApplet( StandardApplet ):
    """
    applet for the watershed segmentation
    """
    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(WatershedSegmentationApplet, self).__init__(guiName, workflow)
        self._serializableItems = [ WatershedSegmentationSerializer(self.topLevelOperator, projectFileGroupName) ]

    @property
    def singleLaneOperatorClass(self):
        return OpWatershedSegmentation
        #return OpCachedWatershedSegmentation

    @property
    def broadcastingSlots(self):
        """
        Only needed for multiple image lanes 
        (must be inplemented for all image lanes)
        Mainly to restore the gui-parameters

        Needed to have these inputSlots (and their values) 
        available for other image lanes, means, that if you have 
        30 images for each ImageInput, change from one to another 
        Image-tuple, the parameters must stay the same.

        :return: the name of the slots as list of string, e.g. ['ChannelSelection', 'BrushValue;]
        :rtype: list of str
        """
        return [ ]

    @property
    def singleLaneGuiClass(self):
        from watershedSegmentationGui import WatershedSegmentationGui
        return WatershedSegmentationGui

    @property
    def dataSerializers(self):
        return self._serializableItems

