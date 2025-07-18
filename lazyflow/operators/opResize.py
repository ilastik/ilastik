###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2025, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#          http://ilastik.org/license/
###############################################################################
import logging
from enum import IntEnum
from typing import List, Union, Tuple

import numpy as np
from numpy.typing import NDArray
from scipy import ndimage as scipy_ndimage

from lazyflow.graph import Operator, InputSlot, OutputSlot, Slot
from lazyflow.roi import enlargeRoiForHalo, roiToSlice
from lazyflow.rtype import SubRegion

logger = logging.getLogger(__name__)


def ceil_roi(roi: NDArray) -> NDArray:
    """
    Expand roi to nearest integer
    """
    return np.array([np.floor(roi[0]), np.ceil(roi[1])])


class OpResize(Operator):
    """
    Reimplements scikit-image.transform.resize as a lazyflow operator,
    handling in particular the halo for antialiasing in the context of subregions.

    The gaussian filter for antialiasing is run with custom sigmas that are negligibly larger
    than the scikit-image default at scaling factors <2, and smaller at scaling factors >2.
    This should save some computation cost for large scaling steps. Cf. GitHub #3037.

    Cannot resize along channel axis (would be nonsense).
    Time is treated like space axes, so resize along t at your own risk.
    """

    class Interpolation(IntEnum):
        NEAREST = 0
        LINEAR = 1

    required_min_padding = {  # minimum pixels of halo required for accurate interpolation
        Interpolation.NEAREST: 0,
        Interpolation.LINEAR: 2,
    }

    RawImage = InputSlot()
    TargetShape = InputSlot()
    InterpolationOrder = InputSlot(value=Interpolation.LINEAR)
    ResizedImage = OutputSlot()

    def __init__(
        self,
        parent=None,
        graph=None,
        RawImage: Slot = None,
        TargetShape: Union[Tuple[int, ...], Slot, None] = None,
        InterpolationOrder: Union[Interpolation, Slot, None] = None,
        **kwargs,
    ):
        super().__init__(parent=parent, graph=graph, **kwargs)
        self.scaling_factors: Union[NDArray, None] = None  # one factor per axis. Factor 2.0 = downscale to half size
        self.antialiasing_sigmas: Union[NDArray, None] = None  # one sigma per axis
        self.RawImage.setOrConnectIfAvailable(RawImage)
        self.TargetShape.setOrConnectIfAvailable(TargetShape)
        self.InterpolationOrder.setOrConnectIfAvailable(InterpolationOrder)

    def setupOutputs(self):
        if self.TargetShape.value == self.RawImage.meta.shape:
            # Shortcut: no resizing needed
            self.ResizedImage.connect(self.RawImage)
        input_axiskeys = self.RawImage.meta.getAxisKeys()
        assert len(input_axiskeys) == len(
            self.TargetShape.value
        ), f"Input image ({self.RawImage.meta.shape}) and target shape ({self.TargetShape.value}) must have same axes"
        assert (
            "c" not in input_axiskeys
            or self.TargetShape.value[input_axiskeys.index("c")] == self.RawImage.meta.getTaggedShape()["c"]
        ), "Cannot resize along channel axis"
        if (
            "t" in input_axiskeys
            and self.TargetShape.value[input_axiskeys.index("t")] != self.RawImage.meta.getTaggedShape()["t"]
        ):
            logger.warning("Resizing along time axis. Are you sure this is what you want?")
        self.ResizedImage.meta.assignFrom(self.RawImage.meta)
        self.ResizedImage.meta.shape = self.TargetShape.value

        # Scaling factors are the inverse of zoom factors in the scipy.ndimage sense.
        # E.g. 2 if the output shape is half the input shape (rather than 0.5).
        shape_in = self.RawImage.meta.shape
        shape_out = self.ResizedImage.meta.shape
        self.scaling_factors = np.divide(shape_in, shape_out)

        interpolation_order = self.InterpolationOrder.value
        # If higher-order interpolation is desired, need to figure out required padding
        assert (
            interpolation_order in self.required_min_padding
        ), "supports only order 0 (nearest-neighbor) or 1 (linear)"

        if interpolation_order > 0:
            # Antialiasing only for downscale (f > 1), not identity or upscale.
            # This also ensures that we never run a gaussian across channels (since scaling along c is forbidden).
            self.antialiasing_sigmas = np.array([f / 4 if f > 1 else 0 for f in self.scaling_factors])
        else:
            # No antialiasing for nearest-neighbor interpolation
            self.antialiasing_sigmas = np.zeros_like(self.scaling_factors)

    def execute(self, slot, subindex, roi, result):
        """
        Roi is scaled: The requester is asking for (a subportion of) the scaled image.
        - Reverse scaling of roi
        - Pad with halo to request sufficient subregion of raw image for antialiasing and interpolation
        - Compute scaled coordinates of source pixels within the padded blurred raw subregion
        - Use map_coordinates to interpolate values at those source coordinates
        """
        assert slot is self.ResizedImage, "Unknown output slot"

        factors = self.scaling_factors
        antialiasing_sigmas = self.antialiasing_sigmas
        interpolation_order = self.InterpolationOrder.value
        axes_to_pad = np.not_equal(self.scaling_factors, 1)
        raw_roi = self._reverse_roi_scaling(roi, factors)
        raw_roi_antialiasing_halo = enlargeRoiForHalo(
            raw_roi[0],
            raw_roi[1],
            self.RawImage.meta.shape,
            sigma=antialiasing_sigmas,
            enlarge_axes=axes_to_pad,
        )
        raw_roi_interpolation_halo = self._extend_halo_to_minimum(
            raw_roi_antialiasing_halo, self.required_min_padding[interpolation_order], axes_to_pad, raw_roi
        )
        raw_roi_final_halo = np.clip(ceil_roi(raw_roi_interpolation_halo), 0, self.RawImage.meta.shape)

        raw = self.RawImage[roiToSlice(*raw_roi_final_halo)].wait().astype(np.float64)
        filtered = scipy_ndimage.gaussian_filter(raw, antialiasing_sigmas, mode="mirror")

        roi_shape = roi.stop - roi.start
        result_roi_within_filtered = raw_roi - raw_roi_final_halo[0]
        source_coords_starts = result_roi_within_filtered[0]
        source_coords_stops = result_roi_within_filtered[1] - factors
        if "c" not in self.RawImage.meta.getAxisKeys():
            scaled_source_grid = self._roi_to_coord_grid(source_coords_starts, source_coords_stops, roi_shape)
            result[...] = scipy_ndimage.map_coordinates(
                filtered, scaled_source_grid, order=interpolation_order, mode="mirror"
            )
            return

        # Split channels and interpolate each separately. Not faster but less RAM.
        channel_axis = self.ResizedImage.meta.getAxisKeys().index("c")
        n_channels = roi_shape[channel_axis]
        roi_shape[channel_axis] = 1  # Will be 1 after splitting
        source_coords_starts[channel_axis] = 1
        source_coords_stops[channel_axis] = 1
        scaled_source_grid = self._roi_to_coord_grid(source_coords_starts, source_coords_stops, roi_shape)
        filtered_split = np.split(filtered, n_channels, axis=channel_axis)
        for c in range(n_channels):
            channel_slicing = [slice(None)] * len(factors)
            channel_slicing[channel_axis] = slice(c, c + 1)
            channel_slicing = tuple(channel_slicing)
            result[channel_slicing] = scipy_ndimage.map_coordinates(
                filtered_split[c], scaled_source_grid, order=interpolation_order, mode="mirror"
            )

    def propagateDirty(self, slot, subindex, roi):
        # roi is on RawImage scale here (unscaled). Would technically need to scale it to ResizedImage scale,
        # but should be unnecessary because the entire scaled image needs to be recomputed anyway.
        self.ResizedImage.setDirty(slice(None))

    @staticmethod
    def _roi_to_coord_grid(starts: NDArray, stops: NDArray, steps: NDArray) -> List[NDArray]:
        """
        Converts roi ([starts, stops]) to grids of `steps` pixel coordinates within the roi.
        Meshgrid returns a list of one coordinate grid per axis.
        """
        assert len(starts) == len(stops) == len(steps), "Dimensions must match"
        return np.meshgrid(
            *(np.linspace(start, stop, n) for start, stop, n in zip(starts, stops, steps)),
            indexing="ij",
        )

    @staticmethod
    def _extend_halo_to_minimum(
        roi_with_halo: NDArray, minimum: int, axes_to_extend: NDArray, original_roi: NDArray
    ) -> NDArray:
        """
        Extend an existing halo on `roi_with_halo` to `minimum` along axes in `axes_to_extend`.
        `original_roi` required to determine how much halo was already present.
        """
        if minimum == 0:
            return roi_with_halo
        assert len(roi_with_halo[0]) == len(axes_to_extend) == len(original_roi[0]), "Dimensions must match"
        min_halo = np.zeros_like(roi_with_halo) + minimum
        min_halo[0] = min_halo[0] * -1
        existing_halo = roi_with_halo - original_roi
        required_padding = min_halo - existing_halo
        # Avoid negative if halo was already larger than minimum
        required_padding[0] = np.minimum(0, required_padding[0])
        required_padding[1] = np.maximum(0, required_padding[1])
        return roi_with_halo + required_padding * axes_to_extend

    @staticmethod
    def _get_first_pixel_shift(s: NDArray) -> NDArray:
        """
        Compute the offset of the first pixel on scale s from the raw scale origin.
        E.g. on scale 3, each pixel accounts for +-1.5 of the data space from its
        position. The data space begins at -0.5, therefore the first scale-3 pixel
        is positioned at coordinate 1.0 and accounts for -0.5 to 2.5
        (which is the same data space that three scale-1, i.e. raw pixels account for).
        This fixes the infamous "half-pixel offset", block boundary and rounding errors,
        and enables handling arbitrary fractional scales.
        """
        return s / 2 - 0.5

    @staticmethod
    def _reverse_roi_scaling(roi: SubRegion, factors: NDArray) -> NDArray:
        """
        Given the roi is requested at the target scale, compute the corresponding roi at the raw scale.
        The scaled roi's bounds can be outside the raw image shape.
        Returns roi as numpy.ndarray[start, stop] instead of SubRegion to be independent of slot.
        """
        assert len(factors) == len(roi.start) == len(roi.stop), "Dimensions must match"
        raw_shape = np.multiply(roi.stop - roi.start, factors)
        raw_start = np.multiply(roi.start, factors) + OpResize._get_first_pixel_shift(factors)
        raw_stop = raw_start + raw_shape
        return np.array([raw_start, raw_stop])
