import pytest

import numpy

from lazyflow.utility.helpers import bigintprod


@pytest.mark.parametrize(
    "nums,result",
    [
        ((10, 10, 10), 1000),
        ((numpy.power(2, 16), numpy.power(2, 16), 2), 2 ** 33),  # would fail with numpy.prod already on windows
    ],
)
def test_bigintprod(nums, result):
    assert bigintprod(nums) == result
