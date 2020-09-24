from unittest import mock

from lazyflow.operators.tiktorch.classifier import ModelSession

import pytest
from tiktorch.proto import inference_pb2


@pytest.fixture
def pb_session():
    return inference_pb2.ModelSession(
        halo=[
            inference_pb2.TensorDim(name="x", size=256),
            inference_pb2.TensorDim(name="y", size=128),
            inference_pb2.TensorDim(name="c", size=1),
        ]
    )


def test_get_halo_returns_values_specified_by_tags(pb_session):
    model_session = ModelSession(session=pb_session, factory=mock.Mock())
    assert model_session.get_halo(axes="xy") == [256, 128]
    assert model_session.get_halo(axes="yx") == [128, 256]
    assert model_session.get_halo(axes="yxc") == [128, 256, 1]


def test_get_halo_returns_0_if_value_is_unspecified(pb_session):
    model_session = ModelSession(session=pb_session, factory=mock.Mock())
    assert model_session.get_halo(axes="xyz") == [256, 128, 0]
    assert model_session.get_halo(axes="txyz") == [0, 256, 128, 0]
