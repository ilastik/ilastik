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
import logging
import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import Dict, Union

import numpy
import tifffile
import xml.etree.ElementTree as ET
import vigra

from lazyflow.graph import InputSlot, Operator, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.utility.helpers import get_default_axisordering
from lazyflow.utility.resolution import UnitAxisInfo, UnitAxisTags

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

    """ We want to implement this in workflows, not here.
    def checkUnits(self, metadata):
        for unit in range(len(metadata["units"].split(","))):
            if metadata["axes"].split(",")[unit].lower() == "channel":
                continue
            if metadata["units"].split(",")[unit].lower() not in ["km", "m", "cm", "mm", "μm", "nm", "pm", "sec"]:
                return False
        return True
    """

    def make_axistags(self, axiskeys: str, ij_meta, ome_meta):
        if not ij_meta and not ome_meta:
            return vigra.defaultAxistags(axiskeys)

        axisinfos: Dict[str, Union[UnitAxisInfo, vigra.AxisInfo]] = {}
        with tifffile.TiffFile(self._filepath, mode="r") as f:
            if ij_meta:
                meta = f.pages[0].tags

                # TIFF format stores resolution values as Rational tuples (numerator, denominator)
                if "unit" in ij_meta.keys():

                    res = self.get_tiff_res(meta.get("XResolution", (0, 0)))
                    x_unit = ij_meta.get("unit", "")
                    axisinfos["x"] = UnitAxisInfo(
                        key="x",
                        typeFlags=vigra.AxisType.Space,
                        resolution=res,
                        description="",
                        unit=self.decode_non_ascii(x_unit) if x_unit else "",
                    )

                    res = self.get_tiff_res(meta.get("YResolution", (0, 0)))
                    y_unit = ij_meta.get("yunit", "")
                    axisinfos["y"] = UnitAxisInfo(
                        key="y",
                        typeFlags=vigra.AxisType.Space,
                        resolution=res,
                        description="",
                        unit=self.decode_non_ascii(y_unit) if y_unit else "",
                    )
                    if "z" in axiskeys:
                        res = ij_meta.get("spacing", 0)
                        z_unit = ij_meta.get("zunit", "")
                        axisinfos["z"] = UnitAxisInfo(
                            key="z",
                            typeFlags=vigra.AxisType.Space,
                            resolution=res,
                            description="",
                            unit=self.decode_non_ascii(z_unit) if z_unit else "",
                        )

                    if "t" in axiskeys:
                        res = ij_meta.get("finterval", 0)
                        t_unit = ij_meta.get("tunit", "")
                        axisinfos["t"] = UnitAxisInfo(
                            key="t",
                            typeFlags=vigra.AxisType.Time,
                            resolution=res,
                            description="",
                            unit=self.decode_non_ascii(t_unit) if t_unit else "",
                        )

                    if "c" in axiskeys:
                        axisinfos["c"] = UnitAxisInfo(
                            key="c", typeFlags=vigra.AxisType.Channels, resolution=0.0, description="", unit=None
                        )

            # Look for OME-TIFF metadata (possible in FIJI hyperstacks)
            else:
                xml = ET.fromstring(ome_meta)
                ns = {"ome": "http://www.openmicroscopy.org/Schemas/OME/2016-06"}
                image = xml.find("ome:Image", ns)
                pixels = image.find("ome:Pixels", ns)
                if pixels:
                    size_trans_0 = {"x": "PhysicalSizeX", "y": "PhysicalSizeY"}
                    size_trans_1 = {"z": "PhysicalSizeZ", "t": "TimeIncrement"}
                    unit_trans_0 = {
                        "x": "PhysicalSizeXUnit",
                        "y": "PhysicalSizeYUnit",
                        "z": "PhysicalSizeZUnit",
                        "t": "TimeIncrementUnit",
                    }

                    for axis in axiskeys:
                        if axis.lower() == "c":
                            axisinfos[axis] = UnitAxisInfo(
                                key=axis, typeFlags=vigra.AxisType.Channels, resolution=0, description="", unit=""
                            )
                        if axis.lower() in size_trans_0.keys():
                            unit_value = pixels.attrib.get(unit_trans_0[axis], "")
                            default_unit = ""
                            axisinfos[axis] = UnitAxisInfo(
                                key=axis,
                                typeFlags=vigra.AxisType.Space,
                                resolution=float(pixels.attrib.get(size_trans_0[axis], 0)),
                                description="",
                                unit=self.decode_non_ascii(unit_value) if unit_value else default_unit,
                            )
                        else:
                            if axis.lower() == "t":
                                unit_value = pixels.attrib.get(unit_trans_0[axis], "")
                                axisinfos[axis] = UnitAxisInfo(
                                    key=axis,
                                    typeFlags=vigra.AxisType.Time,
                                    resolution=float(pixels.attrib.get(size_trans_1[axis], 0)),
                                    description="",
                                    unit=self.decode_non_ascii(unit_value) if unit_value else "",
                                )
                            if axis.lower() == "z":
                                unit_value = pixels.attrib.get(unit_trans_0[axis], "")
                                axisinfos[axis] = UnitAxisInfo(
                                    key=axis,
                                    typeFlags=vigra.AxisType.Space,
                                    resolution=float(pixels.attrib.get(size_trans_1[axis], 0)),
                                    description="",
                                    unit=self.decode_non_ascii(unit_value) if unit_value else "",
                                )
            return UnitAxisTags([axisinfos[key] for key in axiskeys])

    def decode_non_ascii(self, raw_string: str):
        return raw_string.encode("utf-8").decode("unicode_escape").encode("utf-16", "surrogatepass").decode("utf-16")

    def get_tiff_res(self, frac):
        if frac.value[0] != 0:
            resolution = frac.value[1] / frac.value[0]
            if abs(resolution - round(resolution)) < 0.001:
                resolution = round(resolution)
            return resolution
        return 0

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
        self.Output.meta.axistags = self.make_axistags(axes, ij_meta, ome_meta)
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
