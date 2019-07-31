from __future__ import absolute_import
from __future__ import division
from builtins import next
from builtins import object

###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
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
# 		   http://ilastik.org/license/
###############################################################################
import numpy
from lazyflow.request import Request
from lazyflow.utility import RoiRequestBatch
from lazyflow.roi import (
    getIntersectingBlocks,
    getBlockBounds,
    getIntersection,
    determine_optimal_request_blockshape,
    determineBlockShape,
)

import logging
import warnings
from .memory import Memory

logger = logging.getLogger(__name__)


class BigRequestStreamer(object):
    """
    Execute a big request by breaking it up into smaller requests.

    This class encapsulates the logic for dividing big rois into smaller ones to be executed separately.
    It relies on a :py:class:`RoiRequestBatch<lazyflow.utility.roiRequestBatch.RoiRequestBatch>` object,
    which is responsible for creating and scheduling the request for each roi.

    Example:

    >>> import sys
    >>> import vigra
    >>> from lazyflow.graph import Graph
    >>> from lazyflow.operators import OpBlockedArrayCache

    >>> # Example data
    >>> data = numpy.indices( (100,100) ).sum(0)
    >>> data = vigra.taggedView( data, vigra.defaultAxistags('xy') )

    >>> op = OpBlockedArrayCache( graph=Graph() )
    >>> op.Input.setValue( data )

    >>> total_roi = [(25, 65), (45, 95)]

    >>> # Init with our output slot and roi to request.
    >>> # batchSize indicates the number of requests to spawn in parallel.
    >>> streamer = BigRequestStreamer( op.Output, total_roi, (10,10), batchSize=2, blockAlignment='relative' )

    >>> # Use a callback to handle sub-results one at a time.
    >>> result_count = [0]
    >>> result_total_sum = [0]
    >>> def handle_block_result(roi, result):
    ...     # No need for locking here if allowParallelResults=True.
    ...     result_count[0] += 1
    ...     result_total_sum[0] += result.sum()
    >>> streamer.resultSignal.subscribe( handle_block_result )

    >>> # Optional: Subscribe to progress updates
    >>> def handle_progress(progress):
    ...     if progress == 0:
    ...         sys.stdout.write("Progress:")
    ...     sys.stdout.write(f" {progress}")
    >>> streamer.progressSignal.subscribe( handle_progress )

    >>> # Execute the batch of requests, and block for the result.
    >>> streamer.execute()
    Progress: 0 16 33 50 66 83 100 100
    >>> print(f"Processed {result_count[0]} result blocks with a total sum of: {result_total_sum[0]}")
    Processed 6 result blocks with a total sum of: 68400
    """

    def __init__(
        self, outputSlot, roi, blockshape=None, batchSize=None, blockAlignment="absolute", allowParallelResults=False
    ):
        """
        Constructor.

        :param outputSlot: The slot to request data from.
        :param roi: The roi `(start, stop)` of interest.  Will be broken up and requested via smaller requests.
        :param blockshape: The amount of data to request in each request. If omitted, a default blockshape is chosen by inspecting the metadata of the given slot.
        :param batchSize: The maximum number of requests to launch in parallel.  This should not be necessary if the blockshape is small enough that you won't run out of RAM.
        :param blockAlignment: Determines how block the requests. Choices are 'absolute' or 'relative'.
        :param allowParallelResults: If False, The resultSignal will not be called in parallel.
                                     In that case, your handler function has no need for locks.
        """
        self._outputSlot = outputSlot
        self._bigRoi = roi
        self._num_threads = max(1, Request.global_thread_pool.num_workers)

        totalVolume = numpy.prod(numpy.subtract(roi[1], roi[0]))

        if batchSize is None:
            batchSize = self._num_threads

        if blockshape is None:
            blockshape = self._determine_blockshape(outputSlot)

        assert blockAlignment in ["relative", "absolute"]
        if blockAlignment == "relative":
            # Align the blocking with the start of the roi
            offsetRoi = ([0] * len(roi[0]), numpy.subtract(roi[1], roi[0]))
            block_starts = getIntersectingBlocks(blockshape, offsetRoi)
            block_starts += roi[0]  # Un-offset

            # For now, simply iterate over the min blocks
            # TODO: Auto-dialate block sizes based on CPU/RAM usage.
            def roiGen():
                block_iter = block_starts.__iter__()
                while True:
                    try:
                        block_start = next(block_iter)
                    except StopIteration:
                        # As of Python 3.7, not allowed to let StopIteration exceptions escape a generator
                        # https://www.python.org/dev/peps/pep-0479
                        break
                    else:
                        # Use offset blocking
                        offset_block_start = block_start - self._bigRoi[0]
                        offset_data_shape = numpy.subtract(self._bigRoi[1], self._bigRoi[0])
                        offset_block_bounds = getBlockBounds(offset_data_shape, blockshape, offset_block_start)

                        # Un-offset
                        block_bounds = (
                            offset_block_bounds[0] + self._bigRoi[0],
                            offset_block_bounds[1] + self._bigRoi[0],
                        )
                        logger.debug("Requesting Roi: {}".format(block_bounds))
                        yield block_bounds

        else:
            # Absolute blocking.
            # Blocks are simply relative to (0,0,0,...)
            # But we still clip the requests to the overall roi bounds.
            block_starts = getIntersectingBlocks(blockshape, roi)

            def roiGen():
                block_iter = block_starts.__iter__()
                while True:
                    try:
                        block_start = next(block_iter)
                    except StopIteration:
                        # As of Python 3.7, not allowed to let StopIteration exceptions escape a generator
                        # https://www.python.org/dev/peps/pep-0479
                        break
                    else:
                        block_bounds = getBlockBounds(outputSlot.meta.shape, blockshape, block_start)
                        block_intersecting_portion = getIntersection(block_bounds, roi)

                        logger.debug("Requesting Roi: {}".format(block_bounds))
                        yield block_intersecting_portion

        self._requestBatch = RoiRequestBatch(self._outputSlot, roiGen(), totalVolume, batchSize, allowParallelResults)

    def _determine_blockshape(self, outputSlot):
        """
        Choose a blockshape using the slot metadata (if available) or an arbitrary guess otherwise.
        """
        input_shape = outputSlot.meta.shape
        ideal_blockshape = outputSlot.meta.ideal_blockshape
        ram_usage_per_requested_pixel = outputSlot.meta.ram_usage_per_requested_pixel
        max_blockshape = outputSlot.meta.max_blockshape or input_shape

        num_channels = 1
        tagged_shape = outputSlot.meta.getTaggedShape()

        available_ram = Memory.getAvailableRamComputation()

        # Generally, we don't want to split requests across channels.
        if "c" in list(tagged_shape.keys()):
            num_channels = tagged_shape["c"]
            channel_index = list(tagged_shape.keys()).index("c")
            input_shape = input_shape[:channel_index] + input_shape[channel_index + 1 :]
            max_blockshape = max_blockshape[:channel_index] + max_blockshape[channel_index + 1 :]
            if ideal_blockshape:
                # Never enlarge 'ideal' in the channel dimension.
                num_channels = ideal_blockshape[channel_index]
                ideal_blockshape = ideal_blockshape[:channel_index] + ideal_blockshape[channel_index + 1 :]
            del tagged_shape["c"]

        # Generally, we don't want to join time slices
        if "t" in tagged_shape.keys():
            blockshape_time_steps = 1
            time_index = list(tagged_shape.keys()).index("t")
            input_shape = input_shape[:time_index] + input_shape[time_index + 1 :]
            max_blockshape = max_blockshape[:time_index] + max_blockshape[time_index + 1 :]
            if ideal_blockshape:
                # Never enlarge 'ideal' in the time dimension.
                blockshape_time_steps = ideal_blockshape[time_index]
                ideal_blockshape = ideal_blockshape[:time_index] + ideal_blockshape[time_index + 1 :]
                available_ram /= blockshape_time_steps
            del tagged_shape["t"]

        if ram_usage_per_requested_pixel is None:
            # Make a conservative guess: 2*(bytes for dtype) * (num channels) + (fudge factor=4)
            ram_usage_per_requested_pixel = 2 * outputSlot.meta.dtype().nbytes * num_channels + 4
            warnings.warn("Unknown per-pixel RAM requirement.  Making a guess.")

        # Safety factor (fudge factor): Double the estimated RAM usage per pixel
        safety_factor = 2.0
        logger.info(
            "Estimated RAM usage per pixel is {} * safety factor ({})".format(
                Memory.format(ram_usage_per_requested_pixel), safety_factor
            )
        )
        ram_usage_per_requested_pixel *= safety_factor

        if ideal_blockshape is None:
            blockshape = determineBlockShape(
                input_shape, (available_ram // (self._num_threads * ram_usage_per_requested_pixel))
            )
            blockshape = tuple(numpy.minimum(max_blockshape, blockshape))
            warnings.warn("Chose an arbitrary request blockshape")
        else:
            logger.info(
                "determining blockshape assuming available_ram is {}"
                ", split between {} threads".format(Memory.format(available_ram), self._num_threads)
            )

            # By convention, ram_usage_per_requested_pixel refers to the ram used when requesting ALL channels of a 'pixel'
            # Therefore, we do not include the channel dimension in the blockshapes here.
            #
            # Also, it rarely makes sense to request more than one time slice, so we omit that, too. (See above.)
            blockshape = determine_optimal_request_blockshape(
                max_blockshape, ideal_blockshape, ram_usage_per_requested_pixel, self._num_threads, available_ram
            )

        # If we removed time and channel from consideration, add them back now before returning
        if "t" in outputSlot.meta.getAxisKeys():
            blockshape = blockshape[:time_index] + (blockshape_time_steps,) + blockshape[time_index:]

        if "c" in outputSlot.meta.getAxisKeys():
            blockshape = blockshape[:channel_index] + (num_channels,) + blockshape[channel_index:]

        logger.info("Chose blockshape: {}".format(blockshape))
        fmt = Memory.format(ram_usage_per_requested_pixel * numpy.prod(blockshape[:-1]))
        logger.info("Estimated RAM usage per block is {}".format(fmt))

        return blockshape

    @property
    def resultSignal(self):
        """
        Results signal. Signature: ``f(roi, result)``.
        Guaranteed not to be called from multiple threads in parallel.
        """
        return self._requestBatch.resultSignal

    @property
    def progressSignal(self):
        """
        Progress Signal Signature: ``f(progress_percent)``
        """
        return self._requestBatch.progressSignal

    def execute(self):
        """
        Request the data for the entire roi by breaking it up into many smaller requests,
        and wait for all of them to complete.
        A batch of N requests is launched, and subsequent requests are
        launched one-by-one as the earlier requests complete.  Thus, there
        will be N requests executing in parallel at all times.

        This method returns ``None``.  All results must be handled via the
        :py:obj:`resultSignal`.
        """
        self._requestBatch.execute()


if __name__ == "__main__":
    import doctest

    doctest.testmod()
