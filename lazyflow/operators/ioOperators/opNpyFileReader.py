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

        # We assume that a 2D array should be treated as a single-channel image
        if len(rawNumpyArray.shape) == 2:
            rawNumpyArray = rawNumpyArray.reshape(rawNumpyArray.shape + (1,))

        # For a 3D image with a large third dimension, we'll assume that
        #  it's a 3D grayscale image, not a 2D multi-channel image
        if len(rawNumpyArray.shape) == 3 and rawNumpyArray.shape[2] > 3:
            rawNumpyArray = rawNumpyArray.reshape(rawNumpyArray.shape + (1,))

        # Cast to vigra array
        self.rawVigraArray = rawNumpyArray.view(vigra.VigraArray)

        # Guess what the axistags should be based on the number of channels
        numDimensions = len(self.rawVigraArray.shape)
        assert numDimensions != 1, "OpNpyFileReader: Support for 1-D data not yet supported"
        assert numDimensions != 2, "OpNpyFileReader: BUG: 2-D was supposed to be reshaped above."
        if numDimensions == 3:
            self.rawVigraArray.axistags = vigra.AxisTags(
                vigra.AxisInfo('x',vigra.AxisType.Space),
                vigra.AxisInfo('y',vigra.AxisType.Space),
                vigra.AxisInfo('c',vigra.AxisType.Channels))
        if numDimensions == 4:
            self.rawVigraArray.axistags = vigra.AxisTags(
                vigra.AxisInfo('x',vigra.AxisType.Space),
                vigra.AxisInfo('y',vigra.AxisType.Space),
                vigra.AxisInfo('z',vigra.AxisType.Space),
                vigra.AxisInfo('c',vigra.AxisType.Channels))
        if numDimensions == 5:
            self.rawVigraArray.axistags =  vigra.AxisTags(
                vigra.AxisInfo('t',vigra.AxisType.Time),
                vigra.AxisInfo('x',vigra.AxisType.Space),
                vigra.AxisInfo('y',vigra.AxisType.Space),
                vigra.AxisInfo('z',vigra.AxisType.Space),
                vigra.AxisInfo('c',vigra.AxisType.Channels))
        
        assert numDimensions <= 5, "OpNpyFileReader: No support for data with more than 5 dimensions."

        # Our output slot should match the shape of the array on disk
        self.Output.meta.dtype = self.rawVigraArray.dtype
        self.Output.meta.axistags = copy.copy(self.rawVigraArray.axistags)
        self.Output.meta.shape = self.rawVigraArray.shape

    def execute(self, slot, roi, result):
        # Simply copy the appropriate slice of array data into the result
        key = roi.toSlice()
        result[:] = self.rawVigraArray[key]

    def propagateDirty(self, inputSlot, roi):
        if inputSlot == self.FileName:
            self.Output.setDirty( roi )
