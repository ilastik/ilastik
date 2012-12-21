import tempfile
import urllib2
import numpy
import h5py
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.jsonConfig import JsonConfigSchema, AutoEval, FormattedField

RESTfulVolumeDescriptionFields = \
{
    "name" : str,
    "format" : str,
    "axes" : str,
    "shape" : list,
    "dtype" : AutoEval(),
    "origin_offset" : list,
    "url_format" : FormattedField( requiredFields=["x_start", "x_stop", "y_start", "y_stop", "z_start", "z_stop"], 
                                   optionalFields=["t_start", "t_stop", "c_start", "c_stop"] ),
    "hdf5_dataset" : str
}

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
        self._configSchema = JsonConfigSchema( RESTfulVolumeDescriptionFields )
        self._origin_offset = None
        self._urlFormat = None
        self._axes = None
        self._hdf5_dataset = None

    def setupOutputs(self):
        # Read the dataset description file
        descriptionFields = self._configSchema.parseConfigFile( self.DescriptionFilePath.value )

        assert descriptionFields.format == "hdf5", "Only hdf5 RESTful volumes are supported so far."
        
        outputShape = tuple( descriptionFields.shape )
        axes = descriptionFields.axes
        assert False not in map(lambda a: a in 'txyzc', axes), "Unknown axis type.  Known axes: txyzc  Your axes:".format(axes)

        self._datasetName = descriptionFields.hdf5_dataset
        assert self._datasetName is not None, "RESTful volume description file must specify the hdf5_dataset name"

#        # If the dataset has no channel axis, add one.
#        if 'c' not in axes:
#            outputShape += (1,)
#            axes += 'c'

        self._axes = axes
        axistags = vigra.defaultAxistags(self._axes)
        
        self._urlFormat = descriptionFields.url_format
        self._origin_offset = numpy.array(descriptionFields.origin_offset)
        self._hdf5_dataset = descriptionFields.hdf5_dataset

        self.Output.meta.shape = outputShape
        self.Output.meta.dtype = descriptionFields.dtype
        self.Output.meta.axistags = axistags

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
        hdf5RawFileObject = urllib2.urlopen( url, timeout=10 )

        # Write the data from the url out to disk (in a temporary file)
        hdf5FilePath = os.path.join(tempfile.mkdtemp(), 'cube.h5')
        with open(hdf5FilePath, 'w') as rawFileToWrite:
            rawFileToWrite.write( hdf5RawFileObject.read() )

        # Open the file we just created using h5py
        with h5py.File( hdf5FilePath, 'r' ) as hdf5File:
            result[...] = hdf5File[self._hdf5_dataset]
        return result

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.DescriptionFilePath, "Unknown input slot."
        self.Output.setDirty( slice(None) )

if __name__ == "__main__":
    testConfig = """
{
    "name" : "Bock11-level0",
    "format" : "hdf5",
    "axes" : "zxy",
    "shape" : [1239, 135424, 119808],
    "dtype" : "numpy.uint8",
    "origin_offset" : [2917, 0, 0],
    "url_format" : "http://openconnecto.me/emca/bock11/hdf5/0/{x_start},{x_stop}/{y_start},{y_stop}/{z_start},{z_stop}/",
    "hdf5_dataset" : "cube"
}
"""

    import os
    from lazyflow.graph import Graph
    
    descriptionFilePath = os.path.join(tempfile.mkdtemp(), 'desc.json')
    with open(descriptionFilePath, 'w') as descFile:
        descFile.write( testConfig )
    
    graph = Graph()
    op = OpRESTfulVolumeReader(graph=graph)
    op.DescriptionFilePath.setValue( descriptionFilePath )
    
    data = op.Output[0:100, 50000:50200, 50000:50200].wait()
    assert data.shape == ( 100, 200, 200 )

    outputDataFilePath = os.path.join(tempfile.mkdtemp(), 'testOutput.h5')
    with h5py.File( outputDataFilePath, 'w' ) as outputDataFile:
        outputDataFile.create_dataset('volume', data=data)

    print "Wrote data to {}".format(outputDataFilePath)


























































