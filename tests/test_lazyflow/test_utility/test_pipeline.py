###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2025, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#          http://ilastik.org/license.html
###############################################################################
import pytest

from lazyflow.graph import InputSlot, Operator, OutputSlot
from lazyflow.utility import Pipeline


class OpNoInput(Operator):
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.shape = (1, 2, 3)
        self.Output.meta.dtype = "uint8"


class OpOptionalInput(OpNoInput):
    SomeOptionalSlot = InputSlot(value="notSet")

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(())


class Op(Operator):
    Input = InputSlot()
    InputOpt = InputSlot(optional=True)
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)


class OpNonStandardOutput(Operator):
    WeirdOutput = OutputSlot()

    def setupOutputs(self):
        self.WeirdOutput.meta.shape = (1, 2, 3)
        self.WeirdOutput.meta.dtype = "uint8"


class OpNonStandardInput(OpNonStandardOutput):
    WeirdInput = InputSlot()

    def setupOutputs(self):
        self.WeirdOutput.meta.assignFrom(self.WeirdInput.meta)


def test_auto_connect(graph):
    with Pipeline(graph=graph) as pl:
        start_op = pl.add(OpNoInput)
        op = pl.add(Op)

        assert op.Input.upstream_slot == start_op.Output
        assert op.Output.meta.shape == start_op.Output.meta.shape


def test_slot_kwargs(graph):
    with Pipeline(graph=graph) as pl:
        start_op = pl.add(OpOptionalInput, SomeOptionalSlot="123")

        assert start_op.SomeOptionalSlot.value == "123"


def test_raises_no_standard_outputs(graph):
    with Pipeline(graph=graph) as pl:
        pl.add(OpNonStandardOutput)
        with pytest.raises(ValueError):
            pl.add(Op)


def test_raises_no_standard_inputs(graph):
    with Pipeline(graph=graph) as pl:
        pl.add(OpNoInput)
        with pytest.raises(ValueError):
            pl.add(OpNonStandardInput)


def test_no_standard_inputs_but_kwargs(graph):
    with Pipeline(graph=graph) as pl:
        op_start = pl.add(OpNoInput)
        pl.add(OpNonStandardInput, WeirdInput=op_start.Output)
