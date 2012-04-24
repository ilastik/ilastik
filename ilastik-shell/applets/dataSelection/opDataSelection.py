from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot

from opInputDataReader import OpInputDataReader

class OpDataSelection(Operator):
    """
    The top-level operator for the data selection applet.
    """
    name = "OpDataSelection"
    category = "Top-level"

    # Input data (typically from our own gui, not from others)
    FileNames = MultiInputSlot(stype='filestring')

    # Output data
    OutputImages = MultiOutputSlot()
    
    def __init__(self, graph):
        super(OpDataSelection, self).__init__(graph=graph)
        self.graph = graph
        
        self.readers = OpInputDataReader(self.graph)
        
        # Connect our filename MULTI-input slot to our internal reader operator, 
        #  which will cause the internal operator to be promoted.
        # self.readers is now a *wrapped* operator with MULTI-input and MULTI-output
        self.readers.FileName.connect( self.FileNames )
        
    def setupOutputs(self):
        for i in range(len(self.readers.FileName)):
            self.OutputImages[i].meta.dtype = self.readers.Output[i].dtype
            self.OutputImages[i].meta.shape = self.readers.Output[i].shape
            self.OutputImages[i].meta.axistags = self.readers.Output[i].axistags

    def getSubOutSlot(self, slots, indexes, key, result):
        req = self.readers.Output[indexes[0]][key].writeInto(result)
        res = req.wait()
        return res

if __name__ == "__main__":
    import os
    import numpy
    import vigra
    import lazyflow

    # Create a couple test images of different types
    # TODO: Use a temporary directory for this instead of the cwd.
    a = numpy.zeros((10, 11))
    for x in range(0,10):
        for y in range(0,11):
            a[x,y] = x+y
    testNpyFileName = 'testImage1.npy'
    numpy.save(testNpyFileName, a)
    
    a = numpy.zeros((100,200))
    for x in range(a.shape[0]):
        for y in range(a.shape[1]):
            a[x,y] = (x+y) % 256
    testPngFileName = 'testImage2.png'
    vigra.impex.writeImage(a, testPngFileName)

    # Now read back our test data using an OpInputDataReader operator
    graph = lazyflow.graph.Graph()
    reader = OpDataSelection(graph=graph)
    reader.FileNames.setValues([testNpyFileName, testPngFileName])

    # Read the test files using the data selection operator and verify the contents
    npyData = reader.OutputImages[0][:].wait()
    pngData = reader.Output[:].wait()

    assert npyData.shape == (10,11)
    for x in range(0,10):
        for y in range(0,11):
            assert npyData[x,y] == x+y
 
    assert pngData.shape == (100, 200, 1)
    for x in range(pngData.shape[0]):
        for y in range(pngData.shape[1]):
            assert pngData[x,y,0] == (x+y) % 256

    # Clean up: Delete the test files.
    os.remove(testNpyFileName)
    os.remove(testPngFileName)
    