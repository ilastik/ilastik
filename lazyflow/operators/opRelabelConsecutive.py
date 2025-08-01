###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2024, the ilastik developers
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
import collections
import logging
import time
from functools import partial
from typing import Dict, Tuple, Union

import numpy
import numpy.typing as npt
import vigra

from lazyflow.graph import InputSlot, OutputSlot
from lazyflow.operators.generic import OpPixelOperator
from lazyflow.operators.opLabelBase import OpLabelBase
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.operators.opResize import OpResize
from lazyflow.operators.opUnblockedArrayCache import OpUnblockedArrayCache, RoiTuple
from lazyflow.request.request import Request, RequestLock, RequestPool
from lazyflow.roi import getIntersectingRois, roiToSlice
from lazyflow.rtype import SubRegion
from lazyflow.slot import Slot
from lazyflow.utility.helpers import get_ram_per_element

logger = logging.getLogger(__name__)


RoiTuple5D = Tuple[Tuple[int, int, int, int, int], Tuple[int, int, int, int, int]]


class OpRelabelConsecutive(OpLabelBase):
    """
    Operator for relabeling label images in a consecutive manner

    This operator sets up the inputs for OpRelabelConsecutive5D:
    * `BlockShape` is set up in to whole time slices, no spatial subblocks
      for valid relabelings.
    * `dtype` of the `Input` is checked (see `supportedDtypes`) and in case of
      `uint16` changed to `uint32` to comply with vigra requirements. `uint16` is
       what we have seen with cellpose data.
    * `Input` is always reordered to `tzyxc`
    """

    StartLabel = InputSlot(value=1)

    RelabelDict = OutputSlot()

    CompressionEnabled = InputSlot(value=False)

    SerializationInput = InputSlot(optional=True)
    SerializationOutput = OutputSlot()

    supportedDtypes = [numpy.uint8, numpy.uint16, numpy.uint32, numpy.uint64]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._opReorder5D = OpReorderAxes(parent=self, Input=self.Input, AxisOrder="tzyxc")
        self._opDtypeConvert = OpPixelOperator(parent=self, Input=self._opReorder5D.Output, Function=lambda x: x)

        self._opRelabelConsecutive = OpRelabelConsecutive5D(
            parent=self,
            Input=self._opDtypeConvert.Output,
            StartLabel=self.StartLabel,
            CompressionEnabled=self.CompressionEnabled,
            SerializationInput=self.SerializationInput,
        )
        self._opReorderToInputOrder = OpReorderAxes(parent=self)
        self.CachedOutput.connect(self._opReorderToInputOrder.Output)
        self.RelabelDict.connect(self._opRelabelConsecutive.RelabelDict)
        self.CleanBlocks.connect(self._opRelabelConsecutive.CleanBlocks)
        self.SerializationOutput.connect(self._opRelabelConsecutive.SerializationOutput)

    def setupOutputs(self):
        input_dtype = self.Input.meta.dtype

        if input_dtype == numpy.uint16:
            self._opDtypeConvert.Function.setValue(lambda x: x.astype("uint32"))
        else:
            self._opDtypeConvert.Function.setValue(lambda x: x)

        self._opReorderToInputOrder.AxisOrder.setValue("".join(self.Input.meta.getAxisKeys()))
        self._opReorderToInputOrder.Input.connect(self._opRelabelConsecutive.Output)

    def propagateDirty(self, slot, subindex, roi):
        # all outputs connected directly
        pass

    def setInSlot(self, slot, subindex, roi, value):
        assert slot == self.SerializationInput, f"Got unexpected slot {slot.name=}"
        # setInSlot handled by downstream input slots
        pass


class OpRelabelConsecutive5D(OpUnblockedArrayCache):
    """
    Operator that computes relabeling and caches both, relabeled array and
    a dictionary that contains the label mapping (used in object classification export).

    Note that the implementation here overrides some methods of
    `OpUnblockedArrayCache` in order to allow the syncrhonized caching of both
    the relabeled image and the dictionary. This is necessary as
    `vigra.relabelConsecutive` produces both in one function call.

    The internal `_blockshape` is always configured for full time slices
    (in order to get a consistent relabeling per time slice).

    Serialization slots expose the internal caches to allow for consistent
    saving and loading.
    """

    StartLabel = InputSlot(value=1)
    RelabelDict = OutputSlot()

    SerializationInput = InputSlot(optional=True)  # expects inputs in the form of tuple(RelabeledArray, RelabelDict)
    SerializationOutput = OutputSlot()  # [tuple(RelabeledArray, RelabelDict), ...]

    supportedDtypes = [numpy.uint8, numpy.uint16, numpy.uint32, numpy.uint64]

    def __init__(
        self,
        parent=None,
        graph=None,
        Input=None,
        StartLabel: Union[int, Slot] = 1,
        CompressionEnabled: Union[bool, Slot] = False,
        SerializationInput=None,
        **kwargs,
    ):
        super().__init__(parent=parent, graph=graph, **kwargs)
        self._blockshape = None
        self.CompressionEnabled.setOrConnectIfAvailable(CompressionEnabled)
        self.StartLabel.setOrConnectIfAvailable(StartLabel)
        self.SerializationInput.setOrConnect(SerializationInput)

        self.Input.setOrConnectIfAvailable(Input)

    def setupOutputs(self):
        # setup Output and CleanBlocks via OpUnblockedArrayCache
        super().setupOutputs()
        self.Output.meta.appropriate_interpolation_order = OpResize.Interpolation.NEAREST

        tagged_shape = self.Input.meta.getTaggedShape()
        assert all(k in tagged_shape for k in "tzyxc"), f"Expected 5D input, got {tagged_shape=}"
        self._blockshape = tuple([1 if k in "ct" else v for k, v in tagged_shape.items()])

        self.Output.meta.ideal_blockshape = tuple(numpy.minimum(self._blockshape, self.Input.meta.shape))

        # check if the input dtype is valid
        if self.Input.ready():
            dtype = self.Input.meta.dtype
            if dtype not in self.supportedDtypes:
                msg = f"{self.name}: dtype '{dtype}' not supported. Supported types: {self.supportedDtypes}"
                raise ValueError(msg)

        if self.Input.meta.dontcache:
            logger.warning("The OpRelabelConsecutive5D operator will always cache, even if input doesn't want it.")

        # Estimate ram usage per requested pixel
        ram_per_pixel = get_ram_per_element(self.Input.meta.dtype)

        # One 'pixel' includes all channels
        if "c" in tagged_shape:
            ram_per_pixel *= float(tagged_shape["c"])

        if self.Input.meta.ram_usage_per_requested_pixel is not None:
            ram_per_pixel = max(ram_per_pixel, self.Input.meta.ram_usage_per_requested_pixel)

        self.Output.meta.ram_usage_per_requested_pixel = ram_per_pixel

        taggedOutputShape = self.Input.meta.getTaggedShape()

        self.RelabelDict.meta.shape = (taggedOutputShape["t"],)
        self.RelabelDict.meta.axistags = vigra.defaultAxistags("t")
        self.RelabelDict.meta.dtype = object

        self.SerializationOutput.meta.shape = (taggedOutputShape["t"],)
        self.SerializationOutput.meta.axistags = vigra.defaultAxistags("t")
        self.SerializationOutput.meta.dtype = object

    def execute(self, slot, subindex, roi, result):
        if slot is self.Output:
            self._execute_Output(slot, subindex, roi, result)

        elif slot is self.RelabelDict:
            self._execute_RelabelDict(slot, subindex, roi, result)

        elif slot is self.SerializationOutput:
            self._execute_SerializationOutput(slot, subindex, roi, result)

        elif slot == self.CleanBlocks:
            self._execute_CleanBlocks(slot, subindex, roi, result)
        else:
            assert False, "Unknown output slot: {}".format(slot.name)

    def _expand_t_based_roi(self, t_roi: Tuple[Tuple[int], Tuple[int]]) -> RoiTuple5D:
        """
        Returns the full 5D roi for a single time slice
        """
        # t_roi[0] --> start
        # t_roi[1] --> stop
        assert len(t_roi[0]) == len(t_roi[1]) == 1, "only 't' axis is expected"
        tagged_shape = self.Output.meta.getTaggedShape()
        assert len(tagged_shape) == 5
        input_roi_start = tuple(0 if k != "t" else t_roi[0][0] for k in tagged_shape)
        input_roi_stop = tuple(v if k != "t" else t_roi[1][0] for k, v in tagged_shape.items())

        return self._standardize_roi(input_roi_start, input_roi_stop)

    def _execute_RelabelDict_impl(self, request_roi, result):
        # here we have to modify the roi, append the block shape
        with self._lock:
            block_roi = self._get_containing_block_roi(request_roi)
            if block_roi is not None:
                # Data is already in the cache. Just extract it.
                assert request_roi == block_roi, f"{request_roi=}, {block_roi=}"
                result[0] = self._block_dicts[block_roi]
                return

        # Data isn't in the cache, so request it and cache it
        self._fetch_and_store_block(request_roi, out=result, slot=self.RelabelDict)

    def _execute_Output_impl(self, request_roi, result):
        request_roi = self._standardize_roi(*request_roi)
        with self._lock:
            block_roi = self._get_containing_block_roi(request_roi)
            if block_roi is not None:
                # Data is already in the cache. Just extract it.
                block_relative_roi = numpy.array(request_roi) - block_roi[0]
                self.Output.stype.copy_data(result, self._block_data[block_roi][roiToSlice(*block_relative_roi)])
                return

        # Data isn't in the cache, so request it and cache it
        self._fetch_and_store_block(request_roi, out=result, slot=self.Output)

    def _execute_SerializationOutput(self, slot, subindex, roi, result):
        """
        Note: does nothing for rois that are not inside the cache
        """
        request_roi = (roi.start, roi.stop)
        assert (
            roi.stop[0] - roi.start[0] == 1
        ), f"Serializers should only request single cache entries {roi.start=} {roi.stop=}"
        request_roi = self._expand_t_based_roi(request_roi)
        with self._lock:
            block_roi = self._get_containing_block_roi(request_roi)
            if block_roi is not None:
                # Data is already in the cache. Just extract it.
                assert request_roi == block_roi
                result[0] = (self._block_data[block_roi], self._block_dicts[block_roi])

    def _fetch_and_store_block(self, block_roi, out, slot):
        """
        Overridden from OpUnblockedArrayCache in order to handle multiple output slots
        """
        if out is not None:
            roi_shape = numpy.array(block_roi[1]) - block_roi[0]
            if slot is self.Output:
                assert (out.shape == roi_shape).all(), f"{out.shape=} != {roi_shape=}"
            elif slot is self.RelabelDict:
                assert out.shape == (1,), f"{out.shape=}"

        # Get lock for this block (create first if necessary)
        with self._lock:
            if block_roi not in self._block_locks:
                self._block_locks[block_roi] = RequestLock()
            block_lock = self._block_locks[block_roi]

        # Handle identical simultaneous requests for the same block
        # without preventing parallel requests for different blocks.
        with block_lock:
            if slot is self.Output and block_roi in self._block_data:
                # Extra [:] here is in case we are decompressing from a chunkedarray
                self.Output.stype.copy_data(out, self._block_data[block_roi][:])
                return

            if slot is self.RelabelDict and block_roi in self._block_dicts:
                out[:] = self._block_dicts[block_roi]
                return

            # f(block_roi, out)
            # can relabelConsecutive can only handle up to 3D - so need to iterate after all
            req = self.Input(*block_roi)

            block_data = vigra.taggedView(req.wait(), axistags=self.Input.meta.axistags)
            img = block_data.squeeze()

            _, __, relabel_dict = vigra.analysis.relabelConsecutive(
                img, start_label=self.StartLabel.value, keep_zeros=True, out=img
            )

            img = img.withAxes(self.Output.meta.axistags).view(numpy.ndarray)

            self._store_block_data(block_roi, img, relabel_dict)

            if slot is self.Output:
                # Extra [:] here is in case we are decompressing from a chunkedarray
                self.Output.stype.copy_data(out, img)
                return

            if slot is self.RelabelDict:
                out[0] = relabel_dict
                return

    def _store_block_data(self, block_roi: RoiTuple, block_data: npt.NDArray, block_relabel_dict: Dict[int, int]):
        """
        Overridden from OpUnblockedArrayCache to ensure cache integrity

        Copy block_data and block_relabel_dict and store it into the cache.
        Both values are assumed to be produced at the same time (same function)
        so they should always both be present.
        The block_lock is not obtained here, so lock it before you call this.
        """
        with self._lock:
            if self.CompressionEnabled.value and numpy.dtype(block_data.dtype) in [
                numpy.dtype(numpy.uint8),
                numpy.dtype(numpy.uint32),
                numpy.dtype(numpy.float32),
            ]:
                compressed_block = vigra.ChunkedArrayCompressed(
                    block_data.shape, vigra.Compression.LZ4, block_data.dtype
                )

                compressed_block[:] = block_data
                block_storage_data = compressed_block
            else:
                block_storage_data = block_data.copy()

            # Store the data.
            # First double-check that the block wasn't removed from the
            #   cache while we were requesting it.
            # (Could have happened via propagateDirty() or eventually the arrayCacheMemoryMgr)
            if block_roi in self._block_locks:
                self._block_data[block_roi] = block_storage_data
                self._block_dicts[block_roi] = block_relabel_dict

        self._last_access_times[block_roi] = time.perf_counter()

    def _resetBlocks(self, *_):
        """
        Overridden from OpUnblockedArrayCache to ensure cache integrity
        """
        with self._lock:
            self._block_data: Dict[RoiTuple, npt.ArrayLike] = {}
            self._block_dicts: Dict[RoiTuple, Dict[int, int]] = {}
            self._block_locks: Dict[RoiTuple, RequestLock] = {}
            self._last_access_times: Dict[RoiTuple, float] = collections.defaultdict(float)

    def setInSlot(self, slot, subindex, roi, block_data: Tuple[npt.NDArray, Dict[int, int]]):
        """
        Load cached data via the SerializationInput slot.

        This slot is special, as it has only a `t` axis, and takes a tuple of
        (relabeled_array, relabel_dict),
        The cache internally uses 5D blocks, in order to easily determine if
        some request roi is contained in one of the saved blocks.
        # TODO: simplification possible by doing everything per time point.
                Also easy to check if ROI is contained in a key, but will lose generality.
        """
        assert slot == self.SerializationInput
        assert len(block_data) == 2, f"Got unexpected block_data size: {len(block_data)=}"

        block_roi = self._expand_t_based_roi((tuple(roi.start), tuple(roi.stop)))

        with self._lock:
            if block_roi not in self._block_locks:
                self._block_locks[block_roi] = RequestLock()
            block_lock = self._block_locks[block_roi]

        with block_lock:
            self._store_block_data(block_roi, block_data[0], block_data[1])

    def _execute_Output(self, slot, subindex, roi, result):
        """
        Overridden from OpUnblockedArrayCache
        """

        def copy_block(full_block_roi, clipped_block_roi):
            full_block_roi = numpy.asarray(full_block_roi)
            clipped_block_roi = numpy.asarray(clipped_block_roi)
            output_roi = numpy.asarray(clipped_block_roi) - roi.start

            block_roi = self._get_containing_block_roi(clipped_block_roi)

            if block_roi is not None or (full_block_roi == clipped_block_roi).all():
                self._execute_Output_impl(clipped_block_roi, result[roiToSlice(*output_roi)])
            else:
                # Data doesn't exist yet in the cache.
                # Request the full block, but then discard the parts we don't need.

                # (We use allocateDestination() here to support MaskedArray types.)
                # TODO: We should probably just get rid of MaskedArray support altogether...
                full_block_data = self.Output.stype.allocateDestination(SubRegion(self.Output, *full_block_roi))
                self._execute_Output_impl(full_block_roi, full_block_data)

                roi_within_block = clipped_block_roi - full_block_roi[0]
                self.Output.stype.copy_data(
                    result[roiToSlice(*output_roi)], full_block_data[roiToSlice(*roi_within_block)]
                )

        clipped_block_rois = getIntersectingRois(self.Input.meta.shape, self._blockshape, (roi.start, roi.stop), True)
        full_block_rois = getIntersectingRois(self.Input.meta.shape, self._blockshape, (roi.start, roi.stop), False)

        pool = RequestPool()
        for full_block_roi, clipped_block_roi in zip(full_block_rois, clipped_block_rois):
            req = Request(partial(copy_block, full_block_roi, clipped_block_roi))
            pool.add(req)
        pool.wait()

    def _execute_RelabelDict(self, slot, subindex, roi, result):
        assert slot == self.RelabelDict
        request_roi = self._expand_t_based_roi((roi.start, roi.stop))

        t_index = self.Input.meta.getAxisKeys().index("t")
        assert t_index >= 0

        def single_t_slice_dict(full_block_roi, result_block):
            self._execute_RelabelDict_impl(full_block_roi, result_block)

        full_block_rois = getIntersectingRois(self.Input.meta.shape, self._blockshape, request_roi, False)
        t_offset = full_block_rois[0][0][t_index]

        pool = RequestPool()
        for full_block_roi in full_block_rois:
            result_block = result[slice(full_block_roi[0][t_index] - t_offset, full_block_roi[1][t_index] - t_offset)]
            req = Request(partial(single_t_slice_dict, self._standardize_roi(*full_block_roi), result_block))
            pool.add(req)
        pool.wait()

    def propagateDirty(self, slot, subindex, roi):
        super().propagateDirty(slot, subindex, roi)

    def _memory_for_block(self, block_key: RoiTuple):
        try:
            block_data = self._block_data[block_key]
            block_dict_memory = len(self._block_dicts[block_key]) * 2 * 8  # assuming int64 keys/values
            bytes_per_pixel = numpy.dtype(block_data.dtype).itemsize
            block_memory = block_data.size * bytes_per_pixel + block_dict_memory
        except (KeyError, AttributeError):
            # what could have happened and why it's fine
            #  * block was deleted (then it does not occupy memory)
            #  * block is not array data (then we don't know how
            #    much memory it ouccupies)
            block_memory = 0.0

        return block_memory

    def usedMemory(self):
        """
        Overridden from UnblockedArrayCache
        """
        total = 0.0
        for k in list(self._block_data.keys()):
            total += self._memory_for_block(k)
        return total

    def freeBlock(self, key: RoiTuple):
        """
        Overridden from OpUnblockedArrayCache to ensure cache integrity
        """
        with self._lock:
            if key not in self._block_locks:
                return 0
            block_mem = self._memory_for_block(key)
            del self._block_data[key]
            del self._block_dicts[key]
            del self._block_locks[key]
            del self._last_access_times[key]
            return block_mem
