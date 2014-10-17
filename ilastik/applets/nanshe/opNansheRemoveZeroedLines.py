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

import nanshe
import nanshe.advanced_image_processing


class OpNansheRemoveZeroedLines(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNansheRemoveZeroedLines"
    category = "Pointwise"

    InputImage = InputSlot()

    ErosionShape = InputSlot(value=[21, 1])
    DilationShape = InputSlot(value=[1, 3])
    
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNansheRemoveZeroedLines, self ).__init__( *args, **kwargs )
    
    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.InputImage.meta )
    
    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()
        raw = self.InputImage[key].wait()
        raw = raw[..., 0]

        erosion_shape = self.ErosionShape.value
        dilation_shape = self.DilationShape.value

        processed = nanshe.advanced_image_processing.remove_zeroed_lines(raw,
                                                                         erosion_shape=erosion_shape,
                                                                         dilation_shape=dilation_shape)
        processed = processed[..., None]
        
        if slot.name == 'Output':
            result[...] = processed

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            self.Output.setDirty(roi)
        elif slot.name == "ErosionShape" or slot.name == "DilationShape":
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"
