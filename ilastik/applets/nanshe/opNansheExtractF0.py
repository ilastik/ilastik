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


class OpNansheExtractF0(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNansheExtractF0"
    category = "Pointwise"
    
    InputImage = InputSlot()

    HalfWindowSize = InputSlot(stype='int')
    WhichQuantile = InputSlot(stype='float')
    TemporalSmoothingGaussianFilterStdev = InputSlot(stype='float')
    SpatialSmoothingGaussianFilterStdev = InputSlot(stype='float')
    Bias = InputSlot(optional=True, stype='float')

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNansheExtractF0, self ).__init__( *args, **kwargs )

        self.HalfWindowSize.setValue(400)
        self.WhichQuantile.setValue(0.15)
        self.TemporalSmoothingGaussianFilterStdev.setValue(5.0)
        self.SpatialSmoothingGaussianFilterStdev.setValue(5.0)
        self.Bias.setValue(None)
    
    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.InputImage.meta )
    
    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()
        raw = self.InputImage[key].wait()

        half_window_size = self.HalfWindowSize.value
        which_quantile = self.WhichQuantile.value

        bias = None
        if self.Bias.ready():
            bias = self.Bias.value

        temporal_smoothing_gaussian_filter_stdev = self.TemporalSmoothingGaussianFilterStdev.value
        spatial_smoothing_gaussian_filter_stdev = self.SpatialSmoothingGaussianFilterStdev.value

        processed = nanshe.advanced_image_processing.extract_f0(raw,
                                                                half_window_size=half_window_size,
                                                                which_quantile=which_quantile,
                                                                temporal_smoothing_gaussian_filter_stdev=temporal_smoothing_gaussian_filter_stdev,
                                                                spatial_smoothing_gaussian_filter_stdev=spatial_smoothing_gaussian_filter_stdev,
                                                                bias=bias)
        
        if slot.name == 'Output':
            result[...] = processed

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            self.Output.setDirty(roi)
        elif slot.name == "Bias" or slot.name == "TemporalSmoothingGaussianFilterStdev" or \
             slot.name == "HalfWindowSize" or slot.name == "WhichQuantile" or \
             slot.name == "SpatialSmoothingGaussianFilterStdev":
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"
