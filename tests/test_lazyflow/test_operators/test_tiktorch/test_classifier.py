from unittest import mock

import pytest

_ = pytest.importorskip("tiktorch", reason="These tests require tiktorch")

from bioimageio.core import AxisId
from bioimageio.spec import ModelDescr, ValidationContext
from bioimageio.spec.common import FileDescr
from bioimageio.spec.model.v0_5 import (
    Author,
    BatchAxis,
    ChannelAxis,
    CiteEntry,
    Identifier,
    InputTensorDescr,
    LicenseId,
    OutputTensorDescr,
    SizeReference,
    SpaceInputAxis,
    SpaceOutputAxisWithHalo,
    TensorId,
    TorchscriptWeightsDescr,
    WeightsDescr,
)
from tiktorch.proto import utils_pb2

from lazyflow.operators.tiktorch.classifier import ModelSession


@pytest.fixture
def pb_session():
    return utils_pb2.ModelSession(id="1")


@pytest.fixture
def model_description() -> ModelDescr:

    with ValidationContext(perform_io_checks=False):
        input_0 = InputTensorDescr(
            id=TensorId("input"),
            axes=[
                BatchAxis(),
                SpaceInputAxis(size=1024, id=AxisId("x")),
                SpaceInputAxis(size=512, id=AxisId("y")),
                ChannelAxis(channel_names=[Identifier("ch0")]),
            ],
            test_tensor=FileDescr(source="käse"),
        )

        output_0 = OutputTensorDescr(
            id=TensorId("output"),
            axes=[
                BatchAxis(),
                SpaceOutputAxisWithHalo(
                    halo=256,
                    scale=1.0,
                    size=SizeReference(tensor_id=TensorId("input"), axis_id=AxisId("x"), offset=16),
                    id=AxisId("x"),
                ),
                SpaceOutputAxisWithHalo(
                    halo=128,
                    scale=0.5,
                    size=SizeReference(tensor_id=TensorId("input"), axis_id=AxisId("y"), offset=16),
                    id=AxisId("y"),
                ),
                ChannelAxis(channel_names=[Identifier("predch0"), Identifier("predch1"), Identifier("predch2")]),
            ],
            test_tensor=FileDescr(source="käse"),
        )

        return ModelDescr(
            name="test42",
            description="test",
            authors=[Author(name="test")],
            cite=[CiteEntry(text="test", url="https://example.comdoesnotexist")],
            license=LicenseId("0BSD"),
            documentation="nop.md",
            inputs=[input_0],  # type: ignore
            outputs=[output_0],  # type: ignore
            weights=WeightsDescr(torchscript=TorchscriptWeightsDescr(source="blah", pytorch_version="2024.12.0")),
        )


def test_get_halo_returns_values_specified_by_tags(pb_session, model_description):
    model_session = ModelSession(session=pb_session, model_descr=model_description, factory=mock.Mock())
    assert model_session.get_halos(axes="xy") == {"output": (256, 128)}
    assert model_session.get_halos(axes="yx") == {"output": (128, 256)}
    assert model_session.get_halos(axes="yxc") == {"output": (128, 256, 0)}


def test_get_halo_returns_0_if_value_is_unspecified(pb_session, model_description):
    model_session = ModelSession(session=pb_session, model_descr=model_description, factory=mock.Mock())
    assert model_session.get_halos(axes="xyz") == {"output": (256, 128, 0)}
    assert model_session.get_halos(axes="txyz") == {"output": (0, 256, 128, 0)}


def test_get_input_shape(pb_session, model_description):
    model_session = ModelSession(session=pb_session, model_descr=model_description, factory=mock.Mock())

    assert model_session.get_input_shapes("xyc") == {"input": [(1024, 512, 1)]}
    assert model_session.get_input_shapes("cyx") == {"input": [(1, 512, 1024)]}
    assert model_session.get_input_shapes("c") == {"input": [(1,)]}
    assert model_session.get_input_shapes("tzyxc") == {"input": [(1, 1, 512, 1024, 1)]}


def test_known_classes(pb_session, model_description):
    model_session = ModelSession(session=pb_session, model_descr=model_description, factory=mock.Mock())
    assert model_session.known_classes == list(range(1, 4))


def test_num_classes(pb_session, model_description):
    model_session = ModelSession(session=pb_session, model_descr=model_description, factory=mock.Mock())
    assert model_session.num_classes == 3


def test_input_axes(pb_session, model_description):
    model_session = ModelSession(session=pb_session, model_descr=model_description, factory=mock.Mock())
    assert model_session.input_axes == ["bxyc"]


def test_get_output_axes(pb_session, model_description):
    model_session = ModelSession(session=pb_session, model_descr=model_description, factory=mock.Mock())
    assert model_session.output_axes == ["bxyc"]
