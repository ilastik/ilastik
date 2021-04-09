from typing import Any, Dict, Iterator, Tuple, Type
from queue import Queue

import numpy

from lazyflow.graph import Slot
from lazyflow.utility.roiRequestBatch import RoiRequestBatch
from lazyflow.utility.helpers import bigintprod


ROI = Tuple[int, int, int, int, int]
SHAPE = ROI
ROI_TUPLE = Tuple[ROI, ROI]


class _RoiIter:
    """Iterate over rois for a given shape"""

    def __init__(self, slot: Slot, iterate_axes: str):
        self._axisorder = slot.meta.getAxisKeys()
        self._tagged_shape = slot.meta.getTaggedShape()
        self._iterate_axes = iterate_axes
        self._iterate_shape = tuple(self._tagged_shape[x] for x in iterate_axes)
        self._shape = slot.meta.shape

    def to_index(self, roi: ROI_TUPLE) -> int:
        """Convert ROI_TUPLE to index

        first ROI_TUPLE -> index = 0
        last ROI_TUPLE -> index = len(self) - 1
        """
        start = roi[0]
        relevant_indices = tuple(start[self._axisorder.index(x)] for x in self._iterate_axes)
        return numpy.ravel_multi_index(relevant_indices, self._iterate_shape)

    def __len__(self) -> int:
        return bigintprod(self._iterate_shape)

    def __iter__(self) -> Iterator[ROI_TUPLE]:
        """iterate in ascending order, according to to_index"""
        for partial_start in numpy.ndindex(self._iterate_shape):
            tagged_start = {k: v for k, v in zip(self._iterate_axes, partial_start)}
            tagged_stop = {k: v + 1 for k, v in zip(self._iterate_axes, partial_start)}
            for k in self._tagged_shape:
                if k not in self._iterate_axes:
                    tagged_start[k] = 0
                    tagged_stop[k] = self._tagged_shape[k]

            start: ROI = tuple(tagged_start[x] for x in self._axisorder)
            stop: ROI = tuple(tagged_stop[x] for x in self._axisorder)
            yield start, stop


class RoiRequestBufferIter:
    """Iterate over first 3 dims of a 5D slot in nd-ascending order."""

    def __init__(self, slot: Slot, batchsize: int, iterate_axes: str):
        """
        Args:
            slot: slot to request data from
            batchsize: maximum number of requests to launch in parallel
        """
        self._slot = slot
        self._batchsize = batchsize
        self._q: Queue[Tuple[ROI_TUPLE, numpy.ndarray]] = Queue()
        self._items: Dict[int, numpy.ndarray] = {}

        self._index = 0
        self._roi_iter = _RoiIter(self._slot, iterate_axes=iterate_axes)
        self._max = len(self._roi_iter)

        self._roi_request_batch = RoiRequestBatch(
            outputSlot=self._slot,
            roiIterator=iter(self._roi_iter),
            totalVolume=bigintprod(self._slot.meta.shape),
            batchSize=self._batchsize,
            allowParallelResults=False,
        )
        self._roi_request_batch.resultSignal.subscribe(self._put)

    def _put(self, *val):
        self._q.put(val)

    @property
    def progress_signal(self):
        return self._roi_request_batch.progressSignal

    def __iter__(self):
        self._roi_request_batch.execute()
        return self

    def __next__(self):
        while True:
            if self._index >= self._max:
                raise StopIteration()
            if self._index not in self._items:
                k, v = self._q.get()
                idx = self._roi_iter.to_index(k)
                self._items[idx] = v
                continue
            i = self._index
            item = self._items.pop(i)
            self._index = i + 1

            return item
