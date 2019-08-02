from builtins import range
from builtins import object

###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
# 		   http://ilastik.org/license/
###############################################################################

import weakref
import gc
import time
import types

from unittest import mock

from lazyflow import graph
from lazyflow import stype
from lazyflow import slot
from lazyflow import operators
from lazyflow import operator
from lazyflow.graph import OperatorWrapper

import numpy
import pytest


class OpA(graph.Operator):
    name = "OpA"

    Input1 = graph.InputSlot()  # required slot
    Input2 = graph.InputSlot(optional=True)  # optional slot
    Input3 = graph.InputSlot(value=3)  # required slot with default value, i.e. already connected
    Input4 = graph.InputSlot(level=1)  # required slot with default value, i.e. already connected

    Output1 = graph.OutputSlot()
    Output2 = graph.OutputSlot()
    Output3 = graph.OutputSlot()

    def __init__(self, *args, **kwargs):
        graph.Operator.__init__(self, *args, **kwargs)
        self._configured = False

    def setupOutputs(self):
        self._configured = True
        self.Output1.meta.shape = self.Input1.meta.shape
        self.Output1.meta.dtype = self.Input1.meta.dtype
        self.Output2.meta.shape = self.Input1.meta.shape
        self.Output2.meta.dtype = self.Input1.meta.dtype
        self.Output3.meta.shape = self.Input1.meta.shape
        self.Output3.meta.dtype = self.Input1.meta.dtype
        # print "OpInternal shape=%r, dtype=%r" % (self.Input1.meta.shape, self.Input1.meta.dtype)

    def execute(self, slot, subindex, roi, result):
        if slot == self.Output1:
            result[0] = self.Input1[:].wait()[0]
        elif slot == self.Output2:
            result[0] = self.Input2[:].wait()[0]
        elif slot == self.Output3:
            result[0] = self.Input3[:].wait()[0]
        return result

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot == self.Input1:
            self.Output1.setDirty(roi)
        if inputSlot == self.Input1:
            self.Output2.setDirty(roi)
        if inputSlot == self.Input3:
            self.Output3.setDirty(roi)


class OpTesting5ToMulti(graph.Operator):
    name = "OpTesting5ToMulti"

    Input0 = graph.InputSlot(optional=True)
    Input1 = graph.InputSlot(optional=True)
    Input2 = graph.InputSlot(optional=True)
    Input3 = graph.InputSlot(optional=True)
    Input4 = graph.InputSlot(optional=True)
    Outputs = graph.OutputSlot(level=1)

    def setupOutputs(self):
        length = 0
        for slot in list(self.inputs.values()):
            if slot.connected():
                length += 1

        self.outputs["Outputs"].resize(length)

        i = 0
        for sname in sorted(self.inputs.keys()):
            slot = self.inputs[sname]
            if slot.connected():
                self.outputs["Outputs"][i].meta.assignFrom(slot.meta)
                i += 1

    def execute(self, slot, subindex, roi, result):
        key = roiToSlice(roi.start, roi.stop)
        index = subindex[0]
        i = 0
        for sname in sorted(self.inputs.keys()):
            slot = self.inputs[sname]
            if slot.connected():
                if i == index:
                    return slot[key].wait()
                i += 1

    def propagateDirty(self, islot, subindex, roi):
        i = 0
        for sname in sorted(self.inputs.keys()):
            slot = self.inputs[sname]
            if slot == islot:
                self.outputs["Outputs"][i].setDirty(roi)
                break
            if slot.connected():
                self.outputs["Outputs"][i].meta.assignFrom(slot.meta)
                i += 1


class TestOperator_setupOutputs(object):
    def setup_method(self, method):
        self.g = graph.Graph()

    def test_disconnected_connected(self):
        # check that operator is not configuerd initiallia
        # since it has a slot without default value
        op = OpA(graph=self.g)
        assert op._configured == False

        # check that operator is not configuerd initiallia
        op.Input1.setValue(1)
        assert op._configured == False

        # check that the operator is configued
        # after connecting the slot without default value
        op.Input1.setValue(1)
        op.Input4.setValues([1, 2])
        assert op._configured == True
        op._configured = False

        # check that the operatir is reconfigured
        # when connecting the slot with default value
        # to another value
        op.Input3.setValue(2)
        assert op._configured == True

    def test_set_values(self):
        op = OpA(graph=self.g)

        # check that Input4 is not connected
        assert op.Input4.connected() is False

        op.Input4.setValues([1])

        # check that the length of Input4 is 1
        assert len(op.Input4) == 1

        # check that Input4 is now connected and configured
        assert op.Input4.connected()
        assert op.Input4.configured()

        # check that the length of Input4 is 2
        op.Input4.setValues([1, 2])
        assert len(op.Input4) == 2

        # check that the values of the subslots are correct
        assert op.Input4[0].value == 1
        assert op.Input4[1].value == 2

        # check that the normal setValue propagates to all subslots
        op.Input4.setValue(3)
        assert len(op.Input4) == 2
        assert op.Input4[0].value == 3
        assert op.Input4[1].value == 3

    def test_default_value(self):
        op = OpA(graph=self.g)
        op.Input1.setValue(1)
        op.Input4.setValues([1])

        # check that the slot with default value
        # returns the correct value
        result = op.Output3[:].wait()[0]
        assert result == 3

        # check that the slot with default value
        # returns the new value when it is connected
        # to something else
        op.Input3.setValue(2)
        result = op.Output3[:].wait()[0]
        assert result == 2

    def test_connect_propagate(self):
        # check that connecting a required slot to an
        # already configured slots notifes the operator
        # of connecting
        op1 = OpA(graph=self.g)
        op1.Input1.setValue(1)
        op1.Input4.setValues([1])
        op2 = OpA(graph=self.g)
        op2.Input1.connect(op1.Output1)
        op2.Input4.setValues([1])
        assert op2._configured == True

    def test_deferred_connect_propagate(self):
        # check that connecting a required slot to an
        # not yet  configured slots notifes the operator
        # of connecting after configuring the first operator
        # in the chain
        op1 = OpA(graph=self.g)
        op1.Input4.setValues([1])
        op2 = OpA(graph=self.g)
        op2.Input1.connect(op1.Output1)
        op2.Input4.setValues([1])
        assert op2._configured == False
        op1.Input1.setValue(1)
        assert op2._configured == True


class OpMultiOutput(graph.Operator):
    Input = graph.InputSlot()
    Outputs = graph.OutputSlot(level=3)

    def __init__(self, *args, **kwargs):
        super(OpMultiOutput, self).__init__(*args, **kwargs)

    def setupOutputs(self):
        self.Outputs.resize(4)
        for i, s in enumerate(self.Outputs):
            s.resize(4)
            for j, t in enumerate(s):
                t.resize(4)
                for k, u in enumerate(t):
                    u.meta.assignFrom(self.Input.meta)

    def execute(self, slot, subindex, roi, result):
        """Result of the output slot is the subslot's subindex."""
        assert slot == self.Outputs
        result[0] = subindex
        return result

    def propagateDirty(self, inputSlot, subindex, roi):
        pass


class TestOperatorMultiSlotExecute(object):
    def setup(self):
        self.g = graph.Graph()

    def test(self):
        op = OpMultiOutput(graph=self.g)
        op.Input.setValue(())
        # Index the output slot with every possible getitem syntax that we support
        assert op.Outputs[1][2][3][...].wait()[0] == (1, 2, 3)
        assert op.Outputs[3, 2, 1][...].wait()[0] == (3, 2, 1)
        assert op.Outputs[(2, 1, 3)][...].wait()[0] == (2, 1, 3)


class TestOperator_meta(object):
    def setup_method(self, method):
        self.g = graph.Graph()

    def test_meta_propagate(self):
        # check that connecting a required slot to an
        # already configured slots notifes the operator
        # of connecting and the meta information of
        # is correctly passed on between the slots
        op1 = OpA(graph=self.g)
        op1.Input1.setValue(numpy.ndarray((10,)))
        op1.Input4.setValues([1])
        op2 = OpA(graph=self.g)
        op2.Input1.connect(op1.Output1)
        op2.Input4.setValues([1])
        assert op2.Output1.meta.shape == (10,)

    def test_deferred_meta_propagate(self):
        # check that connecting a required slot to an
        # not yet  configured slots notifes the operator
        # of connecting after configuring the first operator
        # and propagates the meta information correctly
        # between the slots
        op1 = OpA(graph=self.g)
        op2 = OpA(graph=self.g)
        op1.Input4.setValues([1, 2])
        op2.Input4.setValues([1, 2])
        op2.Input1.connect(op1.Output1)
        op1.Input1.setValue(numpy.ndarray((10,)))
        assert op2.Output1.meta.shape == (10,)
        op1.Input1.setValue(numpy.ndarray((20,)))
        assert op2.Output1.meta.shape == (20,)


class OpWithMultiInputs(graph.Operator):
    Input = graph.InputSlot(level=1)
    Output = graph.OutputSlot(level=1)

    def setupOutputs(self):
        self.Output.resize(len(self.Input))

    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()
        index = subindex[0]
        if slot.name == "Output":
            result[...] = self.Input[index][key]


class TestMultiSlotResize(object):
    def setup_method(self, method):
        self.g = graph.Graph()
        self.op1 = OpWithMultiInputs(graph=self.g)
        self.op2 = OpWithMultiInputs(graph=self.g)

        self.wrappedOp = OperatorWrapper(OpA, graph=self.g)

        self.wrappedOp.Input1.connect(self.op1.Input)
        self.wrappedOp.Input2.connect(self.op2.Input)

    def testResizeToSmaller(self):
        self.op1.Input.resize(5)
        self.op1.Input.resize(0)

    def testDefaultValuesInWrappedOperator(self):
        self.op1.Input.resize(1)
        assert self.wrappedOp.Input3.value == 3


class OpDirectConnection(graph.Operator):
    Input = graph.InputSlot()
    Output = graph.OutputSlot()

    def propagateDirty(self, inputSlot, subindex, roi):
        pass

    def setupOutputs(self):
        self.Output.connect(self.Input)


class TestSlotStates(object):
    def setup(self):
        self.g = graph.Graph()

    def teardown(self):
        pass

    def test_directlyConnectedOutputs(self):
        op = OpDirectConnection(graph=self.g)

        assert not op.Input.connected()
        assert not op.Output.connected()

        assert not op.Input.ready()
        assert not op.Output.ready()

        connectedSlots = {op.Input: False, op.Output: False}

        def handleConnect(slot):
            connectedSlots[slot] = True

        # Test notifyConnect
        op.Input._notifyConnect(handleConnect)
        op.Output._notifyConnect(handleConnect)

        readySlots = {op.Input: False, op.Output: False}

        def handleReady(slot):
            readySlots[slot] = True

        # Test notifyReady
        op.Input.notifyReady(handleReady)
        op.Output.notifyReady(handleReady)

        data = numpy.zeros((10, 10, 10, 10, 10))
        op.Input.setValue(data)

        assert op.Input.ready()
        assert op.Output.ready()

        assert op.Input.connected()
        assert op.Output.connected()

        assert connectedSlots[op.Input] == True
        assert connectedSlots[op.Output] == True

    def test_implicitlyConnectedOutputs(self):
        # The array piper copies its input to its output, creating an "implicit" connection
        op = operators.OpArrayPiper(graph=self.g)

        assert not op.Input.connected()
        assert not op.Output.connected()

        assert not op.Input.ready()
        assert not op.Output.ready()

        connectedSlots = {op.Input: False, op.Output: False}

        def handleConnect(slot):
            connectedSlots[slot] = True

        # Test notifyConnect
        op.Input._notifyConnect(handleConnect)
        op.Output._notifyConnect(handleConnect)

        readySlots = {op.Input: False, op.Output: False}

        def handleReady(slot):
            readySlots[slot] = True

        # Test notifyReady
        op.Input.notifyReady(handleReady)
        op.Output.notifyReady(handleReady)

        data = numpy.zeros((10, 10, 10, 10, 10))
        op.Input.setValue(data)

        assert op.Input.ready()
        assert op.Output.ready()

        assert op.Input.connected()
        assert not op.Output.connected()  # Not connected

        assert connectedSlots[op.Input] == True
        assert connectedSlots[op.Output] == False

        assert readySlots[op.Input] == True
        assert readySlots[op.Output] == True

    def test_implicitlyConnectedMultiOutputs(self):
        # The array piper copies its input to its output, creating an "implicit" connection
        op = OpTesting5ToMulti(graph=self.g)

        assert not op.Input0.connected()
        assert not op.Outputs.connected()

        assert not op.Input0.ready()
        assert not op.Outputs.ready()

        connectedSlots = set()

        def handleConnect(slot):
            connectedSlots.add(slot)

        # Test notifyConnect
        op.Input0._notifyConnect(handleConnect)
        op.Outputs._notifyConnect(handleConnect)

        readySlots = set()

        def handleReady(slot):
            readySlots.add(slot)

        # Test notifyReady
        op.Input0.notifyReady(handleReady)
        op.Outputs.notifyReady(handleReady)

        def subscribeToReady(slot, index, *args):
            slot[index].notifyReady(handleReady)

        op.Outputs.notifyInserted(subscribeToReady)

        data = numpy.zeros((10, 10, 10, 10, 10))
        op.Input0.setValue(data)

        assert op.Input0.ready()
        assert op.Outputs.ready()

        assert op.Input0.connected()
        assert not op.Outputs.connected()  # Not connected

        assert op.Input0 in connectedSlots
        assert op.Outputs not in connectedSlots  # Not connected
        assert op.Outputs[0] not in connectedSlots

        assert op.Input0 in readySlots
        assert op.Outputs in readySlots
        assert op.Outputs[0] in readySlots

    def test_clonedSlotState(self):
        """
        Create a graph that involves "cloned" inputs and outputs,
        and verify that their states are changed correctly at the correct times, with callbacks.
        """
        # The array piper copies its input to its output, creating an "implicit" connection
        op = operators.OpArrayPiper(graph=self.g)

        # op2 gets his input as a clone from op.Input
        op2 = operators.OpArrayPiper(graph=self.g)
        op2.Input.connect(op.Input)

        # op3 gets his input as a clone from op.Output
        op3 = operators.OpArrayPiper(graph=self.g)
        op3.Input.connect(op.Output)

        assert not op.Input.connected()
        assert not op.Output.connected()

        assert not op.Input.ready()
        assert not op.Output.ready()
        assert not op2.Input.ready()
        assert not op2.Output.ready()
        assert not op3.Input.ready()
        assert not op3.Output.ready()

        connectedSlots = {op.Input: False, op.Output: False}

        def handleConnect(slot):
            connectedSlots[slot] = True

        # Test notifyConnect
        op.Input._notifyConnect(handleConnect)
        op.Output._notifyConnect(handleConnect)

        readySlots = {op.Input: False, op.Output: False}

        def handleReady(slot):
            readySlots[slot] = True

        # Test notifyReady
        op.Input.notifyReady(handleReady)
        op.Output.notifyReady(handleReady)
        op2.Input.notifyReady(handleReady)
        op2.Output.notifyReady(handleReady)
        op3.Input.notifyReady(handleReady)
        op3.Output.notifyReady(handleReady)

        # This should trigger setupOutputs and everything to become ready
        data = numpy.zeros((10, 10, 10, 10, 10))
        op.Input.setValue(data)

        assert op.Input.ready()
        assert op.Output.ready()
        assert op2.Input.ready()
        assert op2.Output.ready()
        assert op3.Input.ready()
        assert op3.Output.ready()

        assert op.Input.connected()
        assert not op.Output.connected()  # Not connected

        assert connectedSlots[op.Input] == True
        assert connectedSlots[op.Output] == False

        assert readySlots[op.Input] == True
        assert readySlots[op.Output] == True
        assert readySlots[op2.Input] == True
        assert readySlots[op2.Output] == True
        assert readySlots[op3.Input] == True
        assert readySlots[op3.Output] == True

    def test_unready_propagation(self):
        # The array piper copies its input to its output, creating an "implicit" connection
        op = operators.OpArrayPiper(graph=self.g)
        op.name = "op"

        # op2 gets his input as a clone from op.Input
        op2 = operators.OpArrayPiper(graph=self.g)
        op2.Input.connect(op.Input)
        op2.name = "op2"

        # op3 gets his input as a clone from op.Output
        op3 = operators.OpArrayPiper(graph=self.g)
        op3.Input.connect(op.Output)
        op3.name = "op3"

        #
        # op.Input  --> op2.Input
        #   .Output --> op3.Input
        #

        # This should trigger setupOutputs and everything to become ready
        data = numpy.zeros((10, 10, 10, 10, 10))
        op.Input.setValue(data)

        assert op.Input.ready()
        assert op.Output.ready()
        assert op2.Input.ready()
        assert op2.Output.ready()
        assert op3.Input.ready()
        assert op3.Output.ready()

        assert op.Input.connected()
        assert not op.Output.connected()  # Not connected

        # Disonnecting the head of the chain should cause everything to become unready
        op.Input.disconnect()

        assert not op.Input.ready()
        assert not op.Output.ready()
        assert not op2.Input.ready()
        assert not op2.Output.ready()
        assert not op3.Input.ready()
        assert not op3.Output.ready()

    def test_slicing(self):
        op = operators.OpArrayPiper(graph=self.g)

        a = numpy.zeros(5 * (10,), dtype=int)
        op.Input.setValue(a)

        b = op.Output[:, :, :].wait()
        assert b.shape == a.shape

    def testIssue130(self):
        # Verify the fix for issue ilastik/lazyflow#130
        op = operators.OpArrayPiper(graph=self.g)

        dirty_flag = [False]

        def handleDirty(*args):
            dirty_flag[0] = True

        op.Input.notifyDirty(handleDirty)

        a = numpy.zeros(5 * (10,), dtype=int)
        op.Input.setValue(a)
        dirty_flag[0] = False

        # If setting the same value, still not dirty...
        op.Input.setValue(a)
        assert dirty_flag[0] is False

        # Now if we set an array with different shape, but still broadcastable to the original,
        #  dirtiness should be detected.
        a = numpy.zeros(4 * (10,) + (1,), dtype=int)
        op.Input.setValue(a)
        assert dirty_flag[0] is True


class OpSimple(graph.Operator):
    Input = graph.InputSlot()
    Output = graph.OutputSlot()

    def setupOutputs(self):
        pass


class TestOperatorCleanup(object):
    def testSimpleCleanup(self):
        g = graph.Graph()
        op = OpSimple(graph=g)
        r = weakref.ref(op)
        del op
        gc.collect()
        assert r() is None, "cleanup failed"

    def testConnectedCleanup(self):
        g = graph.Graph()
        op1 = OpSimple(graph=g)
        op2 = OpSimple(graph=g)

        op2.Input.connect(op1.Output)
        op2.Input.disconnect()
        # op2.cleanUp()

        r = weakref.ref(op2)
        del op2
        gc.collect()
        assert r() is None, "cleanup failed"


class TransactionOp(graph.Operator):
    Input1 = graph.InputSlot()  # required slot
    Input2 = graph.InputSlot(optional=True)  # optional slot
    Input3 = graph.InputSlot(value=3)  # required slot with default value, i.e. already connected

    Output1 = graph.OutputSlot()

    setupOutputs = mock.Mock()

    def propagateDirty(self, slot, roid, index):
        pass


class TestTransaction:
    def testTransactionMultipleSetsOnSameSlot(self):
        g = graph.Graph()
        op = TransactionOp(graph=g)

        with op.transaction:
            op.Input1.setValue("val1")
            op.Input1.setValue("val2")

        op.setupOutputs.assert_called_once()

    def testTransactionSetMultipleSlots(self):
        input1, input2 = None, None

        def fetch_values(self, *args, **kwargs):
            nonlocal input1, input2
            input1 = self.Input1.value
            input2 = self.Input2.value

        g = graph.Graph()
        op = TransactionOp(graph=g)

        setup_mock = mock.Mock()
        setup_mock.side_effect = fetch_values

        op.setupOutputs = types.MethodType(setup_mock, op)

        with op.transaction:
            op.Input1.setValue("val1")
            op.Input2.setValue("val2")

        op.setupOutputs.assert_called_once()
        assert input1 == "val1"
        assert input2 == "val2"

    def testNestedTransactionFails(self):
        g = graph.Graph()
        op = TransactionOp(graph=g)

        with op.transaction:
            op.Input1.setValue("val1")

            with pytest.raises(AssertionError):
                with op.transaction:
                    op.Input2.setValue("val2")

    def test_chain(self):
        class OpA(graph.Operator):
            Input = graph.InputSlot()  # required slot

            def setupOutputs(self):
                pass

            def propagateDirty(self, *a, **kw):
                pass

        class OpB(graph.Operator):
            Input = graph.InputSlot()  # required slot
            Output = graph.OutputSlot()

            setupOutputs = mock.Mock()

            def propagateDirty(self, *a, **kw):
                pass

        g = graph.Graph()

        op_a = OpA(graph=g)
        op_b = OpB(graph=g)

        op_b.Input.connect(op_a.Input)

        with op_a.transaction:
            op_a.Input.setValue("fadf")
            op_b.setupOutputs.assert_not_called()

        op_b.setupOutputs.assert_called_once()


class TestCompatibilityChecks:
    class OpA(graph.Operator):
        Output = graph.OutputSlot(stype=stype.ArrayLike)
        OutputOpaque = graph.OutputSlot(stype=stype.Opaque)
        OutputList = graph.OutputSlot(stype=stype.ArrayLike)
        OutputUnsupportedType = graph.OutputSlot(stype=stype.ArrayLike)

        def setupOutputs(self):
            self.Output.meta.shape = (3, 3)
            self.Output.meta.dtype = int
            self.OutputOpaque.meta.shape = (1,)
            self.OutputOpaque.meta.dtype = object
            self.OutputList.meta.shape = (10,)
            self.OutputList.meta.dtype = object
            self.OutputUnsupportedType.meta.shape = (10,)
            self.OutputUnsupportedType.meta.dtype = object

        def propagateDirty(self, *a, **kw):
            pass

        def execute(self, slot, *args, **kwargs):
            if slot == self.OutputList:
                return [1, 2, 3]

            elif slot == self.OutputOpaque:
                return object()

            elif slot == self.OutputUnsupportedType:
                return object()

            else:
                return numpy.ones((2, 2), dtype=int)

    @pytest.fixture
    def op(self, graph):
        return self.OpA(graph=graph)

    def test_arraylike_raises_if_shapes_are_mismatched(self, op):
        with pytest.raises(stype.InvalidResult):
            op.Output[:].wait()

        op.execute = lambda *a, **kw: numpy.ones((3, 3), dtype=int)

        op.Output[:].wait()

    def test_arraylike_raises_if_list_shape_is_mismatched(self, op):
        with pytest.raises(stype.InvalidResult):
            res = op.OutputList[1:2].wait()

        assert op.OutputList[1:4].wait()

    def test_access_opaque_slot_value_should_not_raise_error(self, op):
        assert op.OutputOpaque.value

    def test_arraylike_retun_non_arraylike_object_raises(self, op):
        with pytest.raises(stype.InvalidResult):
            assert op.OutputUnsupportedType.value


class TestOperatorStackFormatter:
    class BrokenOp(operator.Operator):
        Out = slot.OutputSlot()

        def setupOutputs(self):
            self.Out.meta.shape = (1,)
            self.Out.meta.dtype = object

        def execute(self, *args, **kwargs):
            raise Exception()

        def propagateDirty(self, *args, **kwargs):
            pass

    def test_operator_except_formatting(self):
        op = self.BrokenOp(graph=graph.Graph())

        exc = None

        try:
            op.Out.value
        except Exception as e:
            exc = e

        assert exc

        stack = operator.format_operator_stack(exc.__traceback__)
        assert stack
        assert len(stack) == 1
        assert "TestOperatorStackFormatter.BrokenOp.execute" in stack[0]


def test_operator_str():
    g = graph.Graph()

    class OpA(graph.Operator):
        Input = graph.InputSlot(level=2)

    op = OpA(graph=g)
    op.Input.resize(2)

    assert "level=1" in str(op.Input[0])
    assert "index=(0,)" in str(op.Input[0])

    assert "len=2" in str(op.Input)
    assert "index" not in str(op.Input)


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)

    #    test = TestSlotStates()
    #    test.setup()
    #    test.test_implicitlyConnectedMultiOutputs()

    #    test = TestOperator_setupOutputs()
    #    test.setUp()
    #    test.test_disconnected_connected()

    if not ret:
        sys.exit(1)
