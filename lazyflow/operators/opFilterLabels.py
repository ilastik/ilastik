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
    MinLabelSize = InputSlot()
        
    Output = OutputSlot()
    
    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        
    def execute(self, slot, subindex, roi, result):
        minSize = self.MinLabelSize.value
        self.Input.get(roi, result).wait()
        self.remove_small_connected_components(result, min_size=minSize, in_place=True)
        return result
        
    def propagateDirty(self, inputSlot, roi):
        # Both input slots can affect the entire output
        assert inputSlot == self.Input or inputSlot == self.MinLabelSize
        self.Output.setDirty( slice(None) )

    def remove_small_connected_components(self, a, min_size, in_place):
        """
        Adapted from http://github.com/jni/ray/blob/develop/ray/morpho.py
        (MIT License)
        """
        original_dtype = a.dtype
        if not in_place:
            a = a.copy()
        if min_size == 0: # shortcut for efficiency
            return a
        component_sizes = numpy.bincount( a.ravel() )
        too_small = component_sizes < min_size
        too_small_locations = too_small[a]
        a[too_small_locations] = 0
        return a.astype(original_dtype)

