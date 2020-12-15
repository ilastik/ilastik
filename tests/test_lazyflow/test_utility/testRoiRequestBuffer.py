import numpy
import pytest
from unittest import mock

import vigra

from lazyflow.operators import OpArrayPiper
from lazyflow.utility import RoiRequestBufferIter
from lazyflow.utility.roiRequestBuffer import _RoiIter
import lazyflow.utility.roiRequestBuffer


class ProcessingException(Exception):
    pass


class OpArrayPiperError(OpArrayPiper):
    def __init__(self, raise_exception_on_req_no, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._raise_exception_on_req_no = raise_exception_on_req_no
        self._execution_count = 0

    def execute(self, slot, subindex, roi, result):
        self._execution_count += 1
        if self._execution_count == self._raise_exception_on_req_no:
            raise ProcessingException()
        super().execute(slot, subindex, roi, result)


@pytest.fixture
def raising_op(graph):
    op = OpArrayPiperError(3, graph=graph)
    data = vigra.taggedView(numpy.ones((3, 2, 10, 16, 32)), vigra.defaultAxistags("tzcyx"))
    op.Input.setValue(data)
    return op


def test_RoiIter_default():
    mockslot = mock.Mock()
    shape = (200, 42, 3, 15, 27)
    mockslot.meta.shape = (200, 42, 3, 15, 27)
    mockslot.meta.getAxisKeys.return_value = ["t", "z", "c", "y", "x"]
    mockslot.meta.getTaggedShape.return_value = {"t": 200, "z": 42, "c": 3, "y": 15, "x": 27}
    r_iter = _RoiIter(mockslot, iterate_axes="tzc")

    assert len(r_iter) == numpy.prod(shape[:-2])
    assert all(x[-2:] == (0, 0) for x, _ in r_iter)
    assert all(x[0] == y + (0, 0) for x, y in zip(r_iter, numpy.ndindex(*shape[:-2])))


@pytest.mark.parametrize(
    "tagged_shape,iterate_axes,axisorder,expected",
    [
        ({"x": 4}, "x", "x", (((0,), (1,)), ((1,), (2,)), ((2,), (3,)), ((3,), (4,)))),
        ({"x": 1, "y": 2, "z": 3}, "y", "zxy", (((0, 0, 0), (3, 1, 1)), ((0, 0, 1), (3, 1, 2)))),
    ],
)
def test_RoiIter(tagged_shape, iterate_axes, axisorder, expected):
    mockslot = mock.Mock()
    mockslot.meta.shape = tuple(tagged_shape[x] for x in axisorder)
    mockslot.meta.getAxisKeys.return_value = list(axisorder)
    mockslot.meta.getTaggedShape.return_value = tagged_shape

    r_iter = _RoiIter(mockslot, iterate_axes=iterate_axes)
    for gen, exp in zip(r_iter, expected):
        assert gen == exp


def test_in_ascending_order(graph, monkeypatch):
    """Make sure iterator returns data slices in ascending order"""
    op = OpArrayPiper(graph=graph)
    data = vigra.taggedView(
        numpy.ones((3, 2, 10, 16, 32), dtype="uint8") * numpy.arange(32, dtype="uint8"), vigra.defaultAxistags("tzcyx")
    )

    op.Input.setValue(data)

    class RI:
        """Roi iter class that returns rois over the last dimension in descending order"""

        def __init__(self, slot, iterate_axes):
            self._shape = slot.meta.shape

        def to_index(self, roi):
            return roi[0][-1]

        def __len__(self):
            return self._shape[-1]

        def __iter__(self):
            for i in range(self._shape[-1], 0, -1):
                start = (0, 0, 0, 0) + (i - 1,)
                stop = self._shape[:-1] + (i,)
                yield start, stop

    monkeypatch.setattr(lazyflow.utility.roiRequestBuffer, "_RoiIter", RI)
    rb = RoiRequestBufferIter(op.Output, batchsize=2, iterate_axes="tzc")

    for i, item in enumerate(rb):
        assert item.shape == (3, 2, 10, 16, 1)
        assert item.min() == i
        assert item.max() == i


def test_raises(raising_op):
    """Make sure iterator does not block indefinitely if exception occurs in thread"""
    rb = RoiRequestBufferIter(raising_op.Output, batchsize=2, iterate_axes="tzc")

    with pytest.raises(ProcessingException):
        for item in rb:
            assert item.shape == (1, 1, 1, 16, 32)
