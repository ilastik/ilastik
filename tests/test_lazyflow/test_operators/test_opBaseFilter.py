import numpy
import pytest
import vigra

from lazyflow.operators.filterOperators import OpBaseFilter
from lazyflow.roi import sliceToRoi
from lazyflow.graph import InputSlot
from lazyflow.rtype import SubRegion


@pytest.fixture
def dummy_filter_op(graph):
    """OpBaseFilter that passes through input"""

    def _filter_func(source, **filter_kwargs):
        return source

    class OpPassthroughFilter(OpBaseFilter):
        _scale = InputSlot(value=0.5)
        minimum_scale = 0.3

        supports_window = True

        name = "OpPassthroughFilter"
        filter_fn = staticmethod(_filter_func)

        def resultingChannels(self):
            return 1

    op = OpPassthroughFilter(graph=graph)
    return op


@pytest.mark.parametrize(
    "slice1,computeIn2d",
    [
        (numpy.s_[0:1, 0:1, 0:1, 0:20, 0:30], True),
        (numpy.s_[0:1, 0:1, 1:2, 0:20, 0:30], True),  # previous failure case
        (numpy.s_[0:1, 0:1, 2:3, 0:20, 0:30], True),  # previous failure case
        (numpy.s_[0:1, 0:1, 3:4, 0:20, 0:30], True),  # previous failure case
        (numpy.s_[0:1, 0:1, 0:10, 0:1, 0:30], True),
        (numpy.s_[0:1, 0:1, 0:10, 1:2, 0:30], True),
        (numpy.s_[0:1, 0:1, 0:10, 2:3, 0:30], True),
        (numpy.s_[0:1, 0:1, 0:10, 3:4, 0:30], True),
        (numpy.s_[0:1, 0:1, 0:10, 0:20, 0:1], True),
        (numpy.s_[0:1, 0:1, 0:10, 0:20, 1:2], True),
        (numpy.s_[0:1, 0:1, 0:10, 0:20, 2:3], True),
        (numpy.s_[0:1, 0:1, 0:10, 0:20, 3:4], True),
        (numpy.s_[0:1, 0:1, 0:1, 0:20, 0:30], False),
        (numpy.s_[0:1, 0:1, 1:2, 0:20, 0:30], False),
        (numpy.s_[0:1, 0:1, 2:3, 0:20, 0:30], False),
        (numpy.s_[0:1, 0:1, 0:10, 0:1, 0:30], False),
        (numpy.s_[0:1, 0:1, 0:10, 1:2, 0:30], False),
        (numpy.s_[0:1, 0:1, 0:10, 2:3, 0:30], False),
        (numpy.s_[0:1, 0:1, 0:10, 3:4, 0:30], False),
        (numpy.s_[0:1, 0:1, 0:10, 0:20, 0:1], False),
        (numpy.s_[0:1, 0:1, 0:10, 0:20, 1:2], False),
        (numpy.s_[0:1, 0:1, 0:10, 0:20, 2:3], False),
        (numpy.s_[0:1, 0:1, 0:10, 0:20, 3:4], False),
    ],
)
def test_single_slice_requests_first_slices(dummy_filter_op, slice1, computeIn2d):
    data_ref = numpy.arange(10 * 20 * 30).astype(numpy.float32).reshape((1, 1, 10, 20, 30))
    data = vigra.taggedView(data_ref.copy(), "tczyx")
    dummy_filter_op.Input.setValue(data)
    dummy_filter_op.ComputeIn2d.setValue(computeIn2d)
    req_roi = SubRegion(dummy_filter_op.Output, *sliceToRoi(slice1, data_ref.shape))
    target0 = numpy.zeros([x.stop - x.start for x in slice1], dtype=numpy.float32)

    dummy_filter_op.call_execute(
        slot=dummy_filter_op.Output,
        subindex=(),
        roi=req_roi,
        result=target0,
        sourceArray=data,
    )

    numpy.testing.assert_array_almost_equal(data_ref[slice1], target0)
