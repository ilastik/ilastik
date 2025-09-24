from typing import Dict

import numpy
import pytest

from lazyflow.utility.helpers import bigintprod, eq_shapes


@pytest.mark.parametrize(
    "nums,result",
    [
        ((10, 10, 10), 1000),
        ((numpy.power(2, 16), numpy.power(2, 16), 2), 2**33),  # would fail with numpy.prod already on windows
    ],
)
def test_bigintprod(nums, result):
    assert bigintprod(nums) == result


def tagged_shape(keys, shape):
    return dict(zip(keys, shape))


@pytest.mark.parametrize(
    "shape1, shape2, match_expected",
    [
        (tagged_shape("xy", [5, 6]), tagged_shape("xy", [5, 6]), True),
        (tagged_shape("xy", [5, 6]), tagged_shape("yx", [6, 5]), True),
        (tagged_shape("xyc", [5, 6, 3]), tagged_shape("yx", [6, 5]), True),
        (tagged_shape("xy", [5, 6]), tagged_shape("yxc", [6, 5, 3]), True),
        (tagged_shape("xyc", [5, 6, 1]), tagged_shape("yxc", [6, 5, 3]), True),
        (tagged_shape("xyztc", [5, 6, 1, 1, 3]), tagged_shape("yx", [6, 5]), True),
        (tagged_shape("xy", [5, 6]), tagged_shape("tczyx", [1, 3, 1, 6, 5]), True),
        (tagged_shape("xyzt", [3, 4, 5, 6]), tagged_shape("tyzx", [6, 4, 5, 3]), True),
        (tagged_shape("xy", [5, 6]), tagged_shape("xy", [5, 7]), False),
        (tagged_shape("xyztc", [5, 6, 9, 8, 1]), tagged_shape("xy", [5, 6]), False),
        (tagged_shape("xyztc", [5, 6, 9, 8, 1]), tagged_shape("yx", [6, 5]), False),
        (tagged_shape("xyztc", [5, 6, 9, 8, 1]), tagged_shape("zty", [9, 8, 6]), False),
    ],
)
def test_eq_shapes(shape1: Dict[str, int], shape2: Dict[str, int], match_expected: bool):
    assert match_expected == eq_shapes(shape1, shape2)
