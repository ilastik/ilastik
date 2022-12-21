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
from ilastik.applets.base.appletSerializer import (
    AppletSerializer,
    SerialSlot,
    SerialBlockSlot,
    SerialListSlot,
)


class SerialDefaultSlot(SerialSlot):
    """SerialSlot implementation that actually uses the default value

    not recommended to use outside this serializer with default parameter
    being deprecated on the SerialSlot.

    Also _very_ limited implementation -> will only work with level0 slots
    """

    def __init__(self, slot, inslot=None, name=None, subname=None, default=None, depends=None, selfdepends=True):
        assert default is not None, "must supply a default value"
        super().__init__(slot, inslot, name, subname, default, depends, selfdepends)

    def deserialize(self, group):
        """Performs tasks common to all deserializations.

        actually need to override this method to make use of the default value

        :param group: The parent group in which to create this slot's
            group.
        :type group: h5py.Group

        """
        if self.name not in group:
            if self.inslot.level == 0:
                self.inslot.setValue(self.default)
            else:
                raise NotImplementedError("No deserialization for slots with level > 0 implemented.")
        else:
            super().deserialize(group)
            self.dirty = False


class WsdtSerializer(AppletSerializer):
    version = "0.2"

    def __init__(self, operator, projectFileGroupName):
        slots = [
            SerialListSlot(operator.ChannelSelections),
            SerialSlot(operator.Threshold),
            SerialSlot(operator.MinSize),
            SerialSlot(operator.Sigma),
            SerialSlot(operator.Alpha),
            SerialSlot(operator.PixelPitch),
            SerialDefaultSlot(operator.BlockwiseWatershed, default=False),
            SerialBlockSlot(
                operator.Superpixels,
                operator.SuperpixelCacheInput,
                operator.CleanBlocks,
                name="Superpixels",
                subname="superpixels{:03d}",
                selfdepends=False,
                shrink_to_bb=False,
                compression_level=1,
            ),
        ]
        super().__init__(projectFileGroupName, slots=slots, operator=operator)
