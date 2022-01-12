from unittest import mock

from lazyflow.operators.tiktorch.classifier import ModelSession

import pytest
from tiktorch.proto import inference_pb2


@pytest.fixture
def pb_session():
    return inference_pb2.ModelSession(
        inputAxes=["xyc"],
        outputAxes=["xyc"],
        hasTraining=False,
        inputShapes=[
            inference_pb2.InputShape(
                shapeType=0,
                shape=inference_pb2.NamedInts(
                    namedInts=[
                        inference_pb2.NamedInt(name="x", size=1024),
                        inference_pb2.NamedInt(name="y", size=512),
                        inference_pb2.NamedInt(name="c", size=1),
                    ]
                ),
            ),
        ],
        outputShapes=[
            inference_pb2.OutputShape(
                shapeType=1,
                offset=inference_pb2.NamedFloats(
                    namedFloats=[
                        inference_pb2.NamedFloat(name="x", size=16),
                        inference_pb2.NamedFloat(name="y", size=32),
                        inference_pb2.NamedFloat(name="c", size=3),
                    ]
                ),
                scale=inference_pb2.NamedFloats(
                    namedFloats=[
                        inference_pb2.NamedFloat(name="x", size=1),
                        inference_pb2.NamedFloat(name="y", size=0.5),
                        inference_pb2.NamedFloat(name="c", size=2),
                    ]
                ),
                halo=inference_pb2.NamedInts(
                    namedInts=[
                        inference_pb2.NamedInt(name="x", size=256),
                        inference_pb2.NamedInt(name="y", size=128),
                        inference_pb2.NamedInt(name="c", size=1),
                    ]
                ),
            )
        ],
    )


def test_get_halo_returns_values_specified_by_tags(pb_session):
    model_session = ModelSession(session=pb_session, factory=mock.Mock())
    assert model_session.get_halos(axes="xy") == [(256, 128)]
    assert model_session.get_halos(axes="yx") == [(128, 256)]
    assert model_session.get_halos(axes="yxc") == [(128, 256, 1)]


def test_get_halo_returns_0_if_value_is_unspecified(pb_session):
    model_session = ModelSession(session=pb_session, factory=mock.Mock())
    assert model_session.get_halos(axes="xyz") == [(256, 128, 0)]
    assert model_session.get_halos(axes="txyz") == [(0, 256, 128, 0)]


def test_get_output_shape(pb_session):
    """shape = shape(input_tensor) * scale + 2 * offset"""
    model_session = ModelSession(session=pb_session, factory=mock.Mock())

    output_shape = model_session.get_output_shapes()
    assert output_shape == [[{"x": 1056, "y": 320, "c": 8}]]


def test_get_input_shape(pb_session):
    model_session = ModelSession(session=pb_session, factory=mock.Mock())

    assert model_session.get_input_shapes("xyc") == [[(1024, 512, 1)]]
    assert model_session.get_input_shapes("cyx") == [[(1, 512, 1024)]]
    assert model_session.get_input_shapes("c") == [[(1,)]]
    assert model_session.get_input_shapes("tzyxc") == [[(1, 1, 512, 1024, 1)]]


def test_known_classes(pb_session):
    model_session = ModelSession(session=pb_session, factory=mock.Mock())
    assert model_session.known_classes == list(range(1, 9))


def test_num_classes(pb_session):
    model_session = ModelSession(session=pb_session, factory=mock.Mock())
    assert model_session.num_classes == 8


def test_has_training(pb_session):
    model_session = ModelSession(session=pb_session, factory=mock.Mock())
    assert not model_session.has_training


def test_input_axes(pb_session):
    model_session = ModelSession(session=pb_session, factory=mock.Mock())
    assert model_session.input_axes == ["xyc"]


def test_get_output_axes(pb_session):
    model_session = ModelSession(session=pb_session, factory=mock.Mock())
    assert model_session.output_axes == ["xyc"]
