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
__date__ = "$Jan 07, 2015 13:27:52 EST$"



import itertools
import math

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache

from ilastik.applets.base.applet import DatasetConstraintError

import itertools

import numpy

import nanshe
import nanshe.nanshe
import nanshe.nanshe.advanced_image_processing


class OpNansheEstimateF0(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNansheEstimateF0"
    category = "Pointwise"

    InputImage = InputSlot()

    HalfWindowSize = InputSlot(value=400, stype='int')
    WhichQuantile = InputSlot(value=0.15, stype='float')
    TemporalSmoothingGaussianFilterStdev = InputSlot(value=5.0, stype='float')
    TemporalSmoothingGaussianFilterWindowSize = InputSlot(value=5.0, stype='float')
    SpatialSmoothingGaussianFilterStdev = InputSlot(value=5.0, stype='float')
    SpatialSmoothingGaussianFilterWindowSize = InputSlot(value=5.0, stype='float')

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNansheEstimateF0, self ).__init__( *args, **kwargs )

        self._generation = {self.name : 0}

        self.InputImage.notifyReady( self._checkConstraints )

    def _checkConstraints(self, *args):
        slot = self.InputImage

        sh = slot.meta.shape
        ax = slot.meta.axistags
        if (len(slot.meta.shape) != 4) and (len(slot.meta.shape) != 5):
            # Raise a regular exception.  This error is for developers, not users.
            raise RuntimeError("was expecting a 4D or 5D dataset, got shape=%r" % (sh,))

        if "t" not in slot.meta.getTaggedShape():
            raise DatasetConstraintError(
                "EstimateF0",
                "Input must have time.")

        if "y" not in slot.meta.getTaggedShape():
            raise DatasetConstraintError(
                "EstimateF0",
                "Input must have space dim y.")

        if "x" not in slot.meta.getTaggedShape():
            raise DatasetConstraintError(
                "EstimateF0",
                "Input must have space dim x.")

        if "c" not in slot.meta.getTaggedShape():
            raise DatasetConstraintError(
                "EstimateF0",
                "Input must have channel.")

        numChannels = slot.meta.getTaggedShape()["c"]
        if numChannels != 1:
            raise DatasetConstraintError(
                "EstimateF0",
                "Input image must have exactly one channel.  " +
                "You attempted to add a dataset with {} channels".format( numChannels ) )

        if not ax[0].isTemporal():
            raise DatasetConstraintError(
                "EstimateF0",
                "Input image must have time first." )

        if not ax[-1].isChannel():
            raise DatasetConstraintError(
                "EstimateF0",
                "Input image must have channel last." )

        for i in range(1, len(ax) - 1):
            if not ax[i].isSpatial():
                # This is for developers.  Don't need a user-friendly error.
                raise RuntimeError("%d-th axis %r is not spatial" % (i, ax[i]))

    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.InputImage.meta )
        self.Output.meta.dtype = numpy.float32

        self.Output.meta.generation = self._generation

    @staticmethod
    def compute_halo(slicing,
                     image_shape,
                     half_window_size,
                     temporal_smoothing_gaussian_filter_stdev,
                     temporal_smoothing_gaussian_filter_window_size,
                     spatial_smoothing_gaussian_filter_stdev,
                     spatial_smoothing_gaussian_filter_window_size):
        slicing = nanshe.nanshe.additional_generators.reformat_slices(slicing, image_shape)

        halo = list(itertools.repeat(0, len(slicing) - 1))
        halo[0] = max(int(math.ceil(temporal_smoothing_gaussian_filter_window_size*temporal_smoothing_gaussian_filter_stdev)), half_window_size)
        for i in xrange(1, len(halo)):
            halo[i] = int(math.ceil(spatial_smoothing_gaussian_filter_window_size*spatial_smoothing_gaussian_filter_stdev))

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

        temporal_smoothing_gaussian_filter_stdev = self.TemporalSmoothingGaussianFilterStdev.value
        temporal_smoothing_gaussian_filter_window_size = self.TemporalSmoothingGaussianFilterWindowSize.value

        spatial_smoothing_gaussian_filter_stdev = self.SpatialSmoothingGaussianFilterStdev.value
        spatial_smoothing_gaussian_filter_window_size = self.SpatialSmoothingGaussianFilterWindowSize.value


        image_shape = self.InputImage.meta.shape

        key = roi.toSlice()
        halo_key, within_halo_key = OpNansheEstimateF0.compute_halo(key,
                                                                   image_shape,
                                                                   half_window_size,
                                                                   temporal_smoothing_gaussian_filter_stdev,
                                                                   temporal_smoothing_gaussian_filter_window_size,
                                                                   spatial_smoothing_gaussian_filter_stdev,
                                                                   spatial_smoothing_gaussian_filter_window_size)

        raw = self.InputImage[halo_key].wait()
        raw = raw[..., 0]

        f0 = nanshe.nanshe.advanced_image_processing.estimate_f0(
            raw,
            half_window_size=half_window_size,
            which_quantile=which_quantile,
            temporal_smoothing_gaussian_filter_stdev=temporal_smoothing_gaussian_filter_stdev,
            temporal_smoothing_gaussian_filter_window_size=temporal_smoothing_gaussian_filter_window_size,
            spatial_smoothing_gaussian_filter_stdev=spatial_smoothing_gaussian_filter_stdev,
            spatial_smoothing_gaussian_filter_window_size=spatial_smoothing_gaussian_filter_window_size
        )

        f0 = f0[..., None]

        if slot.name == 'Output':
            result[...] = f0[within_halo_key]

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            self._generation[self.name] += 1

            roi_slice = roi.toSlice()
            roi_halo = OpNansheEstimateF0.compute_halo(roi_slice,
                                                       self.InputImage.meta.shape,
                                                       self.HalfWindowSize.value,
                                                       self.TemporalSmoothingGaussianFilterStdev.value,
                                                       self.TemporalSmoothingGaussianFilterWindowSize.value,
                                                       self.SpatialSmoothingGaussianFilterStdev.value,
                                                       self.SpatialSmoothingGaussianFilterWindowSize.value)[0]

            self.Output.setDirty(roi_halo)
        elif slot.name == "TemporalSmoothingGaussianFilterStdev" or \
             slot.name == "TemporalSmoothingGaussianFilterWindowSize" or \
             slot.name == "HalfWindowSize" or slot.name == "WhichQuantile" or \
             slot.name == "SpatialSmoothingGaussianFilterStdev" or \
             slot.name == "SpatialSmoothingGaussianFilterWindowSize":
            self._generation[self.name] += 1
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"


class OpNansheEstimateF0Cached(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNansheEstimateF0Cached"
    category = "Pointwise"


    InputImage = InputSlot()

    HalfWindowSize = InputSlot(value=400, stype='int')
    WhichQuantile = InputSlot(value=0.15, stype='float')
    TemporalSmoothingGaussianFilterStdev = InputSlot(value=5.0, stype='float')
    TemporalSmoothingGaussianFilterWindowSize = InputSlot(value=5.0, stype='float')
    SpatialSmoothingGaussianFilterStdev = InputSlot(value=5.0, stype='float')
    SpatialSmoothingGaussianFilterWindowSize = InputSlot(value=5.0, stype='float')

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNansheEstimateF0Cached, self ).__init__( *args, **kwargs )

        self.opEstimateF0 = OpNansheEstimateF0(parent=self)

        self.opEstimateF0.HalfWindowSize.connect(self.HalfWindowSize)
        self.opEstimateF0.WhichQuantile.connect(self.WhichQuantile)
        self.opEstimateF0.TemporalSmoothingGaussianFilterStdev.connect(self.TemporalSmoothingGaussianFilterStdev)
        self.opEstimateF0.TemporalSmoothingGaussianFilterWindowSize.connect(self.TemporalSmoothingGaussianFilterWindowSize)
        self.opEstimateF0.SpatialSmoothingGaussianFilterStdev.connect(self.SpatialSmoothingGaussianFilterStdev)
        self.opEstimateF0.SpatialSmoothingGaussianFilterWindowSize.connect(self.SpatialSmoothingGaussianFilterWindowSize)

        self.opCache_F0 = OpBlockedArrayCache(parent=self)
        self.opCache_F0.fixAtCurrent.setValue(False)

        self.opEstimateF0.InputImage.connect( self.InputImage )
        self.opCache_F0.Input.connect( self.opEstimateF0.Output )

        self.Output.connect( self.opCache_F0.Output )

    def setupOutputs(self):
        axes_shape_iter = itertools.izip(self.opEstimateF0.Output.meta.axistags, self.opEstimateF0.Output.meta.shape)

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

        halo_slicing = self.opEstimateF0.compute_halo(halo_center_slicing,
                                                     self.InputImage.meta.shape,
                                                     self.HalfWindowSize.value,
                                                     self.TemporalSmoothingGaussianFilterStdev.value,
                                                     self.TemporalSmoothingGaussianFilterWindowSize.value,
                                                     self.SpatialSmoothingGaussianFilterStdev.value,
                                                     self.SpatialSmoothingGaussianFilterWindowSize.value)[0]

        block_shape = nanshe.nanshe.additional_generators.len_slices(halo_slicing)

        block_shape = list(block_shape)

        for i, each_axistag in enumerate(self.opEstimateF0.Output.meta.axistags):
            if each_axistag.isSpatial():
                block_shape[i] = max(block_shape[i], 256)
            elif each_axistag.isTemporal():
                block_shape[i] = max(block_shape[i], 50)

            block_shape[i] = min(block_shape[i], self.opEstimateF0.Output.meta.shape[i])

        block_shape = tuple(block_shape)

        self.opCache_F0.innerBlockShape.setValue(block_shape)
        self.opCache_F0.outerBlockShape.setValue(block_shape)

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass
