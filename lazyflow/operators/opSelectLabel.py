import numpy
from lazyflow.graph import Operator, InputSlot, OutputSlot

class OpSelectLabel(Operator):
    """
    Given a label image and a label number of interest, produce a 
    boolean mask of those pixels that match the selected label.
    """
    Input = InputSlot() # label image
    SelectedLabel = InputSlot() # int
    Output = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( OpSelectLabel, self ).__init__( *args, **kwargs )
    
    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = numpy.uint8
        # As a convenience, store the selected label in the metadata.
        self.Output.meta.selected_label = self.SelectedLabel.value
    
    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output, "Unknown output slot: {}".format( slot.name )
        if self.SelectedLabel.value == 0:
            result[:] = 0
        else:
            # Can't use writeInto() here because dtypes don't match.
            inputLabels = self.Input(roi.start, roi.stop).wait()
            
            # Use two in-place bitwise operations instead of numpy.where
            # This avoids the temporary variable created by (inputLabels == x)
            #result[:] = numpy.where( inputLabels == self.SelectedLabel.value, 1, 0 )
            numpy.bitwise_xor(inputLabels, self.SelectedLabel.value, out=inputLabels) # All 
            numpy.logical_not(inputLabels, out=inputLabels)
            result[:] = inputLabels # Copy from uint32 to uint8
            
        return result
    
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Input:
            self.Output.setDirty( roi.start, roi.stop )
        elif slot == self.SelectedLabel:
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Dirty slot is unknown: {}".format( slot.name )

