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

    """ "preprocess_data" : {

                "__comment__remove_zeroed_lines" : "Optional. Interpolates over missing lines that could not be registered. This is done by finding an outline around all missing points to use for calculating the interpolation. This step only works on 2D data.",

                "remove_zeroed_lines" : {
                    "__comment__dilation_shape" : "Kernel shape for performing dilation. Axis order is [y, x].",
                    "__comment__erosion_shape" : "Kernel shape for performing erosion. Axis order is [y, x].",

                    "erosion_shape" : [21, 1],
                    "dilation_shape" : [1, 3]
                },


                "__comment__extract_f0" : "Optional. Estimates and removes f0 from the data using a percentile (rank order) filter.",

                "extract_f0" : {

                    "__comment__bias" : "To avoid division by zero, this constant is added to the data. If unspecified, a bias will be found so that the smallest value is 1.",

                    "bias" : 100,


                    "__comment__temporal_smoothing_gaussian_filter_stdev" : "What standard deviation to use for the smoothing gaussian applied along time.",

                    "temporal_smoothing_gaussian_filter_stdev" : 5.0,


                    "__comment__half_window_size" : "How many frames to include in half of the window. All windows are odd. So, the total window size will be 2 * half_window_size + 1.",

                    "half_window_size" : 400,


                    "__comment__which_quantile" : "The quantile to be used for filtering. Must be a single float from [0.0, 1.0]. If set to 0.5, this is a median filter.",

                    "which_quantile" : 0.15,


                    "__comment__spatial_smoothing_gaussian_filter_stdev" : "What standard deviation to use for the smoothing gaussian applied along each spatial dimension, independently.",

                    "spatial_smoothing_gaussian_filter_stdev" : 5.0
                },


                "__comment__wavelet_transform" : "Optional. Runs a wavelet transform on the data.",

                "wavelet_transform" : {

                    "__comment__scale" : "This can be a single value, which is then applied on all axes or it can be an array. For the array, the axis order is [t, y, x] for 2D and [t, z, y, x] for 3D.",

                    "scale" : [4, 4, 4]
                },


                "__comment__normalize_data" : "How to normalize data. L_2 norm recommended.",

                "normalize_data" : {
                    "simple_image_processing.renormalized_images": {
                        "ord" : 2
                    }
                }
            },"""
    
    InputImage = InputSlot()

    Scale = InputSlot()
    
    Output = OutputSlot()
    
    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.InputImage.meta )
    
    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()
        raw = self.InputImage[key].wait()
        scale = self.Scale.value

        processed = nanshe.wavelet_transform.wavelet_transform(raw, scale=scale)
        
        if slot.name == 'Output':
            result[...] = processed

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            self.Output.setDirty(roi)
        elif slot.name == "MinValue" or slot.name == "MaxValue":
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"
