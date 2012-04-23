from lazyflow.graph import Operator, InputSlot, OutputSlot

import vigra
import numpy
import copy

class OpNpyFileReader(Operator):
    name = "OpNpyFileReader"
    category = "Input"
    
    FileName = InputSlot(stype='filestring')
    Output = OutputSlot()

    def __init__(self, graph):
        super(OpNpyFileReader, self).__init__(graph=graph)
        self.rawVigraArray = None

    def setupOutputs(self):
        """
        Load the file specified via our input slot and present its data on the output slot.
        """
        fileName = self.FileName.value

        # Load the file in read-only "memmap" mode to avoid reading it from disk all at once.
        rawNumpyArray = numpy.load(str(fileName), 'r')

        # Cast to vigra array
        self.rawVigraArray = rawNumpyArray.view(vigra.VigraArray)
        self.rawVigraArray.axistags =  vigra.AxisTags(
            vigra.AxisInfo('t',vigra.AxisType.Time),
            vigra.AxisInfo('x',vigra.AxisType.Space),
            vigra.AxisInfo('y',vigra.AxisType.Space),
            vigra.AxisInfo('z',vigra.AxisType.Space),
            vigra.AxisInfo('c',vigra.AxisType.Channels))
 
        # Our output slot should match the shape of the array on disk
        self.Output.meta.dtype = self.rawVigraArray.dtype
        self.Output.meta.axistags = copy.copy(self.rawVigraArray.axistags)
        self.Output.meta.shape = self.rawVigraArray.shape
   
    def execute(self, slot, roi, result):
        # Simply copy the appropriate slice of array data into the result
        key = roi.toSlice()
        result[:] = self.rawVigraArray[key]

##
## Simple Test
##
if __name__ == "__main__":
    
    # Start by writing some test data to disk.
    # TODO: Use a temporary directory for this instead of the cwd.
    a = numpy.zeros((10, 11))
    for x in range(0,10):
        for y in range(0,11):
            a[x,y] = x+y
    testDataFileName = 'OpNpyFileReaderTest.npy'
    numpy.save(testDataFileName, a)
    
    # Now read back our test data using an OpNpyFileReader operator
    import lazyflow.graph
    graph = lazyflow.graph.Graph()
    npyReader = OpNpyFileReader(graph)
    npyReader.FileName.setValue(testDataFileName)

    # Read the entire file and verify the contents
    a = npyReader.Output[:].wait()
    assert a.shape == (10,11)
    for x in range(0,10):
        for y in range(0,11):
            assert a[x,y] == x+y
 
    # Clean up: Delete the test file.
    import os
    os.remove(testDataFileName)


























