import nose
from lazyflow import graph
from lazyflow.graph import Operator
from lazyflow import stype
from lazyflow import operators

class OpOuter(graph.Operator):

    Input = graph.InputSlot()
    Output = graph.OutputSlot()

    def __init__(self, graph):
        Operator.__init__(self, graph)
        self._was_executed = False
        self._inner_op = OpInner(self)

        self._inner_op.Input.connect(self.Input)
        self.Output.connect(self._inner_op.Output)

    def setupOutputs(self):
        self.Output.meta.shape = self.Input.meta.shape
        self.Output.meta.dtype = self.Input.meta.dtype

    def execute(self, slot, roi, result):
        self._was_executed = True
        result[0] = self.Input[:].allocate().wait()[0]
        return result

    def propagateDirty(self, inputSlot, roi):
        self.Output.setDirty(roi)

class OpInner(graph.Operator):

    Input = graph.InputSlot()
    Output = graph.OutputSlot()

    def setupOutputs(self):
        self.Output.meta.shape = self.Input.meta.shape
        self.Output.meta.dtype = self.Input.meta.dtype

    def execute(self, slot, roi, result):
        result[0] = self.Input[:].allocate().wait()[0]
        return result

    def propagateDirty(self, inputSlot, roi):
        self.Output.setDirty(roi)

class TestOutputOutputConnection(object):

    def setUp(self):
        self.g = graph.Graph()
        self.op = OpOuter(self.g)

    def tearDown(self):
        self.g.stopGraph()

    def test_value(self):
        """
        This test checks, that requests produce correct
        results in the case of output-output connections
        (the o-o connection exists inside the OpOuter...
        """
        self.op.Input.setValue(True)
        result = self.op.Output[:].allocate().wait()[0]
        assert result == True, "result = %r" % result
        self.op.Input.setValue(False)
        result = self.op.Output[:].allocate().wait()[0]
        assert result == False, "result = %r" % result

    def test_execute(self):
        """
        This test checks that the execute method of the outer
        operator is not called, when the output slot of the
        op is connect to the output slot of another (inner) operator
        """
        self.op.Input.setValue(True)
        self.op._was_executed = False
        result = self.op.Output[:].allocate().wait()[0]
        assert self.op._was_executed is False

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
