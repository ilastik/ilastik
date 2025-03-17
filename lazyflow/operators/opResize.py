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
from typing import Sequence

import numpy as np
from scipy import ndimage as scipy_ndimage

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import enlargeRoiForHalo, roiToSlice
from lazyflow.rtype import SubRegion

logger = logging.getLogger(__name__)


class OpResize(Operator):
    """
    Reimplements scikit-image.transform.resize as a lazyflow operator,
    handling in particular the halo for antialiasing in the context of subregions.

    The gaussian filter for antialiasing is run with custom sigmas that are negligibly larger
    than the scikit-image default at scaling factors <2, and smaller at scaling factors >2.
    This should reduce the required halo sizes and possibly maintain more information
    (remains to be tested).

    Cannot resize along channel axis (would be nonsense).
    Time is treated like space axes, so resize along t at your own risk.
    """

    RawImage = InputSlot()
    TargetShape = InputSlot()  # Tuple[int, ...]
    ResizedImage = OutputSlot()

    def setupOutputs(self):
        input_axiskeys = self.RawImage.meta.getAxisKeys()
        assert len(input_axiskeys) == len(
            self.TargetShape.value
        ), f"Input image ({self.RawImage.meta.shape}) and target shape ({self.TargetShape.value}) must have same axes"
        assert (
            "c" not in input_axiskeys
            or self.TargetShape.value[input_axiskeys.index("c")] == self.RawImage.meta.getTaggedShape["c"]
        ), "Cannot resize along channel axis"
        if (
            "t" in input_axiskeys
            and self.TargetShape.value[input_axiskeys.index("t")] != self.RawImage.meta.getTaggedShape["t"]
        ):
            logger.warning("Resizing along time axis. Are you sure this is what you want?")
        self.ResizedImage.meta.assignFrom(self.RawImage.meta)
        self.ResizedImage.meta.shape = self.TargetShape.value

    def execute(self, slot, subindex, roi, result):
        """Roi is scaled: The requester is asking for (a subportion of) the scaled image.
        Need to reverse scaling of roi and pad that with halo to request sufficient subregion
        of raw image for antialiasing."""
        assert slot is self.ResizedImage, "Unknown output slot"
        downscaling_factors = self._get_scaling_factors()
        midpoint_shift = self.get_data_space_shift()
        assert all(f >= 1 for f in downscaling_factors), "Upscaling not supported yet"
        # antialiasing_sigmas = np.array([f / 4 for f in downscaling_factors])
        antialiasing_sigmas = np.maximum(0, (downscaling_factors - 1) / 2)
        axes_to_pad = downscaling_factors > 1
        raw_roi = self._reverse_roi_scaling(roi, downscaling_factors, midpoint_shift)
        raw_roi_with_halo = enlargeRoiForHalo(
            raw_roi[0],
            raw_roi[1],
            self.RawImage.meta.shape,
            sigma=antialiasing_sigmas,
            enlarge_axes=axes_to_pad,
        )
        raw_roi_with_halo_rounded = np.array([np.floor(raw_roi_with_halo[0]), np.ceil(raw_roi_with_halo[1])])
        raw = self.RawImage[roiToSlice(*raw_roi_with_halo_rounded)].wait().astype(np.float64)
        filtered = scipy_ndimage.gaussian_filter(raw, antialiasing_sigmas, mode="mirror")
        result_roi_within_filtered = raw_roi - raw_roi_with_halo_rounded[0]
        scaled_source_coords = np.meshgrid(
            *(
                np.linspace(start, stop - scale, shape)
                for start, stop, shape, scale in zip(
                    result_roi_within_filtered[0],
                    result_roi_within_filtered[1],
                    roi.stop - roi.start,
                    downscaling_factors,
                )
            ),
            indexing="ij",
        )
        scaled = scipy_ndimage.map_coordinates(filtered, scaled_source_coords, order=1, mode="mirror")
        result[...] = scaled

    def propagateDirty(self, slot, subindex, roi):
        # roi is on RawImage scale here (unscaled). Would technically need to scale it to ResizedImage scale,
        # but should be unnecessary because the entire scaled image needs to be recomputed anyway.
        self.ResizedImage.setDirty(slice(None))

    def _get_scaling_factors(self):
        """
        Scaling factors are the inverse of zoom factors in the scipy.ndimage sense.
        E.g. 2 if the output shape is half the input shape (rather than 0.5).
        """
        assert self.ResizedImage.ready(), "Must not be called when unready"
        shape_in = self.RawImage.meta.shape
        shape_out = self.ResizedImage.meta.shape
        return np.divide(shape_in, shape_out)

    def get_data_space_shift(self) -> np.typing.NDArray:
        """
        Compute the offset of the first scaled pixel relative to the first raw pixel,
        such that the scaled image is centered within the raw image.
        """
        downscaling_factors = self._get_scaling_factors()
        # Total space between first and last pixel
        raw_size = np.array(self.RawImage.meta.shape) - 1
        # Scaled pixels each account for downscaling_factors space inbetween them
        scaled_size = (np.array(self.ResizedImage.meta.shape) - 1) * downscaling_factors
        return (raw_size - scaled_size) / 2

    @staticmethod
    def _reverse_roi_scaling(roi: SubRegion, factors: Sequence[float], shift: Sequence[float]) -> np.typing.NDArray:
        """
        Given the roi is requested at the target scale, compute the corresponding roi at the raw scale.
        The scaled roi's bounds can be outside the raw image shape.
        Returns roi as numpy.ndarray[start, stop] instead of SubRegion to be independent of slot.
        """
        assert len(factors) == len(shift) == len(roi.start) == len(roi.stop), "Dimensions must match"
        raw_shape = np.multiply(roi.stop - roi.start, factors)
        raw_start = np.multiply(roi.start, factors) + shift
        raw_stop = raw_start + raw_shape
        return np.array([raw_start, raw_stop])
