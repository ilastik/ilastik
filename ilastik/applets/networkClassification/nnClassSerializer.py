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
#          http://ilastik.org/license.html
###############################################################################
from ilastik.applets.base.appletSerializer import AppletSerializer, SerialListSlot, SerialDictSlot, SerialPickleableSlot, SerialBlockSlot

import logging

logger = logging.getLogger(__name__)


class NNClassificationSerializer(AppletSerializer):
    def __init__(self, topLevelOperator, projectFileGroupName):
        self.VERSION = 1

        slots = [SerialPickleableSlot(topLevelOperator.FullModel, version=1),
                 SerialDictSlot(topLevelOperator.ModelPath),
                 SerialListSlot(topLevelOperator.LabelNames),
                 SerialListSlot(topLevelOperator.LabelColors, transform=lambda x: tuple(x.flat)),
                 SerialListSlot(topLevelOperator.PmapColors, transform=lambda x: tuple(x.flat)),
                 SerialBlockSlot(topLevelOperator.LabelImages,
                                 topLevelOperator.LabelInputs,
                                 topLevelOperator.NonzeroLabelBlocks,
                                 name='LabelSets',
                                 subname='labels{:03d}',
                                 selfdepends=False,
                                 shrink_to_bb=True)
        ]

        super(NNClassificationSerializer, self).__init__(projectFileGroupName, slots, topLevelOperator)
