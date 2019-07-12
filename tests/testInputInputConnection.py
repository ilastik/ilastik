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
import nose
from lazyflow.graph import Graph, Operator, Slot, InputSlot, OutputSlot, OperatorWrapper
from lazyflow import stype
from lazyflow import operators

import logging

logger = logging.getLogger()


class OpB(Operator):

    Input = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.shape = self.Input.meta.shape
        self.Output.meta.dtype = self.Input.meta.dtype
        # print "OpInternal shape=%r, dtype=%r" % (self.Input.meta.shape, self.Input.meta.dtype)

    def execute(self, slot, subindex, roi, result):
        result[0] = self.Input[:].wait()[0]
        return result

    def propagateDirty(self, inputSlot, subindex, roi):
        self.Output.setDirty(roi)


class OpA(Operator):

    Input = InputSlot()
    Output = OutputSlot()

    def __init__(self, parent=None, graph=None):
        Operator.__init__(self, parent, graph)
        self.internalOp = OpB(self)
        self.internalOp.Input.connect(self.Input)
        self.inputBackup = self.Input

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.shape = self.Input.meta.shape
        self.Output.meta.dtype = self.Input.meta.dtype
        # print "OpA shape=%r, dtype=%r" % (self.Input.meta.shape, self.Input.meta.dtype)

    def execute(self, slot, subindex, roi, result):
        result[0] = self.internalOp.Output[:].wait()[0]
        return result

    def propagateDirty(self, inputSlot, subindex, roi):
        self.Output.setDirty(roi)


class OpDummyOutputResize(Operator):
    """Operator with level 1 output slot, with size corresponding to OutputSize

    acts as an internal operator for OperatorWrapper, primarily used to check
    whether slots in OperatorWrapper follow the resizing of the inner ones
    """

    OutputSize = InputSlot(value=0)
    Output = OutputSlot(level=1)

    def setupOutputs(self):
        n_output_slots = self.OutputSize.value

        self.Output.resize(n_output_slots)

        for i in range(n_output_slots):
            self.Output[i].setValue(i)

    def propagateDirty(self, inputSlot, subindex, roi):
        self.Output.setDirty([])


class TestInputInputConnection(object):
    def setup_method(self, method):
        self.g = Graph()
        self.op = OpA(graph=self.g)

    def test_value(self):
        self.op.Input.setValue(True)
        result = self.op.Output[:].wait()[0]
        assert result == True, "result = %r" % result
        self.op.Input.setValue(False)
        result = self.op.Output[:].wait()[0]
        assert result == False, "result = %r" % result

    def test_none(self):
        self.op.Input.setValue(None)
        # Should not crash.
        caught_exception = False
        try:
            result = self.op.Output[:].wait()[0]
        except Slot.SlotNotReadyError:
            caught_exception = True
        assert caught_exception
        assert not self.op.Input.ready()

    def test_value_none(self):
        self.op.Input.setValue(True)
        result = self.op.Output[:].wait()[0]
        assert result == True, "result = %r" % result

        self.op.Input.setValue(None)
        # Should not crash.
        caught_exception = False
        try:
            result = self.op.Output[:].wait()[0]
        except Slot.SlotNotReadyError:
            caught_exception = True
        assert caught_exception
        assert not self.op.Input.ready()

    def test_value_none_value(self):
        self.op.Input.setValue(True)
        result = self.op.Output[:].wait()[0]
        assert result == True, "result = %r" % result

        self.op.Input.setValue(None)
        # Should not crash.
        caught_exception = False
        try:
            result = self.op.Output[:].wait()[0]
        except Slot.SlotNotReadyError:
            caught_exception = True
        assert caught_exception
        assert not self.op.Input.ready()

        self.op.Input.setValue(True)
        result = self.op.Output[:].wait()[0]
        assert result == True, "result = %r" % result

    def test_disconnect(self):
        self.op.internalOp.Input.disconnect()
        self.op.internalOp.Input.connect(self.op.Input)

    def test_wrapping(self):
        opm = OpDummyOutputResize(graph=self.g)
        opm.OutputSize.setValue(1)

        op = OperatorWrapper(OpA, graph=self.g)
        op.Input.connect(opm.Output)
        result = op.Output[0][:].wait()[0]
        assert result == 0

        opm.OutputSize.setValue(2)
        result = op.Output[1][:].wait()[0]
        assert result == 1

        # Note: operator wrappers do not "restore" back to unwrapped operators after disconnect
        # (That was their behavior at some point, but no longer.)
        op.Input.disconnect()
        op.Input.resize(0)
        op.Input.setValue(2)
        assert len(op.Input) == 0
        assert len(op.Output) == 0


class OpC(Operator):

    Input = InputSlot(level=1)
    Output = OutputSlot(level=1)

    def __init__(self, parent=None, graph=None):
        Operator.__init__(self, parent, graph)
        self.internalOp = OperatorWrapper(OpB, graph=self.graph)
        self.internalOp.Input.connect(self.Input)
        self.inputBackup = self.Input

    def setupOutputs(self):
        numSlots = len(self.Input)
        self.Output.resize(numSlots)
        for i, slot in enumerate(self.Output):
            slot.meta.shape = self.Input[i].meta.shape
            slot.meta.dtype = self.Input[i].meta.dtype

    def execute(self, slot, subindex, roi, result):
        result[0] = self.internalOp.Output[:].wait()[0]
        return result


class TestMultiInputInputConnection(object):
    def setup_method(self, method):
        self.g = Graph()
        self.op = OpC(graph=self.g)

    def test_wrapping(self):
        opm = OpDummyOutputResize(graph=self.g)
        opm.OutputSize.setValue(1)

        self.op.Input.connect(opm.Output)

        assert len(self.op.internalOp.Output) == 1
        assert self.op.internalOp.Output[0].meta.shape is not None
        assert self.op.internalOp.Output[0].value == 0


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
