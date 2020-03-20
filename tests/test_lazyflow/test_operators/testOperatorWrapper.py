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
import copy

from unittest import mock

import numpy

from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot, OperatorWrapper


class OpSimple(Operator):
    InputA = InputSlot()
    InputB = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.shape = self.InputA.meta.shape
        self.Output.meta.dtype = self.InputA.meta.dtype

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output

        result[...] = self.InputA(roi.start, roi.stop).wait() * self.InputB[0:1].wait()

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot == self.InputA:
            self.Output.setDirty(roi)
        elif inputSlot == self.InputB and roi.start[0] == 0 and roi.stop[0] >= 1:
            dirtyRoi = copy.copy(roi)
            dirtyRoi.stop[0] = 1
            self.Output.setDirty(dirtyRoi)
        else:
            assert False


class OpExplicitMulti(Operator):
    Output = OutputSlot(level=1)

    def setupOutputs(self):
        pass


class OpCopyInput(Operator):
    Input = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.setValue(self.Input.value)

    def propagateDirty(self, inputSlot, subindex, roi):
        self.Output.setDirty(roi)


class TestBasic(object):
    @classmethod
    def setup_class(cls):
        cls.graph = Graph()

    @classmethod
    def teardown_class(cls):
        pass

    def test_fullWrapping(self):
        """
        Test basic wrapping functionality (all slots are promoted)
        """
        wrapped = OperatorWrapper(OpSimple, graph=self.graph)
        assert type(wrapped.InputA) == InputSlot
        assert type(wrapped.InputB) == InputSlot
        assert type(wrapped.Output) == OutputSlot
        assert wrapped.InputA.level == 1
        assert wrapped.InputB.level == 1
        assert wrapped.Output.level == 1

        assert len(wrapped.InputA) == 0
        assert len(wrapped.InputB) == 0
        assert len(wrapped.Output) == 0

        wrapped.InputA.resize(2)
        assert len(wrapped.InputB) == 2
        assert len(wrapped.Output) == 2

        a = numpy.array([[1, 2], [3, 4]])
        b = numpy.array([2])
        wrapped.InputA[0].setValue(a)
        wrapped.InputB[0].setValue(b)
        wrapped.InputA[1].setValue(2 * a)
        wrapped.InputB[1].setValue(3 * b)

        result0 = wrapped.Output[0][0:2, 0:2].wait()
        result1 = wrapped.Output[1][0:2, 0:2].wait()
        assert (result0 == a * b[0]).all()
        assert (result1 == 2 * a * 3 * b[0]).all()

    def test_partialWrapping(self):
        """
        By default, OperatorWrapper promotes all slots.
        This function tests what happens when only a subset of the inputs are promoted.
        """
        wrapped = OperatorWrapper(OpSimple, graph=self.graph, promotedSlotNames=set(["InputA"]))
        assert type(wrapped.InputA) == InputSlot
        assert type(wrapped.InputB) == InputSlot
        assert type(wrapped.Output) == OutputSlot
        assert wrapped.InputA.level == 1  # Promoted because it was listed in the constructor call
        assert wrapped.InputB.level == 0  # NOT promoted
        assert wrapped.Output.level == 1  # Promoted because it's an output

        assert len(wrapped.InputA) == 0
        assert len(wrapped.InputB) == 0
        assert len(wrapped.Output) == 0

        wrapped.InputA.resize(2)
        assert len(wrapped.InputB) == 0  # Not promoted
        assert len(wrapped.Output) == 2

        a = numpy.array([[1, 2], [3, 4]])
        b = numpy.array([2])
        wrapped.InputA[0].setValue(a)
        wrapped.InputB.setValue(b)
        wrapped.InputA[1].setValue(2 * a)

        result0 = wrapped.Output[0][0:2, 0:2].wait()
        result1 = wrapped.Output[1][0:2, 0:2].wait()
        assert (result0 == a * b[0]).all()
        assert (result1 == 2 * a * b[0]).all()


class TestMultiOutputToWrapped(object):
    @classmethod
    def setup_class(cls):
        cls.graph = Graph()

    def test_input_output_resize(self):
        exMulti = OpExplicitMulti(graph=self.graph)

        wrappedSimple = OperatorWrapper(OpSimple, graph=self.graph)
        assert len(wrappedSimple.InputA) == 0

        wrappedSimple.InputA.connect(exMulti.Output)
        assert len(wrappedSimple.InputA) == 0

        exMulti.Output.resize(1)
        assert len(wrappedSimple.InputA) == 1
        assert len(wrappedSimple.InputB) == 1
        assert len(wrappedSimple.Output) == 1

    def test_setValues(self):
        wrappedCopier = OperatorWrapper(OpCopyInput, graph=self.graph)

        values = ["Subslot One", "Subslot Two"]
        wrappedCopier.Input.setValues(values)

        assert wrappedCopier.Output[0].value == values[0]
        assert wrappedCopier.Output[1].value == values[1]


class TestOperatorWrapperTransaction:
    def test_transaction(self, graph):
        class OpTest(Operator):
            Input = InputSlot()
            Output = OutputSlot()

            setupOutputs = mock.Mock()

            def propagateDirty(self, inputSlot, subindex, roi):
                self.Output.setDirty(roi)

        wrapped = OperatorWrapper(OpTest, graph=graph)
        values = ["Subslot One", "Subslot Two"]

        with wrapped.transaction:
            wrapped.Input.setValues(values)
            OpTest.setupOutputs.assert_not_called()

        assert OpTest.setupOutputs.call_count == 2, "Should call setupOutputs for each lane on exit"


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
