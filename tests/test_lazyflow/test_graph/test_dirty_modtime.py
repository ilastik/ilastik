from lazyflow.graph import Operator, InputSlot, OutputSlot

from unittest import mock
import pytest


class MockOp(Operator):
    Input = InputSlot(value=(10,))
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(())

    def execute(self, slot, subindex, roi):
        pass


def test_op_mod_time(graph):
    """setDirty _mod_time modifies parent op correctly"""
    op = MockOp(graph=graph)

    assert op._pending_dirty_mod_time == -1

    for mod_time in (1, 2, 13, 42):
        op.Input.setDirty((), _mod_time=mod_time)
        assert op._previous_dirty_mod_time_buffer == mod_time
        assert op._pending_dirty_mod_time == -1


def test_op_lower_mod_time_does_not_modify(graph):
    """setDirty _mod_time modifies parent op correctly"""
    op = MockOp(graph=graph)

    assert op._pending_dirty_mod_time == -1

    op.Input.setDirty((), _mod_time=42)
    assert op._previous_dirty_mod_time_buffer == 42
    assert op._pending_dirty_mod_time == -1

    op.Input.setDirty((), _mod_time=41)
    assert op._previous_dirty_mod_time_buffer == 42
    assert op._pending_dirty_mod_time == -1


def test_op_mod_time_chain(graph):
    """mod_time is propagated to all ops in the chain"""
    op1 = MockOp(graph=graph)
    op2 = MockOp(graph=graph)
    op2.Input.connect(op1.Output)

    assert op1._previous_dirty_mod_time_buffer == -1
    assert op2._previous_dirty_mod_time_buffer == -1

    for mod_time in (1, 2, 13, 42):
        op1.Input.setDirty((), _mod_time=mod_time)
        assert op1._previous_dirty_mod_time_buffer == mod_time
        assert op2._previous_dirty_mod_time_buffer == mod_time
        assert op1._pending_dirty_mod_time == -1
        assert op2._pending_dirty_mod_time == -1


def test_op_mod_time_source(graph):
    """setDirty on Input should always modify OPs ._previous_dirty_mod_time_buffer"""
    op = MockOp(graph=graph)

    assert op._previous_dirty_mod_time_buffer == -1
    assert op._pending_dirty_mod_time == -1

    op.Input.setDirty(())

    assert op._previous_dirty_mod_time_buffer > -1


def test_op_output_dirty(graph):
    """setDirty on output should not modify OPs ._previous_dirty_mod_time_buffer"""
    op = MockOp(graph=graph)

    assert op._previous_dirty_mod_time_buffer == -1

    op.Output.setDirty(())

    assert op._previous_dirty_mod_time_buffer == -1


class SourceOp(Operator):
    Input = InputSlot(value=(10,))

    Output1 = OutputSlot()
    Output2 = OutputSlot()

    def setupOutputs(self):
        self.Output1.meta.assignFrom(self.Input.meta)
        self.Output2.meta.assignFrom(self.Input.meta)

    def propagateDirty(self, slot, subindex, roi):
        self.Output1.setDirty()
        self.Output2.setDirty()

    def execute(self, slot, subindex, roi):
        pass


class AllDirtyOp(Operator):
    Input1 = InputSlot()
    Input2 = InputSlot()

    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input1.meta)

    def propagateDirty(self, slot, subindex, roi):
        self.propagateDirtyIfNewModTime()

    def execute(self, slot, subindex, roi):
        pass


def test_op_all_dirty(graph):
    """using propagateDirtyIfNewModTime prevents subsequent dirty-prop with same mod_time"""
    op_source = SourceOp(graph=graph)

    op_all_dirty = AllDirtyOp(graph=graph)

    dirty_cb = mock.Mock()
    op_all_dirty.Output.notifyDirty(dirty_cb)

    op_all_dirty.Input1.connect(op_source.Output1)
    op_all_dirty.Input2.connect(op_source.Output2)

    op_source.Input.setDirty((), _mod_time=42)

    dirty_cb.assert_called_once()
    assert op_all_dirty._previous_dirty_mod_time_buffer == 42


class MockOpLastDirty(Operator):
    Input = InputSlot(value=(10,))
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._previous_dirty_mod_time_buffer = 13

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)

    def propagateDirty(self, slot, subindex, roi):
        assert self._previous_dirty_mod_time_buffer == 13
        self.Output.setDirty(())

    def execute(self, slot, subindex, roi):
        pass


def test_previous_dirty_mod_time_buffer_set(graph):
    op = MockOpLastDirty(graph=graph)
    assert op._pending_dirty_mod_time == -1
    assert op._previous_dirty_mod_time_buffer == 13

    op.Input.setDirty((), _mod_time=42)
    assert op._pending_dirty_mod_time == -1
    assert op._previous_dirty_mod_time_buffer == 42


class MockOpLastDirtyEx(MockOpLastDirty):
    def propagateDirty(self, slot, subindex, roi):
        assert self._previous_dirty_mod_time_buffer == 13
        self.Output.setDirty(())
        raise ValueError()


def test_previous_dirty_mod_time_buffer_ex(graph):
    op = MockOpLastDirtyEx(graph=graph)
    assert op._pending_dirty_mod_time == -1
    assert op._previous_dirty_mod_time_buffer == 13

    with pytest.raises(ValueError):
        op.Input.setDirty((), _mod_time=42)

    assert op._pending_dirty_mod_time == -1
    assert op._previous_dirty_mod_time_buffer == 42
