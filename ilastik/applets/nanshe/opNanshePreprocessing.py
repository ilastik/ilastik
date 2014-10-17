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


    ToRemoveZeroedLines = InputSlot(value=True)
    ErosionShape = InputSlot(value=[21, 1])
    DilationShape = InputSlot(value=[1, 3])

    ToExtractF0 = InputSlot(value=True)
    HalfWindowSize = InputSlot(value=400, stype='int')
    WhichQuantile = InputSlot(value=0.15, stype='float')
    TemporalSmoothingGaussianFilterStdev = InputSlot(value=5.0, stype='float')
    SpatialSmoothingGaussianFilterStdev = InputSlot(value=5.0, stype='float')
    Bias = InputSlot(optional=True, stype='float')

    ToWaveletTransform = InputSlot(value=True)
    Scale = InputSlot(value=4)

    Ord = InputSlot(value=2.0)


    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNanshePreprocessing, self ).__init__( *args, **kwargs )

        self.opNansheRemoveZeroedLines = OpNansheRemoveZeroedLines(parent=self)
        self.opNansheRemoveZeroedLines.ErosionShape.connect(self.ErosionShape)
        self.opNansheRemoveZeroedLines.DilationShape.connect(self.DilationShape)

        self.opNansheExtractF0 = OpNansheExtractF0(parent=self)
        self.opNansheExtractF0.HalfWindowSize.connect(self.HalfWindowSize)
        self.opNansheExtractF0.WhichQuantile.connect(self.WhichQuantile)
        self.opNansheExtractF0.TemporalSmoothingGaussianFilterStdev.connect(self.TemporalSmoothingGaussianFilterStdev)
        self.opNansheExtractF0.SpatialSmoothingGaussianFilterStdev.connect(self.SpatialSmoothingGaussianFilterStdev)
        self.opNansheExtractF0.Bias.connect(self.Bias)

        self.opNansheWaveletTransform = OpNansheWaveletTransform(parent=self)
        self.opNansheWaveletTransform.Scale.connect(self.Scale)
        self.opNansheWaveletTransform.IncludeLowerScales.setValue(False)

        self.opNansheNormalizeData = OpNansheNormalizeData(parent=self)
        self.opNansheNormalizeData.Ord.connect(self.Ord)

        self.Output.connect( self.opNansheNormalizeData.Output )
    
    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.InputImage.meta )

        self.opNansheRemoveZeroedLines.InputImage.disconnect()
        self.opNansheExtractF0.InputImage.disconnect()
        self.opNansheWaveletTransform.InputImage.disconnect()
        self.opNansheNormalizeData.InputImage.disconnect()

        next_output = self.InputImage

        if self.ToRemoveZeroedLines.value:
            self.opNansheRemoveZeroedLines.InputImage.connect(next_output)
            next_output = self.opNansheRemoveZeroedLines.Output

        if self.ToExtractF0.value:
            self.opNansheExtractF0.InputImage.connect(next_output)
            next_output = self.opNansheExtractF0.Output

        if self.ToWaveletTransform.value:
            self.opNansheWaveletTransform.InputImage.connect(next_output)
            next_output = self.opNansheWaveletTransform.Output

        self.opNansheNormalizeData.InputImage.connect(next_output)

    # Don't need execute as the output will be drawn through the Output slot.

    def propagateDirty(self, slot, subindex, roi):
        # Dirtiness is already effectively propagated internally.
        # TODO: Revisit whether dirtiness is handled in the case reconnecting components.
        pass
