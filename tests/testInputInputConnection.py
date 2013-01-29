import nose
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow import stype
from lazyflow import operators

import logging
logger = logging.getLogger()
logger.addHandler( logging.NullHandler() )

class OpB(Operator):

    Input = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.shape = self.Input.meta.shape
        self.Output.meta.dtype = self.Input.meta.dtype
        print "OpInternal shape=%r, dtype=%r" % (self.Input.meta.shape, self.Input.meta.dtype)

    def execute(self, slot, subindex, roi, result):
        result[0] = self.Input[:].allocate().wait()[0]
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
        self.Output.meta.assignFrom( self.Input.meta )
        self.Output.meta.shape = self.Input.meta.shape
        self.Output.meta.dtype = self.Input.meta.dtype
        print "OpA shape=%r, dtype=%r" % (self.Input.meta.shape, self.Input.meta.dtype)


    def execute(self, slot, subindex, roi, result):
        result[0] = self.internalOp.Output[:].allocate().wait()[0]
        return result

    def propagateDirty(self, inputSlot, subindex, roi):
        self.Output.setDirty(roi)


class TestInputInputConnection(object):

    def setUp(self):
        self.g = Graph()
        self.op = OpA(graph=self.g)

    def tearDown(self):
        self.g.stopGraph()

    def test_value(self):
        self.op.Input.setValue(True)
        result = self.op.Output[:].allocate().wait()[0]
        assert result == True, "result = %r" % result
        self.op.Input.setValue(False)
        result = self.op.Output[:].allocate().wait()[0]
        assert result == False, "result = %r" % result

    def test_disconnect(self):
        self.op.internalOp.Input.disconnect()
        self.op.internalOp.Input.connect(self.op.Input)


    def test_wrapping(self):
        opm = operators.Op5ToMulti(graph=self.g)
        opm.Input0.setValue(1)

        op = OperatorWrapper( OpA, graph=self.g )
        op.Input.connect(opm.Outputs)
        result = op.Output[0][:].allocate().wait()[0]
        assert result == 1

        opm.Input1.setValue(2)
        result = op.Output[1][:].allocate().wait()[0]
        assert result == 2

        # Note: operator wrappers do not "restore" back to unwrapped operators after disconnect
        # (That was their behavior at some point, but no longer.)
        op.Input.disconnect()
        op.Input.resize(0)
        op.Input.setValue(2)
        assert len(op.Input) == 0
        assert len(op.Output) == 0

class OpC(Operator):

    Input = InputSlot(level = 1)
    Output = OutputSlot( level = 1)

    def __init__(self,parent=None, graph=None):
        Operator.__init__(self, parent, graph)
        self.internalOp = OperatorWrapper( OpB, graph=self.graph )
        self.internalOp.Input.connect(self.Input)
        self.inputBackup = self.Input

    def setupOutputs(self):
        numSlots = len(self.Input)
        self.Output.resize(numSlots)
        for i, slot in enumerate(self.Output):
            slot.meta.shape = self.Input[i].meta.shape
            slot.meta.dtype = self.Input[i].meta.dtype

    def execute(self, slot, subindex, roi, result):
        result[0] = self.internalOp.Output[:].allocate().wait()[0]
        return result

class TestMultiInputInputConnection(object):

    def setUp(self):
        self.g = Graph()
        self.op = OpC(graph=self.g)

    def tearDown(self):
        self.g.stopGraph()

    def test_wrapping(self):
        opm = operators.Op5ToMulti(graph=self.g)
        opm.Input0.setValue(1)

        self.op.Input.connect(opm.Outputs)

        assert len(self.op.internalOp.Output) == 1
        assert self.op.internalOp.Output[0].meta.shape is not None
        assert self.op.internalOp.Output[0].value == 1

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
