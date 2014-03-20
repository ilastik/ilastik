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

import numpy

from lazyflow.graph import Operator, InputSlot, OutputSlot

class OpMaskedSelect(Operator):
    """
    For pixels where Mask == True, Output is a copy of the Input.
    For all other pixels, Output is 0.
    """
    Input = InputSlot()
    Mask = InputSlot()
    
    Output = OutputSlot()
    
    def setupOutputs(self):
        # Merge all meta fields from both
        self.Output.meta.assignFrom( self.Input.meta )
        self.Output.meta.updateFrom( self.Mask.meta )
        
        # Use Input dtype (mask may be bool)
        self.Output.meta.dtype = self.Input.meta.dtype
    
    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output, "Unknown output slot: {}".format( slot.name )
        self.Input(roi.start, roi.stop).writeInto( result ).wait()
        mask = self.Mask(roi.start, roi.stop).wait()
        result[:] = numpy.where( mask, result, 0 )
        return result
    
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Input or slot == self.Mask:
            self.Output.setDirty(roi)
        else:
            assert False, "Unknown input slot: {}".format( slot.name )
