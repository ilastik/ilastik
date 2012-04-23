from opNpyFileReader import OpNpyFileReader
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpImageReader, OpH5Reader

import vigra
import os

class OpInputDataReader(Operator):
    """
    This operator can read input data of any supported type.
    The data format is determined from the file extension.
    """
    name = "OpInputDataReader"
    category = "Input"
    
    FileName = InputSlot(stype='filestring')
    Output = OutputSlot()

    def __init__(self, graph):
        super(OpInputDataReader, self).__init__(parent=None, graph=graph)
        self.graph = graph
        self.internalOperator = None
        self.internalOutput = None

    def setupOutputs(self):
        """
        Inspect the file name and instantiate and connect an internal operator of the appropriate type.
        TODO: Handle datasets of non-standard (non-5d) dimensions.
        """
        fileName = self.FileName.value
        fileExtension = os.path.splitext(fileName)[1].lower()
        fileExtension = fileExtension.lstrip('.') # Remove leading dot
        
        # Check all supported types
        # Numpy
        if fileExtension == 'npy':
            # Create an internal operator
            npyReader = OpNpyFileReader(graph=self.graph)
            npyReader.FileName.setValue(fileName)
            self.internalOperator = npyReader
            self.internalOutput = npyReader.Output
        elif fileExtension == 'h5':
            h5Reader = OpH5Reader(graph=self.graph)
            h5Reader.Filename.setValue(fileName)
            h5Reader.hdf5Path.setValue('volume/data') # TODO: This shouldn't be hardcoded
            self.internalOperator = h5Reader
            self.internalOutput = h5Reader.Image
        # Check for vigra.impex support for this image type
        elif fileExtension in vigra.impex.listExtensions().split():
            vigraReader = OpImageReader(graph=self.graph)
            vigraReader.Filename.setValue(fileName)
            self.internalOperator = vigraReader
            self.internalOutput = vigraReader.Image

        # If we found a case that supports this type
        if self.internalOperator is not None and self.internalOutput is not None:
            self.Output.meta.dtype = self.internalOutput.meta.dtype
            self.Output.meta.shape = self.internalOutput.meta.shape
            self.Output.meta.axistags = self.internalOutput.meta.axistags
    
    def execute(self, slot, roi, result):
        # Ask our internal operator's output slot to write the result into the destination        
        # TODO: Is it really necessary to use a key (slice) here?  Or can the roi be used directly?
        key = roi.toSlice()
        self.internalOutput[key].writeInto(result).wait()

##
## Simple Test
##
if __name__ == "__main__":

    import lazyflow.graph
    import numpy

    #
    # Numpy support
    #
    
    # Start by writing some test data to disk.
    # TODO: Use a temporary directory for this instead of the cwd.
    a = numpy.zeros((10, 11))
    for x in range(0,10):
        for y in range(0,11):
            a[x,y] = x+y
    testDataFileName = 'OpInputDataReader.npy'
    numpy.save(testDataFileName, a)
    
    # Now read back our test data using an OpInputDataReader operator
    graph = lazyflow.graph.Graph()
    reader = OpInputDataReader(graph=graph)
    reader.FileName.setValue(testDataFileName)

    # Read the entire file and verify the contents
    a = reader.Output[:].wait()
    assert a.shape == (10,11)
    for x in range(0,10):
        for y in range(0,11):
            assert a[x,y] == x+y
 
    # Clean up: Delete the test file.
    os.remove(testDataFileName)

    #
    # Vigra Impex support
    #
    
    # Create a test image
    a = numpy.zeros((100,200))
    for x in range(a.shape[0]):
        for y in range(a.shape[1]):
            a[x,y] = (x+y) % 256
    testImageFileName = 'OpInputDataReader.png'
    vigra.impex.writeImage(a, testImageFileName)

    # Now read back the image using the Reader
    graph = lazyflow.graph.Graph()
    reader = OpInputDataReader(graph=graph)
    reader.FileName.setValue(testImageFileName)
    
    a = reader.Output[:].wait()
    for x in range(a.shape[0]):
        for y in range(a.shape[1]):
            assert a[x,y,0] == (x+y) % 256
                 
    # Clean up: Delete the test file.
    os.remove(testImageFileName)
    
    #
    # Hdf5 support
    #
    import h5py
    testH5FileName = 'OpInputDataReader.h5'
    f = h5py.File(testH5FileName)
    f.create_group('volume')
    shape = (1,2,3,4,5)
    f['volume'].create_dataset('data', shape)
    
    for i in range(0,shape[0]):
        for j in range(0,shape[1]):
            for k in range(0,shape[2]):
                for l in range(0,shape[3]):
                    for m in range(0,shape[4]):
                        f['volume/data'][i,j,k,l,m] = i + j + k + l + m
    
    f.close()
    
    # Now read (part of) it back
    graph = lazyflow.graph.Graph()
    reader = OpInputDataReader(graph=graph)
    reader.FileName.setValue(testH5FileName)

    a = reader.Output[0,0,:,:,:].wait()
    for l in range(0,shape[3]):
        for m in range(0,shape[4]):
            assert a[0,0,k,l,m] == k + l + m
    
    # Clean up: Delete the test file.
    os.remove(testH5FileName)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    



