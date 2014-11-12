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
__date__ = "$Nov 12, 2014 15:20:09 EST$"



import itertools
import math

from lazyflow.graph import Operator, InputSlot, OutputSlot

import vigra

import nanshe
import nanshe.wavelet_transform
import nanshe.additional_generators


class OpMeanProjection(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpMeanProjection"
    category = "Pointwise"


    InputImage = InputSlot()

    Axis = InputSlot(value=0, stype="int")

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpMeanProjection, self ).__init__( *args, **kwargs )

        self._generation = {self.name : 0}

    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.InputImage.meta )

        self.Output.meta.shape = self.Output.meta.shape[:self.Axis.value] +\
                                 (1,) +\
                                 self.Output.meta.shape[self.Axis.value+1:]

        self.Output.meta.generation = self._generation

    @staticmethod
    def compute_halo(slicing, image_shape, axis):
        slicing = nanshe.additional_generators.reformat_slices(slicing, image_shape)

        halo_slicing = slicing
        halo_slicing = list(halo_slicing)
        halo_slicing[axis] = nanshe.additional_generators.reformat_slice(slice(None), image_shape[axis])
        halo_slicing = tuple(halo_slicing)

        within_halo_slicing = halo_slicing
        within_halo_slicing = list(within_halo_slicing)
        within_halo_slicing[axis] = slice(0, 1, 1)
        within_halo_slicing = tuple(within_halo_slicing)

        return(halo_slicing, within_halo_slicing)

    def execute(self, slot, subindex, roi, result):
        image_shape = self.InputImage.meta.shape

        key = roi.toSlice()
        halo_key, within_halo_key = OpMeanProjection.compute_halo(key, image_shape, self.Axis.value)

        raw = self.InputImage[halo_key].wait()

        processed = raw.mean(axis=self.Axis.value)
        processed = nanshe.expanded_numpy.add_singleton_axis_pos(processed, self.Axis.value)

        if slot.name == 'Output':
            result[...] = processed

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            self._generation[self.name] += 1
            self.Output.setDirty(OpMeanProjection.compute_halo(roi.toSlice(),
                                                              self.InputImage.meta.shape,
                                                              self.Axis.value)[0])
        elif slot.name == "Axis":
            self._generation[self.name] += 1
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"
