import numpy
import pytest
import vigra

from lazyflow.operators.filterOperators import OpBaseFilter
from lazyflow.roi import sliceToRoi
from lazyflow.graph import InputSlot
from lazyflow.rtype import SubRegion


class OpPassthroughFilter(OpBaseFilter):
    """OpBaseFilter that passes through input"""

    _scale = InputSlot(value=0.5)
    minimum_scale = 0.3
    supports_window = True
    name = "OpPassthroughFilter"

    @staticmethod
    def filter_fn(source, **kwargs):
        return source

    def resultingChannels(self):
        return 1


ref_slicing = numpy.s_[0:1, 0:1, 0:10, 0:20, 0:30]  # fmt: skip
@pytest.mark.parametrize(
    "slice1",
    [
        (*ref_slicing[:dim], slice(i, i + 1), *ref_slicing[dim + 1:])
        for dim in (2, 3, 4)
        for i in (0, 1, 2, 3)
    ],
)  # fmt: skip
@pytest.mark.parametrize("computeIn2d", [True, False])
def test_single_slice_requests_first_slices(graph, slice1, computeIn2d):
    dummy_filter_op = OpPassthroughFilter(graph=graph)
    shape = tuple(s.stop for s in ref_slicing)
    data_ref = numpy.arange(numpy.prod(shape)).astype(numpy.float32).reshape(shape)
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
