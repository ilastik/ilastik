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
from lazyflow.operators import OpBlockedArrayCache

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


class OpMeanProjectionCached(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpMeanProjectionCached"
    category = "Pointwise"


    InputImage = InputSlot()

    Axis = InputSlot(value=0, stype="int")

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpMeanProjectionCached, self ).__init__( *args, **kwargs )

        self.opMeanProjection = OpMeanProjection(parent=self)

        self.opMeanProjection.Axis.connect(self.Axis)


        self.opCache = OpBlockedArrayCache(parent=self)
        self.opCache.fixAtCurrent.setValue(False)

        self.opMeanProjection.InputImage.connect( self.InputImage )
        self.opCache.Input.connect( self.opMeanProjection.Output )
        self.Output.connect( self.opCache.Output )

    def setupOutputs(self):
        axes_shape_iter = itertools.izip(self.opMeanProjection.Output.meta.axistags,
                                         self.opMeanProjection.Output.meta.shape)

        halo_center_slicing = []

        for each_axistag, each_len in axes_shape_iter:
            each_halo_center = each_len
            each_halo_center_slicing = slice(0, each_len, 1)

            if each_axistag.isTemporal() or each_axistag.isSpatial():
                each_halo_center /= 2.0
                # Must take floor consider the singleton dimension case
                each_halo_center = int(math.floor(each_halo_center))
                each_halo_center_slicing = slice(each_halo_center, each_halo_center + 1, 1)

            halo_center_slicing.append(each_halo_center_slicing)

        halo_center_slicing = tuple(halo_center_slicing)

        halo_slicing = self.opMeanProjection.compute_halo(halo_center_slicing,
                                                         self.InputImage.meta.shape,
                                                         self.Axis.value)[0]


        block_shape = nanshe.additional_generators.len_slices(halo_slicing)


        block_shape = list(block_shape)

        for i, each_axistag in enumerate(self.opMeanProjection.Output.meta.axistags):
            if each_axistag.isSpatial():
                block_shape[i] = max(block_shape[i], 256)

            block_shape[i] = min(block_shape[i], self.opMeanProjection.Output.meta.shape[i])

        block_shape = tuple(block_shape)


        self.opCache.innerBlockShape.setValue(block_shape)
        self.opCache.outerBlockShape.setValue(block_shape)

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass
