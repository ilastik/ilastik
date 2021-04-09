###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2017, the ilastik developers
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
import os
import copy
import tempfile
import h5py
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility.io_util.RESTfulPrecomputedChunkedVolume import RESTfulPrecomputedChunkedVolume
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
import lazyflow.roi
from lazyflow.utility.helpers import bigintprod
import logging

import numpy

logger = logging.getLogger(__name__)


class OpRESTfulPrecomputedChunkedVolumeReaderNoCache(Operator):
    """
    An operator to retrieve precomputed chunked volumes from a remote server.
    These types of volumes are e.g. used in neuroglancer.
    """

    name = "OpRESTfulPrecomputedChunkedVolumeReader"

    # Base url of the chunked volume
    BaseUrl = InputSlot()

    # There is also the scale to configure
    Scale = InputSlot(optional=True)

    # Available scales of the data
    AvailableScales = OutputSlot()
    # The data itself
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._axes = None
        self._volume_object = None

    def setupOutputs(self):
        # Create a RESTfulPrecomputedChunkedVolume object to handle
        if self._volume_object is not None:
            # check if the volume url has changed, to avoid downloading
            # info twice (i.e. setting up the volume twice)
            if self._volume_object.volume_url == self.BaseUrl.value:
                return

        self._volume_object = RESTfulPrecomputedChunkedVolume(self.BaseUrl.value)

        self._axes = self._volume_object.axes

        self.AvailableScales.setValue(self._volume_object.available_scales)
        output_shape = tuple(self._volume_object.get_shape(scale=self._volume_object._use_scale))
        self.Output.meta.shape = output_shape
        self.Output.meta.dtype = numpy.dtype(self._volume_object.dtype).type
        self.Output.meta.axistags = vigra.defaultAxistags(self._axes)

        # scale needs to be defined for the following, so:
        # override whatever was set before to the lowest available scale:
        # is this a good idea? Triggers setupOutputs again
        self.Scale.setValue(self._volume_object._use_scale)

    @staticmethod
    def get_intersecting_blocks(blockshape, roi, shape):
        """Find block indices for given roi

        Wraps around lazyflow.roi.getIntersectingBlocks
        Idea is that only the required blocks are allocated using

        Everything in 'czyx' - order

        Args:
            blockshape (iterable): block shape
            roi (tuple): (start, stop), inclusive start of block, exclusive end

        Difference is that it returns a dictionary consisting of
          * 'array_of_blocks' the array of blocks
          * 'subimage_shape' shape of the subimage
          * 'block_offsets' array of offset for each of the blocks
          * 'subimage_roi' the roi in the sub_image
        """
        blocks = lazyflow.roi.getIntersectingBlocks(blockshape, roi, asarray=True)

        num_indexes = bigintprod(blocks.shape[0:-1])
        axiscount = blocks.shape[-1]
        blocks_array = numpy.reshape(blocks, (num_indexes, axiscount))

        block_aligned_subimage_start = blocks_array.min(axis=0)
        block_aligned_subimage_end = blocks_array.max(axis=0)

        assert (block_aligned_subimage_start == blocks_array).all(axis=1).any(), "roi does not seem to be block aligned"
        assert (block_aligned_subimage_end == blocks_array).all(axis=1).any(), "roi does not seem to be block aligned"

        # get the real end of the image:
        block_aligned_subimage_end += blockshape
        # take care of image border
        block_aligned_subimage_end = numpy.min([block_aligned_subimage_end, shape], axis=0)

        subimage_shape = block_aligned_subimage_end - block_aligned_subimage_start
        block_offsets = blocks_array - block_aligned_subimage_start
        subimage_start = roi[0] - block_aligned_subimage_start
        subimage_roi = ((subimage_start), (subimage_start + (roi[1] - roi[0])))

        return blocks_array, block_offsets, subimage_roi, subimage_shape

    def execute(self, slot, subindex, roi, result):
        """
        Args:
            slot (OutputSlot): Requested slot
            subindex (tuple): Subslot index for multi-level slots
            roi (rtype.Roi): we assume czyx order here
            result (ndarray): array in which the results are written in

        """
        start, stop = roi.start, roi.stop
        roi = (start, stop)

        scale = self.Scale.value
        assert len(roi) == 2
        assert all(len(x) == len(self._volume_object.get_shape(scale)) for x in roi)
        block_shape = self._volume_object.get_block_shape(scale)
        image_shape = self._volume_object.get_shape(scale)
        array_of_blocks, block_offsets, subimage_roi, subimage_shape = self.get_intersecting_blocks(
            blockshape=block_shape, roi=roi, shape=image_shape
        )
        subimage = numpy.zeros((subimage_shape))
        assert array_of_blocks.shape[-1] == 4

        for block, offset in zip(array_of_blocks, block_offsets):
            slicing = lazyflow.roi.roiToSlice(offset, offset + block_shape)
            subimage[slicing] = self._volume_object.download_block(block, scale)
        slicing = lazyflow.roi.roiToSlice(subimage_roi[0], subimage_roi[1])
        result[...] = subimage[slicing]
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(slice(None))


class OpRESTfulPrecomputedChunkedVolumeReader(Operator):
    fixAtCurrent = InputSlot(value=False, stype="bool")

    BaseUrl = InputSlot()

    # There is also the scale to configure
    Scale = InputSlot(optional=True)

    # Available scales of the data
    AvailableScales = OutputSlot()
    # The data itself
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.RESTfulReader = OpRESTfulPrecomputedChunkedVolumeReaderNoCache(parent=self)
        self.RESTfulReader.BaseUrl.connect(self.BaseUrl)
        self.AvailableScales.connect(self.RESTfulReader.AvailableScales)
        self.RESTfulReader.Scale.backpropagate_values = True
        self.RESTfulReader.Scale.connect(self.Scale)

        self.cache = OpBlockedArrayCache(parent=self)
        self.cache.name = "input_image_cache"
        self.cache.fixAtCurrent.connect(self.fixAtCurrent)
        self.cache.Input.connect(self.RESTfulReader.Output)
        self.Output.connect(self.cache.Output)

    def setupOutputs(self):
        # TODO: make this generic, for all dimensionalities
        self.cache.BlockShape.setValue((1, 64, 64, 64))

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(slice(None))

    def cleanup(self):
        self.cache.Input.disconnect()


if __name__ == "__main__":
    # assumes there is a server running at localhost
    logging.basicConfig(level=logging.DEBUG)
    volume_url = "http://localhost:8000/cremi"

    from lazyflow import graph

    g = graph.Graph()
    op = OpRESTfulPrecomputedChunkedVolumeReader(graph=g)
    op.BaseUrl.setValue(volume_url)
    print(f"available scales: {op.AvailableScales.value}")
    print(f"Selected scale: {op.Scale.value}")

    # get some data
    roi = ((0, 0, 0, 0), (1, 10, 100, 100))
    data = op.Output(*roi).wait()
    import h5py

    with h5py.File("/tmp/temph5.h5", "w") as f:
        f.create_dataset("exported", data=data)

    # get some data for the second time, check on server that it has only
    # been requested once
    data2 = op.Output(*roi).wait()
