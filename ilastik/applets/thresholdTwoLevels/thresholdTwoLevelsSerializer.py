from __future__ import absolute_import
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
from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialDictSlot, SerialBlockSlot
from .opThresholdTwoLevels import ThresholdMethod

class ThresholdTwoLevelsSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
        slots = [SerialSlot(operator.CurOperator, selfdepends=True),
                 SerialSlot(operator.MinSize, selfdepends=True),
                 SerialSlot(operator.MaxSize, selfdepends=True),
                 SerialSlot(operator.HighThreshold, selfdepends=True),
                 SerialSlot(operator.LowThreshold, selfdepends=True),
                 SerialDictSlot(operator.SmootherSigma, selfdepends=True),
                 SerialSlot(operator.Channel, selfdepends=True),
                 SerialSlot(operator.CoreChannel, selfdepends=True),
                 SerialBlockSlot(operator.CachedOutput,
                                 operator.CacheInput,
                                 operator.CleanBlocks,
                                 name='CachedThresholdLabels',
                                 subname='threshold{:03d}',
                                 selfdepends=False,
                                 shrink_to_bb=False,
                                 compression_level=1) ]

        super(self.__class__, self).__init__(projectFileGroupName, slots, operator)

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath, headless=False):
        """
        Override from AppletSerializer.
        Implement any additional deserialization that wasn't already accomplished by our list of serializable slots.
        
        In our case, we use this function to maintain backwards compatibility with old projects, which used different slots.
        """
        # We used to store a separate threshold value for the 'simple' threshold parameter,
        # but now we re-use the 'low threshold' slot for both 'simple' and 'hysteresis' modes.
        method = self.operator.CurOperator.value
        if method == ThresholdMethod.SIMPLE and 'SingleThreshold' in list(topGroup.keys()):
            threshold = topGroup['SingleThreshold'].value
            self.operator.LowThreshold.setValue(threshold)

        # We used to always compute cores from the same channel as the 'final' threshold input.
        # If the user has an old project file, make sure channels are matching by default.
        if method in (ThresholdMethod.HYSTERESIS, ThresholdMethod.IPHT) \
        and 'Channel' in list(topGroup.keys()) \
        and 'CoreChannel' not in list(topGroup.keys()):
            channel = topGroup['Channel'].value
            self.operator.CoreChannel.setValue(channel)
