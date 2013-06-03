import numpy
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice, roiFromShape

class OpDenseLabelArray(Operator):
    """
    The simplest, most naive implementation of a labeling operator.
    
    - Does not track max label value correctly
    - Does not ensure consecutive labeling (i.e. If you delete a label, the other labels are not 'shifted down'.
    """
    
    MetaInput = InputSlot()
    LabelSinkInput = InputSlot(optional=True)
    EraserLabelValue = InputSlot(value=255) # Value slot.  Specifies the magic 'eraser' label.

    DeleteLabel = InputSlot(value=-1) # If > 0, remove that label from the array.

    Output = OutputSlot()    
    MaxLabelValue = OutputSlot() # Hard-coded for now
    NonzeroBlocks = OutputSlot() # list of slicings
    
    def __init__(self, *args, **kwargs):
        super( OpDenseLabelArray, self ).__init__(*args, **kwargs)
        self._cache = None
    
    def setupOutputs(self):
        self.Output.meta.assignFrom( self.MetaInput.meta )
        self.Output.meta.dtype = numpy.uint8
        
        self.MaxLabelValue.meta.dtype = numpy.uint8 
        self.MaxLabelValue.meta.shape = (1,)
        
        self.NonzeroBlocks.meta.dtype = object
        self.NonzeroBlocks.meta.shape = (1,)

        assert self.EraserLabelValue.value != 0, "Eraser label value must be non-zero."

        if self._cache is None or self._cache.shape != self.Output.meta.shape:
            self._cache = numpy.zeros( self.Output.meta.shape, dtype=self.Output.meta.dtype )
        
        delete_label_value = self.DeleteLabel.value
        if self.DeleteLabel.value != -1:
            self._cache[self._cache == delete_label_value] = 0 

    def execute(self, slot, subindex, roi, destination):
        if slot == self.Output:
            destination[:] = self._cache[roiToSlice(roi.start, roi.stop)]
        elif slot == self.MaxLabelValue:
            # FIXME: Don't hard-code this
            destination[0] = 2
        elif slot == self.NonzeroBlocks:
            # Only one block.  Return the roi for the entire array.
            volume_roi = roiFromShape(self.Output.meta.shape)
            destination[0] = [roiToSlice(*volume_roi)]
        else:
            assert False, "Unknown output slot: {}".format( slot.name )
        return destination
    
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.LabelSinkInput:
            self.Output.setDirty(*roi)
    
    def setInSlot(self, slot, subindex, roi, value):
        if slot == self.LabelSinkInput:
            # Extract the data to modify
            orig_block = self._cache[roiToSlice(roi.start, roi.stop)]
            
            # Reset the pixels we need to change
            orig_block[value.nonzero()] = 0
            
            # Update
            orig_block |= value

            # Replace 'eraser' values with zeros.
            cleaned_block = numpy.where(orig_block == self.EraserLabelValue.value, 0, orig_block[:])

            # Set in the cache.
            self._cache[roiToSlice(roi.start, roi.stop)] = cleaned_block
            self.Output.setDirty( roi.start, roi.stop )







