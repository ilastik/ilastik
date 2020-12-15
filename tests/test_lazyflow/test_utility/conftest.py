import pytest

import numpy

from lazyflow.operators import OpArrayPiper


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
def op_raising_at_3(graph):
    op = OpArrayPiperError(3, graph=graph)
    data = numpy.arange(10 * 20 * 30).reshape((10, 20, 30))
    op.Input.setValue(data)
    return op
