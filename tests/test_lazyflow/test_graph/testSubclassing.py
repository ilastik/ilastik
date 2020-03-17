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
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot


class OpBase(Operator):
    InputA = InputSlot()
    InputB = InputSlot()

    OutputA = OutputSlot()
    OutputB = OutputSlot()

    def setupOutputs(self):
        self.OutputA.meta.assignFrom(self.InputA.meta)
        self.OutputB.meta.assignFrom(self.InputB.meta)

    def execute(self, slot, subindex, roi, result):
        if slot == self.OutputA:
            return self.InputA(roi.start, roi.stop)
        if slot == self.OutputB:
            return self.InputB(roi.start, roi.stop)

    def propagateDirty(self, slot, subindex, roi):
        pass


class OpSubclass(OpBase):
    InputC = InputSlot()
    InputD = InputSlot()

    OutputC = OutputSlot()
    OutputD = OutputSlot()

    def setupOutputs(self):
        self.OutputC.meta.assignFrom(self.InputC.meta)
        self.OutputD.meta.assignFrom(self.InputD.meta)

    def execute(self, slot, subindex, roi, result):
        if slot == self.OutputC:
            return self.InputC(roi.start, roi.stop)
        if slot == self.OutputD:
            return self.InputD(roi.start, roi.stop)

        return super(OpSubclass, self).execute(slot, subindex, roi, result)

    def propagateDirty(self, slot, subindex, roi):
        pass


class TestSubclassing(object):
    def test(self):
        op = OpSubclass(graph=Graph())

        assert list(op.inputs.keys()) == ["InputA", "InputB", "InputC", "InputD"]
        assert list(op.outputs.keys()) == ["OutputA", "OutputB", "OutputC", "OutputD"]


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
