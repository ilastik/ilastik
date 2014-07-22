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
from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialDictSlot, SerialHdf5BlockSlot

class ThresholdTwoLevelsSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
        slots = [SerialSlot(operator.CurOperator, selfdepends=True),
                 SerialSlot(operator.MinSize, selfdepends=True),
                 SerialSlot(operator.MaxSize, selfdepends=True),
                 SerialSlot(operator.HighThreshold, selfdepends=True),
                 SerialSlot(operator.LowThreshold, selfdepends=True),
                 SerialSlot(operator.SingleThreshold, selfdepends=True),
                 SerialDictSlot(operator.SmootherSigma, selfdepends=True),
                 SerialSlot(operator.Channel, selfdepends=True),
                 SerialHdf5BlockSlot(operator.OutputHdf5,
                                     operator.InputHdf5,
                                     operator.CleanBlocks,
                                     name="CachedThresholdOutput")
                ]

        super(self.__class__, self).__init__(projectFileGroupName, slots=slots)
