import pytest

from lazyflow.graph import Operator, InputSlot, OutputSlot, Graph
from ilastik.applets.networkClassification.nnClassSerializer import (
    SerialModelSlot,
    SerialModelStateSlot,
)
from ilastik.applets.base.appletSerializer import AppletSerializer
from tiktorch.types import Model, ModelState

import h5py

import json


@pytest.fixture
def graph():
    return Graph()


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
    def serialized(self, serializer, op):
        outfile = h5py.File("/tmp/data.h5", "w")

        serializer.serializeToHdf5(outfile, None)

        yield outfile

        outfile.close()

    def test_serialization(self, graph, serialized):
        # NOTE: Should we actually test internals of hdf5 file or does it break encapsulation?
        key_to_serialized = [("code", b"code"), ("config", b'{"val": 1}')]

        for key, serialized_value in key_to_serialized:
            assert serialized[f"mygroup/Out/{key}"][()] == serialized_value

    def test_deserializetion(self, graph, serialized):
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
    def serialized(self, serializer, op):
        outfile = h5py.File("/tmp/data.h5", "w")

        serializer.serializeToHdf5(outfile, None)

        yield outfile

        outfile.close()

    def test_deserializetion(self, graph, serialized):
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
