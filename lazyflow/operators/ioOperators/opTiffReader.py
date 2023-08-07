###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2023, the ilastik developers
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
#          http://ilastik.org/license.html
###############################################################################
from collections import defaultdict
import logging

import numpy
import tifffile
import vigra

from lazyflow.graph import InputSlot, Operator, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.utility.helpers import get_default_axisordering

logger = logging.getLogger(__name__)


class UnsupportedTiffError(Exception):
    def __init__(self, filepath, details):
        super().__init__(f"Unable to open TIFF file: {filepath}. {details}")


class OpTiffReader(Operator):
    """
    Reads TIFF files as an ND array. We use two different libraries:

    - To read the image metadata (determine axis order), we use tifffile.py (by Christoph Gohlke)

    Note: This operator intentionally ignores any colormap
          information and uses only the raw stored pixel values.
          (In fact, avoiding the colormapping is not trivial using the tifffile implementation.)

    TODO: Add an option to output color-mapped pixels.
    """

    Filepath = InputSlot()
    Output = OutputSlot()

    TIFF_EXTS = [".tif", ".tiff"]

    def __init__(self, *args, **kwargs):
        super(OpTiffReader, self).__init__(*args, **kwargs)
        self._filepath = None
        self._page_shape = None
        self._non_page_shape = None

    def setupOutputs(self):
        self._filepath = self.Filepath.value
        with tifffile.TiffFile(self._filepath, mode="r") as tiff_file:
            series = tiff_file.series[0]
            if len(tiff_file.series) > 1:
                raise UnsupportedTiffError(
                    filepath=self._filepath,
                    details=f"Don't know how to read TIFF files with more than one image series (Your image has {len(tiff_file.series)} series",
                )

            axes = series.axes.lower()
            shape = series.shape
            dtype_code = series.dtype

            # we treat "sample" axis as "channel"
            # "i" ("sequence") can either be "time", "z", or "channel", in that order.
            for old, new in ("sc", "it", "iz", "ic"):
                axes = axes.replace(old, new)

            # tifffile will add potentially multiple "q" axes to data when saving without specifying them
            if "q" in axes:
                axes = get_default_axisordering(shape)

            axes_set = set(axes)
            if len(shape) < 2 or len(shape) > 5 or len(axes_set) != len(axes) or axes_set.difference("tzyxc"):
                raise UnsupportedTiffError(
                    filepath=self._filepath,
                    details=f"Only 2D-5D TIFFs with unique 'tzyxc' axes are allowed (got {len(shape)}D TIFF with {axes} axes)",
                )

            self._page_axes = series.pages[0].axes.lower()
            self._page_shape = series.pages[0].shape

            self._non_page_shape = shape[: -len(self._page_shape)]

        self.Output.meta.shape = shape
        self.Output.meta.axistags = vigra.defaultAxistags(axes)
        self.Output.meta.dtype = numpy.dtype(dtype_code).type

        blockshape = defaultdict(lambda: 1, zip(self._page_axes, self._page_shape))
        # optimization: reading bigger blockshapes in z means much smoother user experience
        # but don't change z if it's part of the page shape
        blockshape.setdefault("z", 32)
        self.Output.meta.ideal_blockshape = tuple(blockshape[k] for k in axes)

    def execute(self, slot, subindex, roi, result):
        """
        Use tifffile to read the result.
        This allows us to support JPEG-compressed TIFFs.
        """
        num_page_axes = len(self._page_shape)
        roi = numpy.array([roi.start, roi.stop])
        # page axes are assumed to be last in roi
        page_index_roi = roi[:, :-num_page_axes]
        roi_within_page = roi[:, -num_page_axes:]

        logger.debug("Roi: {}".format(list(map(tuple, roi))))

        # Read each page out individually
        page_index_roi_shape = page_index_roi[1] - page_index_roi[0]

        with tifffile.TiffFile(self._filepath, mode="r") as f:
            for roi_page_ndindex in numpy.ndindex(*page_index_roi_shape):
                key = None
                if self._non_page_shape:
                    tiff_page_ndindex = page_index_roi[0] + roi_page_ndindex
                    key = int(numpy.ravel_multi_index(tiff_page_ndindex, self._non_page_shape))
                    logger.debug(...)

                page_data = f.series[0].asarray(key=key, maxworkers=1)

                assert page_data.shape == self._page_shape, "Unexpected page shape: {} vs {}".format(
                    page_data.shape, self._page_shape
                )

                result[roi_page_ndindex] = page_data[roiToSlice(*roi_within_page)]

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Filepath:
            self.Output.setDirty(slice(None))
