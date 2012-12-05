from lazyflow.graph import Operator, InputSlot, OutputSlot
import numpy
from ilastik.utility import MultiLaneOperatorABC, OperatorSubView

class OpDeviationFromMean(Operator):
    """
    Multi-image operator.
    Calculates the pixelwise mean of a set of images, and produces a set of corresponding images for the difference from the mean.
    Inputs must all have the same shape.
    """    
    ScalingFactor = InputSlot() # Scale after subtraction
    Offset = InputSlot()        # Offset final results
    Input = InputSlot(level=1)  # Multi-image input

    Mean = OutputSlot()
    Output = OutputSlot(level=1) # Multi-image output
    
    def setupOutputs(self):
        # Ensure all inputs have the same shape
        if len(self.Input) > 0:
            shape = self.Input[0].meta.shape
            for islot in self.Input:
                if islot.meta.shape != shape:
                    raise RuntimeError("Input images must have the same shape.")

        # Copy the meta info from each input to the corresponding output        
        self.Output.resize( len(self.Input) )
        for index, islot in enumerate(self.Input):
            self.Output[index].meta.assignFrom(islot.meta)
        
        self.Mean.meta.assignFrom(self.Input[0].meta)

        def markAllOutputsDirty( *args ):
            self.propagateDirty( self.Input, (), slice(None) )
        self.Input.notifyInserted( markAllOutputsDirty )
        self.Input.notifyRemoved( markAllOutputsDirty )

    def execute(self, slot, subindex, roi, result):
        """
        Compute.  This is a simple implementation, without optimizations.
        """
        # Compute average of *all* inputs
        result[:] = 0.0
        for s in self.Input:
            result[:] += s.get(roi).wait()
        result[:] = result / len(self.Input)

        # If the user wanted the mean, we're done.
        if slot == self.Mean:
            return result

        assert slot == self.Output

        # Subtract average from the particular image being requested
        result[:] = self.Input[subindex].get(roi).wait() - result

        # Scale
        result[:] *= self.ScalingFactor.value

        # Add constant offset
        result[:] += self.Offset.value
        
        return result

    def propagateDirty(self, slot, subindex, roi):
        # If the dirty slot is one of our two constants, then the entire image region is dirty
        if slot == self.Offset or slot == self.ScalingFactor:
            roi = slice(None) # The whole image region
        
        # All inputs affect all outputs, so every image is dirty now
        for oslot in self.Output:
            oslot.setDirty( roi )

    #############################################
    ## Methods to satisfy MultiLaneOperatorABC ##
    #############################################

    def addLane(self, laneIndex):
        """
        Add an image lane to the top-level operator.
        """
        numLanes = len(self.Input)
        assert numLanes == laneIndex, "Image lanes must be appended."        
        self.Input.resize(numLanes+1)
        self.Output.resize(numLanes+1)
        
    def removeLane(self, laneIndex, finalLength):
        """
        Remove the specified image lane from the top-level operator.
        """
        self.Input.removeSlot(laneIndex, finalLength)
        self.Output.removeSlot(laneIndex, finalLength)

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)

assert issubclass(OpDeviationFromMean, MultiLaneOperatorABC)

if __name__ == "__main__":
    from lazyflow.graph import Graph
    op = OpDeviationFromMean(graph=Graph())

    shape = (5,5)
    zeros = numpy.zeros( shape, dtype=numpy.float )
    ones = numpy.ones( shape, dtype=numpy.float )
    twos = 2*numpy.ones( shape, dtype=numpy.float )

    scalingFactor = 5
    offset = 10
    
    op.ScalingFactor.setValue(scalingFactor)
    op.Offset.setValue(offset)
        
    op.Input.resize(3)
    op.Input[0].setValue( zeros )
    op.Input[1].setValue( ones )
    op.Input[2].setValue( twos )
    
    expected = offset + scalingFactor * (ones - (zeros + ones + twos) / len(op.Input)) 
    print "expected:", expected

    output = op.Output[1][:].wait()
    print "output:",output
    assert ( output == expected).all()
