from typing import Any, Dict, Iterator, Tuple, Type
from queue import Queue

import numpy

from lazyflow.graph import Slot
from lazyflow.utility.roiRequestBatch import RoiRequestBatch


ROI = Tuple[int, int, int, int, int]
SHAPE = ROI
ROI_TUPLE = Tuple[ROI, ROI]


class _RoiIter:
    """Iterate over rois for a given shape"""

    def __init__(self, slot: Slot):
        if "".join(slot.meta.getAxisKeys()) != "tzcyx":
            raise ValueError("Only axisorder tzcyx supported.")
        self._shape = slot.meta.shape

    def to_index(self, roi: ROI_TUPLE) -> int:
        """Convert ROI_TUPLE to index

        first ROI_TUPLE -> index = 0
        last ROI_TUPLE -> index = len(self) - 1
        """
        return numpy.ravel_multi_index(roi[0][:-2], self._shape[:-2])

    def __len__(self) -> int:
        return numpy.prod(self._shape[:-2])

    def __iter__(self) -> Iterator[ROI_TUPLE]:
        """iterate in ascending order, according to to_index"""
        for partial_start in numpy.ndindex(self._shape[:-2]):
            start: ROI = partial_start + (0, 0)
            stop: ROI = tuple(i + 1 for i in partial_start) + self._shape[-2:]
            yield start, stop


class RoiRequestBufferIter:
    """Iterate over first 3 dims of a 5D slot in nd-ascending order."""

    def __init__(self, slot: Slot, batchsize: int):
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
        self._roi_iter = _RoiIter(self._slot)
        self._max = len(self._roi_iter)

        self._roi_request_batch = RoiRequestBatch(
            outputSlot=self._slot,
            roiIterator=iter(self._roi_iter),
            totalVolume=numpy.prod(self._slot.meta.shape),
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
