import nose
from lazyflow import graph
from lazyflow import stype
from lazyflow import operators

import logging
logger = logging.getLogger()
logger.addHandler( logging.NullHandler() )

class OpB(graph.Operator):

    Input = graph.InputSlot()
    Output = graph.OutputSlot()

    def setupOutputs(self):
        self.Output.meta.shape = self.Input.meta.shape
        self.Output.meta.dtype = self.Input.meta.dtype
        print "OpInternal shape=%r, dtype=%r" % (self.Input.meta.shape, self.Input.meta.dtype)

    def execute(self, slot, roi, result):
        result[0] = self.Input[:].allocate().wait()[0]
        return result

    def propagateDirty(self, inputSlot, roi):
        self.Output.setDirty(roi)

class OpA(graph.Operator):

    Input = graph.InputSlot()
    Output = graph.OutputSlot()

    def __init__(self,parent):
        graph.Operator.__init__(self, parent)
        self.internalOp = OpB(self)
        self.internalOp.Input.connect(self.Input)
        self.inputBackup = self.Input

    def setupOutputs(self):
        self.Output.meta.shape = self.Input.meta.shape
        self.Output.meta.dtype = self.Input.meta.dtype
        print "OpA shape=%r, dtype=%r" % (self.Input.meta.shape, self.Input.meta.dtype)


    def execute(self, slot, roi, result):
        result[0] = self.internalOp.Output[:].allocate().wait()[0]
        return result

    def propagateDirty(self, inputSlot, roi):
        self.Output.setDirty(roi)


class TestInputInputConnection(object):

    def setUp(self):
        self.g = graph.Graph()
        self.op = OpA(self.g)

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
        opm = operators.Op5ToMulti(self.g)
        opm.Input0.setValue(1)

        self.op.Input.connect(opm.Outputs)
        result = self.op.Output[0][:].allocate().wait()[0]
        assert result == 1

        opm.Input1.setValue(2)
        result = self.op.Output[1][:].allocate().wait()[0]
        assert result == 2

        self.op.Input.disconnect()
        print "test_wrapping: self.op.Input =  ",self.op.Input
        print "test_wrapping: self.op.inputs[\"Input\"] =  ",self.op.inputs["Input"]
        self.op.Input.setValue(2)
        result = self.op.Output[:].allocate().wait()[0]
        assert result == 2


class OpC(graph.Operator):

    Input = graph.InputSlot(level = 1)
    Output = graph.OutputSlot( level = 1)

    def __init__(self,parent):
        graph.Operator.__init__(self, parent)
        self.internalOp = OpB(self)
        self.internalOp.Input.connect(self.Input)
        self.inputBackup = self.Input

    def setupOutputs(self):
        numSlots = len(self.Input)
        self.Output.resize(numSlots)
        for i, slot in enumerate(self.Output):
            slot.meta.shape = self.Input[i].meta.shape
            slot.meta.dtype = self.Input[i].meta.dtype

    def execute(self, slot, roi, result):
        result[0] = self.internalOp.Output[:].allocate().wait()[0]
        return result

class TestMultiInputInputConnection(object):

    def setUp(self):
        self.g = graph.Graph()
        self.op = OpC(self.g)

    def tearDown(self):
        self.g.stopGraph()

    def test_wrapping(self):
        opm = operators.Op5ToMulti(self.g)
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
