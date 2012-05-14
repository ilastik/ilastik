from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpImageReader
from opStreamingHdf5Reader import OpStreamingHdf5Reader
from opNpyFileReader import OpNpyFileReader
from lazyflow.operators.ioOperators import OpStackLoader

import h5py
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
    WorkingDirectory = InputSlot(stype='filestring', optional=True)
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
        
        # Does this look like a relative path?
        useRelativePath = (filePath[0] != '/')
        
        if useRelativePath:
            # If using a relative path, we need both inputs before proceeding
            if not self.WorkingDirectory.connected():
                return
            else:
                # Convert this relative path into an absolute path
                filePath = self.WorkingDirectory.value + '/' + filePath
        
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
            
            # Open the h5 file in read-only mode
            h5File = h5py.File(externalPath, 'r')
            
            h5Reader = OpStreamingHdf5Reader(graph=self.graph)
            h5Reader.ProjectFile.setValue(h5File)
            
            # Can't set the internal path yet if we don't have one
            if internalPath != '':
                h5Reader.InternalPath.setValue(internalPath)
            
            self.internalOperator = h5Reader
            self.internalOutput = h5Reader.OutputImage
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

