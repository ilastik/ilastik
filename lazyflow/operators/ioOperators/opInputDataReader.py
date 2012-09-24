from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpImageReader, OpArrayCache
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

    h5Exts = ['h5', 'hdf5']
    npyExts = ['npy']
    imageExts = vigra.impex.listExtensions().split()
    SupportedExtensions = h5Exts + npyExts + imageExts

    # FilePath is inspected to determine data type.
    # For hdf5 files, append the internal path to the filepath,
    #  e.g. /mydir/myfile.h5/internal/path/to/dataset
    # For stacks, provide a globstring, e.g. /mydir/input*.png
    # Other types are determined via file extension
    WorkingDirectory = InputSlot(stype='filestring', optional=True)
    DefaultAxisOrder = InputSlot(stype="string", value='txyzc')
    FilePath = InputSlot(stype='filestring')
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpInputDataReader, self).__init__(*args, **kwargs)
        self.internalOperator = None
        self.internalOutput = None

    def __del__(self):
        if self.internalOperator is not None:
            self.internalOperator.disconnect()
            del self.internalOperator

    def setupOutputs(self):
        """
        Inspect the file name and instantiate and connect an internal operator of the appropriate type.
        TODO: Handle datasets of non-standard (non-5d) dimensions.
        """
        filePath = self.FilePath.value
        assert type(filePath) == str

        # Does this look like a relative path?
        useRelativePath = not os.path.isabs(filePath)

        if useRelativePath:
            # If using a relative path, we need both inputs before proceeding
            if not self.WorkingDirectory.ready():
                return
            else:
                # Convert this relative path into an absolute path
                filePath = os.path.normpath(os.path.join(self.WorkingDirectory.value, filePath))

        if self.internalOperator is not None:
            self.internalOperator.disconnect()
            del self.internalOperator
            self.internalOperator = None

        # Check for globstring
        if self.internalOperator is None and '*' in filePath:
            # Load as a stack
            stackReader = OpStackLoader(parent=self, graph=self.graph)
            stackReader.globstring.setValue(filePath)
            self.internalOperator = stackReader
            self.internalOutput = stackReader.stack

        # If we still haven't found a matching file type
        if self.internalOperator is None:
            # Check for an hdf5 extension
            h5Exts = self.h5Exts + ['ilp']
            h5Exts = ['.' + ex for ex in h5Exts]
            ext = None
            for x in h5Exts:
                if x in filePath:
                    ext = x
            if ext is not None:
                externalPath = filePath.split(ext)[0] + ext
                internalPath = filePath.split(ext)[1]

                if not os.path.exists(externalPath):
                    raise RuntimeError("Input file does not exist: " + externalPath)

                # Open the h5 file in read-only mode
                h5File = h5py.File(externalPath, 'r')

                h5Reader = OpStreamingHdf5Reader(parent=self, graph=self.graph)
                h5Reader.DefaultAxisOrder.connect( self.DefaultAxisOrder )
                h5Reader.Hdf5File.setValue(h5File)

                # Can't set the internal path yet if we don't have one
                if internalPath != '':
                    h5Reader.InternalPath.setValue(internalPath)

                self.internalOperator = h5Reader
                self.internalOutput = h5Reader.OutputImage

        # If we still haven't found a matching file type
        if self.internalOperator is None:
            fileExtension = os.path.splitext(filePath)[1].lower()
            fileExtension = fileExtension.lstrip('.') # Remove leading dot

            # Check for numpy extension
            if fileExtension in self.npyExts:
                # Create an internal operator
                npyReader = OpNpyFileReader(parent=self, graph=self.graph)
                npyReader.AxisOrder.connect( self.DefaultAxisOrder )
                npyReader.FileName.setValue(filePath)
                self.internalOperator = npyReader
                self.internalOutput = npyReader.Output
            # Check if this file type is supported by vigra.impex
            elif fileExtension in vigra.impex.listExtensions().split():
                vigraReader = OpImageReader(parent=self, graph=self.graph)
                vigraReader.Filename.setValue(filePath)

                # Cache the image instead of reading the hard disk for every access.
                imageCache = OpArrayCache(parent=self, graph=self.graph)
                imageCache.Input.connect(vigraReader.Image)
                imageCache.blockShape.setValue( vigraReader.Image.meta.shape ) # Just one block for the whole image
                assert imageCache.Output.ready()
                
                self.internalOperator = imageCache
                self.internalOutput = imageCache.Output

        assert self.internalOutput is not None, "Can't read " + filePath + " because it has an unrecognized format."

        # Directly connect our own output to the internal output
        self.Output.connect( self.internalOutput )

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here because our output is directly connected..."

    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly conncted to internal operators
        pass
