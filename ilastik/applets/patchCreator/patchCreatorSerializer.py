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
from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot

class PatchCreatorSerializer(AppletSerializer):
    """Serializes the user's settings in the "Steerable Pyramid"
    applet to an ilastik v0.6 project file.

    """
    def __init__(self, topLevelOperator, projectFileGroupName):
        slots = [SerialSlot(topLevelOperator.PatchWidth, selfdepends=True),
                 SerialSlot(topLevelOperator.PatchHeight, selfdepends=True),
                 SerialSlot(topLevelOperator.PatchOverlapVertical, selfdepends=True),
                 SerialSlot(topLevelOperator.PatchOverlapHorizontal, selfdepends=True),
                 SerialSlot(topLevelOperator.GridStartVertical, selfdepends=True),
                 SerialSlot(topLevelOperator.GridStartHorizontal, selfdepends=True),
                 SerialSlot(topLevelOperator.GridWidth, selfdepends=True),
                 SerialSlot(topLevelOperator.GridHeight, selfdepends=True)]

        super(PatchCreatorSerializer, self).__init__(projectFileGroupName,
                                                         slots=slots)
        self.topLevelOperator = topLevelOperator
