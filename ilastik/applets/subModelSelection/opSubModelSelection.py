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

import numpy

class OpSubModelSelection(Operator):
    """
    Given an input image and visible crop lines,
    allows selection of a SubModel.
    """
    name = "OpSubModelSelection"
    category = "Pointwise"
    
    InputImage = InputSlot()
    PredictionImage = InputSlot()

    MinValueT = InputSlot(value=0)
    MaxValueT = InputSlot(value=0)
    MinValueX = InputSlot(value=0)
    MaxValueX = InputSlot(value=0)
    MinValueY = InputSlot(value=0)
    MaxValueY = InputSlot(value=0)
    MinValueZ = InputSlot(value=0)
    MaxValueZ = InputSlot(value=0)

    CropImage = OutputSlot()
    CropPrediction = OutputSlot()

    def setupOutputs(self):
        self.CropImage.meta.assignFrom( self.InputImage.meta )
        self.CropPrediction.meta.assignFrom( self.PredictionImage.meta )
        self._MinValueT=self.MinValueT.value
        self._MaxValueT=self.MaxValueT.value
        self._MinValueX=self.MinValueX.value
        self._MaxValueX=self.MaxValueX.value
        self._MinValueY=self.MinValueY.value
        self._MaxValueY=self.MaxValueY.value
        self._MinValueZ=self.MinValueZ.value
        self._MaxValueZ=self.MaxValueZ.value

    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()

        if slot.name == 'CropImage':
            raw = self.InputImage[key].wait()
            mask = numpy.ones_like(raw)
            result[...] = mask * raw
        if slot.name == 'CropPrediction':
            raw = self.PredictionImage[key].wait()
            mask = numpy.ones_like(raw)
            result[...] = numpy.logical_not(mask) * raw

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            self.CropImage.setDirty(roi)
        elif slot.name == "PredictionImage":
            self.CropPrediction.setDirty( roi )
        else:
            self.CropImage.setDirty( slice(None) )
            self.CropPrediction.setDirty( slice(None) )
