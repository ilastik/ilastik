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
from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialBlockSlot, SerialListSlot

class WsdtSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
        slots = [ SerialListSlot(operator.ChannelSelections),
                  SerialSlot(operator.Pmin), 
                  SerialSlot(operator.MinMembraneSize), 
                  SerialSlot(operator.MinSegmentSize), 
                  SerialSlot(operator.SigmaMinima), 
                  SerialSlot(operator.SigmaWeights), 
                  SerialSlot(operator.GroupSeeds),
                  SerialSlot(operator.PreserveMembranePmaps),
                  SerialBlockSlot(operator.Superpixels,
                                  operator.SuperpixelCacheInput,
                                  operator.CleanBlocks,
                                  name='Superpixels',
                                  subname='superpixels{:03d}',
                                  selfdepends=False,
                                  shrink_to_bb=False,
                                  compression_level=1) ]
        super(WsdtSerializer, self).__init__(projectFileGroupName, slots=slots, operator=operator)
