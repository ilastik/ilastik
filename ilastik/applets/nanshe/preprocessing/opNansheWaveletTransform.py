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
import math

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache

from ilastik.applets.base.applet import DatasetConstraintError

import numpy

import nanshe
import nanshe.util.iters
import nanshe.imp.wavelet_transform


class OpNansheWaveletTransform(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNansheWaveletTransform"
    category = "Pointwise"


    Input = InputSlot()

    Scale = InputSlot(value=4, stype="int")
    
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNansheWaveletTransform, self ).__init__( *args, **kwargs )

        self._generation = {self.name : 0}

        self.Input.notifyReady( self._checkConstraints )

    def _checkConstraints(self, *args):
        slot = self.Input

        sh = slot.meta.shape
        ax = slot.meta.axistags
        if (len(slot.meta.shape) != 4) and (len(slot.meta.shape) != 5):
            # Raise a regular exception.  This error is for developers, not users.
            raise RuntimeError("was expecting a 4D or 5D dataset, got shape=%r" % (sh,))

        if "t" not in slot.meta.getTaggedShape():
            raise DatasetConstraintError(
                "WaveletTransform",
                "Input must have time.")

        if "y" not in slot.meta.getTaggedShape():
            raise DatasetConstraintError(
                "WaveletTransform",
                "Input must have space dim y.")

        if "x" not in slot.meta.getTaggedShape():
            raise DatasetConstraintError(
                "WaveletTransform",
                "Input must have space dim x.")

        if "c" not in slot.meta.getTaggedShape():
            raise DatasetConstraintError(
                "WaveletTransform",
                "Input must have channel.")

        numChannels = slot.meta.getTaggedShape()["c"]
        if numChannels != 1:
            raise DatasetConstraintError(
                "WaveletTransform",
                "Input image must have exactly one channel.  " +
                "You attempted to add a dataset with {} channels".format( numChannels ) )

        if not ax[0].isTemporal():
            raise DatasetConstraintError(
                "WaveletTransform",
                "Input image must have time first." )

        if not ax[-1].isChannel():
            raise DatasetConstraintError(
                "WaveletTransform",
                "Input image must have channel last." )

        for i in range(1, len(ax) - 1):
            if not ax[i].isSpatial():
                # This is for developers.  Don't need a user-friendly error.
                raise RuntimeError("%d-th axis %r is not spatial" % (i, ax[i]))
    
    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.Input.meta )
        self.Output.meta.dtype = numpy.float32

        self.Output.meta.generation = self._generation
    
    @staticmethod
    def compute_halo(slicing, image_shape, scale):
        slicing = nanshe.util.iters.reformat_slices(slicing, image_shape)

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

        image_shape = self.Input.meta.shape

        key = roi.toSlice()
        halo_key, within_halo_key = OpNansheWaveletTransform.compute_halo(key, image_shape, scale)

        raw = self.Input[halo_key].wait()
        raw = raw[..., 0]

        processed = nanshe.imp.wavelet_transform.wavelet_transform(raw,
                                                                      scale=scale,
                                                                      include_intermediates = False,
                                                                      include_lower_scales = False)
        processed = processed[..., None]
        
        if slot.name == 'Output':
            result[...] = processed[within_halo_key]

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "Input":
            self._generation[self.name] += 1
            self.Output.setDirty(OpNansheWaveletTransform.compute_halo(roi.toSlice(),
                                                                       self.Input.meta.shape,
                                                                       self.Scale.value)[0])
        elif slot.name == "Scale":
            self._generation[self.name] += 1
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"


class OpNansheWaveletTransformCached(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNansheWaveletTransformCached"
    category = "Pointwise"


    Input = InputSlot()

    Scale = InputSlot(value=4, stype="int")

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNansheWaveletTransformCached, self ).__init__( *args, **kwargs )

        self.opWaveletTransform = OpNansheWaveletTransform(parent=self)

        self.opWaveletTransform.Scale.connect(self.Scale)


        self.opCache = OpBlockedArrayCache(parent=self)
        self.opCache.fixAtCurrent.setValue(False)

        self.opWaveletTransform.Input.connect( self.Input )
        self.opCache.Input.connect( self.opWaveletTransform.Output )
        self.Output.connect( self.opCache.Output )

    def setupOutputs(self):
        axes_shape_iter = itertools.izip(self.opWaveletTransform.Output.meta.axistags,
                                         self.opWaveletTransform.Output.meta.shape)

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

        halo_slicing = self.opWaveletTransform.compute_halo(halo_center_slicing,
                                                            self.Input.meta.shape,
                                                            self.Scale.value)[0]


        block_shape = nanshe.util.iters.len_slices(halo_slicing)


        block_shape = list(block_shape)

        for i, each_axistag in enumerate(self.opWaveletTransform.Output.meta.axistags):
            if each_axistag.isSpatial():
                block_shape[i] = max(block_shape[i], 256)
            elif each_axistag.isTemporal():
                block_shape[i] = max(block_shape[i], 50)

            block_shape[i] = min(block_shape[i], self.opWaveletTransform.Output.meta.shape[i])

        block_shape = tuple(block_shape)

        self.opCache.innerBlockShape.setValue(block_shape)
        self.opCache.outerBlockShape.setValue(block_shape)

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass
