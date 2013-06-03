import numpy
import vigra
from lazyflow.graph import Graph
from lazyflow.operators.opDenseLabelArray import OpDenseLabelArray

from lazyflow.utility.slicingtools import sl, slicing2shape

class TestOpBlockedSparseLabelArray(object):
    """
    This is a bare-bones test, adapted from the OpBlockedSparseLabelArray test.
    This test doesn't really test anything except for the most basic functionality.
    """
    def setup(self):
        graph = Graph()
        
        op = OpDenseLabelArray(graph=graph)
        arrayshape = (1,100,100,10,1)

        op.EraserLabelValue.setValue(100)

        dummyData = vigra.VigraArray(arrayshape, axistags=vigra.defaultAxistags('txyzc'))
        op.MetaInput.setValue( dummyData )

        slicing = sl[0:1, 1:15, 2:36, 3:7, 0:1]
        inDataShape = slicing2shape(slicing)
        inputData = ( 3*numpy.random.random(inDataShape) ).astype(numpy.uint8)
        op.LabelSinkInput[slicing] = inputData
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
        #assert op.maxLabel.value == inData.max()

        # nonzeroValues
        #nz = op.nonzeroValues.value
        #assert len(nz) == len(numpy.unique(inData))-1

    def testSetupTwice(self):
        """
        If one of the inputs to the label array is changed, the output should not change (including max label value!)
        """
        # Change one of the inputs, causing setupOutputs to be changed.
        
        self.op.EraserLabelValue.setValue(255)
        # Run the plain output test.
        self.testOutput()
        
    def testDeleteLabel(self):
        """
        Check behavior after deleting an entire label class from the sparse array.
        """
        op = self.op
        slicing = self.slicing
        inData = self.inData
        data = self.data

        op.DeleteLabel.setValue(1)
        outputData = op.Output[...].wait()

        # Expected: All 1s removed
        expectedOutput = numpy.where(self.data == 1, 0, self.data)
        #expectedOutput = numpy.where(expectedOutput == 2, 1, expectedOutput)
        assert (outputData[...] == expectedOutput[...]).all()
        
        #assert op.maxLabel.value == expectedOutput.max() == 1

        # delete label input resets automatically
        # assert op.deleteLabel.value == -1 # Apparently not?
    
    def testDeleteLabel2(self):
        """
        Another test to check behavior after deleting an entire label class from the sparse array.
        This one ensures that different blocks have different max label values before the delete occurs.
        """
        op = self.op
        slicing = self.slicing
        data = self.data

        #assert op.maxLabel.value == 2
        
        # Choose slicings that do NOT intersect with any of the previous data or with each other
        # The goal is to make sure that the data for each slice ends up in a separate block
        slicing1 = sl[0:1, 60:65, 0:10, 3:7, 0:1]
        slicing2 = sl[0:1, 90:95, 0:90, 3:7, 0:1]

        expectedData = self.data[...]

        labels1 = numpy.ndarray(slicing2shape(slicing1), dtype=numpy.uint8)
        labels1[...] = 1
        op.LabelSinkInput[slicing1] = labels1
        expectedData[slicing1] = labels1

        labels2 = numpy.ndarray(slicing2shape(slicing2), dtype=numpy.uint8)
        labels2[...] = 2
        op.LabelSinkInput[slicing2] = labels2
        expectedData[slicing2] = labels2

        # Sanity check:
        # Does the data contain our new labels?
        assert (op.Output[...].wait() == expectedData).all()
        assert expectedData.max() == 2
        #assert op.maxLabel.value == 2

        # Delete label 1
        op.DeleteLabel.setValue(1)
        outputData = op.Output[...].wait()

        # Expected: All 1s removed
        expectedData = numpy.where(expectedData == 1, 0, expectedData)
        #expectedData = numpy.where(expectedData == 2, 1, expectedData)
        assert (outputData[...] == expectedData[...]).all()
        
        #assert op.maxLabel.value == expectedData.max() == 1
        
    def testEraser(self):
        """
        Check that some labels can be deleted correctly from the sparse array.
        """
        op = self.op
        slicing = self.slicing
        inData = self.inData
        data = self.data

        #assert op.maxLabel.value == 2
        
        erasedSlicing = list(slicing)
        erasedSlicing[1] = slice(1,2)

        outputWithEraser = data
        outputWithEraser[erasedSlicing] = 100
        
        op.LabelSinkInput[erasedSlicing] = outputWithEraser[erasedSlicing]

        expectedOutput = outputWithEraser
        expectedOutput[erasedSlicing] = 0
        
        outputData = op.Output[...].wait()
        assert (outputData[...] == expectedOutput[...]).all()
        
        assert expectedOutput.max() == 2
        #assert op.maxLabel.value == 2
    
    def testEraseAll(self):
        """
        Test behavior when all labels of a particular class are erased.
        Note that this is not the same as deleting a label class, but should have the same effect on the output slots.
        """
        op = self.op
        slicing = self.slicing
        data = self.data

        #assert op.maxLabel.value == 2
        
        newSlicing = list(slicing)
        newSlicing[1] = slice(1,2)

        # Add some new labels for a class that hasn't been seen yet (3)        
        threeData = numpy.ndarray(slicing2shape(newSlicing), dtype=numpy.uint8)
        threeData[...] = 3
        op.LabelSinkInput[newSlicing] = threeData        
        expectedData = data[...]
        expectedData[newSlicing] = 3
        
        # Sanity check: Are the new labels in the data?
        assert (op.Output[...].wait() == expectedData).all()
        assert expectedData.max() == 3
        #assert op.maxLabel.value == 3

        # Now erase all the 3s
        eraserData = numpy.ones(slicing2shape(newSlicing), dtype=numpy.uint8) * 100
        op.LabelSinkInput[newSlicing] = eraserData
        expectedData = data[...]
        expectedData[newSlicing] = 0
        
        # The data we erased should be zeros
        assert (op.Output[...].wait() == expectedData).all()
        
        # The maximum label should be reduced, because all the 3s were removed.
        assert expectedData.max() == 2
        #assert op.maxLabel.value == 2


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
