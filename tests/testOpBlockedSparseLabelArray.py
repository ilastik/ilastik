import numpy
from lazyflow.graph import Graph
from lazyflow.operators import OpBlockedSparseLabelArray

from lazyflow.slicingtools import sl, slicing2shape

class TestOpSparseLabelArray(object):
    
    def setup(self):
        graph = Graph()
        op = OpBlockedSparseLabelArray(graph=graph)
        arrayshape = (1,100,100,10,1)
        op.inputs["shape"].setValue( arrayshape )
        blockshape = (1,10,10,10,1) # Why doesn't this work if blockshape is an ndarray?
        op.inputs["blockShape"].setValue( blockshape )
        op.eraser.setValue(100)

        slicing = sl[0:1, 1:15, 2:36, 3:7, 0:1]
        inDataShape = slicing2shape(slicing)
        inputData = ( 3*numpy.random.random(inDataShape) ).astype(numpy.uint8)
        op.Input[slicing] = inputData
        data = numpy.zeros(arrayshape, dtype=numpy.uint8)
        data[slicing] = inputData
        
        self.op = op
        self.slicing = slicing
        self.inData = inputData
        self.data = data

    def testOutput(self):
        """
        Verify that the label array has all of the data it was given.
        """
        op = self.op
        slicing = self.slicing
        inData = self.inData
        data = self.data

        # Output
        outputData = op.Output[...].wait()
        assert numpy.all(outputData[...] == data[...])

        # maxLabel        
        assert op.maxLabel.value == inData.max()

        # nonzeroValues
        nz = op.nonzeroValues.value
        assert len(nz) == len(numpy.unique(inData))-1
        
    def testDeleteLabel(self):
        """
        Check behavior after deleting an entire label class from the sparse array.
        """
        op = self.op
        slicing = self.slicing
        inData = self.inData
        data = self.data

        op.deleteLabel.setValue(1)
        outputData = op.Output[...].wait()

        # Expected: All 1s removed, all 2s converted to 1s
        expectedOutput = numpy.where(self.data == 1, 0, self.data)
        expectedOutput = numpy.where(expectedOutput == 2, 1, expectedOutput)
        assert (outputData[...] == expectedOutput[...]).all()
        
        assert op.maxLabel.value == expectedOutput.max() == 1

        # delete label input resets automatically
        # assert op.deleteLabel.value == -1 # Apparently not?
    
    def testEraser(self):
        """
        Check that some labels can be deleted correctly from the sparse array.
        """
        op = self.op
        slicing = self.slicing
        inData = self.inData
        data = self.data

        assert op.maxLabel.value == 2
        
        erasedSlicing = list(slicing)
        erasedSlicing[1] = slice(1,2)

        outputWithEraser = data
        outputWithEraser[erasedSlicing] = 100
        
        op.Input[erasedSlicing] = outputWithEraser[erasedSlicing]

        expectedOutput = outputWithEraser
        expectedOutput[erasedSlicing] = 0
        
        outputData = op.Output[...].wait()
        assert (outputData[...] == expectedOutput[...]).all()
        
        assert expectedOutput.max() == 2
        assert op.maxLabel.value == 2
    
    def testEraseAll(self):
        """
        Test behavior when all labels of a particular class are erased.
        Note that this is not the same as deleting a label class, but should have the same effect on the output slots.
        """
        op = self.op
        slicing = self.slicing
        data = self.data

        assert op.maxLabel.value == 2
        
        newSlicing = list(slicing)
        newSlicing[1] = slice(1,2)

        # Add some new labels for a class that hasn't been seen yet (3)        
        threeData = numpy.ndarray(slicing2shape(newSlicing), dtype=numpy.uint8)
        threeData[...] = 3
        op.Input[newSlicing] = threeData        
        expectedData = data[...]
        expectedData[newSlicing] = 3
        
        # Sanity check: Are the new labels in the data?
        assert (op.Output[...].wait() == expectedData).all()
        assert expectedData.max() == 3
        assert op.maxLabel.value == 3

        # Now erase all the 3s
        eraserData = numpy.ones(slicing2shape(newSlicing), dtype=numpy.uint8) * 100
        op.Input[newSlicing] = eraserData        
        expectedData = data[...]
        expectedData[newSlicing] = 0
        
        # The data we erased should be zeros
        assert (op.Output[...].wait() == expectedData).all()
        
        # The maximum label should be reduced, because all the 3s were removed.
        assert expectedData.max() == 2
        assert op.maxLabel.value == 2


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
