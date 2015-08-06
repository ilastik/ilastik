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
from ilastik.applets.base.appletSerializer import \
    AppletSerializer, SerialSlot, SerialBlockSlot

class NansheDictionaryLearningSerializer(AppletSerializer):
    """
    Serializes the user's pixel feature selections to an ilastik v0.6 project file.
    """
    def __init__(self, operator, projectFileGroupName):
        super(NansheDictionaryLearningSerializer, self).__init__(projectFileGroupName,
                                                            slots=[SerialSlot(operator.Ord, selfdepends=True),
                                                                   SerialSlot(operator.K, selfdepends=True),
                                                                   SerialSlot(operator.Gamma1, selfdepends=True),
                                                                   SerialSlot(operator.Gamma2, selfdepends=True),
                                                                   SerialSlot(operator.NumThreads, selfdepends=True),
                                                                   SerialSlot(operator.Batchsize, selfdepends=True),
                                                                   SerialSlot(operator.NumIter, selfdepends=True),
                                                                   SerialSlot(operator.Lambda1, selfdepends=True),
                                                                   SerialSlot(operator.Lambda2, selfdepends=True),
                                                                   SerialSlot(operator.PosAlpha, selfdepends=True),
                                                                   SerialSlot(operator.PosD, selfdepends=True),
                                                                   SerialSlot(operator.Clean, selfdepends=True),
                                                                   SerialSlot(operator.Mode, selfdepends=True),
                                                                   SerialSlot(operator.ModeD, selfdepends=True),
                                                                   SerialBlockSlot(operator.Output,
                                                                                   operator.CacheInput,
                                                                                   operator.CleanBlocks, selfdepends=True)])
