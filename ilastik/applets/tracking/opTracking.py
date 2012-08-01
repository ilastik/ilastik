from lazyflow.graph import Operator, InputSlot, OutputSlot

import numpy

class OpTracking(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpTracking"
    category = "other"
    
    #InputImage = InputSlot()
    #MinValue = InputSlot(stype='int')
    #MaxValue = InputSlot(stype='int')
    
    Output = OutputSlot()
    RawData = OutputSlot()
    #InvertedOutput = OutputSlot()
    
    def setupOutputs(self):
        print "tracking: setupOutputs"
        # Copy the input metadata to both outputs
        #self.Output.meta.assignFrom( self.InputImage.meta )
        #self.InvertedOutput.meta.assignFrom( self.InputImage.meta )
    
    def execute(self, slot, roi, result):
        print "tracking: execute"
        # key = roi.toSlice()
        # raw = self.InputImage[key].wait()
        # mask = numpy.logical_and(self.MinValue.value <= raw, raw <= self.MaxValue.value)
        
        # if slot.name == 'Output':
        #     result[...] = mask * raw
        # if slot.name == 'InvertedOutput':
        #     result[...] = numpy.logical_not(mask) * raw

    def propagateDirty(self, inputSlot, roi):
        print "tracking: propagateDirty"
        # if inputSlot.name == "InputImage":
        #     self.Output.setDirty(roi)
        #     self.InvertedOutput.setDirty(roi)
        # if inputSlot.name == "MinValue" or inputSlot.name == "MaxValue":
        #     self.Output.setDirty( slice(None) )
        #     self.InvertedOutput.setDirty( slice(None) )
