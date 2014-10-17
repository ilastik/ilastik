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
import nanshe.wavelet_transform


class OpNansheWaveletTransform(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNansheWaveletTransform"
    category = "Pointwise"


    InputImage = InputSlot()

    Scale = InputSlot(value=4, stype="int")
    IncludeLowerScales = InputSlot(value=False, stype="bool")
    
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNansheWaveletTransform, self ).__init__( *args, **kwargs )
    
    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.InputImage.meta )
    
    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()
        raw = self.InputImage[key].wait()

        scale = self.Scale.value
        include_lower_scales = self.IncludeLowerScales.value

        processed = nanshe.wavelet_transform.wavelet_transform(raw,
                                                               scale=scale,
                                                               include_intermediates = False,
                                                               include_lower_scales = include_lower_scales)
        
        if slot.name == 'Output':
            result[...] = processed

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            self.Output.setDirty(roi)
        elif slot.name == "Scale" or slot.name == "IncludeLowerScales":
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"
