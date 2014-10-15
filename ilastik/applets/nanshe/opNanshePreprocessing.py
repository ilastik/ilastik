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
from lazyflow.graph import Operator, InputSlot, OutputSlot

from opNansheRemoveZeroedLines import OpNansheRemoveZeroedLines
from opNansheExtractF0 import OpNansheExtractF0
from opNansheWaveletTransform import OpNansheWaveletTransform
from opNansheNormalizeData import OpNansheNormalizeData

import numpy

import nanshe
import nanshe.advanced_image_processing


class OpNanshePreprocessing(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNanshePreprocessing"
    category = "Pointwise"

    
    InputImage = InputSlot()


    ErosionShape = InputSlot()
    DilationShape = InputSlot()

    HalfWindowSize = InputSlot(stype='int')
    WhichQuantile = InputSlot(stype='float')
    TemporalSmoothingGaussianFilterStdev = InputSlot(stype='float')
    SpatialSmoothingGaussianFilterStdev = InputSlot(stype='float')
    Bias = InputSlot(stype='float')

    Scale = InputSlot()

    Ord = InputSlot()


    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNanshePreprocessing, self ).__init__( *args, **kwargs )

        self.opNansheRemoveZeroedLines = OpNansheRemoveZeroedLines(parent=self)
        self.opNansheRemoveZeroedLines.InputImage.connect(self.InputImage)
        self.opNansheRemoveZeroedLines.ErosionShape.connect(self.ErosionShape)
        self.opNansheRemoveZeroedLines.DilationShape.connect(self.DilationShape)

        self.opNansheExtractF0 = OpNansheExtractF0(parent=self)
        self.opNansheExtractF0.InputImage.connect(self.opNansheRemoveZeroedLines.Output)
        self.opNansheExtractF0.HalfWindowSize.connect(self.HalfWindowSize)
        self.opNansheExtractF0.WhichQuantile.connect(self.WhichQuantile)
        self.opNansheExtractF0.TemporalSmoothingGaussianFilterStdev.connect(self.TemporalSmoothingGaussianFilterStdev)
        self.opNansheExtractF0.SpatialSmoothingGaussianFilterStdev.connect(self.SpatialSmoothingGaussianFilterStdev)
        self.opNansheExtractF0.Bias.connect(self.Bias)

        self.opNansheWaveletTransform = OpNansheWaveletTransform(parent=self)
        self.opNansheWaveletTransform.InputImage.connect(self.opNansheExtractF0.Output)
        self.opNansheWaveletTransform.Scale.connect(self.Scale)
        self.opNansheWaveletTransform.IncludeLowerScales.setValue(False)

        self.opNansheNormalizeData = OpNansheNormalizeData(parent=self)
        self.opNansheNormalizeData.InputImage.connect(self.opNansheWaveletTransform.Output)
        self.opNansheNormalizeData.Ord.connect(self.Ord)

        self.Output.connect( self.opNansheNormalizeData.Output )


        self.ErosionShape.setValue([21, 1])
        self.DilationShape.setValue([1, 3])

        self.HalfWindowSize.setValue(400)
        self.WhichQuantile.setValue(0.15)
        self.TemporalSmoothingGaussianFilterStdev.setValue(5.0)
        self.SpatialSmoothingGaussianFilterStdev.setValue(5.0)
        self.Bias.setValue(None)

        self.Scale.setValue(4)

        self.Ord.setValue(2)
    
    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.InputImage.meta )

    # Don't need execute as the output will be drawn through the Output slot.

    def propagateDirty(self, slot, subindex, roi):
        # Dirtiness is already effectively propagated internally.
        pass
