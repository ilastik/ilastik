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
__date__ = "$Oct 14, 2014 16:35:36 EDT$"



import itertools

from lazyflow.graph import Operator, InputSlot, OutputSlot

import numpy

import nanshe
import nanshe.wavelet_transform
import nanshe.additional_generators


class OpNansheWaveletTransform(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNansheWaveletTransform"
    category = "Pointwise"


    InputImage = InputSlot()

    Scale = InputSlot(value=4, stype="int")
    
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNansheWaveletTransform, self ).__init__( *args, **kwargs )

        self._generation = {self.name : 0}
    
    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.InputImage.meta )

        self.Output.meta.generation = self._generation
    
    @staticmethod
    def compute_halo(slicing, image_shape, scale):
        slicing = nanshe.additional_generators.reformat_slices(slicing, image_shape)

        half_halo = list(itertools.repeat(0, len(slicing)))
        halo_slicing = list(slicing)
        within_halo_slicing = list(slicing)
        try:
            scale_iter = enumerate(scale)
        except TypeError:
            scale_iter = enumerate(itertools.repeat(scale, len(halo_slicing)))

        for i, each_scale in scale_iter:
            half_halo_i = 0
            for j in xrange(1, 1+each_scale):
                half_halo_i += 2**j

            halo_slicing_i_start = (halo_slicing[i].start - half_halo_i)
            within_halo_slicing_i_start = half_halo_i
            if (halo_slicing_i_start < 0):
                within_halo_slicing_i_start += halo_slicing_i_start
                halo_slicing_i_start = 0


            halo_slicing_i_stop = (halo_slicing[i].stop + half_halo_i)
            within_halo_slicing_i_stop = (slicing[i].stop - slicing[i].start) + within_halo_slicing_i_start
            if (halo_slicing_i_stop > image_shape[i]):
                halo_slicing_i_stop = image_shape[i]

            half_halo[i] = half_halo_i
            halo_slicing[i] = slice(halo_slicing_i_start, halo_slicing_i_stop, halo_slicing[i].step)
            within_halo_slicing[i] = slice(within_halo_slicing_i_start,
                                           within_halo_slicing_i_stop,
                                           within_halo_slicing[i].step)

        half_halo = tuple(half_halo)
        halo_slicing = tuple(halo_slicing)
        within_halo_slicing = tuple(within_halo_slicing)

        return(halo_slicing, within_halo_slicing)
    
    def execute(self, slot, subindex, roi, result):
        scale = self.Scale.value
        # include_lower_scales = self.IncludeLowerScales.value

        image_shape = self.InputImage.meta.shape

        key = roi.toSlice()
        halo_key, within_halo_key = OpNansheWaveletTransform.compute_halo(key, image_shape, scale)

        raw = self.InputImage[halo_key].wait()
        raw = raw[..., 0]

        processed = nanshe.wavelet_transform.wavelet_transform(raw,
                                                               scale=scale,
                                                               include_intermediates = False,
                                                               include_lower_scales = False)
        processed = processed[..., None]
        
        if slot.name == 'Output':
            result[...] = processed[within_halo_key]

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            self._generation[self.name] += 1
            self.Output.setDirty(OpNansheWaveletTransform.compute_halo(roi.toSlice(),
                                                                       self.InputImage.meta.shape,
                                                                       self.Scale.value)[0])
        elif slot.name == "Scale":
            self._generation[self.name] += 1
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"
