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
        self.msg = f"Unable to open TIFF file: {filepath}. {details}"
        super().__init__(self.msg)


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
            axes = axes.replace("s", "c")
            if "i" in axes:
                for k in "tzc":
                    if k not in axes:
                        axes = axes.replace("i", k)
                        break
                if "i" in axes:
                    raise UnsupportedTiffError(
                        filepath=self._filepath,
                        details=f"Image has an 'I' axis, and I don't know what it represents (separate T,Z,C axes already exist): {axes}",
                    )

            # tifffile will add potentially multiple "q" axes to data when saving without specifying them
            if "q" in axes:
                axes = get_default_axisordering(shape)

            if any(ax not in "tzyxc" for ax in axes) or len(shape) > 5:
                raise UnsupportedTiffError(
                    filepath=self._filepath,
                    details=f"Don't know how to read TIFF files with more than 5 dimensions (Your image has {len(shape)} dimensions). Axes: {axes}.",
                )

            self._page_axes = tiff_file.series[0].pages[0].axes.lower()
            self._page_shape = tiff_file.series[0].pages[0].shape

            self._non_page_shape = shape[: -len(self._page_shape)]

        self.Output.meta.shape = shape
        self.Output.meta.axistags = vigra.defaultAxistags(axes)
        self.Output.meta.dtype = numpy.dtype(dtype_code).type
        self.Output.meta.ideal_blockshape = (1,) * len(self._non_page_shape) + self._page_shape

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
        for roi_page_ndindex in numpy.ndindex(*page_index_roi_shape):
            if self._non_page_shape:
                tiff_page_ndindex = roi_page_ndindex + page_index_roi[0]
                tiff_page_list_index = numpy.ravel_multi_index(tiff_page_ndindex, self._non_page_shape)
                logger.debug("Reading page: {} = {}".format(tuple(tiff_page_ndindex), tiff_page_list_index))
                with tifffile.TiffFile(self._filepath, mode="r") as f:
                    page_data = f.series[0].asarray(key=int(tiff_page_list_index), maxworkers=1)
            else:
                # Only a single page
                with tifffile.TiffFile(self._filepath, mode="r") as f:
                    page_data = f.series[0].asarray(maxworkers=1)

            assert page_data.shape == self._page_shape, "Unexpected page shape: {} vs {}".format(
                page_data.shape, self._page_shape
            )

            result[roi_page_ndindex] = page_data[roiToSlice(*roi_within_page)]

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Filepath:
            self.Output.setDirty(slice(None))


if __name__ == "__main__":
    from lazyflow.graph import Graph

    graph = Graph()
    opReader = OpTiffReader(graph=graph)
    opReader.Filepath.setValue("/groups/flyem/home/bergs/Downloads/Tiff_t4_HOM3_10frames_4slices_28sec.tif")
    print(opReader.Output.meta.axistags)
    print(opReader.Output.meta.shape)
    print(opReader.Output.meta.dtype)
    print(opReader.Output[2:3, 2:3, 2:3, 10:20, 20:50].wait().shape)

#     opReader.Filepath.setValue('/magnetic/data/synapse_small.tiff')
#     print opReader.Output.meta.axistags
#     print opReader.Output.meta.shape
#     print opReader.Output.meta.dtype
