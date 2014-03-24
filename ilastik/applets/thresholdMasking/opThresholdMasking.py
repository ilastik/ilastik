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

import numpy

class OpThresholdMasking(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpThresholdMasking"
    category = "Pointwise"
    
    InputImage = InputSlot()
    MinValue = InputSlot(stype='int')
    MaxValue = InputSlot(stype='int')
    
    Output = OutputSlot()
    InvertedOutput = OutputSlot()
    
    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.InputImage.meta )
        self.InvertedOutput.meta.assignFrom( self.InputImage.meta )
    
    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()
        raw = self.InputImage[key].wait()
        mask = numpy.logical_and(self.MinValue.value <= raw, raw <= self.MaxValue.value)
        
        if slot.name == 'Output':
            result[...] = mask * raw
        if slot.name == 'InvertedOutput':
            result[...] = numpy.logical_not(mask) * raw

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            self.Output.setDirty(roi)
            self.InvertedOutput.setDirty(roi)
        elif slot.name == "MinValue" or slot.name == "MaxValue":
            self.Output.setDirty( slice(None) )
            self.InvertedOutput.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"
