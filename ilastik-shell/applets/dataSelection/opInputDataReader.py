from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpImageReader, OpH5Reader
from opNpyFileReader import OpNpyFileReader
from lazyflow.operators.ioOperators import OpStackLoader

import vigra
import os

class OpInputDataReader(Operator):
    """
    This operator can read input data of any supported type.
    The data format is determined from the file extension.
    """
    name = "OpInputDataReader"
    category = "Input"
    
    # FilePath is inspected to determine data type.
    # For hdf5 files, append the internal path to the filepath,
    #  e.g. /mydir/myfile.h5/internal/path/to/dataset
    # For stacks, provide a globstring, e.g. /mydir/input*.png
    # Other types are determined via file extension
    FilePath = InputSlot(stype='filestring')
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
        filePath = self.FilePath.value
        assert type(filePath) == str
        
                
        # Check for globstring
        if '*' in filePath:
            # Load as a stack
            stackReader = OpStackLoader(graph=self.graph)
            stackReader.globstring.setValue(filePath)
            self.internalOperator = stackReader
            self.internalOutput = stackReader.stack
        # Check for hdf5
        elif '.h5' in filePath or '.hdf5' in filePath:
            ext = '.hdf5'
            if '.h5' in filePath:
                ext = '.h5'
            externalPath = filePath.split(ext)[0] + ext
            internalPath = filePath.split(ext)[1]
            
            h5Reader = OpH5Reader(graph=self.graph)
            h5Reader.Filename.setValue(externalPath)
            h5Reader.hdf5Path.setValue(internalPath)
            self.internalOperator = h5Reader
            self.internalOutput = h5Reader.Image
        else:
            fileExtension = os.path.splitext(filePath)[1].lower()
            fileExtension = fileExtension.lstrip('.') # Remove leading dot

            # Check for numpy
            if fileExtension == 'npy':
                # Create an internal operator
                npyReader = OpNpyFileReader(graph=self.graph)
                npyReader.FileName.setValue(filePath)
                self.internalOperator = npyReader
                self.internalOutput = npyReader.Output
            # Check for vigra.impex support for this image type
            elif fileExtension in vigra.impex.listExtensions().split():
                vigraReader = OpImageReader(graph=self.graph)
                vigraReader.Filename.setValue(filePath)
                self.internalOperator = vigraReader
                self.internalOutput = vigraReader.Image

        assert self.internalOutput is not None, "Can't read " + filePath + " because it has an unrecognized format."
        
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

    # Start by writing some test data to disk in various formats
    # TODO: Use a temporary directory for this instead of the cwd.
    
    testNpyDataFileName = 'test.npy'
    testImageFileName = 'test.png'
    testH5FileName = 'test.h5'

    # Clean up: Remove the test data files we created last time (just in case)
    for f in [testNpyDataFileName, testImageFileName, testH5FileName]:
        try:
            os.remove(f)
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

    # Now read back our test data using an OpInputDataReader operator
    graph = lazyflow.graph.Graph()
    npyReader = OpInputDataReader(graph=graph)
    npyReader.FilePath.setValue(testNpyDataFileName)

    # Read the entire NPY file and verify the contents
    npyData = npyReader.Output[:].wait()
    assert npyData.shape == (10,11,1)
    for x in range(0,10):
        for y in range(0,11):
            assert npyData[x,y] == x+y
 
    # Read the entire PNG file and verify the contents
    pngReader = OpInputDataReader(graph=graph)
    pngReader.FilePath.setValue(testImageFileName)
    pngData = pngReader.Output[:].wait()
    for x in range(pngData.shape[0]):
        for y in range(pngData.shape[1]):
            assert pngData[x,y,0] == (x+y) % 256
                 
    # Read the entire HDF5 file and verify the contents
    h5Reader = OpInputDataReader(graph=graph)
    h5Reader.FilePath.setValue(testH5FileName + '/volume/data') # Append internal path

    # Grab a section of the h5 data
    h5Data = h5Reader.Output[0,0,:,:,:].wait()
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
    
    
       
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    



