from collections import OrderedDict

import pytest
from attr import dataclass
from bioimageio.spec.model.v0_5 import (
    AxisId,
    BatchAxis,
    ChannelAxis,
    Identifier,
    InputAxis,
    ParameterizedSize,
    SizeReference,
    SpaceInputAxis,
    TensorId,
    TimeInputAxis,
)

import ilastik.utility.bioimageio_utils


@dataclass
class MockTensorDescr:
    id: str
    axes: list[InputAxis]


MOCK_MIN_SIZE_2D = 128
MOCK_MIN_SIZE_3D = 64


@pytest.fixture
def mock_min_tile_sizes(monkeypatch):
    monkeypatch.setattr(
        ilastik.utility.bioimageio_utils.InputAxisUtils,
        "MIN_SIZE_2D",
        MOCK_MIN_SIZE_2D,
    )
    monkeypatch.setattr(
        ilastik.utility.bioimageio_utils.InputAxisUtils,
        "MIN_SIZE_3D",
        MOCK_MIN_SIZE_3D,
    )


@pytest.mark.parametrize(
    "axes, expected_dict",
    (
        (
            [
                BatchAxis(),
                ChannelAxis(channel_names=[Identifier("ch0")]),
                SpaceInputAxis(size=10, id=AxisId("x")),
                SpaceInputAxis(size=11, id=AxisId("y")),
            ],
            OrderedDict({"c": 1, "x": 10, "y": 11}),
        ),
        (
            [
                BatchAxis(),
                ChannelAxis(channel_names=[Identifier("ch0")]),
                SpaceInputAxis(size=10, id=AxisId("x")),
                SpaceInputAxis(size=11, id=AxisId("y")),
                SpaceInputAxis(size=12, id=AxisId("z")),
                TimeInputAxis(size=1),
            ],
            OrderedDict({"c": 1, "x": 10, "y": 11, "z": 12, "t": 1}),
        ),
        (
            [
                BatchAxis(),
                SpaceInputAxis(size=ParameterizedSize(min=10, step=2), id=AxisId("x")),
                SpaceInputAxis(size=11, id=AxisId("y")),
            ],
            OrderedDict({"x": MOCK_MIN_SIZE_2D, "y": 11}),
        ),
        (
            [
                BatchAxis(),
                ChannelAxis(channel_names=[Identifier("ch0")]),
                SpaceInputAxis(size=10, id=AxisId("x")),
                SpaceInputAxis(size=11, id=AxisId("y")),
                SpaceInputAxis(size=ParameterizedSize(min=12, step=2), id=AxisId("z")),
            ],
            OrderedDict({"c": 1, "x": 10, "y": 11, "z": MOCK_MIN_SIZE_3D}),
        ),
        (
            [
                BatchAxis(),
                SpaceInputAxis(size=ParameterizedSize(min=MOCK_MIN_SIZE_2D + 1, step=2), id=AxisId("x")),
                SpaceInputAxis(size=11, id=AxisId("y")),
            ],
            OrderedDict({"x": MOCK_MIN_SIZE_2D + 1, "y": 11}),
        ),
    ),
    ids=["Fixed-2Dc", "Fixed-3Dtc", "Mixed-2D", "Mixed-3Dc", "Mixed-2D-larger-than-min"],
)
def test_get_best_tile_shape_single_tensor(mock_min_tile_sizes, axes, expected_dict):
    descr = MockTensorDescr("test", axes=axes)
    ut = ilastik.utility.bioimageio_utils.InputAxisUtils([descr])  # type: ignore
    tile_shape = ut.get_best_tile_shape("test")

    assert tile_shape == expected_dict


@pytest.mark.parametrize(
    "axes, expected_dict",
    (
        (
            [SpaceInputAxis(size=10, id=AxisId("x"))],
            OrderedDict({"x": 10, "y": 11}),
        ),
        (
            [SpaceInputAxis(size=ParameterizedSize(min=10, step=2), id=AxisId("x"))],
            OrderedDict({"x": MOCK_MIN_SIZE_2D, "y": 11}),
        ),
    ),
    ids=["Fixed-2D", "Mixed-2D"],
)
def test_get_best_tile_shape_size_ref(mock_min_tile_sizes, axes, expected_dict):
    descr1 = MockTensorDescr("ref", axes=axes)
    descr2 = MockTensorDescr(
        "test",
        [
            BatchAxis(),
            SpaceInputAxis(size=SizeReference(tensor_id=TensorId("ref"), axis_id=AxisId("x")), id=AxisId("x")),
            SpaceInputAxis(size=11, id=AxisId("y")),
        ],
    )
    ut = ilastik.utility.bioimageio_utils.InputAxisUtils([descr1, descr2])  # type: ignore
    tile_shape = ut.get_best_tile_shape("test")
    assert tile_shape == expected_dict
