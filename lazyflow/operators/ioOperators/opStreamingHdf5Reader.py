from lazyflow.graph import Operator, InputSlot, OutputSlot
import vigra

class OpStreamingHdf5Reader(Operator):
    """
    The top-level operator for the data selection applet.
    """
    name = "OpStreamingHdf5Reader"
    category = "Reader"

    # The project hdf5 File object (already opened)
    Hdf5File = InputSlot(stype='hdf5File')

    # The internal path for project-local datasets
    InternalPath = InputSlot(stype='string')

    # Output data
    OutputImage = OutputSlot()

    def __init__(self, graph):
        super(OpStreamingHdf5Reader, self).__init__(graph=graph)

    def setupOutputs(self):
        # Read the dataset meta-info from the HDF5 dataset
        hdf5File = self.Hdf5File.value
        internalPath = self.InternalPath.value

        dataset = hdf5File[internalPath]        
        outputShape = dataset.shape

        try:
            # Read the axistags property without actually importing the data
            axistagsJson = hdf5File[internalPath].attrs['axistags'] # Throws KeyError if 'axistags' can't be found
            axistags = vigra.AxisTags.fromJSON(axistagsJson)
        except KeyError:
            # No axistags found.
            numDimensions = len(dataset.shape)
            assert numDimensions != 0, "OpStreamingHdf5Reader: Zero-dimensional datasets not supported."
            assert numDimensions != 1, "OpStreamingHdf5Reader: Support for 1-D data not yet supported"

            if numDimensions == 2:
                # Add a singleton channel dimension to the data
                outputShape = outputShape + (1,)
                axistags = vigra.AxisTags(
                    vigra.AxisInfo('x',vigra.AxisType.Space),
                    vigra.AxisInfo('y',vigra.AxisType.Space),
                    vigra.AxisInfo('c',vigra.AxisType.Channels))

            if numDimensions == 3 and dataset.shape[2] <= 3:
                axistags = vigra.AxisTags(
                    vigra.AxisInfo('x',vigra.AxisType.Space),
                    vigra.AxisInfo('y',vigra.AxisType.Space),
                    vigra.AxisInfo('c',vigra.AxisType.Channels))
            elif numDimensions == 3 and dataset.shape[2] > 3:
                # Add a singleton channel dimension to the data
                outputShape = outputShape + (1,)
                axistags = vigra.AxisTags(
                    vigra.AxisInfo('x',vigra.AxisType.Space),
                    vigra.AxisInfo('y',vigra.AxisType.Space),
                    vigra.AxisInfo('z',vigra.AxisType.Space),
                    vigra.AxisInfo('c',vigra.AxisType.Channels))
            
            if numDimensions == 4:
                axistags = vigra.AxisTags(
                    vigra.AxisInfo('x',vigra.AxisType.Space),
                    vigra.AxisInfo('y',vigra.AxisType.Space),
                    vigra.AxisInfo('z',vigra.AxisType.Space),
                    vigra.AxisInfo('c',vigra.AxisType.Channels))
            
            if numDimensions == 5:
                axistags =  vigra.AxisTags(
                    vigra.AxisInfo('t',vigra.AxisType.Time),
                    vigra.AxisInfo('x',vigra.AxisType.Space),
                    vigra.AxisInfo('y',vigra.AxisType.Space),
                    vigra.AxisInfo('z',vigra.AxisType.Space),
                    vigra.AxisInfo('c',vigra.AxisType.Channels))

        # Configure our slot meta-info
        self.OutputImage.meta.dtype = dataset.dtype
        self.OutputImage.meta.shape = outputShape
        self.OutputImage.meta.axistags = axistags

        # If the dataset specifies a datarange, add it to the slot metadata
        if 'drange' in hdf5File[internalPath].attrs:
            self.OutputImage.meta.drange = tuple( hdf5File[internalPath].attrs['drange'] )

    def execute(self, slot, subindex, roi, result):
        # Read the desired data directly from the hdf5File
        key = roi.toSlice()
        hdf5File = self.Hdf5File.value
        internalPath = self.InternalPath.value
        
        # On windows, internalPath may have backslashes, so replace them with forward slashes.
        internalPath = internalPath.replace('\\', '/')

        if len(key) > len(hdf5File[internalPath].shape):
            key = key[:len(hdf5File[internalPath].shape)]
            result[...,0] = hdf5File[internalPath][key]
        else:
            result[...] = hdf5File[internalPath][key]            

    def propagateDirty(self, slot, roi):
        if slot == self.Hdf5File or slot == self.InternalPath:
            self.OutputImage.setDirty( slice(None) )
