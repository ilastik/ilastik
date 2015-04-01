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
    AppletSerializer, SerialSlot, SerialListSlot, SerialBlockSlot

class NanshePreprocessingSerializer(AppletSerializer):
    """
    Serializes the user's pixel feature selections to an ilastik v0.6 project file.
    """
    def __init__(self, operator, projectFileGroupName):
        super(NanshePreprocessingSerializer, self).__init__(projectFileGroupName,
                                                            slots=[SerialSlot(operator.ToRemoveZeroedLines, selfdepends=True),
                                                                   SerialListSlot(operator.ErosionShape, selfdepends=True),
                                                                   SerialListSlot(operator.DilationShape, selfdepends=True),
                                                                   SerialSlot(operator.ToExtractF0, selfdepends=True),
                                                                   SerialSlot(operator.HalfWindowSize, selfdepends=True),
                                                                   SerialSlot(operator.WhichQuantile, selfdepends=True),
                                                                   SerialSlot(operator.TemporalSmoothingGaussianFilterStdev, selfdepends=True),
                                                                   SerialSlot(operator.SpatialSmoothingGaussianFilterStdev, selfdepends=True),
                                                                   SerialSlot(operator.TemporalSmoothingGaussianFilterWindowSize, selfdepends=True),
                                                                   SerialSlot(operator.SpatialSmoothingGaussianFilterWindowSize, selfdepends=True),
                                                                   SerialSlot(operator.BiasEnabled, selfdepends=True),
                                                                   SerialSlot(operator.Bias, selfdepends=True),
                                                                   SerialSlot(operator.ToWaveletTransform, selfdepends=True),
                                                                   SerialListSlot(operator.Scale, selfdepends=True),
                                                                   SerialBlockSlot(operator.CacheOutput,
                                                                                   operator.CacheInput,
                                                                                   operator.CleanBlocks, selfdepends=True)])
