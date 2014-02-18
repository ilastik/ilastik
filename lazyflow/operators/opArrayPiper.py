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

from lazyflow.graph import Operator, InputSlot, OutputSlot

class OpArrayPiper(Operator):
    name = "ArrayPiper"
    description = "simple piping operator"

    #Inputs
    Input = InputSlot() 
   
    #Outputs
    Output = OutputSlot()

    def setupOutputs(self):
        inputSlot = self.inputs["Input"]
        self.outputs["Output"].meta.assignFrom(inputSlot.meta)

    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()
        req = self.inputs["Input"][key].writeInto(result)
        req.wait()
        return result

    def propagateDirty(self, slot, subindex, roi):
        key = roi.toSlice()
        # Check for proper name because subclasses may define extra inputs.
        # (but decline to override notifyDirty)
        if slot.name == 'Input':
            self.outputs["Output"].setDirty(key)
        else:
            # If some input we don't know about is dirty (i.e. we are subclassed by an operator with extra inputs),
            # then mark the entire output dirty.  This is the correct behavior for e.g. 'sigma' inputs.
            self.outputs["Output"].setDirty(slice(None))

    def setInSlot(self, slot, subindex, roi, value):
        # Forward to output
        assert subindex == ()
        assert slot == self.Input
        key = roi.toSlice()
        self.outputs["Output"][key] = value
    