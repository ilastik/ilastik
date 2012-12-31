import os
import tempfile
import urllib2
import numpy
import h5py
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.RESTfulVolumeDescription import parseRESTfulVolumeDescriptionFile
import logging
logger = logging.getLogger(__name__)

class OpRESTfulVolumeReader(Operator):
    """
    An operator to retrieve hdf5 volumes from a remote server that provides a RESTful interface.
    The operator requires a LOCAL json config file that describes the remote dataset and interface.
    """
    name = "OpRESTfulVolumeReader"

    DescriptionFilePath = InputSlot(stype='filestring')
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpRESTfulVolumeReader, self).__init__(*args, **kwargs)
        self._origin_offset = None
        self._urlFormat = None
        self._axes = None
        self._hdf5_dataset = None

    def setupOutputs(self):
        # Read the dataset description file
        descriptionFields = parseRESTfulVolumeDescriptionFile( self.DescriptionFilePath.value )

        # Check for errors in the description file
        axes = descriptionFields.axes 
        assert False not in map(lambda a: a in 'txyzc', axes), "Unknown axis type.  Known axes: txyzc  Your axes:".format(axes)
        assert descriptionFields.format == "hdf5", "Only hdf5 RESTful volumes are supported so far."
        assert descriptionFields.hdf5_dataset is not None, "RESTful volume description file must specify the hdf5_dataset name"

        # Save description file members
        self._axes = descriptionFields.axes
        self._urlFormat = descriptionFields.url_format
        self._origin_offset = numpy.array(descriptionFields.origin_offset)
        self._hdf5_dataset = descriptionFields.hdf5_dataset

        outputShape = tuple( descriptionFields.shape )

        # If the dataset has no channel axis, add one.
        if 'c' not in axes:
            outputShape += (1,)
            self._axes += 'c'
            self._origin_offset = numpy.array( list(self._origin_offset) + [0] )

        self.Output.meta.shape = outputShape
        self.Output.meta.dtype = descriptionFields.dtype
        self.Output.meta.axistags = vigra.defaultAxistags(self._axes)

    def execute(self, slot, subindex, roi, result):
        accessStart = numpy.array(roi.start)
        accessStart += self._origin_offset
        accessStop = numpy.array(roi.stop)
        accessStop += self._origin_offset

        axistags = self.Output.meta.axistags
        RESTArgs = {}
        for axisindex, tag in enumerate(axistags):
            startKey = '{}_start'.format(tag.key)
            stopKey = '{}_stop'.format(tag.key)
            RESTArgs[startKey] = accessStart[ axisindex ]
            RESTArgs[stopKey] = accessStop[ axisindex ]

        # Open the url
        url = self._urlFormat.format( **RESTArgs )
        logger.debug( "Downloading region {}..{}: {}".format(roi.start, roi.stop, url) )
        hdf5RawFileObject = urllib2.urlopen( url, timeout=10 )

        # Write the data from the url out to disk (in a temporary file)
        hdf5FilePath = os.path.join(tempfile.mkdtemp(), 'cube.h5')
        logger.debug( "Saving temporary file: {}".format( hdf5FilePath ) )
        with open(hdf5FilePath, 'w') as rawFileToWrite:
            rawFileToWrite.write( hdf5RawFileObject.read() )

        # Open the file we just created using h5py
        with h5py.File( hdf5FilePath, 'r' ) as hdf5File:
            dataset = hdf5File[self._hdf5_dataset]
            if len(result.shape) > len(dataset.shape):
                # We appended a channel axis to Output, but the dataset doesn't have that.
                result[...,0] = dataset[...]
            else:
                result[...] = dataset[...]
        return result

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.DescriptionFilePath, "Unknown input slot."
        self.Output.setDirty( slice(None) )

if __name__ == "__main__":
    testConfig0 = """
{
    "_schema_name" : "RESTful-volume-description",
    "_schema_version" : 1.0,

    "name" : "Bock11-level0",
    "format" : "hdf5",
    "axes" : "zyx",
    "##NOTE":"The first z-slice of the bock dataset is 2917, so the origin_offset must be at least 2917",
    "origin_offset" : [2917, 50000, 50000],
    "###shape" : [1239, 135424, 119808],
    "shape" : [1239, 10000, 10000],
    "dtype" : "numpy.uint8",
    "url_format" : "http://openconnecto.me/emca/bock11/hdf5/0/{x_start},{x_stop}/{y_start},{y_stop}/{z_start},{z_stop}/",
    "hdf5_dataset" : "cube"
}
"""

    testConfig4 = """
{
    "_schema_name" : "RESTful-volume-description",
    "_schema_version" : 1.0,

    "name" : "Bock11-level4",
    "format" : "hdf5",
    "axes" : "zyx",
    "##NOTE":"The first z-slice of the bock dataset is 2917, so the origin_offset must be at least 2917",
    "origin_offset" : [2917, 0, 0],
    "shape" : [1239, 8704, 7680],
    "dtype" : "numpy.uint8",
    "url_format" : "http://openconnecto.me/emca/bock11/hdf5/4/{x_start},{x_stop}/{y_start},{y_stop}/{z_start},{z_stop}/",
    "hdf5_dataset" : "cube"
}
"""

    from lazyflow.graph import Graph

    import sys    
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    
    descriptionFilePath = os.path.join(tempfile.mkdtemp(), 'desc.json')
    with open(descriptionFilePath, 'w') as descFile:
        descFile.write( testConfig4 )
    
    graph = Graph()
    op = OpRESTfulVolumeReader(graph=graph)
    op.DescriptionFilePath.setValue( descriptionFilePath )
    
    #data = op.Output[0:100, 50000:50200, 50000:50200].wait()
    data = op.Output[0:100, 4000:4200, 4000:4200].wait()
    
    # We expect a channel dimension to be added automatically...
    assert data.shape == ( 100, 200, 200, 1 )

    outputDataFilePath = os.path.join(tempfile.mkdtemp(), 'testOutput.h5')
    with h5py.File( outputDataFilePath, 'w' ) as outputDataFile:
        outputDataFile.create_dataset('volume', data=data)

    print "Wrote data to {}".format(outputDataFilePath)


























































