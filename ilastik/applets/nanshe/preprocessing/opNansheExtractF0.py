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
__date__ = "$Oct 14, 2014 16:33:55 EDT$"



import itertools
import math

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

    HalfWindowSize = InputSlot(value=400, stype='int')
    WhichQuantile = InputSlot(value=0.15, stype='float')
    TemporalSmoothingGaussianFilterStdev = InputSlot(value=5.0, stype='float')
    SpatialSmoothingGaussianFilterStdev = InputSlot(value=5.0, stype='float')
    Bias = InputSlot(optional=True, stype='float')

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNansheExtractF0, self ).__init__( *args, **kwargs )

        self._generation = {self.name : 0}
    
    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.InputImage.meta )

        self.Output.meta.generation = self._generation
    
    def execute(self, slot, subindex, roi, result):
        half_window_size = self.HalfWindowSize.value
        which_quantile = self.WhichQuantile.value

        bias = None
        if self.Bias.ready():
            bias = self.Bias.value

        temporal_smoothing_gaussian_filter_stdev = self.TemporalSmoothingGaussianFilterStdev.value
        spatial_smoothing_gaussian_filter_stdev = self.SpatialSmoothingGaussianFilterStdev.value


        image_shape = self.InputImage.meta.shape

        key = roi.toSlice()
        key = nanshe.additional_generators.reformat_slices(key, image_shape)

        halo = list(itertools.repeat(0, len(key) - 1))
        halo[0] = max(int(math.ceil(5*temporal_smoothing_gaussian_filter_stdev)), half_window_size)
        for i in xrange(1, len(halo)):
            halo[i] = int(math.ceil(5*spatial_smoothing_gaussian_filter_stdev))

        halo_key = list(key)
        within_halo_key = list(key)

        for i in xrange(len(halo)):
            halo_key_i_start = (halo_key[i].start - halo[i])
            within_halo_key_i_start = halo[i]
            if (halo_key_i_start < 0):
                within_halo_key_i_start += halo_key_i_start
                halo_key_i_start = 0


            halo_key_i_stop = (halo_key[i].stop + halo[i])
            within_halo_key_i_stop = (key[i].stop - key[i].start) + within_halo_key_i_start
            if (halo_key_i_stop > image_shape[i]):
                halo_key_i_stop = image_shape[i]

            halo_key[i] = slice(halo_key_i_start, halo_key_i_stop, halo_key[i].step)
            within_halo_key[i] = slice(within_halo_key_i_start, within_halo_key_i_stop, within_halo_key[i].step)

        raw = self.InputImage[halo_key].wait()
        raw = raw[..., 0]

        processed = nanshe.advanced_image_processing.extract_f0(raw,
                                                                half_window_size=half_window_size,
                                                                which_quantile=which_quantile,
                                                                temporal_smoothing_gaussian_filter_stdev=temporal_smoothing_gaussian_filter_stdev,
                                                                spatial_smoothing_gaussian_filter_stdev=spatial_smoothing_gaussian_filter_stdev,
                                                                bias=bias)
        processed = processed[..., None]
        
        if slot.name == 'Output':
            result[...] = processed[within_halo_key]

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            self._generation[self.name] += 1
            self.Output.setDirty(roi)
        elif slot.name == "Bias" or slot.name == "TemporalSmoothingGaussianFilterStdev" or \
             slot.name == "HalfWindowSize" or slot.name == "WhichQuantile" or \
             slot.name == "SpatialSmoothingGaussianFilterStdev":
            self._generation[self.name] += 1
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"
