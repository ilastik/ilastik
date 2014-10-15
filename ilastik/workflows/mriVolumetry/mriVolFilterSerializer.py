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
import numpy as np
from ilastik.applets.base.appletSerializer import AppletSerializer
from ilastik.applets.base.appletSerializer import SerialHdf5BlockSlot
from ilastik.applets.base.appletSerializer import SerialDictSlot
from ilastik.applets.base.appletSerializer import SerialSlot

import logging
logger = logging.getLogger(__name__)


class MriVolFilterSerializer(AppletSerializer):
    """
    ...
    """
    def __init__(self, op, projectFileGroupName):
        slots = [SerialDictSlot(op.Configuration),
                 SerialSlot(op.SmoothingMethod),
                 SerialSlot(op.Threshold),
                 SerialSlot(op.ActiveChannels),
                 SerialHdf5BlockSlot(op.OutputHdf5,
                                     op.InputHdf5,
                                     op.CleanBlocks,
                                     name='caches',
                                     subname='cache{:03d}',),
                 ]
        # TODO serialize ActiveChannels

        super(MriVolFilterSerializer, self).__init__(
            projectFileGroupName, slots, op)
