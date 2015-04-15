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

from opCropThresholdTwoLevels import OpCropThresholdTwoLevels
from cropThresholdTwoLevelsSerializer import CropThresholdTwoLevelsSerializer

class CropThresholdTwoLevelsApplet( StandardApplet ):
    """
    This is a crop thresholding applet
    """
    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(self.__class__, self).__init__( guiName, workflow )
        self._serializableItems = [ CropThresholdTwoLevelsSerializer(self.topLevelOperator, projectFileGroupName) ]
        
    @property
    def singleLaneOperatorClass(self):
        return OpCropThresholdTwoLevels

    @property
    def broadcastingSlots(self):
        return [ 'MinSize',
                 'MaxSize',
                 'HighThreshold',
                 'LowThreshold',
                 'SmootherSigma',
                 'CurOperator',
                 'SingleThreshold',
                 'Channel' ]
    
    @property
    def singleLaneGuiClass(self):
        from cropThresholdTwoLevelsGui import CropThresholdTwoLevelsGui
        return CropThresholdTwoLevelsGui

    @property
    def dataSerializers(self):
        return self._serializableItems
