from opNpyFileReader import OpNpyFileReader
from lazyflow.graph import Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot
from lazyflow.operators import OpImageReader, OpH5Reader
from lazyflow.operators.ioOperators import OpStackLoader

import vigra
import os

class OpMultiInputDataReader(Operator):
    """
    This operator can read input data of any supported type.
    The data format is determined from the file extension.
    """
    name = "OpMultiInputDataReader"
    category = "Input"
    
    FileNames = MultiInputSlot(stype='filestring') # Also used as a globstring input! (for stacks)
    Outputs = MultiOutputSlot()

    def __init__(self, graph):
        super(OpMultiInputDataReader, self).__init__(parent=None, graph=graph)
        self.graph = graph
        self.internalOperators = []
        self.internalOutputs = []

    def setupOutputs(self):
        """
        Inspect the file name and instantiate and connect an internal operator of the appropriate type.
        TODO: Handle datasets of non-standard (non-5d) dimensions.
        """
        
        # Rebuild our list of internal operators
        self.internalOperators = []
        self.internalOutputs = []

        # Ensure the proper number of outputs
        self.Outputs.resize(len(self.FileNames))

        for i in range(0, len(self.FileNames)):
            fileName = self.FileNames[i].value
            assert type(fileName) == str
            
            fileExtension = os.path.splitext(fileName)[1].lower()
            fileExtension = fileExtension.lstrip('.') # Remove leading dot
            
            newOperator = None
            newOutput = None
            # Check all supported types
            # Stack (filename is the globstring)
            if '*' in fileName:
                stackReader = OpStackLoader(graph=self.graph)
                stackReader.globstring.setValue(fileName)
                newOperator = stackReader
                newOutput = stackReader.stack
            # Numpy
            elif fileExtension == 'npy':
                npyReader = OpNpyFileReader(graph=self.graph)
                npyReader.FileName.setValue(fileName)
                newOperator = npyReader
                newOutput = npyReader.Output
            # HDF5
            elif fileExtension == 'h5':
                h5Reader = OpH5Reader(graph=self.graph)
                h5Reader.Filename.setValue(fileName)
                h5Reader.hdf5Path.setValue('volume/data') # TODO: This shouldn't be hardcoded
                newOperator = h5Reader
                newOutput = h5Reader.Image
            # Check for vigra.impex support for this image type
            elif fileExtension in vigra.impex.listExtensions().split():
                vigraReader = OpImageReader(graph=self.graph)
                vigraReader.Filename.setValue(fileName)
                newOperator = vigraReader
                newOutput = vigraReader.Image
            else:
                error = "OpMultiInputDataReader doesn't support extension: ." + fileExtension 
                raise RuntimeError(error)
    
            self.internalOperators.append(newOperator)
            self.internalOutputs.append(newOutput)
            self.Outputs[i].meta.dtype = newOutput.meta.dtype
            self.Outputs[i].meta.shape = newOutput.meta.shape
            self.Outputs[i].meta.axistags = newOutput.meta.axistags
    
    def getSubOutSlot(self, slots, indexes, key, result):
        req = self.internalOutputs[indexes[0]][key].writeInto(result)
        res = req.wait()
        return res

##
## Simple Test
##
if __name__ == "__main__":

    import lazyflow.graph
    import numpy

    #
    # Numpy support
    #
    
    # Start by writing some test data to disk in various formats
    # TODO: Use a temporary directory for this instead of the cwd.
    
    testNpyDataFileName = 'OpInputDataReader.npy'
    testImageFileName = 'OpInputDataReader.png'
    testH5FileName = 'OpInputDataReader.h5'

    # Clean up: Remove the test data files we created last time (just in case)
    try:    
        os.remove(testNpyDataFileName)
        os.remove(testImageFileName)
        os.remove(testH5FileName)
    except:
        pass

    # Create Numpy test data
    a = numpy.zeros((10, 11))
    for x in range(0,10):
        for y in range(0,11):
            a[x,y] = x+y
    numpy.save(testNpyDataFileName, a)
    
    # Create PNG test data
    a = numpy.zeros((100,200))
    for x in range(a.shape[0]):
        for y in range(a.shape[1]):
            a[x,y] = (x+y) % 256
    vigra.impex.writeImage(a, testImageFileName)

    # Create HDF5 test data
    import h5py
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

    # Now read back our test data using an OpMultiInputDataReader operator
    graph = lazyflow.graph.Graph()
    reader = OpMultiInputDataReader(graph=graph)
    reader.FileNames.setValues([testNpyDataFileName, testImageFileName, testH5FileName])

    # Read the entire file and verify the contents
    npyData = reader.Outputs[0][:].wait()
    assert npyData.shape == (10,11)
    for x in range(0,10):
        for y in range(0,11):
            assert npyData[x,y] == x+y
 
    pngData = reader.Outputs[1][:].wait()
    for x in range(pngData.shape[0]):
        for y in range(pngData.shape[1]):
            assert pngData[x,y,0] == (x+y) % 256
                 
    # Grab a section of the h5 data
    h5Data = reader.Outputs[2][0,0,:,:,:].wait()
    assert h5Data.shape == (1,1,3,4,5)
    # (Just check part of the data)
    for k in range(0,shape[2]):
        for l in range(0,shape[3]):
            for m in range(0,shape[4]):
                assert h5Data[0,0,k,l,m] == k + l + m

    # Clean up: Remove the test data files we created    
    os.remove(testNpyDataFileName)
    os.remove(testImageFileName)
    os.remove(testH5FileName)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    



