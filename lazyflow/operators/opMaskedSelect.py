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
