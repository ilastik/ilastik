from lazyflow.graph import Operator, InputSlot, OutputSlot, Graph
from lazyflow import stype
from ilastik.applets.networkClassification.nnClassSerializer import (
    SerialModelSlot,
    SerialModelStateSlot,
    SerialListModelStateSlot,
)
from ilastik.applets.base.appletSerializer import AppletSerializer
from tiktorch.types import Model, ModelState

import h5py
import numpy as np
import pytest


@pytest.fixture
def graph():
    return Graph()


@pytest.fixture
def outfile(tmp_path):
    out = tmp_path / "data.h5"
    return h5py.File(str(out), "w")


class TestModelSlotSerialization:
    class NNSerializer(AppletSerializer):
        def __init__(self, topLevelOperator, projectFileGroupName):
            self.VERSION = 1

            slots = [SerialModelSlot(topLevelOperator.Out)]

            super().__init__(projectFileGroupName, slots)

    class OpA(Operator):
        Out = OutputSlot()

        def setupOutputs(self):
            self.Out.meta.shape = (1,)
            self.Out.meta.dtype = object

        def execute(self, *args, **kwargs):
            pass

        def propagateDirty(self, *args, **kwargs):
            pass

    @pytest.fixture
    def op(self, graph):
        op = self.OpA(graph=graph)
        op.Out.setValue(Model(code=b"code", config={"val": 1}))
        return op

    @pytest.fixture
    def serializer(self, op):
        return self.NNSerializer(op, "mygroup")

    @pytest.fixture
    def serialized(self, outfile, serializer, op):
        serializer.serializeToHdf5(outfile, None)

        yield outfile

        outfile.close()

    def test_deserialization(self, graph, serialized):
        op_a = self.OpA(graph=graph)
        serializer = self.NNSerializer(op_a, "mygroup")
        serializer.deserializeFromHdf5(serialized, None)

        assert op_a.Out.value == Model(code=b"code", config={"val": 1})

    def test_consecutive_serialization(self, graph, serializer, serialized, op):
        op.Out.setValue(Model.Empty)

        serializer.serializeToHdf5(serialized, None)
        serializer.deserializeFromHdf5(serialized, None)

        assert not op.Out.value
        assert op.Out.value is Model.Empty

    def test_serialization_with_embedded_nulls(self, op, outfile):
        op.Out.setValue(Model(code=b"\x00nullbyteshere", config={}))
        serializer = self.NNSerializer(op, "mygroup")

        serializer.serializeToHdf5(outfile, None)
        serializer.deserializeFromHdf5(outfile, None)


class TestModelStateSlotSerialization:
    class NNSerializer(AppletSerializer):
        def __init__(self, topLevelOperator, projectFileGroupName):
            self.VERSION = 1

            slots = [SerialModelStateSlot(topLevelOperator.Out)]

            super().__init__(projectFileGroupName, slots)

    class OpA(Operator):
        Out = OutputSlot()

        def setupOutputs(self):
            self.Out.meta.shape = (1,)
            self.Out.meta.dtype = object

        def execute(self, *args, **kwargs):
            pass

        def propagateDirty(self, *args, **kwargs):
            pass

    @pytest.fixture
    def op(self, graph):
        op = self.OpA(graph=graph)
        op.Out.setValue(
            ModelState(model_state=b"model_state", optimizer_state=b"optimizer_state")
        )
        return op

    @pytest.fixture
    def serializer(self, op):
        return self.NNSerializer(op, "mygroup")

    @pytest.fixture
    def serialized(self, outfile, serializer, op):

        serializer.serializeToHdf5(outfile, None)

        yield outfile

        outfile.close()

    def test_deserialization(self, graph, op, serialized):
        op_a = self.OpA(graph=graph)
        serializer = self.NNSerializer(op_a, "mygroup")
        serializer.deserializeFromHdf5(serialized, None)

        assert (
            ModelState(model_state=b"model_state", optimizer_state=b"optimizer_state")
            == op_a.Out.value
        )

    def test_consecutive_serialization(self, graph, serializer, serialized, op):
        op.Out.setValue(ModelState(model_state=b""))

        serializer.serializeToHdf5(serialized, None)
        serializer.deserializeFromHdf5(serialized, None)

        assert not op.Out.value

    def test_serialization_with_null_bytes(self, serializer, outfile, op):
        state = ModelState(
            model_state=b"\x00null0testestset", optimizer_state=b"\x00null1"
        )
        op.Out.setValue(state)

        serializer.serializeToHdf5(outfile, None)
        op.Out.setValue(None)
        serializer.deserializeFromHdf5(outfile, None)

        assert state is not op.Out.value
        assert state == op.Out.value


class TestListModelStateSlotSerialization:
    class NNSerializer(AppletSerializer):
        def __init__(self, topLevelOperator, projectFileGroupName):
            self.VERSION = 1

            slots = [SerialListModelStateSlot(topLevelOperator.Out)]

            super().__init__(projectFileGroupName, slots)

    class OpA(Operator):
        Out = OutputSlot(stype=stype.Opaque)

        def setupOutputs(self):
            self.Out.meta.shape = (1,)
            self.Out.meta.dtype = object

        def execute(self, *args, **kwargs):
            pass

        def propagateDirty(self, *args, **kwargs):
            pass

    @pytest.fixture
    def op(self, graph):
        op = self.OpA(graph=graph)
        op.Out.setValue(
            ModelState(model_state=b"model_state", optimizer_state=b"optimizer_state")
        )
        return op

    @pytest.fixture
    def serializer(self, op):
        return self.NNSerializer(op, "mygroup")

    def test_serialize_deserialize(self, outfile, op, serializer):
        states = [
            ModelState(
                model_state=b"\x00null0testestset",
                optimizer_state=b"\x00null1",
                epoch=100,
                loss=0.1,
            ),
            ModelState(
                model_state=b"f" * 200,
                optimizer_state=b"\x00null1",
                epoch=1292,
                loss=1e-3,
            ),
            ModelState(model_state=b"fdas", optimizer_state=b"", epoch=1, loss=np.inf),
        ]

        op.Out.setValue(states)
        serializer.serializeToHdf5(outfile, None)
        op.Out.setValue(None)
        serializer.deserializeFromHdf5(outfile, None)
        assert states == op.Out.value

    def test_serialize_deserialize_empty(self, outfile, op, serializer):
        op.Out.setValue([])

        serializer.serializeToHdf5(outfile, None)
        op.Out.setValue(None)
        serializer.deserializeFromHdf5(outfile, None)

        assert [] == op.Out.value
