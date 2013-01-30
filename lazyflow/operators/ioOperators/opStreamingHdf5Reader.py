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

    # If the dataset has no axistags attribute, this slot specifies the assumed order.
    # Must have all 5 axes, e.g. "txyzc"
    # If the dataset has only 4 axes, then 't' is dropped from the ordering.
    # If the dataset has only 4 axes, then 't' and 'z' are dropped from the ordering.
    DefaultAxisOrder = InputSlot(stype='string', value='txyzc')

    # Output data
    OutputImage = OutputSlot()
    
    class DatasetReadError(Exception):
        def __init__(self, internalPath):
            self.internalPath = internalPath
            self.msg = "Unable to open Hdf5 dataset: {}".format( internalPath )
            super(OpStreamingHdf5Reader.DatasetReadError, self).__init__( self.msg )

    def __init__(self, *args, **kwargs):
        super(OpStreamingHdf5Reader, self).__init__(*args, **kwargs)
        self._hdf5File = None

    def setupOutputs(self):
        if self._hdf5File is not None:
            self._hdf5File.close()
        
        # Read the dataset meta-info from the HDF5 dataset
        self._hdf5File = self.Hdf5File.value
        internalPath = self.InternalPath.value

        if internalPath not in self._hdf5File:
            raise OpStreamingHdf5Reader.DatasetReadError(internalPath)

        dataset = self._hdf5File[internalPath]
        outputShape = dataset.shape

        try:
            # Read the axistags property without actually importing the data
            axistagsJson = self._hdf5File[internalPath].attrs['axistags'] # Throws KeyError if 'axistags' can't be found
            axistags = vigra.AxisTags.fromJSON(axistagsJson)
        except KeyError:
            axisorder = self.DefaultAxisOrder.value
            for a in 'txyzc':
                assert a in axisorder

            # No axistags found.
            numDimensions = len(dataset.shape)
            assert numDimensions != 0, "OpStreamingHdf5Reader: Zero-dimensional datasets not supported."
            assert numDimensions != 1, "OpStreamingHdf5Reader: Support for 1-D data not yet supported"

            if numDimensions == 2 or (numDimensions == 3 and dataset.shape[2] > 3):
                # Add a singleton channel dimension to the data
                outputShape = outputShape + (1,)
                numDimensions = len(outputShape)

            if numDimensions < 5:
                axisorder = axisorder.replace('t', '')
            if numDimensions < 4:
                axisorder = axisorder.replace('z', '')

            axistags = vigra.defaultAxistags(axisorder)

        # Configure our slot meta-info
        self.OutputImage.meta.dtype = dataset.dtype
        self.OutputImage.meta.shape = outputShape
        self.OutputImage.meta.axistags = axistags

        # If the dataset specifies a datarange, add it to the slot metadata
        if 'drange' in self._hdf5File[internalPath].attrs:
            self.OutputImage.meta.drange = tuple( self._hdf5File[internalPath].attrs['drange'] )

    def execute(self, slot, subindex, roi, result):
        assert self._hdf5File is not None
        # Read the desired data directly from the hdf5File
        key = roi.toSlice()
        hdf5File = self._hdf5File
        internalPath = self.InternalPath.value
        
        # On windows, internalPath may have backslashes, so replace them with forward slashes.
        # Ulli: this is not the right place to fix this -- we need to do it during filename analysis
        # internalPath = internalPath.replace('\\', '/')

        if len(key) > len(hdf5File[internalPath].shape):
            key = key[:len(hdf5File[internalPath].shape)]
            result[...,0] = hdf5File[internalPath][key]
        else:
            result[...] = hdf5File[internalPath][key]

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Hdf5File or slot == self.InternalPath:
            self.OutputImage.setDirty( slice(None) )
