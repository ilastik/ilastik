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
__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Oct 23, 2014 16:27:11 EDT$"


from ilastik.applets.base.appletSerializer import \
    AppletSerializer, SerialSlot, SerialListSlot

class NanshePostprocessingSerializer(AppletSerializer):
    """
    Serializes the user's pixel feature selections to an ilastik v0.6 project file.
    """
    def __init__(self, operator, projectFileGroupName):
        super(NanshePostprocessingSerializer, self).__init__(projectFileGroupName,
                                                            slots=[SerialSlot(operator.SignificanceThreshold, selfdepends=True),
                                                                   SerialListSlot(operator.WaveletTransformScale, selfdepends=True),
                                                                   SerialSlot(operator.NoiseThreshold, selfdepends=True),
                                                                   SerialSlot(operator.AcceptedRegionShapeConstraints_MajorAxisLength_Min, selfdepends=True),
                                                                   SerialSlot(operator.AcceptedRegionShapeConstraints_MajorAxisLength_Min_Enabled, selfdepends=True),
                                                                   SerialSlot(operator.AcceptedRegionShapeConstraints_MajorAxisLength_Max, selfdepends=True),
                                                                   SerialSlot(operator.AcceptedRegionShapeConstraints_MajorAxisLength_Max_Enabled, selfdepends=True),
                                                                   SerialSlot(operator.MinLocalMaxDistance, selfdepends=True),
                                                                   SerialSlot(operator.AcceptedNeuronShapeConstraints_Area_Min, selfdepends=True),
                                                                   SerialSlot(operator.AcceptedNeuronShapeConstraints_Area_Min_Enabled, selfdepends=True),
                                                                   SerialSlot(operator.AcceptedNeuronShapeConstraints_Area_Max, selfdepends=True),
                                                                   SerialSlot(operator.AcceptedNeuronShapeConstraints_Area_Max_Enabled, selfdepends=True),
                                                                   SerialSlot(operator.AcceptedNeuronShapeConstraints_Eccentricity_Min, selfdepends=True),
                                                                   SerialSlot(operator.AcceptedNeuronShapeConstraints_Eccentricity_Min_Enabled, selfdepends=True),
                                                                   SerialSlot(operator.AcceptedNeuronShapeConstraints_Eccentricity_Max, selfdepends=True),
                                                                   SerialSlot(operator.AcceptedNeuronShapeConstraints_Eccentricity_Max_Enabled, selfdepends=True),
                                                                   SerialSlot(operator.AlignmentMinThreshold, selfdepends=True),
                                                                   SerialSlot(operator.OverlapMinThreshold, selfdepends=True),
                                                                   SerialSlot(operator.Fuse_FractionMeanNeuronMaxThreshold, selfdepends=True)])
