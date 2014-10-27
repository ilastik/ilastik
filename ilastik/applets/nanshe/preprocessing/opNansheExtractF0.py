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

from lazyflow.operators import OpBlockedArrayCache

import itertools

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
    BiasEnabled = InputSlot(value=False, stype='bool')
    Bias = InputSlot(value=0.0, stype='float')

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNansheExtractF0, self ).__init__( *args, **kwargs )

        self._generation = {self.name : 0}
    
    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.InputImage.meta )

        self.Output.meta.generation = self._generation

    @staticmethod
    def compute_halo(slicing, image_shape, half_window_size,
                                           temporal_smoothing_gaussian_filter_stdev,
                                           spatial_smoothing_gaussian_filter_stdev):
        slicing = nanshe.additional_generators.reformat_slices(slicing, image_shape)

        halo = list(itertools.repeat(0, len(slicing) - 1))
        halo[0] = max(int(math.ceil(5*temporal_smoothing_gaussian_filter_stdev)), half_window_size)
        for i in xrange(1, len(halo)):
            halo[i] = int(math.ceil(5*spatial_smoothing_gaussian_filter_stdev))

        halo_slicing = list(slicing)
        within_halo_slicing = list(slicing)

        for i in xrange(len(halo)):
            halo_slicing_i_start = (halo_slicing[i].start - halo[i])
            within_halo_slicing_i_start = halo[i]
            if (halo_slicing_i_start < 0):
                within_halo_slicing_i_start += halo_slicing_i_start
                halo_slicing_i_start = 0


            halo_slicing_i_stop = (halo_slicing[i].stop + halo[i])
            within_halo_slicing_i_stop = (slicing[i].stop - slicing[i].start) + within_halo_slicing_i_start
            if (halo_slicing_i_stop > image_shape[i]):
                halo_slicing_i_stop = image_shape[i]

            halo_slicing[i] = slice(halo_slicing_i_start, halo_slicing_i_stop, halo_slicing[i].step)
            within_halo_slicing[i] = slice(within_halo_slicing_i_start,
                                           within_halo_slicing_i_stop,
                                           within_halo_slicing[i].step)

        halo_slicing = tuple(halo_slicing)
        within_halo_slicing = tuple(within_halo_slicing)

        return(halo_slicing, within_halo_slicing)
    
    def execute(self, slot, subindex, roi, result):
        half_window_size = self.HalfWindowSize.value
        which_quantile = self.WhichQuantile.value

        bias = None
        if self.BiasEnabled.value:
            bias = self.Bias.value

        temporal_smoothing_gaussian_filter_stdev = self.TemporalSmoothingGaussianFilterStdev.value
        spatial_smoothing_gaussian_filter_stdev = self.SpatialSmoothingGaussianFilterStdev.value


        image_shape = self.InputImage.meta.shape

        key = roi.toSlice()
        halo_key, within_halo_key = OpNansheExtractF0.compute_halo(key, image_shape, half_window_size,
                                                                   temporal_smoothing_gaussian_filter_stdev,
                                                                   spatial_smoothing_gaussian_filter_stdev)

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
            self.Output.setDirty(OpNansheExtractF0.compute_halo(roi.toSlice(), self.InputImage.meta.shape,
                                                                self.HalfWindowSize.value,
                                                                self.TemporalSmoothingGaussianFilterStdev.value,
                                                                self.SpatialSmoothingGaussianFilterStdev.value)[0])
        elif slot.name == "Bias" or slot.name == "BiasEnabled" or \
             slot.name == "TemporalSmoothingGaussianFilterStdev" or \
             slot.name == "HalfWindowSize" or slot.name == "WhichQuantile" or \
             slot.name == "SpatialSmoothingGaussianFilterStdev":
            self._generation[self.name] += 1
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"


class OpNansheExtractF0Cached(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNansheExtractF0Cached"
    category = "Pointwise"


    InputImage = InputSlot()

    HalfWindowSize = InputSlot(value=400, stype='int')
    WhichQuantile = InputSlot(value=0.15, stype='float')
    TemporalSmoothingGaussianFilterStdev = InputSlot(value=5.0, stype='float')
    SpatialSmoothingGaussianFilterStdev = InputSlot(value=5.0, stype='float')
    BiasEnabled = InputSlot(value=False, stype='bool')
    Bias = InputSlot(value=0.0, stype='float')

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNansheExtractF0Cached, self ).__init__( *args, **kwargs )

        self.opExtractF0 = OpNansheExtractF0(parent=self)

        self.opExtractF0.HalfWindowSize.connect(self.HalfWindowSize)
        self.opExtractF0.WhichQuantile.connect(self.WhichQuantile)
        self.opExtractF0.TemporalSmoothingGaussianFilterStdev.connect(self.TemporalSmoothingGaussianFilterStdev)
        self.opExtractF0.SpatialSmoothingGaussianFilterStdev.connect(self.SpatialSmoothingGaussianFilterStdev)
        self.opExtractF0.BiasEnabled.connect(self.BiasEnabled)
        self.opExtractF0.Bias.connect(self.Bias)


        self.opCache = OpBlockedArrayCache(parent=self)
        self.opCache.fixAtCurrent.setValue(False)

        self.opExtractF0.InputImage.connect( self.InputImage )
        self.opCache.Input.connect( self.opExtractF0.Output )
        self.Output.connect( self.opCache.Output )

    def setupOutputs(self):
        axes_shape_iter = itertools.izip(self.opExtractF0.Output.meta.axistags, self.opExtractF0.Output.meta.shape)

        block_shape = [_v if not _k.isSpatial() else 256 for _k, _v in axes_shape_iter]
        block_shape = tuple(block_shape)

        self.opCache.innerBlockShape.setValue(block_shape)
        self.opCache.outerBlockShape.setValue(self.opExtractF0.Output.meta.shape)

    def propagateDirty(self, slot, subindex, roi):
        pass
