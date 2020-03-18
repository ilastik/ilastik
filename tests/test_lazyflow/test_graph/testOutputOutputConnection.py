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
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
from lazyflow import stype
from lazyflow import operators


class OpOuter(Operator):

    Input = InputSlot()
    Output = OutputSlot()

    def __init__(self, graph):
        Operator.__init__(self, graph=graph)
        self._was_executed = False
        self._inner_op = OpInner(self)

        self._inner_op.Input.connect(self.Input)
        self.Output.connect(self._inner_op.Output)

    def setupOutputs(self):
        self.Output.meta.shape = self.Input.meta.shape
        self.Output.meta.dtype = self.Input.meta.dtype

    def execute(self, slot, subindex, roi, result):
        self._was_executed = True
        result[0] = self.Input[:].wait()[0]
        return result

    def propagateDirty(self, inputSlot, subindex, roi):
        self.Output.setDirty(roi)


class OpInner(Operator):

    Input = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.shape = self.Input.meta.shape
        self.Output.meta.dtype = self.Input.meta.dtype

    def execute(self, slot, subindex, roi, result):
        result[0] = self.Input[:].wait()[0]
        return result

    def propagateDirty(self, inputSlot, subindex, roi):
        self.Output.setDirty(roi)


class TestOutputOutputConnection(object):
    def setup_method(self, method):
        self.g = Graph()
        self.op = OpOuter(graph=self.g)

    def test_value(self):
        """
        This test checks, that requests produce correct
        results in the case of output-output connections
        (the o-o connection exists inside the OpOuter...
        """
        self.op.Input.setValue(True)
        result = self.op.Output[:].wait()[0]
        assert result == True, "result = %r" % result
        self.op.Input.setValue(False)
        result = self.op.Output[:].wait()[0]
        assert result == False, "result = %r" % result

    def test_execute(self):
        """
        This test checks that the execute method of the outer
        operator is not called, when the output slot of the
        op is connect to the output slot of another (inner) operator
        """
        self.op.Input.setValue(True)
        self.op._was_executed = False
        result = self.op.Output[:].wait()[0]
        assert self.op._was_executed is False


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
