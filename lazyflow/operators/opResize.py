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
from skimage import transform as sk_transform

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import enlargeRoiForHalo, roiToSlice
from lazyflow.rtype import SubRegion

logger = logging.getLogger(__name__)


class OpResize(Operator):
    """
    Presents scikit-image.transform.resize as a lazyflow operator,
    handling in particular the halo for antialiasing in the context of subregions.

    Resizes input image to desired output size.
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
        of raw image for antialiasing. Then resize that raw image with halo. Then crop
        the scaled halo."""
        assert slot is self.ResizedImage, "Unknown output slot"
        downsampling_factors = self._get_scaling_factors()
        assert all(f >= 1 for f in downsampling_factors), "Upsampling not supported yet"
        # @haesleinhuepf sigmas for antialiasing (cf BioImageAnalysisNotebooks downscaling and denoising).
        # skimage.transform.resize does np.maximum(0, (downsampling_factors - 1) / 2) instead,
        # but this seems to cause bigger artifacts at block boundaries.
        antialiasing_sigmas = tuple(f / 4 for f in downsampling_factors)
        axes_to_pad = downsampling_factors > 1
        raw_roi = self._reverse_roi_scaling(roi, downsampling_factors)
        raw_roi_with_halo, raw_result_roi = enlargeRoiForHalo(
            raw_roi[0],
            raw_roi[1],
            self.RawImage.meta.shape,
            sigma=antialiasing_sigmas,
            enlarge_axes=axes_to_pad,
            return_result_roi=True,
        )
        raw_image_with_halo = self.RawImage[roiToSlice(*raw_roi_with_halo)].wait()
        scaled_roi_with_halo = self._scale_roi(raw_roi_with_halo, downsampling_factors)
        scaled_image = sk_transform.resize(
            raw_image_with_halo,
            scaled_roi_with_halo[1] - scaled_roi_with_halo[0],
            anti_aliasing=True,
            anti_aliasing_sigma=antialiasing_sigmas,
            preserve_range=True,
        )
        scaled_result_roi = self._scale_roi(raw_result_roi, downsampling_factors)
        assert np.all(
            scaled_result_roi[1] - scaled_result_roi[0] == roi.stop - roi.start
        ), "Scaled image shape does not match requested shape"
        result[...] = scaled_image[roiToSlice(*scaled_result_roi)]

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
