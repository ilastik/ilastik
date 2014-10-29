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
__date__ = "$Oct 14, 2014 16:37:05 EDT$"

from lazyflow.graph import Operator, InputSlot, OutputSlot

from lazyflow.operators import OpArrayCache

from ilastik.applets.nanshe.preprocessing.opNansheRemoveZeroedLines import OpNansheRemoveZeroedLines, OpNansheRemoveZeroedLinesCached
from ilastik.applets.nanshe.preprocessing.opNansheExtractF0 import OpNansheExtractF0, OpNansheExtractF0Cached
from ilastik.applets.nanshe.preprocessing.opNansheWaveletTransform import OpNansheWaveletTransform, OpNansheWaveletTransformCached


class OpNanshePreprocessData(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNanshePreprocessData"
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
    BiasEnabled = InputSlot(value=False, stype='bool')
    Bias = InputSlot(value=0.0, stype='float')

    ToWaveletTransform = InputSlot(value=True)
    Scale = InputSlot(value=4)


    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNanshePreprocessData, self ).__init__( *args, **kwargs )

        self.opNansheRemoveZeroedLines = OpNansheRemoveZeroedLines(parent=self)
        self.opNansheRemoveZeroedLines.ErosionShape.connect(self.ErosionShape)
        self.opNansheRemoveZeroedLines.DilationShape.connect(self.DilationShape)

        self.opNansheExtractF0 = OpNansheExtractF0(parent=self)
        self.opNansheExtractF0.HalfWindowSize.connect(self.HalfWindowSize)
        self.opNansheExtractF0.WhichQuantile.connect(self.WhichQuantile)
        self.opNansheExtractF0.TemporalSmoothingGaussianFilterStdev.connect(self.TemporalSmoothingGaussianFilterStdev)
        self.opNansheExtractF0.SpatialSmoothingGaussianFilterStdev.connect(self.SpatialSmoothingGaussianFilterStdev)
        self.opNansheExtractF0.BiasEnabled.connect(self.BiasEnabled)
        self.opNansheExtractF0.Bias.connect(self.Bias)

        self.opNansheWaveletTransform = OpNansheWaveletTransform(parent=self)
        self.opNansheWaveletTransform.Scale.connect(self.Scale)


    
    def setupOutputs(self):
        self.opNansheRemoveZeroedLines.InputImage.disconnect()
        self.opNansheExtractF0.InputImage.disconnect()
        self.opNansheWaveletTransform.InputImage.disconnect()

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

        self.Output.connect(next_output)

    # Don't need execute as the output will be drawn through the Output slot.

    def setInSlot(self, slot, subindex, key, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            if self.ToRemoveZeroedLines.value:
                self.opNansheRemoveZeroedLines.InputImage.setDirty(roi)
            elif self.ToExtractF0.value:
                self.opNansheExtractF0.InputImage.setDirty(roi)
            elif self.ToWaveletTransform.value:
                self.opNansheWaveletTransform.InputImage.setDirty(roi)
            else:
                self.Output.setDirty(roi)
        elif (slot.name == "ErosionShape") or (slot.name == "DilationShape"):
            if self.ToRemoveZeroedLines.value:
                self.opNansheRemoveZeroedLines.Output.setDirty( slice(None) )
        elif (slot.name == "HalfWindowSize") or (slot.name == "WhichQuantile") or\
                (slot.name == "TemporalSmoothingGaussianFilterStdev") or\
                (slot.name == "SpatialSmoothingGaussianFilterStdev") or\
                (slot.name == "Bias"):
            if self.ToExtractF0.value:
                self.opNansheExtractF0.Output.setDirty( slice(None) )
        elif (slot.name == "Scale"):
            if self.ToWaveletTransform.value:
                self.opNansheWaveletTransform.Output.setDirty( slice(None) )
        elif slot.name == "ToRemoveZeroedLines":
            if slot.value:
                self.opNansheRemoveZeroedLines.Output.setDirty( slice(None) )
            else:
                if self.ToExtractF0.value is not None:
                    self.opNansheExtractF0.InputImage.setDirty( slice(None) )
                elif self.ToWaveletTransform.value is not None:
                    self.opNansheWaveletTransform.InputImage.setDirty( slice(None) )
                else:
                    self.Output.setDirty( slice(None) )
        elif slot.name == "ToExtractF0":
            if slot.value:
                self.opNansheExtractF0.Output.setDirty( slice(None) )
            else:
                if self.ToWaveletTransform.value is not None:
                    self.opNansheWaveletTransform.InputImage.setDirty( slice(None) )
                else:
                    self.Output.setDirty( slice(None) )
        elif slot.name == "ToWaveletTransform":
            if slot.value:
                self.opNansheWaveletTransform.Output.setDirty( slice(None) )
            else:
                self.Output.setDirty( slice(None) )


class OpNanshePreprocessDataCached(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNanshePreprocessDataCached"
    category = "Pointwise"


    InputImage = InputSlot()
    CacheInput = InputSlot(optional=True)


    ToRemoveZeroedLines = InputSlot(value=True)
    ErosionShape = InputSlot(value=[21, 1])
    DilationShape = InputSlot(value=[1, 3])

    ToExtractF0 = InputSlot(value=True)
    HalfWindowSize = InputSlot(value=400, stype='int')
    WhichQuantile = InputSlot(value=0.15, stype='float')
    TemporalSmoothingGaussianFilterStdev = InputSlot(value=5.0, stype='float')
    SpatialSmoothingGaussianFilterStdev = InputSlot(value=5.0, stype='float')
    BiasEnabled = InputSlot(value=False, stype='bool')
    Bias = InputSlot(value=0.0, stype='float')

    ToWaveletTransform = InputSlot(value=True)
    Scale = InputSlot(value=4)


    CleanBlocks = OutputSlot()
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNanshePreprocessDataCached, self ).__init__( *args, **kwargs )

        self.opNansheRemoveZeroedLines = OpNansheRemoveZeroedLinesCached(parent=self)
        self.opNansheRemoveZeroedLines.ErosionShape.connect(self.ErosionShape)
        self.opNansheRemoveZeroedLines.DilationShape.connect(self.DilationShape)

        self.opNansheExtractF0 = OpNansheExtractF0Cached(parent=self)
        self.opNansheExtractF0.HalfWindowSize.connect(self.HalfWindowSize)
        self.opNansheExtractF0.WhichQuantile.connect(self.WhichQuantile)
        self.opNansheExtractF0.TemporalSmoothingGaussianFilterStdev.connect(self.TemporalSmoothingGaussianFilterStdev)
        self.opNansheExtractF0.SpatialSmoothingGaussianFilterStdev.connect(self.SpatialSmoothingGaussianFilterStdev)
        self.opNansheExtractF0.BiasEnabled.connect(self.BiasEnabled)
        self.opNansheExtractF0.Bias.connect(self.Bias)

        self.opNansheWaveletTransform = OpNansheWaveletTransformCached(parent=self)
        self.opNansheWaveletTransform.Scale.connect(self.Scale)

        self.opCache = OpArrayCache(parent=self)
        self.opCache.fixAtCurrent.setValue(False)
        self.CleanBlocks.connect(self.opCache.CleanBlocks)

        self.Output.connect(self.opCache.Output)

    def setupOutputs(self):
        self.opNansheRemoveZeroedLines.InputImage.disconnect()
        self.opNansheExtractF0.InputImage.disconnect()
        self.opNansheWaveletTransform.InputImage.disconnect()
        self.opCache.Input.disconnect()

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

        self.opCache.Input.connect(next_output)

        self.opCache.blockShape.setValue( self.opCache.Output.meta.shape )

    # Don't need execute as the output will be drawn through the Output slot.

    def setInSlot(self, slot, subindex, key, value):
        assert slot == self.CacheInput

        self.opCache.setInSlot(self.opCache.Input, subindex, key, value)

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            if self.ToRemoveZeroedLines.value:
                self.opNansheRemoveZeroedLines.InputImage.setDirty(roi)
            elif self.ToExtractF0.value:
                self.opNansheExtractF0.InputImage.setDirty(roi)
            elif self.ToWaveletTransform.value:
                self.opNansheWaveletTransform.InputImage.setDirty(roi)
            else:
                self.opCache.Input.setDirty(roi)
        elif (slot.name == "ErosionShape") or (slot.name == "DilationShape"):
            if self.ToRemoveZeroedLines.value:
                self.opNansheRemoveZeroedLines.Output.setDirty( slice(None) )
        elif (slot.name == "HalfWindowSize") or (slot.name == "WhichQuantile") or\
                (slot.name == "TemporalSmoothingGaussianFilterStdev") or\
                (slot.name == "SpatialSmoothingGaussianFilterStdev") or\
                (slot.name == "Bias"):
            if self.ToExtractF0.value:
                self.opNansheExtractF0.Output.setDirty( slice(None) )
        elif (slot.name == "Scale"):
            if self.ToWaveletTransform.value:
                self.opNansheWaveletTransform.Output.setDirty( slice(None) )
        elif slot.name == "ToRemoveZeroedLines":
            if slot.value:
                self.opNansheRemoveZeroedLines.Output.setDirty( slice(None) )
            else:
                if self.ToExtractF0.value is not None:
                    self.opNansheExtractF0.InputImage.setDirty( slice(None) )
                elif self.ToWaveletTransform.value is not None:
                    self.opNansheWaveletTransform.InputImage.setDirty( slice(None) )
                else:
                    self.Output.setDirty( slice(None) )
        elif slot.name == "ToExtractF0":
            if slot.value:
                self.opNansheExtractF0.Output.setDirty( slice(None) )
            else:
                if self.ToWaveletTransform.value is not None:
                    self.opNansheWaveletTransform.InputImage.setDirty( slice(None) )
                else:
                    self.Output.setDirty( slice(None) )
        elif slot.name == "ToWaveletTransform":
            if slot.value:
                self.opNansheWaveletTransform.Output.setDirty( slice(None) )
            else:
                self.Output.setDirty( slice(None) )
