import numpy as np
import tifffile
import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice

import logging

logger = logging.getLogger(__name__)


def is_bigtiff(filepath: str) -> bool:
    with tifffile.TiffFile(filepath, mode="r") as f:
        return f.is_bigtiff


class OpBigTiffReader(Operator):
    Filepath = InputSlot()
    Output = OutputSlot()

    TIFF_EXTS = [".tif", ".tiff"]

    class BigTiffError(Exception):
        pass

    class NotBigTiffError(BigTiffError):
        """Raised if the file you're attempting to open isn't a BigTiff file."""

    class BigTiffMultiPageError(BigTiffError):
        """Attemting to load a big tiff with multiple pages, not supported"""

    class BigTiffMultiSeriesError(BigTiffError):
        """Attemting to load a big tiff with multiple series, not supported"""

    class BigTiffAxistagsError(BigTiffError):
        """Attemting to load a big tiff with unsupported axistags"""

    def __init__(self, *args, **kwargs):
        super(OpBigTiffReader, self).__init__(*args, **kwargs)

    def cleanUp(self):
        super(OpBigTiffReader, self).cleanUp()

    def setupOutputs(self):
        filepath = self.Filepath.value

        with tifffile.TiffFile(filepath) as f:
            if not f.is_bigtiff:
                raise OpBigTiffReader.NotBigTiffError(filepath)

            if f.pages.is_multipage:
                raise BigTiffMultiPageError("Multipage BigTiff not supported yet.")

            if len(f.series) != 1:
                raise BigTiffMultiSeriesError("Miltiple Series BigTiff not supported yet.")

            bigtiff_axes = f.series[0].axes
            if any(ax not in "cyx" for ax in bigtiff_axes.lower()):
                BigTiffAxistagsError(f"Unrecognized axistags in bigtiff file. Got {bigtiff_axes}.")

        bigtiff = tifffile.memmap(filepath)

        self.Output.meta.dtype = bigtiff.dtype

        assert len(bigtiff.shape) == len(bigtiff_axes)
        self.Output.meta.axistags = vigra.defaultAxistags(bigtiff_axes.lower())
        self.Output.meta.shape = bigtiff.shape

        self._bigtiff = bigtiff

    def execute(self, slot, subindex, roi, result):
        result[:] = self._bigtiff[roiToSlice(roi.start, roi.stop)]

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Filepath:
            self.Output.setDirty(slice(None))


#
# Quick test
#
if __name__ == "__main__":
    from lazyflow.graph import Graph

    op = OpBigTiffReader(graph=Graph())
    # op.Filepath.setValue('/magnetic/workspace/pytiff/test_data/rgb_sample.tif')
    op.Filepath.setValue("/magnetic/workspace/pytiff/test_data/bigtif_example.tif")

    print(op.Output.meta.shape)
    print(op.Output.meta.dtype)
    print(op.Output.meta.getAxisKeys())
    print(op.Output[:10, :10].wait())
