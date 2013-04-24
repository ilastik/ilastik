from lazyflow.graph import Operator, InputSlot, OutputSlot

import vigra
import numpy
import copy

class OpNpyFileReader(Operator):
    name = "OpNpyFileReader"
    category = "Input"

    FileName = InputSlot(stype='filestring')

    # This slot specifies the assumed order of the data.
    # If the dataset has fewer axes than the specified axis order, 
    #  axes will be dropped in the following order: 't', 'z', 'c'
    AxisOrder = InputSlot(stype='string', value='txyzc')
    Output = OutputSlot()

    class DatasetReadError(Exception):
        pass

    def __init__(self, *args, **kwargs):
        super(OpNpyFileReader, self).__init__(*args, **kwargs)
        self.memmapFile = None
        self.rawVigraArray = None

    def setupOutputs(self):
        """
        Load the file specified via our input slot and present its data on the output slot.
        """
        fileName = self.FileName.value

        try:
            # Load the file in read-only "memmap" mode to avoid reading it from disk all at once.
            rawNumpyArray = numpy.load(str(fileName), 'r')
            self.memmapFile = rawNumpyArray._mmap
        except:
            raise OpNpyFileReader.DatasetReadError( "Unable to open numpy dataset: {}".format( fileName ) )

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
        assert numDimensions <= 5, "OpNpyFileReader: No support for data with more than 5 dimensions."

        axisorder = self.AxisOrder.value

        if numDimensions < len(axisorder):
            axisorder = axisorder.replace('t', '')
        if numDimensions < len(axisorder):
            axisorder = axisorder.replace('z', '')
        if numDimensions < len(axisorder):
            axisorder = axisorder.replace('c', '')

        assert len(axisorder) == len( self.rawVigraArray.shape ), "Mismatch between shape {} and axisorder {}".format( self.rawVigraArray.shape, axisorder )
        self.rawVigraArray.axistags = vigra.defaultAxistags(axisorder)

        # Our output slot should match the shape of the array on disk
        self.Output.meta.dtype = self.rawVigraArray.dtype
        self.Output.meta.axistags = copy.copy(self.rawVigraArray.axistags)
        self.Output.meta.shape = self.rawVigraArray.shape

    def execute(self, slot, subindex, roi, result):
        # Simply copy the appropriate slice of array data into the result
        key = roi.toSlice()
        result[:] = self.rawVigraArray[key]

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.FileName:
            self.Output.setDirty( roi )
        
    def cleanUp(self):
        if self.memmapFile is not None:
            self.memmapFile.close()
        super(OpNpyFileReader, self).cleanUp()
