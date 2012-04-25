from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot

from opMultiInputDataReader import OpMultiInputDataReader
from lazyflow.operators.obsolete.vigraOperators import OpGrayscaleInverter, OpRgbToGraysacle

class OpDataSelection(Operator):
    """
    The top-level operator for the data selection applet.
    """
    name = "OpDataSelection"
    category = "Top-level"

    # Input data
    FileNames = MultiInputSlot(stype='filestring')
    
    # Dataset Guids
    
    # Input formatting options (indexes MUST match the FileNames input)
    InvertFlags = MultiInputSlot(stype='bool')
    GrayConvertFlags = MultiInputSlot(stype='bool')

    # Output data
    OutputImages = MultiOutputSlot()
    
    def __init__(self, graph):
        super(OpDataSelection, self).__init__(graph=graph)

        # Create an internal operator for reading data
        self.multiReader = OpMultiInputDataReader(graph=graph)        

        # FIXME: MultiInputSlot-to-MultiInputSlot clones don't work, so we can't make this connection.
        # Instead, we copy the slot values manually (below)
        # self.multiReader.FileNames.connect(self.FileNames)
        
        # Each output subslot comes from a different operator.
        # Keep track of the subslot outputs in this list.
        self.providerSlots = []
        
    def setupOutputs(self):
        # We can't do anything unless all input slots are the same length
        if len(self.FileNames) == len(self.InvertFlags) == len(self.GrayConvertFlags):
            # Ensure the proper number of outputs
            self.OutputImages.resize(len(self.FileNames))
    
            # Rebuild the list of provider slots from scratch
            self.providerSlots = []

            # FIXME: MultiInputSlot-to-MultiInputSlot clones don't work, so we have to set the value manually...
            self.multiReader.FileNames.resize( len(self.FileNames) )
            for i in range(0, len(self.FileNames)):
                self.multiReader.FileNames[i].setValue(self.FileNames[i].value)
    
            for i in range(len(self.FileNames)):
                
                # By default, our output is the raw multi-reader output
                providerSlot = self.multiReader.Outputs[i]
    
                # If the user wants to invert the image,
                #  insert an intermediate inversion operator on this subslot
                if self.InvertFlags[i].value:
                    inverter = OpGrayscaleInverter(graph=self.graph)
                    inverter.input.connect(providerSlot)
                    providerSlot = inverter.output
                
                # If the user wants to convert to grayscale,
                #  insert an intermediate rgb-to-grayscale operator on this subslot
                if self.GrayConvertFlags[i].value:
                    converter = OpRgbToGraysacle(graph=self.graph)
                    converter.input.connect(providerSlot)
                    providerSlot = converter.output
                
                # Remember which operator is providing the output on this subslot
                self.providerSlots.append(providerSlot)
    
                # Copy the metadata from the provider we ended up with
                self.OutputImages[i].meta.dtype = providerSlot.meta.dtype
                self.OutputImages[i].meta.shape = providerSlot.meta.shape
                self.OutputImages[i].meta.axistags = providerSlot.meta.axistags

    def getSubOutSlot(self, slots, indexes, key, result):
        # Request the output from the appropriate internal operator output.
        req = self.providerSlots[indexes[0]][key].writeInto(result)
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
    
    a = numpy.zeros((100,200,3))
    for x in range(a.shape[0]):
        for y in range(a.shape[1]):
            for c in range(a.shape[2]):
                a[x,y,c] = (x+y) % 256
    testPngFileName = 'testImage2.png'
    vigra.impex.writeImage(a, testPngFileName)

    # Now read back our test data using an OpInputDataReader operator
    graph = lazyflow.graph.Graph()
    reader = OpDataSelection(graph=graph)
    reader.FileNames.setValues([testNpyFileName, testPngFileName,  # Raw
                                testNpyFileName, testPngFileName,  # Inverted
                                testNpyFileName, testPngFileName,  # Rgb-to-Gray
                                testNpyFileName, testPngFileName]) # Inverted AND Rgb-to-gray
    reader.InvertFlags.setValues([False, False,
                                  True,  True,
                                  False, False,
                                  True,  True])
    reader.GrayConvertFlags.setValues([False, False,
                                       False, False,
                                       True,  True,
                                       True,  True])

    # Read the test files using the data selection operator and verify the contents
    npyData = reader.OutputImages[0][...].wait()
    pngData = reader.OutputImages[1][...].wait()
    
    invertedNpyData = reader.OutputImages[2][...].wait()
    invertedPngData = reader.OutputImages[3][...].wait()

    grayscaleNpyData = reader.OutputImages[4][...].wait()
    grayscalePngData = reader.OutputImages[5][...].wait()

    invertedGrayscaleNpyData = reader.OutputImages[6][...].wait()
    invertedGrayscalePngData = reader.OutputImages[7][...].wait()

    # Check raw images
    assert npyData.shape == (10,11,1)
    for x in range(npyData.shape[0]):
        for y in range(npyData.shape[1]):
            assert npyData[x,y,0] == x+y
 
    assert pngData.shape == (100, 200, 3)
    for x in range(pngData.shape[0]):
        for y in range(pngData.shape[1]):
            for c in range(a.shape[2]):
                assert pngData[x,y,c] == (x+y) % 256

    # Check inverted images
    assert invertedNpyData.shape == npyData.shape
    for x in range(invertedNpyData.shape[0]):
        for y in range(invertedNpyData.shape[1]):
            assert invertedNpyData[x,y,0] == 255-npyData[x,y]
 
    assert invertedPngData.shape == pngData.shape
    for x in range(invertedPngData.shape[0]):
        for y in range(pngData.shape[1]):
            for c in range(a.shape[2]):
                assert invertedPngData[x,y,c] == 255-pngData[x,y,0]

    # Check grayscale conversion 
    assert grayscalePngData.shape == (100, 200, 1)
    for x in range(grayscalePngData.shape[0]):
        for y in range(grayscalePngData.shape[1]):
            # (See formula in OpRgbToGrayscale)
            assert grayscalePngData[x,y,0] == int(numpy.round(  0.299*pngData[x,y,0]
                                                              + 0.587*pngData[x,y,1] 
                                                              + 0.114*pngData[x,y,2] ))

    # Check inverted grayscale conversion 
    assert invertedGrayscalePngData.shape == (100, 200, 1)
    for x in range(invertedGrayscalePngData.shape[0]):
        for y in range(invertedGrayscalePngData.shape[1]):
            # (See formula in OpRgbToGrayscale)
            assert invertedGrayscalePngData[x,y,0] == int(numpy.round(  0.299*invertedPngData[x,y,0]
                                                                      + 0.587*invertedPngData[x,y,1] 
                                                                      + 0.114*invertedPngData[x,y,2] ))

    # Clean up: Delete the test files.
    os.remove(testNpyFileName)
    os.remove(testPngFileName)

































