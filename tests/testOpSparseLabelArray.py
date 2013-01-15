import numpy
from lazyflow.graph import Graph
from lazyflow.operators import OpSparseLabelArray

from lazyflow.utility.slicingtools import sl, slicing2shape

class TestOpSparseLabelArray(object):
    
    def setup(self):
        graph = Graph()
        op = OpSparseLabelArray(graph=graph)
        arrayshape = numpy.array([1,10,10,10,1])
        op.inputs["shape"].setValue( arrayshape )
        op.eraser.setValue(100)

        slicing = sl[0:1, 1:5, 2:6, 3:7, 0:1]
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
        assert nz.size == numpy.count_nonzero(inData)
        
        # nonzeroCoordinates
        # TODO: Actually validate the coordinate values, not just the number of them.
        assert self.data.nonzero()[0].size == op.nonzeroCoordinates.value.size
        
    def testDeleteLabel(self):
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
        assert op.deleteLabel.value == -1
    
    def testEraser(self):
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
        

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
 