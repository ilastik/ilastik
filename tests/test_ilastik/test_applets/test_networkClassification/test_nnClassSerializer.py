import pytest

pytest.importorskip("lazyflow.operators.tiktorch")

from lazyflow.graph import Operator, InputSlot, OutputSlot, Graph
from lazyflow import stype
from ilastik.applets.networkClassification.nnClassSerializer import BinarySlot
from ilastik.applets.base.appletSerializer import AppletSerializer
from tiktorch.types import Model, ModelState
from tiktorch.rpc import RPCFuture

import h5py
import numpy as np


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

            slots = [BinarySlot(topLevelOperator.Out)]

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
        op.Out.setValue(b"value")
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

        assert b"value" == op_a.Out.value

    def test_consecutive_serialization(self, graph, serializer, serialized, op):
        op.Out.setValue(b"")

        serializer.serializeToHdf5(serialized, None)
        serializer.deserializeFromHdf5(serialized, None)

        assert not op.Out.value
        assert b"" == op.Out.value

    def test_serialization_with_embedded_nulls(self, op, outfile):
        op.Out.setValue(b"\x00nullbyteshere")
        serializer = self.NNSerializer(op, "mygroup")

        serializer.serializeToHdf5(outfile, None)
        serializer.deserializeFromHdf5(outfile, None)

        assert b"\x00nullbyteshere" == op.Out.value


