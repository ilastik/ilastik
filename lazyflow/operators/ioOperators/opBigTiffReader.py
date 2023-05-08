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
import tifffile
import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice

import logging

logger = logging.getLogger(__name__)


class OpBigTiffReader(Operator):
    Filepath = InputSlot()
    Output = OutputSlot()

    TIFF_EXTS = [".tif", ".tiff"]

    class BigTiffError(Exception):
        pass

    class NotBigTiffError(BigTiffError):
        """Raised if the file you're attempting to open isn't a BigTiff file."""

    class UnsupportedBigTiffError(BigTiffError):
        """File is recognized as bigtiff, but we don't know how to handle it."""

    def __init__(self, *args, **kwargs):
        super(OpBigTiffReader, self).__init__(*args, **kwargs)
        self._bigtiff = None

    def cleanUp(self):
        # currently the only way to close the memmap
        del self._bigtiff
        super(OpBigTiffReader, self).cleanUp()

    def setupOutputs(self):
        filepath: str = self.Filepath.value

        with tifffile.TiffFile(filepath) as f:
            if not f.is_bigtiff:
                raise OpBigTiffReader.NotBigTiffError(f"File {filepath} is not a BigTiff file.")

            if f.pages.is_multipage:
                raise OpBigTiffReader.UnsupportedBigTiffError(
                    f"File {filepath} is multipage! Multipage BigTiff not supported yet."
                )

            if len(f.series) != 1:
                raise OpBigTiffReader.UnsupportedBigTiffError(
                    f"File {filepath} has {len(f.series)} series! Multiple Series BigTiff not supported yet."
                )

            bigtiff_axes = f.series[0].axes
            if any(ax not in "cyx" for ax in bigtiff_axes.lower()):
                OpBigTiffReader.UnsupportedBigTiffError(f"File {filepath} has unrecognized axistags {bigtiff_axes}.")

        bigtiff = tifffile.memmap(filepath)
        try:
            self.Output.meta.dtype = bigtiff.dtype
            assert len(bigtiff.shape) == len(bigtiff_axes)
            self.Output.meta.axistags = vigra.defaultAxistags(bigtiff_axes.lower())
            self.Output.meta.shape = bigtiff.shape

        except Exception as e:
            del bigtiff
            raise e

        self._bigtiff = bigtiff

    def execute(self, slot, subindex, roi, result):
        result[:] = self._bigtiff[roiToSlice(roi.start, roi.stop)]

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Filepath:
            self.Output.setDirty(slice(None))
