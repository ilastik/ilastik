import pytest

import numpy

from ilastik.utility.slottools import DtypeConvertFunction


@pytest.mark.parametrize(
    "input_array,dtype,expected",
    [
        (numpy.array((1,), dtype="uint32"), "uint8", numpy.array((255,), dtype="uint8")),
        (
            numpy.array(
                (
                    0.0,
                    1.0,
                ),
                dtype="float",
            ),
            "uint8",
            numpy.array(
                (
                    0,
                    255,
                ),
                dtype="uint8",
            ),
        ),
        (numpy.array((42 ** 3,), dtype="uint32"), "float32", numpy.array((42 ** 3,), dtype="float32")),
    ],
)
def test_rescaling(input_array, dtype, expected):
    result = DtypeConvertFunction(dtype)(input_array)
    assert result.dtype == expected.dtype
    assert result.shape == expected.shape
    numpy.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize(
    "dtype_a,dtype_b,expected",
    [
        ("uint8", "uint8", True),
        ("float", "uint8", False),
        ("float32", "float64", False),
    ],
)
def test_eq(dtype_a, dtype_b, expected):
    fn_a = DtypeConvertFunction(dtype_a)
    fn_b = DtypeConvertFunction(dtype_b)

    assert (fn_a == fn_b) == expected
