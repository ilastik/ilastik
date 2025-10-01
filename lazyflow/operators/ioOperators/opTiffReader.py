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
import xml.etree.ElementTree as ET
import tifffile
import vigra

from lazyflow.graph import InputSlot, Operator, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.utility.helpers import get_default_axisordering
from lazyflow.utility.io_util import tiff_encoding

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
            ij_meta = tiff_file.imagej_metadata
            ome_meta = tiff_file.ome_metadata
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

        self.Output.meta.axis_units = {key: "" for key in axes}

        if ij_meta or ome_meta:
            self.setPixelSizes(axes, ij_meta, ome_meta)

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

    def setPixelSizes(self, axes, ij_meta, ome_meta):
        with tifffile.TiffFile(self._filepath, mode="r") as f:
            if ome_meta:
                xml = ET.fromstring(ome_meta)
                ns = {"ome": "http://www.openmicroscopy.org/Schemas/OME/2016-06"}
                image = xml.find("ome:Image", ns)
                pixels = image.find("ome:Pixels", ns)
                if pixels:
                    size_keys = {"x": "PhysicalSizeX", "y": "PhysicalSizeY", "z": "PhysicalSizeZ", "t": "TimeIncrement"}
                    unit_keys = {
                        "x": "PhysicalSizeXUnit",
                        "y": "PhysicalSizeYUnit",
                        "z": "PhysicalSizeZUnit",
                        "t": "TimeIncrementUnit",
                    }

                    for axis in axes:
                        if axis.lower() == "c":
                            continue
                        else:
                            self.Output.meta.axistags.setResolution(
                                axis.lower(), float(pixels.attrib.get(size_keys[axis], 0))
                            )
                            self.Output.meta.axis_units[axis.lower()] = pixels.attrib.get(
                                unit_keys[axis], ""
                            )  # OME uses unicode
            else:
                meta = f.pages[0].tags
                resolution_keys = {"x": "XResolution", "y": "YResolution", "z": "spacing", "t": "finterval"}
                unit_keys = {"x": "unit", "y": "yunit", "z": "zunit", "t": "tunit"}
                for ax in axes:
                    if ax == "c":
                        continue
                    self.Output.meta.axistags.setResolution(
                        ax,
                        (
                            self.round_resolution_to_tiff_precision(meta.get(resolution_keys[ax], None))
                            if ax in "xy"
                            else ij_meta.get(resolution_keys[ax], 0)
                        ),
                    )
                    # (TIFF format stores resolution values as Rational tuples (numerator, denominator))
                    unit = self.handle_stringified_tuples(ij_meta.get(unit_keys[ax], ""))
                    self.Output.meta.axis_units[ax] = tiff_encoding.from_ascii(unit) if unit else ""

    def round_resolution_to_tiff_precision(self, frac):
        """
        Rounding is employed for axes with resolutions deviating extremely slightly from integer values.
        This is because the TIFF standard introduces floating-point precision errors
        by storing resolutions as numerator/denominator pairs.
        """
        if frac and frac.value[0] != 0:
            resolution = frac.value[1] / frac.value[0]
            if abs(resolution - round(resolution)) < 1e-8:
                resolution = round(resolution)
            return resolution
        return 0

    def handle_stringified_tuples(self, unit):
        """
        Necessary because sometimes FIJI units are stored as 1-item tuples,
        and thus the unit needs to be extracted from the enveloping tuple syntax.
        """
        if isinstance(unit, str) and unit.startswith("('") and unit.endswith("',)"):
            if len(unit) > 5:
                return unit[2:-3]
            return ""
        return unit

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Filepath:
            self.Output.setDirty(slice(None))
