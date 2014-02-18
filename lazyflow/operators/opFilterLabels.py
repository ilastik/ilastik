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
import logging

logger = logging.getLogger(__name__)

class OpFilterLabels(Operator):
    """
    Given a labeled volume, discard labels that have too few pixels.
    Zero is used as the background label
    """
    name = "OpFilterLabels"
    category = "generic"

    Input = InputSlot() 
    MinLabelSize = InputSlot(stype='int')
    MaxLabelSize = InputSlot(optional=True, stype='int')
    BinaryOut = InputSlot(optional=True, value = False, stype='bool')
        
    Output = OutputSlot()
    
    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        
    def execute(self, slot, subindex, roi, result):
        minSize = self.MinLabelSize.value
        maxSize = None
        if self.MaxLabelSize.ready():
            maxSize = self.MaxLabelSize.value
        req = self.Input.get(roi)
        req.writeInto(result)
        req.wait()
        
        self.remove_wrongly_sized_connected_components(result, min_size=minSize, max_size=maxSize, in_place=True)
        return result
        
    def propagateDirty(self, inputSlot, subindex, roi):
        # Both input slots can affect the entire output
        assert inputSlot == self.Input or inputSlot == self.MinLabelSize or inputSlot == self.MaxLabelSize
        self.Output.setDirty( slice(None) )

    def remove_wrongly_sized_connected_components(self, a, min_size, max_size, in_place):
        """
        Adapted from http://github.com/jni/ray/blob/develop/ray/morpho.py
        (MIT License)
        """
        bin_out = self.BinaryOut.value
        
        original_dtype = a.dtype
            
        if not in_place:
            a = a.copy()
        if min_size == 0 and (max_size is None or max_size > numpy.prod(a.shape)): # shortcut for efficiency
            return a
        
        try:
            component_sizes = numpy.bincount( a.ravel() )
        except TypeError:
            # On 32-bit systems, must explicitly convert from uint32 to int
            # (This fix is just for VM testing.)
            component_sizes = numpy.bincount( numpy.asarray(a.ravel(), dtype=int) )
        bad_sizes = component_sizes < min_size
        if max_size is not None:
            numpy.logical_or( bad_sizes, component_sizes > max_size, out=bad_sizes )
        
        bad_locations = bad_sizes[a]
        a[bad_locations] = 0
        if (bin_out):
            a[a>0]=1
        return numpy.array(a, dtype=original_dtype)

