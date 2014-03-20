# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

import unittest

import numpy as np
import vigra
from lazyflow.graph import Graph, OperatorWrapper, Operator
from lazyflow.slot import InputSlot, OutputSlot, Slot
from lazyflow.rtype import SubRegion
from lazyflow.operators import OpArrayPiper, OpMultiArrayStacker
from lazyflow.operatorWrapper import OperatorWrapper


class TestOpMultiArrayStacker(unittest.TestCase):

    def setUp(self):
        self.g = Graph()
        vol = np.zeros((100,200,2))
        vol = vigra.taggedView(vol, axistags='xyz')
        self.vol = vol

    def testSimpleUsage(self):
        n = self.vol.shape[2]
        op = OpMultiArrayStacker(graph=self.g)
        op.AxisFlag.setValue('z')

        provider = OperatorWrapper(OpArrayPiper, graph=self.g)
        vol = self.vol

        op.Images.connect(provider.Output)
        provider.Input.resize(n)

        for i in range(n):
            provider.Input[i].setValue(vol[..., i])

        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags='xyz')
        np.testing.assert_array_equal(out, vol)

    def testIndexing(self):
        n = self.vol.shape[2]
        op = OpMultiArrayStacker(graph=self.g)
        op.AxisFlag.setValue('z')
        op.AxisIndex.setValue(0)

        provider = OperatorWrapper(OpArrayPiper, graph=self.g)
        vol = self.vol

        op.Images.connect(provider.Output)
        provider.Input.resize(n)

        for i in range(n):
            provider.Input[i].setValue(vol[..., i])

        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags='zxy')
        out = out.withAxes(*"xyz")
        np.testing.assert_array_equal(out, vol)

    
    ## slots could become unready after a while, the old implementation used to
    ## ignore this
    def testNonReady(self):
        n = self.vol.shape[2]
        op = OpMultiArrayStacker(graph=self.g)
        op.AxisFlag.setValue('z')
        op.AxisIndex.setValue(0)

        providers = [OpNonReady(graph=self.g),OpNonReady(graph=self.g)]
        provider = OperatorWrapper(OpArrayPiper, graph=self.g)
        provider.Input.resize(n)
        vol = self.vol

        op.Images.resize(n)

        for i in range(n):
            provider.Input[i].setValue(vol[..., i])
            providers[i].Input.connect(provider.Output[i])
            op.Images[i].connect(providers[i].Output)

        out = op.Output[...].wait()

        with self.assertRaises(Slot.SlotNotReadyError):
            providers[0].screwWithOutput()
            out = op.Output[...].wait()


class OpNonReady(Operator):
    Input = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)

    def execute(self, slot, subindex, roi, result):
        assert self.Output.ready()
        result[:] = 0

    def propagateDirty(self, slot, subindex, roi):
        newroi = roi.copy()
        self.Output.setDirty(roi)

    def screwWithOutput(self):
        self.Input.disconnect()
        self.Output.meta.NOTREADY = True

