import numpy
import pytest

from ilastik.utility.gui.qtcompat import QtConversionError, ensure_bool, ensure_float, ensure_int, NP_BOOL


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, True),
        (False, False),
        (1, True),
        (0, False),
        (-1, True),
        (1.5, True),
        (0.0, False),
        (numpy.bool_(True), True),
        (numpy.bool_(False), False),
        (NP_BOOL(True), True),
        (NP_BOOL(False), False),
        (numpy.int8(1), True),
        (numpy.uint8(0), False),
        (numpy.int32(1), True),
        (numpy.uint32(1), True),
        (numpy.int64(0), False),
        (numpy.int64(1), True),
        (numpy.float32(2.5), True),
        (numpy.float64(0.0), False),
    ],
)
def test_ensure_bool(value, expected):
    assert ensure_bool(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, 1),
        (False, 0),
        (1, 1),
        (-3, -3),
        (1.9, 1),
        (-1.9, -1),
        (numpy.bool_(True), 1),
        (numpy.bool_(False), 0),
        (NP_BOOL(True), 1),
        (NP_BOOL(False), 0),
        (numpy.int8(13), 13),
        (numpy.uint8(8), 8),
        (numpy.int32(42), 42),
        (numpy.uint32(142), 142),
        (numpy.int64(-7), -7),
        (numpy.uint64(5), 5),
        (numpy.float32(3.9), 3),
        (numpy.float64(-2.1), -2),
    ],
)
def test_ensure_int(value, expected):
    assert ensure_int(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, 1.0),
        (False, 0.0),
        (1, 1.0),
        (-3, -3.0),
        (1.5, 1.5),
        (numpy.bool_(True), 1.0),
        (numpy.bool_(False), 0.0),
        (NP_BOOL(True), 1.0),
        (NP_BOOL(False), 0.0),
        (numpy.int8(-13), -13.0),
        (numpy.uint8(8), 8.0),
        (numpy.int32(42), 42.0),
        (numpy.uint32(142), 142.0),
        (numpy.int64(-7), -7.0),
        (numpy.uint64(5), 5.0),
        (numpy.float32(3.5), 3.5),
        (numpy.float64(-2.25), -2.25),
    ],
)
def test_ensure_float(value, expected):
    assert ensure_float(value) == pytest.approx(expected)


@pytest.mark.parametrize(
    "value",
    [
        None,
        "123",
        "",
        b"1",
        [],
        [1],
        (),
        (1,),
        {},
        {"a": 1},
        object(),
        complex(1, 2),
        numpy.array(1),
        numpy.array([1]),
        numpy.array(True),
        numpy.array([True]),
    ],
)
@pytest.mark.parametrize("func", [ensure_bool, ensure_int, ensure_float])
def test_ensure_raises_for_unsupported_types(func, value):
    with pytest.raises(QtConversionError):
        func(value)
