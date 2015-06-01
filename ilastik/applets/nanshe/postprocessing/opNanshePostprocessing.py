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
__date__ = "$Oct 23, 2014 09:45:39 EDT$"



from lazyflow.graph import Operator, InputSlot, OutputSlot

from ilastik.applets.nanshe.postprocessing.opNanshePostprocessData import OpNanshePostprocessDataCached

import vigra

import numpy

import nanshe
import nanshe.util.xnumpy
import nanshe.imp.segment


class OpNanshePostprocessing(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNanshePostprocessing"
    category = "Pointwise"


    Input = InputSlot()
    CacheInput = InputSlot(optional=True)

    SignificanceThreshold = InputSlot(value=3.0, stype="float")
    WaveletTransformScale = InputSlot(value=4, stype="int")
    NoiseThreshold = InputSlot(value=4.0, stype="float")
    AcceptedRegionShapeConstraints_MajorAxisLength_Min = InputSlot(value=0.0, stype="float")
    AcceptedRegionShapeConstraints_MajorAxisLength_Min_Enabled = InputSlot(value=True, stype="bool")
    AcceptedRegionShapeConstraints_MajorAxisLength_Max = InputSlot(value=25.0, stype="float")
    AcceptedRegionShapeConstraints_MajorAxisLength_Max_Enabled = InputSlot(value=True, stype="bool")

    PercentagePixelsBelowMax = InputSlot(value=0.8, stype="float")
    MinLocalMaxDistance = InputSlot(value=20.0, stype="float")

    AcceptedNeuronShapeConstraints_Area_Min = InputSlot(value=45, stype="int")
    AcceptedNeuronShapeConstraints_Area_Min_Enabled = InputSlot(value=True, stype="bool")
    AcceptedNeuronShapeConstraints_Area_Max = InputSlot(value=600, stype="int")
    AcceptedNeuronShapeConstraints_Area_Max_Enabled = InputSlot(value=True, stype="bool")

    AcceptedNeuronShapeConstraints_Eccentricity_Min = InputSlot(value=0.0, stype="float")
    AcceptedNeuronShapeConstraints_Eccentricity_Min_Enabled = InputSlot(value=True, stype="bool")
    AcceptedNeuronShapeConstraints_Eccentricity_Max = InputSlot(value=0.9, stype="float")
    AcceptedNeuronShapeConstraints_Eccentricity_Max_Enabled = InputSlot(value=True, stype="bool")

    AlignmentMinThreshold = InputSlot(value=0.6, stype="float")
    OverlapMinThreshold = InputSlot(value=0.6, stype="float")

    Fuse_FractionMeanNeuronMaxThreshold = InputSlot(value=0.01, stype="float")

    CleanBlocks = OutputSlot()
    Output = OutputSlot()
    ColorizedOutput = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNanshePostprocessing, self ).__init__( *args, **kwargs )

        self.opPostprocess = OpNanshePostprocessDataCached(parent=self)


        self.opPostprocess.SignificanceThreshold.connect(self.SignificanceThreshold)
        self.opPostprocess.WaveletTransformScale.connect(self.WaveletTransformScale)
        self.opPostprocess.NoiseThreshold.connect(self.NoiseThreshold)
        self.opPostprocess.AcceptedRegionShapeConstraints_MajorAxisLength_Min.connect(self.AcceptedRegionShapeConstraints_MajorAxisLength_Min)
        self.opPostprocess.AcceptedRegionShapeConstraints_MajorAxisLength_Min_Enabled.connect(self.AcceptedRegionShapeConstraints_MajorAxisLength_Min_Enabled)
        self.opPostprocess.AcceptedRegionShapeConstraints_MajorAxisLength_Max.connect(self.AcceptedRegionShapeConstraints_MajorAxisLength_Max)
        self.opPostprocess.AcceptedRegionShapeConstraints_MajorAxisLength_Max_Enabled.connect(self.AcceptedRegionShapeConstraints_MajorAxisLength_Max_Enabled)
        self.opPostprocess.PercentagePixelsBelowMax.connect(self.PercentagePixelsBelowMax)
        self.opPostprocess.MinLocalMaxDistance.connect(self.MinLocalMaxDistance)
        self.opPostprocess.AcceptedNeuronShapeConstraints_Area_Min.connect(self.AcceptedNeuronShapeConstraints_Area_Min)
        self.opPostprocess.AcceptedNeuronShapeConstraints_Area_Min_Enabled.connect(self.AcceptedNeuronShapeConstraints_Area_Min_Enabled)
        self.opPostprocess.AcceptedNeuronShapeConstraints_Area_Max.connect(self.AcceptedNeuronShapeConstraints_Area_Max)
        self.opPostprocess.AcceptedNeuronShapeConstraints_Area_Max_Enabled.connect(self.AcceptedNeuronShapeConstraints_Area_Max_Enabled)
        self.opPostprocess.AcceptedNeuronShapeConstraints_Eccentricity_Min.connect(self.AcceptedNeuronShapeConstraints_Eccentricity_Min)
        self.opPostprocess.AcceptedNeuronShapeConstraints_Eccentricity_Min_Enabled.connect(self.AcceptedNeuronShapeConstraints_Eccentricity_Min_Enabled)
        self.opPostprocess.AcceptedNeuronShapeConstraints_Eccentricity_Max.connect(self.AcceptedNeuronShapeConstraints_Eccentricity_Max)
        self.opPostprocess.AcceptedNeuronShapeConstraints_Eccentricity_Max_Enabled.connect(self.AcceptedNeuronShapeConstraints_Eccentricity_Max_Enabled)
        self.opPostprocess.AlignmentMinThreshold.connect(self.AlignmentMinThreshold)
        self.opPostprocess.OverlapMinThreshold.connect(self.OverlapMinThreshold)
        self.opPostprocess.Fuse_FractionMeanNeuronMaxThreshold.connect(self.Fuse_FractionMeanNeuronMaxThreshold)


        self.opPostprocess.Input.connect( self.Input )
        self.opPostprocess.CacheInput.connect( self.CacheInput )


        self.CleanBlocks.connect( self.opPostprocess.CleanBlocks )
        self.Output.connect( self.opPostprocess.Output )
        self.ColorizedOutput.connect(self.opPostprocess.ColorizedOutput)

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass
