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
from lazyflow.operators.generic import OpTransposeSlots


class OpMultiPassthrough(Operator):
    Inputs = InputSlot(level=2, optional=True)
    Outputs = OutputSlot(level=2)

    def setupOutputs(self):
        self.Outputs.connect(self.Inputs)

    def execute(self, slot, subindex, roi, result):
        pass

    def propagateDirty(self, inputSlot, subindex, roi):
        pass


class TestOpTransposeSlots(object):
    def testBasic(self):
        graph = Graph()
        op1 = OpMultiPassthrough(graph=graph)

        opTranspose = OpTransposeSlots(graph=graph)
        opTranspose.Inputs.connect(op1.Outputs)
        opTranspose.OutputLength.setValue(2)
        assert len(opTranspose.Outputs) == 2

        # Input is 3x2.
        op1.Inputs.resize(3)
        op1.Inputs[0].resize(2)
        op1.Inputs[1].resize(2)
        op1.Inputs[2].resize(2)

        op1.Inputs[0][0].setValue((0, 0))
        op1.Inputs[0][1].setValue((0, 1))

        # don't configure the middle multi-input (see assert test below)
        # op1.Inputs[1][0].setValue( (1,0) )
        # op1.Inputs[1][0].setValue( (1,1) )

        op1.Inputs[2][0].setValue((2, 0))
        op1.Inputs[2][1].setValue((2, 1))

        assert len(op1.Outputs) == 3
        assert len(opTranspose.Outputs[0]) == 3

        # Sanity check...
        assert op1.Outputs[0][0].ready()
        assert op1.Outputs[0][0].value == (0, 0)

        assert opTranspose.Outputs[0][0].ready()
        assert opTranspose.Outputs[0][0].value == (0, 0)

        op1.Inputs[0][1].setValue((0, 1))

        # Sanity check...
        assert op1.Outputs[0][1].ready()
        assert op1.Outputs[0][1].value == (0, 1)

        assert opTranspose.Outputs[1][0].ready()
        assert opTranspose.Outputs[1][0].value == (0, 1)

        op1.Inputs[2].resize(2)
        op1.Inputs[2][0].setValue((2, 0))

        # Sanity check...
        assert op1.Outputs[2][0].ready()
        assert op1.Outputs[2][0].value == (2, 0)

        assert opTranspose.Outputs[0][2].ready()
        assert opTranspose.Outputs[0][2].value == (2, 0)

        op1.Inputs[2][1].setValue((2, 1))

        # Sanity check...
        assert op1.Outputs[2][1].ready()
        assert op1.Outputs[2][1].value == (2, 1)

        assert opTranspose.Outputs[1][2].ready()
        assert opTranspose.Outputs[1][2].value == (2, 1)

        # The middle input multi-input was never configured.
        # Therefore, the middle slot of each multi-output is not ready.
        assert not opTranspose.Outputs[0, 1].ready()
        assert not opTranspose.Outputs[1, 1].ready()


#        for i, mslot in enumerate(op1.Outputs):
#            for j, oslot in enumerate(mslot):
#                print "op1[{}][{}].ready() : {}".format( i, j, oslot.ready() )
#
#        for i, mslot in enumerate(opTranspose.Outputs):
#            for j, oslot in enumerate(mslot):
#                print "opTranspose[{}][{}].ready() : {}".format( i, j, oslot.ready() )

if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
