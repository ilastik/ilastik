from builtins import zip
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
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.operators import OpPixelOperator, OpTransposeSlots


class OpA(Operator):

    Inputs = InputSlot(level=2, optional=True)
    Outputs = OutputSlot(level=2)

    def setupOutputs(self):
        self.Outputs.resize(len(self.Inputs))
        for imslot, omslot in zip(self.Inputs, self.Outputs):
            omslot.resize(len(imslot))
            for islot, oslot in zip(imslot, omslot):
                oslot.meta.assignFrom(islot.meta)

    def execute(self, slot, subindex, roi, result):
        result[:] = self.Inputs[subindex](roi)

    def propagateDirty(self, slot, subindex, roi):
        self.Outputs[subindex].setDirty(roi)


class TestMultiSlotResize(object):
    def testMulitSlotResize(self):
        graph = Graph()
        opA = OpA(graph=graph)
        opB = OpA(graph=graph)
        opC = OpA(graph=graph)

        opP = OperatorWrapper(OpPixelOperator, graph=graph)

        opB.Inputs.connect(opA.Inputs)
        opC.Inputs.connect(opB.Inputs)

        opT = OpTransposeSlots(graph=graph)
        opT.Inputs.connect(opA.Outputs)
        opT.OutputLength.setValue(2)

        assert len(opT.Outputs) == 2

        opA.Inputs.resize(3)
        assert len(opT.Outputs[0]) == 3
        assert len(opT.Outputs[1]) == 3

        opP.Input.connect(opT.Outputs[0])
        assert len(opP.Input) == 3

    def testMultiSlotPartners(self):
        graph = Graph()
        opA = OpA(graph=graph)
        opB = OpA(graph=graph)

        opB.Inputs.connect(opA.Inputs)
        opA.Inputs.resize(2)
        assert len(opB.Inputs) == 2
        assert opB.Inputs[0].upstream_slot == opA.Inputs[0]
        assert opB.Inputs[1].upstream_slot == opA.Inputs[1]


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
