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
from typing import Union, Iterable

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
        of raw image for antialiasing. Then apply the gaussian filter for antialiasing,
        remove the halo, and scale the blurred image."""
        assert slot is self.ResizedImage, "Unknown output slot"
        downscaling_factors = self._get_scaling_factors()
        assert all(f >= 1 for f in downscaling_factors), "Upscaling not supported yet"
        antialiasing_sigmas = np.array([f / 4 for f in downscaling_factors])
        axes_to_pad = downscaling_factors > 1
        raw_roi = self._reverse_roi_scaling(roi, downscaling_factors)
        raw_roi_with_halo, raw_result_roi = enlargeRoiForHalo(
            raw_roi[0],
            raw_roi[1],
            self.RawImage.meta.shape,
            sigma=antialiasing_sigmas,
            enlarge_axes=axes_to_pad,
            return_result_roi=True,
        )
        raw_image_with_halo = self.RawImage[roiToSlice(*raw_roi_with_halo)].wait().astype(np.float64)
        filtered_with_halo = scipy_ndimage.gaussian_filter(raw_image_with_halo, antialiasing_sigmas, mode="mirror")
        filtered = filtered_with_halo[roiToSlice(*raw_result_roi)]
        zoom_factors = [1 / f for f in downscaling_factors]
        scaled_image = scipy_ndimage.zoom(filtered, zoom_factors, grid_mode=True, mode="mirror", order=1)
        result[...] = scaled_image

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

    @staticmethod
    def _scale_roi(roi: Union[np.typing.NDArray, SubRegion], factors: Iterable[float]) -> np.typing.NDArray:
        """
        Returns roi as numpy.ndarray[start, stop] instead of SubRegion to be independent of slot.
        np.round matches behavior of skimage.transform.resize when rounding resized image shape.
        """
        start = roi.start if isinstance(roi, SubRegion) else roi[0]
        stop = roi.stop if isinstance(roi, SubRegion) else roi[1]
        scaled_shape = np.round(np.divide(stop - start, factors)).astype(int)
        scaled_start = np.round(np.divide(start, factors)).astype(int)
        scaled_stop = scaled_start + scaled_shape
        return np.array([scaled_start, scaled_stop])

    @staticmethod
    def _reverse_roi_scaling(roi: SubRegion, factors: Iterable[float]) -> np.typing.NDArray:
        """
        Returns roi as numpy.ndarray[start, stop] instead of SubRegion to be independent of slot.
        np.round matches behavior of skimage.transform.resize when rounding resized image shape.
        """
        raw_shape = np.round(np.multiply(roi.stop - roi.start, factors)).astype(int)
        raw_start = np.round(np.multiply(roi.start, factors)).astype(int)
        raw_stop = raw_start + raw_shape
        return np.array([raw_start, raw_stop])
