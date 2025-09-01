###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2025, the ilastik developers
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
from lazyflow.operator import Operator, InputSlot, OutputSlot


class OpSimpleInput(Operator):
    Input = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass


class OpMultiInput(Operator):
    MultiInput = InputSlot(level=1)
    Output = OutputSlot()

    def setupOutputs(self):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass


def test_simple_input_sets_output_ready_and_unready(graph):
    op = OpSimpleInput(graph=graph)
    op.Input.setValue(True)
    assert op.Output.ready()
    op.Input.disconnect()
    assert not op.Output.ready()


def test_multi_input_sets_output_ready_and_unready(graph):
    op = OpMultiInput(graph=graph)
    op.MultiInput.resize(1)
    op.MultiInput[0].setValue(True)
    assert op.Output.ready()
    op.MultiInput.disconnect()
    assert not op.Output.ready()
