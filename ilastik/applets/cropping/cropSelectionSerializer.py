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
import numpy
from ilastik.applets.base.appletSerializer import AppletSerializer, SerialDictSlot, SerialSlot, SerialBlockSlot, SerialListSlot

class CropSelectionSerializer(AppletSerializer):
    """
    Serializes to an ilastik v0.6 project file.
    """
    def __init__(self, operator, projectFileGroupName):
        slots = [#SerialSlot(
                 #   operator.CropNames,
                 #   transform=str),
                 #SerialListSlot(operator.CropColors, transform=lambda x: tuple(x.flat)),
                 #SerialSlot(operator.PmapColors, transform=lambda x: tuple(x.flat)),
                 SerialDictSlot(operator.Crops),
                 SerialSlot(operator.MinValueT, selfdepends=True),
                 SerialSlot(operator.MaxValueT, selfdepends=True),
                 SerialSlot(operator.MinValueX, selfdepends=True),
                 SerialSlot(operator.MaxValueX, selfdepends=True),
                 SerialSlot(operator.MinValueY, selfdepends=True),
                 SerialSlot(operator.MaxValueY, selfdepends=True),
                 SerialSlot(operator.MinValueZ, selfdepends=True),
                 SerialSlot(operator.MaxValueZ, selfdepends=True),
                 #SerialBlockSlot(operator.CropImage,
                 #                operator.CropInputs,
                 #                operator.NonzeroCropBlocks,
                 #                name='CropSets',
                 #                subname='crops{:03d}',
                 #                selfdepends=False,
                 #                shrink_to_bb=True)
                 ]

        super(CropSelectionSerializer, self).__init__(projectFileGroupName,
                                                         slots=slots)
