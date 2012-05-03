from lazyflow.graph import Operator, InputSlot, OutputSlot
import vigra

class OpProjectDatasetReader(Operator):
    """
    The top-level operator for the data selection applet.
    """
    name = "OpProjectDatasetReader"
    category = "Reader"
    
    # The project hdf5 File object (already opened)
    ProjectFile = InputSlot(stype='hdf5File')

    # The internal path for project-local datasets
    InternalPath = InputSlot(stype='string')

    # Output data
    OutputImage = OutputSlot()
    
    def __init__(self, graph):
        super(OpProjectDatasetReader, self).__init__(graph=graph)

    def setupOutputs(self):
        # Read the dataset meta-info from the HDF5 dataset
        hdf5File = self.ProjectFile.value
        internalPath = self.InternalPath.value

        dataset = hdf5File[internalPath]
        self.axisorder = None
        
        try:
            # Read the axistags property without actually importing the data
            axistagsJson = hdf5File[internalPath].attrs['axistags'] # Throws KeyError if 'axistags' can't be found
            self.serializedAxistags = vigra.AxisTags.fromJSON(axistagsJson)
        except KeyError:
            # No axistags found.
            numDimensions = len(dataset.shape) 
            assert numDimensions != 1, "OpProjectDatasetReader: Support for 1-D data not yet supported"
            assert numDimensions != 2, "OpProjectDatasetReader: BUG: 2-D was supposed to be reshaped above."
            if numDimensions == 3:
                axistags = vigra.AxisTags(
                    vigra.AxisInfo('x',vigra.AxisType.Space),
                    vigra.AxisInfo('y',vigra.AxisType.Space),
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
            self.serializedAxistags = axistags

        try:
            # Recreate the original axis order
            self.axisorder = hdf5File[internalPath].attrs['axisorder'].split('-')
            shape = [dataset.shape[self.serializedAxistags.index(key)] for key in self.axisorder]
            axistags = vigra.AxisTags(*[self.serializedAxistags[key] for key in self.axisorder])
        except KeyError:
            # Use the order as we read it from disk
            shape = dataset.shape

        # Configure our slot meta-info
        self.OutputImage.meta.dtype = dataset.dtype
        self.OutputImage.meta.shape = tuple(shape)
        self.OutputImage.meta.axistags = axistags

    def execute(self, slot, roi, result):
        # Read the desired data directly from the hdf5File
        key = roi.toSlice()
        hdf5File = self.ProjectFile.value
        internalPath = self.InternalPath.value
        if self.axisorder is not None:
            # Reorder our key so we can use it to access the serialized data
            axistags = self.OutputImage.meta.axistags
            serializedAxisOrder = [axis.key for axis in self.serializedAxistags]
            diskKey = tuple([key[axistags.index(axiskey)] for axiskey in serializedAxisOrder])
            
            # Access the data
            data = hdf5File[internalPath][diskKey]

            # View it as a vigra array so we can reorder it according to the axistags
            vdata = data.view(vigra.VigraArray)
            vdata.axistags = self.serializedAxistags
            vdata = vdata.withAxes( *self.axisorder )
            result[...] = vdata
        else:
            data = hdf5File[internalPath][key]
            result[...] = data

# TODO: Put this in a unit test
if __name__ == "__main__":
    from lazyflow.graph import Graph
    import h5py
    import numpy
    import os
    
    graph = Graph()
    op = OpProjectDatasetReader(graph)
    
    # Create a test dataset
    datashape = (1,2,3,4,5)
    data = numpy.zeros(datashape, dtype=numpy.float32)
    for i in range(datashape[0]):
        for j in range(datashape[1]):
            for k in range(datashape[2]):
                for l in range(datashape[3]):
                    for m in range(datashape[4]):
                        data[i,j,k,l,m] = i+j+k+l+m
    testDataFileName = 'test.h5'

    # Clean up: Delete the test file from any previous run
    try:
        os.remove(testDataFileName)
    except:
        pass

    # Write the dataset to an hdf5 file
    f = h5py.File(testDataFileName)
    f.create_group('volume')
    f['volume'].create_dataset('data', data=data)

    # Write it again, this time with weird axistags
    vdata = data.view(vigra.VigraArray)
    vdata.axistags = vigra.AxisTags(
        vigra.AxisInfo('x',vigra.AxisType.Space),
        vigra.AxisInfo('y',vigra.AxisType.Space),
        vigra.AxisInfo('z',vigra.AxisType.Space),
        vigra.AxisInfo('c',vigra.AxisType.Channels),
        vigra.AxisInfo('t',vigra.AxisType.Time))
    vigra.impex.writeHDF5(vdata, f, 'volume/vdata')
    f['volume/vdata'].attrs['axisorder'] = 'x-y-z-c-t'

    # Read the data with an operator
    op.ProjectFile.setValue(f)
    op.InternalPath.setValue('volume/data')
 
    assert op.OutputImage.meta.shape == datashape
    assert op.OutputImage[0,1,2,1,0].wait() == 4
    
    # Read the tagged data
    op.InternalPath.setValue('volume/vdata')
    
    # Note axis re-ordering
    #assert op.OutputImage[0,2,1,0,1].wait() == 4
    assert op.OutputImage.meta.shape == datashape
    assert op.OutputImage[0,1,2,1,0].wait() == 4

    # Clean up: Delete the test file.
    import os
    os.remove(testDataFileName)
