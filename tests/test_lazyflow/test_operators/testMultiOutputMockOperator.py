from lazyflow.utility.testing import build_multi_output_mock_op, SlotDescription
from lazyflow.graph import Operator, OutputSlot
import numpy
import pytest
import vigra


def test_empty(graph):
    op = build_multi_output_mock_op(dict(), graph)

    assert isinstance(op, Operator)
    assert len(op.inputs) == 0
    assert len(op.outputs) == 0


def test_single_default_slot(graph):
    op = build_multi_output_mock_op({"Output": SlotDescription()}, graph)

    assert len(op.inputs) == 0
    assert len(op.outputs) == 1
    assert isinstance(op.Output, OutputSlot)
    assert op.Output.ready()
    assert op.Output.level == 0


def test_multiple_default_slots(graph):
    op = build_multi_output_mock_op({"Output0": SlotDescription(), "Output1": SlotDescription()}, graph)

    assert len(op.inputs) == 0
    assert len(op.outputs) == 2
    assert op.Output0.ready()
    assert op.Output1.ready()
    assert op.Output0.level == 0
    assert op.Output1.level == 0
    assert op.Output0 != op.Output1


def test_multi_lane_slot(graph):
    op = build_multi_output_mock_op({"Output": SlotDescription(level=1)}, graph)

    assert op.Output.level == 1


def test_multi_lane_slot_w_lanes(graph):
    op = build_multi_output_mock_op({"Output": SlotDescription(level=1)}, graph, n_lanes=42)

    assert op.Output.level == 1
    assert len(op.Output) == 42
    assert all(subslot.ready() for subslot in op.Output)


def test_all_meta_w_lanes(graph):
    op = build_multi_output_mock_op(
        {
            "Lvl0": SlotDescription(level=0, shape=(10, 42), axistags=vigra.defaultAxistags("xy"), dtype=numpy.uint8),
            "Lvl1": SlotDescription(
                level=1, shape=(10, 42, 100), axistags=vigra.defaultAxistags("xyz"), dtype=numpy.float32
            ),
        },
        graph,
        n_lanes=12,
    )

    assert op.Lvl0.level == 0
    assert op.Lvl1.level == 1

    assert op.Lvl0.ready()
    assert all(subslot.ready() for subslot in op.Lvl1)

    assert op.Lvl0.meta.shape == (10, 42)
    assert all(subslot.meta.shape == (10, 42, 100) for subslot in op.Lvl1)

    assert op.Lvl0.meta.getAxisKeys() == ["x", "y"]
    assert all(subslot.meta.getAxisKeys() == ["x", "y", "z"] for subslot in op.Lvl1)


def test_data_access_lvl0(graph):
    op = build_multi_output_mock_op({"Output": SlotDescription(data=numpy.array([42]))}, graph)

    assert op.Output.value == 42
